"""Grava o status.json lido pelo painel ao vivo (escrita atômica)."""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

AGENTES_SKILL = [("Analista de dados", "Haiku"), ("Estrategista", "Sonnet"),
                 ("Revisor jurídico", "Sonnet"), ("Redator", "Haiku")]


class StatusWriter:
    def __init__(self, caminho: Path, cliente: str, agentes: list[tuple[str, str]]):
        self.caminho = Path(caminho)
        self.dados = self._inicial(cliente, agentes)
        with self._trava():
            self._gravar()

    @staticmethod
    def _inicial(cliente: str, agentes: list[tuple[str, str]]) -> dict:
        return {
            "cliente": cliente, "etapa": "iniciando…",
            "agentes": [{"nome": n, "modelo": m, "estado": "", "nota": ""} for n, m in agentes],
            "cenarios": [], "log": [], "recomendado": None, "fluxo": [],
        }

    @classmethod
    def abrir(cls, caminho: Path, cliente: str = "aguardando dados",
              agentes: list[tuple[str, str]] | None = None) -> "StatusWriter":
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        obj = cls.__new__(cls)
        obj.caminho = caminho
        with obj._trava():
            dados = obj._ler()
            if dados is None:
                obj.dados = cls._inicial(cliente, agentes or AGENTES_SKILL)
                obj._gravar()
            else:
                obj.dados = dados
        return obj

    @contextmanager
    def _trava(self):
        lock = self.caminho.with_name(self.caminho.name + ".lock")
        with open(lock, "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def _ler(self) -> dict | None:
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return dados if isinstance(dados, dict) else None

    def _gravar(self) -> None:
        fd, tmp = tempfile.mkstemp(dir=self.caminho.parent, prefix=self.caminho.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(json.dumps(self.dados, ensure_ascii=False))
            os.replace(tmp, self.caminho)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def _mutar(self, fn):
        """Relê o arquivo sob trava, aplica só a mudança de fn e grava."""
        with self._trava():
            atual = self._ler()
            if atual is not None:
                self.dados = atual
            resultado = fn(self.dados)
            self._gravar()
            return resultado

    def definir_cliente(self, nome: str) -> None:
        self._mutar(lambda d: d.__setitem__("cliente", nome))

    def etapa(self, texto: str | None, log: str | None = None, fluxo: list | None = None) -> None:
        def f(d):
            if texto is not None:
                d["etapa"] = texto
            if log:
                d["log"].append(log)
            if fluxo is not None:
                d["fluxo"] = fluxo
        self._mutar(f)

    def agente(self, indice: int, estado: str, nota: str = "") -> None:
        self._mutar(lambda d: d["agentes"][indice].update(estado=estado, nota=nota))

    def agente_por_nome(self, nome: str, estado: str, nota: str = "") -> int:
        def f(d):
            for i, a in enumerate(d["agentes"]):
                if a["nome"] == nome:
                    a.update(estado=estado, nota=nota)
                    return i
            raise KeyError(nome)
        return self._mutar(f)

    def cenario(self, nome: str, valor: float | None) -> None:
        def f(d):
            for c in d["cenarios"]:
                if c["nome"] == nome:
                    c["valor"] = valor
                    break
            else:
                d["cenarios"].append({"nome": nome, "valor": valor})
        self._mutar(f)

    def recomendar(self, nome: str, valor: float, risco: int,
                   aumento_vs_hoje: float | None = None,
                   economia_vs_manter_6x1: float | None = None) -> None:
        if economia_vs_manter_6x1 is not None and aumento_vs_hoje is None:
            raise ValueError("economia vs. manter a 6x1 exige o aumento vs. hoje")
        r = {"nome": nome, "valor": valor, "risco": risco}
        if aumento_vs_hoje is not None:
            r["aumento_vs_hoje"] = aumento_vs_hoje
        if economia_vs_manter_6x1 is not None:
            r["economia_vs_manter_6x1"] = economia_vs_manter_6x1
        self._mutar(lambda d: d.__setitem__("recomendado", r))
