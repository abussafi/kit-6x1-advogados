from datetime import date
from pathlib import Path

import pytest

from kit6x1.demanda import demanda
from kit6x1.modelos import Empresa, Entrada, Funcionamento, Funcionario, carregar_entrada
from kit6x1.turnos import Escala, Turno, horas_noturnas_intervalo, respeita_interjornada, turnos_possiveis

FIX = Path(__file__).parent / "fixtures"


def test_turno_basico():
    t = Turno(15)
    assert t.fim == 24
    assert t.horas_trabalhadas == [15, 16, 17, 18, 20, 21, 22, 23]
    assert t.horas_noturnas == 2
    assert t.rotulo() == "15:00–00:00"


def test_turnos_possiveis():
    assert [t.inicio for t in turnos_possiveis(Funcionamento(11, 23, "baixo"))] == [11, 12, 13, 14]
    # casa aberta menos de 9h: um turno começando na abertura
    assert [t.inicio for t in turnos_possiveis(Funcionamento(11, 17, "alto"))] == [11]


def test_interjornada():
    assert respeita_interjornada(Turno(15), Turno(11))      # sai 0h, volta 11h: 11h de descanso
    assert not respeita_interjornada(Turno(15), Turno(10))  # 10h de descanso


def test_horas_noturnas_intervalo():
    assert horas_noturnas_intervalo(15, 23 + 20 / 60) == pytest.approx(1 + 20 / 60)
    assert horas_noturnas_intervalo(9, 17) == 0
    assert horas_noturnas_intervalo(20, 30) == pytest.approx(7)  # 22h às 5h


def test_escala_datas():
    e = Escala(date(2027, 1, 4), {"Ana": [None] * 28})
    assert e.dias == 28
    assert e.data(6) == date(2027, 1, 10)


def test_demanda_restaurante():
    d = demanda(carregar_entrada(FIX / "restaurante_12.json"))
    # Garçons às 16h: 4 presentes em 6x1, 7h20 trabalhadas em turno de 8h20
    # => 4 * 6/7 * 0,88 = 3,02; segunda (baixo, 75%) => round(2,26) = 2
    assert d[("garcom", 0, 16)] == 2
    # Sábado (alto, 100%) => round(3,02) = 3
    assert d[("garcom", 5, 16)] == 3
    # Fora do funcionamento não há demanda
    assert ("garcom", 6, 20) not in d
    # Cozinha às 10h existe no turno atual, mas a casa só abre às 11h
    assert ("cozinheiro", 0, 10) not in d


def test_demanda_fracao_da_hora_conta_proporcional():
    d = demanda(carregar_entrada(FIX / "restaurante_12.json"))
    # Sexta (alto, fecha 24h): Caio e Duda trabalham 23h às 23h20 => 1/3 de peso cada
    # => 2 * 6/7 * 0,88 * 1/3 = 0,50 => mínimo de 1
    assert d[("garcom", 4, 23)] == 1
    # Segunda (baixo, 75%): Edu 10h–18h20 conta 1/3 às 18h; Fabi e Gil inteiros
    # => (1/3 + 2) * 0,754 * 0,75 = 1,32 => 1
    assert d[("cozinheiro", 0, 18)] == 1


def test_demanda_minimo_de_um_com_presenca_pequena():
    # Um só funcionário 12x36 (turno de 12h), casa aberta 7h–19h todos os dias, pico baixo.
    # 0,5 * 1,0 * 0,75 = 0,375 arredondaria para 0 sem a regra do mínimo de 1.
    emp = Empresa("Teste", "outro", "simples", "Cidade/UF")
    fun = {dia: Funcionamento(7, 19, "baixo") for dia in range(7)}
    trab = [Funcionario("Zé", "operador", 1500.0, 7, 19, "12x36")]
    d = demanda(Entrada(emp, fun, trab))
    assert d[("operador", 0, 10)] == 1
    # sem demanda fora do funcionamento
    assert ("operador", 0, 20) not in d


def test_arredondamento_meio_para_cima():
    from kit6x1.demanda import arredondar_demanda

    assert arredondar_demanda(2.5) == 3   # round() do Python daria 2
    assert arredondar_demanda(3.5) == 4
    assert arredondar_demanda(2.49) == 2
    assert arredondar_demanda(0.001) == 1  # mínimo de 1 para presença positiva
