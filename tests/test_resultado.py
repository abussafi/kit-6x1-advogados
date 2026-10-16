import json
from datetime import date

import pytest

from kit6x1.cenarios import Cenario
from kit6x1.modelos import Empresa, Entrada, Funcionamento, Funcionario
from kit6x1.regras import regras_clt
from kit6x1.resultado import CHAVES_OBRIGATORIAS, montar_resultado, salvar_resultado, validar_resultado
from kit6x1.turnos import Escala, Turno


def _dados():
    f = Funcionario("Ana", "garcom", 2000, 11, 19.33, "6x1")
    e = Entrada(Empresa("X", "alimentacao", "simples", "SP"), {d: Funcionamento(11, 23, "medio") for d in range(7)}, [f])
    hoje = Cenario("hoje", "Hoje", 2580, 0, 0, 100, 0)
    m6 = Cenario("manter_6x1", "Manter a 6x1", 3400.0, 31.8, 0, 100, 10, ["passivo"])
    c52 = Cenario("5x2_otimizado", "5x2 otimizado", 2580, 0, 0, 100, 1)
    semana = [Turno(11)] * 5 + [None, None]
    esc = Escala(date(2026, 12, 28), {"Ana": semana * 4})  # inclui 01/01/2027
    return e, regras_clt(40, "alimentacao"), hoje, [m6, c52], c52, esc


def test_monta_com_chaves_obrigatorias():
    d = montar_resultado(*_dados())
    assert validar_resultado(d) == []
    assert d["versao"] == "1.0"
    assert set(CHAVES_OBRIGATORIAS) <= d.keys()
    assert d["recomendado"]["id"] == "5x2_otimizado"
    m6 = next(c for c in d["cenarios"] if c["id"] == "manter_6x1")
    assert m6["diferenca_vs_hoje"] == pytest.approx(2580 - 3400.0)
    assert m6["custo_anual"] == pytest.approx(3400.0 * 12)


def test_escala_marca_feriado_trabalhado():
    d = montar_resultado(*_dados())
    dias = d["escala"][0]["dias"]
    ano_novo = next(x for x in dias if x["data"] == "2027-01-01")
    assert ano_novo["feriado"] == "Confraternização Universal"
    assert ano_novo["turno"] == "11:00–20:00"
    assert any("feriado" in r for r in d["riscos"])


def test_salvar_recusa_invalido(tmp_path):
    d = montar_resultado(*_dados())
    p = salvar_resultado(d, tmp_path)
    assert json.loads(p.read_text())["versao"] == "1.0"
    del d["cenarios"]
    with pytest.raises(ValueError):
        salvar_resultado(d, tmp_path)


def test_justificativa_normal_menciona_risco_ate_5():
    d = montar_resultado(*_dados())
    assert "risco jurídico até 5" in d["recomendado"]["justificativa"]


def test_justificativa_fallback_quando_nenhum_cenario_aceitavel():
    e, r, hoje, _cens, _c52, esc = _dados()
    m6 = Cenario("manter_6x1", "Manter a 6x1", 3400.0, 31.8, 0, 100, 10, ["passivo"])
    c52 = Cenario("5x2_otimizado", "5x2 otimizado", 2900, 10, 0, 90, 6, ["faltas habituais"])
    d = montar_resultado(e, r, hoje, [m6, c52], c52, esc)
    j = d["recomendado"]["justificativa"]
    assert "Nenhum cenário ficou com risco até 5" in j
    assert "menor risco (nota 6)" in j
    assert "faltas habituais" in j
    assert "Menor custo entre" not in j


def test_cenario_dict_tem_horas_sem_cobertura_e_rotulo():
    e, r, hoje, _c, _c52, esc = _dados()
    m6 = Cenario("manter_6x1", "M", 3400.0, 31.8, 0, 100, 10, rotulo_horas="descanso trabalhado e horas extras")
    c52 = Cenario("5x2_otimizado", "5", 2600, 12.0, 0, 90, 3, estimativa=True, horas_sem_cobertura_mes=12.0,
                  rotulo_horas="horas sem cobertura valorizadas a preço de hora extra")
    d = montar_resultado(e, r, hoje, [m6, c52], c52, esc)
    a, b = d["cenarios"]
    assert a["horas_sem_cobertura_mes"] == 0 and a["rotulo_horas"] == "descanso trabalhado e horas extras"
    assert b["horas_sem_cobertura_mes"] == 12.0 and b["estimativa"] is True and "sem cobertura" in b["rotulo_horas"]


def test_baselines_aumento_e_economia():
    d = montar_resultado(*_dados())
    m6, c52 = d["cenarios"]
    assert m6["aumento_vs_hoje"] == pytest.approx(3400.0 - 2580)
    assert m6["diferenca_vs_hoje"] == pytest.approx(-m6["aumento_vs_hoje"])
    assert m6["economia_vs_manter_6x1"] == 0
    assert c52["aumento_vs_hoje"] == 0
    assert c52["economia_vs_manter_6x1"] == pytest.approx(3400.0 - 2580)


def test_situacao_atual_horas_contratadas():
    d = montar_resultado(*_dados())
    assert d["situacao_atual"]["horas_semanais_equipe"] == 44
    assert d["situacao_atual"]["horas_mensais_equipe"] == pytest.approx(44 * 52 / 12, abs=0.1)


def test_semana_tipo_e_faltas():
    e, r, hoje, cens, rec, esc = _dados()
    faltas = {("garcom", 5, 12): 2, ("garcom", 0, 24): 1}
    d = montar_resultado(e, r, hoje, cens, rec, esc, faltas)
    st = d["escala"][0]["semana_tipo"]
    assert [x["dia_semana"] for x in st] == ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
    assert st[0]["turno"] == "11:00–20:00" and st[5]["turno"] is None
    assert {"funcao": "garcom", "data": "2027-01-02", "hora": 12, "pessoas": 2} in d["faltas"]
    assert {"funcao": "garcom", "data": "2026-12-28", "hora": 24, "pessoas": 1} in d["faltas"]
    assert "faltas" in CHAVES_OBRIGATORIAS


def test_faltas_padrao_vazio():
    assert montar_resultado(*_dados())["faltas"] == []
