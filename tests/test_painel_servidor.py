import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from kit6x1.painel_servidor import criar_servidor

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def servidor(tmp_path):
    srv = criar_servidor(tmp_path, 0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", tmp_path
    srv.shutdown()


def _get(url):
    with urllib.request.urlopen(url) as r:
        return r.status, r.headers, r.read()


def _post(url, corpo: bytes):
    req = urllib.request.Request(url, data=corpo, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_serve_paginas_e_arquivos_da_rodada(servidor):
    base, pasta = servidor
    st, h, corpo = _get(base + "/")
    assert st == 200 and b"painel ao vivo" in corpo
    assert h["Cache-Control"] == "no-store"
    (pasta / "status.json").write_text('{"etapa": "x"}')
    assert json.loads(_get(base + "/status.json?t=1")[2]) == {"etapa": "x"}
    for nome in ("calendario.html", "entrada.html"):
        assert _get(base + "/" + nome)[0] == 200


def test_nega_caminho_fora(servidor):
    base, pasta = servidor
    for nome in ("entrada.json", "entrada.rascunho.json", "segredo.txt"):
        (pasta / nome).write_text("{}")
    for caminho in ("/../pyproject.toml", "/segredo.txt", "/entrada.json", "/entrada.rascunho.json"):
        with pytest.raises(urllib.error.HTTPError) as e:
            _get(base + caminho)
        assert e.value.code == 404


def test_serve_resultado_json(servidor):
    base, pasta = servidor
    (pasta / "resultado.json").write_text('{"a": 1}')
    assert json.loads(_get(base + "/resultado.json")[2]) == {"a": 1}


def _bruto(base, cabecalhos, corpo=b"{}", caminho="/entrada"):
    """POST com cabeçalhos explícitos (urllib não permite Content-Length inválido, então usa http.client)."""
    import http.client
    host, porta = base.removeprefix("http://").split(":")
    c = http.client.HTTPConnection(host, int(porta))
    c.putrequest("POST", caminho, skip_host=True, skip_accept_encoding=True)
    for k, v in cabecalhos.items():
        c.putheader(k, v)
    c.endheaders(corpo)
    r = c.getresponse()
    dados = json.loads(r.read())
    c.close()
    return r.status, dados


def _cab(base, **extra):
    h = {"Host": base.removeprefix("http://"), "Content-Type": "application/json"}
    h.update(extra)
    return {k: v for k, v in h.items() if v is not None}


def test_content_length_ausente_invalido_e_negativo(servidor):
    base, _ = servidor
    for cl in (None, "abc", "-5"):
        st, d = _bruto(base, _cab(base, **{"Content-Length": cl}), corpo=b"")
        assert st == 400 and d["ok"] is False and d["erros"]


def test_corpo_grande_demais(servidor):
    base, _ = servidor
    st, d = _bruto(base, _cab(base, **{"Content-Length": "1000001"}), corpo=b"")
    assert st == 413 and d["ok"] is False


def test_content_type_errado(servidor):
    base, _ = servidor
    st, d = _bruto(base, _cab(base, **{"Content-Type": "text/plain", "Content-Length": "2"}))
    assert st == 415 and d["ok"] is False


def test_host_estranho(servidor):
    base, _ = servidor
    st, d = _bruto(base, _cab(base, **{"Host": "evil.example:80", "Content-Length": "2"}))
    assert st == 403 and d["ok"] is False


def test_origin_estrangeira(servidor):
    base, _ = servidor
    st, d = _bruto(base, _cab(base, **{"Origin": "http://evil.example", "Content-Length": "2"}))
    assert st == 403 and d["ok"] is False


def test_origin_propria_aceita_e_sem_cors(servidor):
    base, _ = servidor
    st, d = _bruto(base, _cab(base, **{"Origin": base, "Content-Length": "2"}))
    assert st == 200 and d["ok"] is False  # {} chega até a validação da entrada


def test_post_em_outro_caminho(servidor):
    base, _ = servidor
    st, _d = _bruto(base, _cab(base, **{"Content-Length": "2"}), caminho="/outro")
    assert st == 404


def test_rascunho_unico_sem_sobras(servidor):
    base, pasta = servidor
    _post(base + "/entrada", b'{"empresa": 1}')
    assert not list(pasta.glob("entrada.rascunho.*"))


def test_excecao_inesperada_vira_erro_json(servidor, monkeypatch):
    base, _ = servidor
    from kit6x1 import painel_servidor

    def boom(_):
        raise KeyError("x")
    monkeypatch.setattr(painel_servidor, "carregar_entrada", boom)
    st, d = _post(base + "/entrada", b"{}")
    assert st == 200 and d == {"ok": False, "erros": ["Dados inválidos: KeyError."]}


def test_post_entrada_valida(servidor):
    base, pasta = servidor
    st, d = _post(base + "/entrada", (FIX / "loja_8.json").read_bytes())
    assert st == 200 and d == {"ok": True}
    assert json.loads((pasta / "entrada.json").read_text())["empresa"]["nome"] == "Loja Exemplo"


def test_post_entrada_invalida(servidor):
    base, pasta = servidor
    dados = json.loads((FIX / "loja_8.json").read_text())
    dados["empresa"]["setor"] = "padaria"
    st, d = _post(base + "/entrada", json.dumps(dados).encode())
    assert st == 200 and d["ok"] is False and any("setor" in e for e in d["erros"])
    assert not (pasta / "entrada.json").exists()
    st, d = _post(base + "/entrada", b"{nao json")
    assert st == 400 and d["ok"] is False


def _get_com_host(base, caminho, host):
    req = urllib.request.Request(base + caminho, headers={"Host": host})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_get_com_host_estranho_403(servidor):
    base, pasta = servidor
    (pasta / "status.json").write_text('{"etapa": "x"}')
    st, corpo = _get_com_host(base, "/status.json", "evil.example")
    assert st == 403 and corpo["ok"] is False
    assert _get_com_host(base, "/status.json", "evil.example:80")[0] == 403
    assert _get_com_host(base, "/status.json", base.split("//")[1].replace("127.0.0.1", "localhost"))[0] == 200
    assert _get(base + "/status.json")[0] == 200
