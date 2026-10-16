from datetime import date

import pytest

from kit6x1.cenarios import (
    Cenario, cenario_5x2, cenario_hoje, cenario_manter_6x1, escolher_recomendado,
)
from kit6x1.modelos import Empresa, Entrada, Funcionamento, Funcionario
from kit6x1.otimizador import ResultadoOtimizacao
from kit6x1.turnos import Escala, Turno
from kit6x1.validador import Violacao

SEG = date(2027, 1, 4)


def _entrada(turno=(11.0, 11 + 8 + 20 / 60)):
    f = Funcionario("Ana", "garcom", 2000, turno[0], turno[1], "6x1")
    fun = {d: Funcionamento(11, 23, "medio") for d in range(7)}
    return Entrada(Empresa("X", "alimentacao", "simples", "SP"), fun, [f])


def test_hoje_sem_noturno():
    c = cenario_hoje(_entrada())
    assert c.custo_mensal == pytest.approx(2000 * 1.29)
    assert c.horas_extras_mes == 0


def test_manter_6x1_teto_40():
    c = cenario_manter_6x1(_entrada(), 40)
    horas = 44 / 6 * 52 / 12
    assert c.id == "manter_6x1"
    assert c.horas_extras_mes == pytest.approx(horas)
    assert c.custo_mensal == pytest.approx(2580 + horas * 12.9 * 2)
    assert c.nota_risco == 10


def test_manter_6x1_teto_42_mesmas_horas_custo_hora_maior_divisor():
    c = cenario_manter_6x1(_entrada(), 42)
    horas = 44 / 6 * 52 / 12
    assert c.horas_extras_mes == pytest.approx(horas)
    assert c.custo_mensal == pytest.approx(2580 + horas * (2000 * 1.29 / 210) * 2)


def test_5x2_sem_faltas_nem_noturno():
    semana = [Turno(11)] * 5 + [None, None]
    otim = ResultadoOtimizacao(Escala(SEG, {"Ana": semana * 4}), {}, "OPTIMAL")
    c = cenario_5x2(_entrada(), 40, otim, [])
    assert c.custo_mensal == pytest.approx(2580)
    assert c.cobertura_pct == pytest.approx(100.0)
    assert c.nota_risco == 1


def test_5x2_com_faltas_cobradas_como_hora_extra():
    semana = [Turno(11)] * 5 + [None, None]
    otim = ResultadoOtimizacao(Escala(SEG, {"Ana": semana * 4}), {("garcom", 5, 12): 1}, "OPTIMAL")
    c = cenario_5x2(_entrada(), 40, otim, [])
    assert c.horas_extras_mes == pytest.approx(1 * 52 / 12 / 4)
    assert c.custo_mensal == pytest.approx(2580 + 52 / 12 / 4 * 19.35)
    assert c.cobertura_pct < 100
    assert c.nota_risco == 3


def test_5x2_com_violacao_tem_risco_maximo():
    semana = [Turno(11)] * 5 + [None, None]
    otim = ResultadoOtimizacao(Escala(SEG, {"Ana": semana * 4}), {}, "OPTIMAL")
    c = cenario_5x2(_entrada(), 40, otim, [Violacao("Ana", 1, "interjornada", "x")])
    assert c.nota_risco == 10


def test_recomendado_menor_custo_com_risco_aceitavel():
    a = Cenario("a", "A", 1000, 0, 0, 100, 8, [])
    b = Cenario("b", "B", 1200, 0, 0, 100, 2, [])
    assert escolher_recomendado([a, b]).id == "b"


def test_5x2_faltas_habituais_risco_6():
    semana = [Turno(11)] * 5 + [None, None]
    faltas = {("garcom", d, 12): 1 for d in range(28)}  # 28h em 4 semanas ≈ 30h/mês para 1 funcionário
    otim = ResultadoOtimizacao(Escala(SEG, {"Ana": semana * 4}), faltas, "OPTIMAL")
    c = cenario_5x2(_entrada(), 40, otim, [])
    assert c.nota_risco == 6
    assert any("tempo parcial" in m for m in c.motivos)


def _otim_com_faltas(faltas):
    semana = [Turno(11)] * 5 + [None, None]
    return ResultadoOtimizacao(Escala(SEG, {"Ana": semana * 4}), faltas, "OPTIMAL")


def test_5x2_sem_faltas_nao_e_estimativa():
    c = cenario_5x2(_entrada(), 40, _otim_com_faltas({}), [])
    assert c.estimativa is False
    assert c.horas_sem_cobertura_mes == 0


def test_5x2_com_faltas_e_estimativa_e_conta_horas_alem_de_2h_por_dia():
    # dia 5 (sábado): Ana folga, ninguém da função -> 1h não pode ser hora extra.
    # dia 0 (segunda): Ana trabalha -> limite 2h; 3h faltando -> 1h excedente.
    faltas = {("garcom", 5, 12): 1, ("garcom", 0, 12): 1, ("garcom", 0, 13): 1, ("garcom", 0, 14): 1}
    c = cenario_5x2(_entrada(), 40, _otim_com_faltas(faltas), [])
    assert c.estimativa is True
    excedente_mes = 2 * 52 / 12 / 4
    assert c.horas_sem_cobertura_mes == pytest.approx(4 * 52 / 12 / 4)
    assert c.horas_extras_mes == pytest.approx(c.horas_sem_cobertura_mes)
    motivo = next(m for m in c.motivos if "2h" in m)
    assert f"{excedente_mes:.1f}h" in motivo
    assert "dobro" in motivo and "reforço" in motivo
    assert "hora extra" in c.rotulo_horas and "sem cobertura" in c.rotulo_horas


def test_5x2_faltas_dentro_do_limite_nao_geram_motivo_de_excedente():
    faltas = {("garcom", 0, 12): 1, ("garcom", 0, 13): 1}  # 2h com Ana presente
    c = cenario_5x2(_entrada(), 40, _otim_com_faltas(faltas), [])
    assert c.estimativa is True
    assert not any("2h por dia" in m for m in c.motivos)


def test_manter_6x1_rotulo_e_sem_cobertura_zero():
    c = cenario_manter_6x1(_entrada(), 40)
    assert c.rotulo_horas == "descanso trabalhado e horas extras"
    assert c.horas_sem_cobertura_mes == 0
