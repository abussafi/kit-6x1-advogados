from datetime import date

import pytest

from kit6x1.custo import custo_hora, custo_noturno_relogio, fator_encargos, valor_hora_extra
from kit6x1.regras import feriados_nacionais, parametros_aplicados, regras_clt


def test_fator_encargos():
    # Simples: FGTS 8% + provisões (13º, férias e 1/3 = 7/36) com reflexo do FGTS
    assert fator_encargos("simples") == pytest.approx(1.29)
    # Presumido/Real: + INSS patronal 20%, RAT 2%, terceiros 5,8%
    assert fator_encargos("presumido_real") == pytest.approx(1.358 + 7 / 36 * 1.358)


def test_custo_hora_por_teto():
    assert custo_hora(2000, "simples", 44) == pytest.approx(2000 * 1.29 / 220)
    assert custo_hora(2000, "simples", 42) == pytest.approx(2000 * 1.29 / 210)
    assert custo_hora(2000, "simples", 40) == pytest.approx(12.9)


def test_hora_extra_e_noturno():
    assert valor_hora_extra(2000, "simples", 40) == pytest.approx(19.35)
    # hora noturna de 52min30s (8/7) com 20%: custo extra = hora * (8/7*1.2 - 1)
    assert custo_noturno_relogio(2000, "simples", 40) == pytest.approx(12.9 * (8 / 7 * 1.2 - 1))


def test_regras_clt():
    r = regras_clt(40, "varejo")
    assert r.divisor == 200
    assert r.domingo_folga_cada_semanas == 3
    assert regras_clt(42, "alimentacao").domingo_folga_cada_semanas == 7
    with pytest.raises(ValueError):
        regras_clt(38, "varejo")


def test_parametros_tem_origem():
    ps = parametros_aplicados(regras_clt(40, "varejo"))
    assert all({"regra", "valor", "origem"} <= p.keys() for p in ps)
    assert any("Lei 10.101" in p["origem"] for p in ps)


def test_feriados_2027():
    f = feriados_nacionais(2027)
    assert f[date(2027, 3, 26)] == "Sexta-feira Santa"  # Páscoa 2027 = 28/03
    assert f[date(2027, 11, 20)].startswith("Dia Nacional de Zumbi")
    assert date(2027, 2, 9) not in f  # Carnaval não é feriado nacional
