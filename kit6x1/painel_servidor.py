"""Servidor local do painel: páginas do pacote, arquivos da rodada e formulário de entrada."""
from __future__ import annotations

import json
import os
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .modelos import EntradaInvalida, carregar_entrada
from .status import StatusWriter

PASTA_PAINEL = Path(__file__).parent / "painel"
ESTATICOS = {"index.html", "calendario.html", "entrada.html"}
DA_RODADA = {"status.json", "resultado.json"}
LIMITE_CORPO = 1_000_000
TIPOS = {".html": "text/html; charset=utf-8", ".json": "application/json; charset=utf-8"}


def pasta_ponteiro() -> Path:
    return Path(os.environ.get("KIT6X1_HOME", Path.home() / ".kit6x1"))


def _handler(pasta_rodada: Path) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args) -> None:
            return None

        def _enviar(self, codigo: int, corpo: bytes, tipo: str) -> None:
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def _json(self, codigo: int, dados: dict) -> None:
            self._enviar(codigo, json.dumps(dados, ensure_ascii=False).encode(), TIPOS[".json"])

        def _hosts_permitidos(self) -> set[str]:
            porta = self.server.server_address[1]
            return {f"127.0.0.1:{porta}", f"localhost:{porta}"}

        def do_GET(self) -> None:
            if self.headers.get("Host") not in self._hosts_permitidos():
                return self._json(403, {"ok": False, "erros": ["Host não permitido."]})
            nome = self.path.split("?", 1)[0].lstrip("/") or "index.html"
            if nome in ESTATICOS:
                arq = PASTA_PAINEL / nome
            elif nome in DA_RODADA:
                arq = pasta_rodada / nome
            else:
                return self._json(404, {"erro": "não encontrado"})
            if not arq.is_file():
                return self._json(404, {"erro": "não encontrado"})
            self._enviar(200, arq.read_bytes(), TIPOS[arq.suffix])

        def _origem_permitida(self) -> bool:
            hosts = self._hosts_permitidos()
            if self.headers.get("Host") not in hosts:
                return False
            origem = self.headers.get("Origin")
            return origem is None or origem in {f"http://{h}" for h in hosts}

        def do_POST(self) -> None:
            if self.path.split("?", 1)[0] != "/entrada":
                return self._json(404, {"erro": "não encontrado"})
            if not self._origem_permitida():
                return self._json(403, {"ok": False, "erros": ["Origem não permitida."]})
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self._json(415, {"ok": False, "erros": ["Envie os dados como application/json."]})
            try:
                n = int(self.headers.get("Content-Length", ""))
                if n < 0:
                    raise ValueError
            except ValueError:
                return self._json(400, {"ok": False, "erros": ["Content-Length ausente ou inválido."]})
            if n > LIMITE_CORPO:
                return self._json(413, {"ok": False, "erros": ["Dados grandes demais."]})
            corpo = self.rfile.read(n)
            try:
                dados = json.loads(corpo)
            except (ValueError, UnicodeDecodeError):
                return self._json(400, {"ok": False, "erros": ["Os dados enviados não são um JSON válido."]})
            fd, nome = tempfile.mkstemp(prefix="entrada.rascunho.", suffix=".json", dir=pasta_rodada)
            rascunho = Path(nome)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(json.dumps(dados, ensure_ascii=False, indent=2))
                try:
                    carregar_entrada(rascunho)
                except EntradaInvalida as e:
                    return self._json(200, {"ok": False, "erros": e.erros})
                except Exception as e:  # noqa: BLE001 - qualquer falha vira resposta JSON
                    return self._json(200, {"ok": False, "erros": [f"Dados inválidos: {type(e).__name__}."]})
                os.replace(rascunho, pasta_rodada / "entrada.json")
            finally:
                rascunho.unlink(missing_ok=True)
            self._json(200, {"ok": True})

    return Handler


def criar_servidor(pasta_rodada: Path, porta: int) -> ThreadingHTTPServer:
    pasta_rodada = Path(pasta_rodada)
    pasta_rodada.mkdir(parents=True, exist_ok=True)
    return ThreadingHTTPServer(("127.0.0.1", porta), _handler(pasta_rodada))


def servir(pasta_rodada: Path, porta_inicial: int = 8765) -> None:
    pasta_rodada = Path(pasta_rodada).resolve()
    status = pasta_rodada / "status.json"
    StatusWriter.abrir(status)
    ponteiro = pasta_ponteiro()
    ponteiro.mkdir(parents=True, exist_ok=True)
    (ponteiro / "rodada-atual").write_text(str(status), encoding="utf-8")
    for porta in range(porta_inicial, porta_inicial + 11):
        try:
            srv = criar_servidor(pasta_rodada, porta)
        except OSError:
            continue
        print(f"PAINEL http://127.0.0.1:{porta}/", flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            srv.server_close()
        return
    raise SystemExit(f"Nenhuma porta livre entre {porta_inicial} e {porta_inicial + 10}.")
