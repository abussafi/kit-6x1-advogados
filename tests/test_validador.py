from datetime import date
from pathlib import Path

from kit6x1.modelos import carregar_entrada
from kit6x1.regras import regras_clt
from kit6x1.turnos import Escala, Turno
from kit6x1.validador import validar

FIX = Path(__file__).parent / "fixtures"
SEG = date(2027, 1, 4)  # segunda-feira


def _semana(folgas: set[int], inicio: int = 9) -> list:
    return [None if d in folgas else Turno(inicio) for d in range(7)]


def _loja():
    return carregar_entrada(FIX / "loja_8.json")


def test_escala_valida_sem_violacoes():
    e = _loja()
    # 3 semanas; domingo de folga na 1ª semana (dia 6), demais folgas seg/ter
    semanas = _semana({0, 6}) + _semana({0, 1}) + _semana({0, 1})
    esc = Escala(SEG, {f.nome: list(semanas) for f in e.funcionarios})
    assert validar(esc, e, regras_clt(40, "varejo")) == []


def test_seis_dias_viola_duas_folgas():
    e = _loja()
    esc = Escala(SEG, {f.nome: _semana({6}) for f in e.funcionarios})
    regras = {v.regra for v in validar(esc, e, regras_clt(40, "varejo"))}
    assert "duas_folgas" in regras
    assert "teto_semanal" in regras


def test_interjornada_violada():
    e = _loja()
    dias = [Turno(15), Turno(9), Turno(9), Turno(9), Turno(9), None, None]
    esc = Escala(SEG, {f.nome: list(dias) for f in e.funcionarios})
    vs = [v for v in validar(esc, e, regras_clt(40, "varejo")) if v.regra == "interjornada"]
    assert vs and vs[0].dia == 1


def test_domingo_varejo_tres_semanas():
    e = _loja()
    semanas = _semana({0, 1}) * 3  # trabalha os 3 domingos
    esc = Escala(SEG, {f.nome: list(semanas) for f in e.funcionarios})
    assert any(v.regra == "domingo" for v in validar(esc, e, regras_clt(40, "varejo")))
