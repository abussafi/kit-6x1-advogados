import json
from pathlib import Path

from kit6x1.cli import main
from kit6x1.status import AGENTES_SKILL, StatusWriter

FIX = Path(__file__).parent / "fixtures"


def test_abrir_cria_e_reabre(tmp_path):
    p = tmp_path / "status.json"
    s = StatusWriter.abrir(p)
    assert [a["nome"] for a in s.dados["agentes"]] == [n for n, _ in AGENTES_SKILL]
    s.agente_por_nome("Estrategista", "run", "x")
    s2 = StatusWriter.abrir(p)
    assert s2.dados["agentes"][1]["estado"] == "run"


def test_recomendar_com_baselines(tmp_path):
    s = StatusWriter.abrir(tmp_path / "s.json")
    s.recomendar("5x2 otimizado", -5876.27, 6, aumento_vs_hoje=5876.27, economia_vs_manter_6x1=4483.81)
    r = json.loads((tmp_path / "s.json").read_text())["recomendado"]
    assert r == {"nome": "5x2 otimizado", "valor": -5876.27, "risco": 6,
                 "aumento_vs_hoje": 5876.27, "economia_vs_manter_6x1": 4483.81}


def test_subcomando_status(tmp_path):
    p = tmp_path / "status.json"
    assert main(["status", str(p), "--cliente", "Loja X", "--agente", "Revisor jurídico",
                 "--estado", "fail", "--nota", "12x36", "--etapa", "Revisor reprovou",
                 "--log", "reprovado", "--fluxo", '[[2, 1, "back"]]']) == 0
    d = json.loads(p.read_text())
    assert d["cliente"] == "Loja X"
    assert d["agentes"][2]["estado"] == "fail"
    assert d["etapa"] == "Revisor reprovou"
    assert d["fluxo"] == [[2, 1, "back"]]
    assert d["log"] == ["reprovado"]


def test_analisar_com_agentes_externos_nao_mexe_em_agentes(tmp_path):
    p = tmp_path / "status.json"
    StatusWriter.abrir(p).agente_por_nome("Estrategista", "run", "pelo hook")
    assert main(["analisar", str(FIX / "loja_8.json"), "--saida", str(tmp_path), "--status", str(p),
                 "--agentes-externos", "--tempo", "10"]) == 0
    d = json.loads(p.read_text())
    assert d["agentes"][1] == {"nome": "Estrategista", "modelo": "Sonnet", "estado": "run", "nota": "pelo hook"}
    assert d["fluxo"] == []
    assert d["cliente"] == "Loja Exemplo"
    assert {c["nome"] for c in d["cenarios"]} == {"Manter a 6x1", "5x2 otimizado"}
    assert d["recomendado"]["aumento_vs_hoje"] is not None
    assert d["recomendado"]["economia_vs_manter_6x1"] is not None


def test_analisar_com_agentes_externos_nao_fecha_etapa(tmp_path):
    p = tmp_path / "status.json"
    StatusWriter.abrir(p).etapa("Estrategista trabalhando")
    assert main(["analisar", str(FIX / "loja_8.json"), "--saida", str(tmp_path), "--status", str(p),
                 "--agentes-externos", "--tempo", "10"]) == 0
    d = json.loads(p.read_text())
    assert d["etapa"] == "Estrategista trabalhando"
    assert "concluído" not in d["etapa"]
    assert any("Cálculo concluído" in linha for linha in d["log"])


def test_intercalado_preserva_agentes_e_fluxo_de_outro_processo(tmp_path):
    p = tmp_path / "status.json"
    a = StatusWriter.abrir(p)
    b = StatusWriter.abrir(p)
    b.agente_por_nome("Estrategista", "ok", "feito")
    b.etapa("hook", fluxo=[[1, "orq", "go"]])
    a.cenario("X", 1.0)
    a.etapa("t")
    d = json.loads(p.read_text())
    assert d["agentes"][1]["estado"] == "ok"
    assert d["fluxo"] == [[1, "orq", "go"]]
    assert d["cenarios"] == [{"nome": "X", "valor": 1.0}]
    assert d["etapa"] == "t"


def test_threads_concorrentes_nao_perdem_cenarios(tmp_path):
    import threading
    p = tmp_path / "status.json"
    StatusWriter.abrir(p)

    def trabalho(t):
        w = StatusWriter.abrir(p)
        for i in range(25):
            w.cenario(f"c{t}-{i}", i)

    ts = [threading.Thread(target=trabalho, args=(t,)) for t in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    d = json.loads(p.read_text())
    assert len(d["cenarios"]) == 100
    assert not list(tmp_path.glob("*.tmp"))


def test_abrir_arquivo_corrompido_ou_vazio_recria(tmp_path):
    for conteudo in ("", "{nao e json"):
        p = tmp_path / "s.json"
        p.write_text(conteudo)
        s = StatusWriter.abrir(p, cliente="Fulano")
        assert s.dados["cliente"] == "Fulano"
        assert [a["nome"] for a in s.dados["agentes"]] == [n for n, _ in AGENTES_SKILL]
        assert json.loads(p.read_text())["cliente"] == "Fulano"


def test_recomendar_economia_sem_aumento_levanta(tmp_path):
    import pytest
    s = StatusWriter.abrir(tmp_path / "s.json")
    with pytest.raises(ValueError, match="economia vs. manter a 6x1 exige o aumento vs. hoje"):
        s.recomendar("x", 1.0, 1, economia_vs_manter_6x1=2.0)


def test_status_entradas_invalidas_saem_com_2(tmp_path, capsys):
    p = tmp_path / "s.json"
    assert main(["status", str(p), "--agente", "Fantasma", "--estado", "ok"]) == 2
    assert "Fantasma" in capsys.readouterr().err
    assert main(["status", str(p), "--fluxo", "{ruim"]) == 2
    assert capsys.readouterr().err
    assert main(["status", str(p), "--agente", "Redator"]) == 2
    assert capsys.readouterr().err
