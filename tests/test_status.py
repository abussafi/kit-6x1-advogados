import json

from kit6x1.status import StatusWriter


def test_grava_formato_do_painel(tmp_path):
    p = tmp_path / "status.json"
    s = StatusWriter(p, "Loja X", [("Analista de dados", "Haiku"), ("Estrategista", "Sonnet")])
    s.etapa("Analista validando", log="planilha recebida", fluxo=[["orq", 0, "go"]])
    s.agente(0, "run", "validando…")
    s.cenario("Só hora extra", -4950)
    s.cenario("Só hora extra", -4800)
    s.recomendar("5x2 otimizado", 900, 1)
    d = json.loads(p.read_text())
    assert d["cliente"] == "Loja X"
    assert d["agentes"][0] == {"nome": "Analista de dados", "modelo": "Haiku", "estado": "run", "nota": "validando…"}
    assert d["cenarios"] == [{"nome": "Só hora extra", "valor": -4800}]
    assert d["fluxo"] == [["orq", 0, "go"]]
    assert d["log"] == ["planilha recebida"]
    assert d["recomendado"] == {"nome": "5x2 otimizado", "valor": 900, "risco": 1}
    assert sorted(f.name for f in tmp_path.iterdir() if f.name != "status.json.lock") == ["status.json"]
    assert not list(tmp_path.glob("*.tmp"))
