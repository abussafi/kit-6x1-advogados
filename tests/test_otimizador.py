from datetime import date
from pathlib import Path

import pytest

from kit6x1.modelos import carregar_entrada
from kit6x1.otimizador import otimizar
from kit6x1.regras import regras_clt
from kit6x1.validador import validar

FIX = Path(__file__).parent / "fixtures"
SEG = date(2027, 1, 4)


@pytest.mark.parametrize("arquivo", ["loja_8.json", "restaurante_12.json"])
def test_escala_sem_violacoes(arquivo):
    e = carregar_entrada(FIX / arquivo)
    r = regras_clt(40, e.empresa.setor)
    res = otimizar(e, r, SEG, semanas=4, tempo_limite_s=15)
    assert res.status in {"OPTIMAL", "FEASIBLE"}
    assert res.escala.dias == 28
    assert set(res.escala.turnos) == {f.nome for f in e.funcionarios}
    assert validar(res.escala, e, r) == []


def test_cada_semana_tem_cinco_dias():
    e = carregar_entrada(FIX / "restaurante_12.json")
    res = otimizar(e, regras_clt(40, "alimentacao"), SEG, semanas=4, tempo_limite_s=15)
    for dias in res.escala.turnos.values():
        for s in range(4):
            assert sum(t is not None for t in dias[s * 7:(s + 1) * 7]) == 5


def test_inicio_precisa_ser_segunda():
    e = carregar_entrada(FIX / "loja_8.json")
    with pytest.raises(ValueError):
        otimizar(e, regras_clt(40, "varejo"), date(2027, 1, 5))


def test_resolucao_e_deterministica():
    e = carregar_entrada(FIX / "restaurante_12.json")
    r = regras_clt(40, e.empresa.setor)
    a = otimizar(e, r, SEG, semanas=4, tempo_limite_s=15)
    b = otimizar(e, r, SEG, semanas=4, tempo_limite_s=15)
    assert a.escala.turnos == b.escala.turnos
    assert a.faltas == b.faltas


def test_tempo_esgotado_difere_de_inviavel():
    from kit6x1.otimizador import SemSolucao, TempoEsgotado
    e = carregar_entrada(FIX / "restaurante_12.json")
    with pytest.raises(TempoEsgotado) as exc:
        otimizar(e, regras_clt(40, e.empresa.setor), SEG, semanas=4, tempo_limite_s=0.001)
    assert "tempo esgotado sem encontrar escala; aumente --tempo" in str(exc.value)
    assert issubclass(TempoEsgotado, SemSolucao)
