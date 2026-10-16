"""Cenários comparados da versão Grátis: hoje, manter a 6x1 e 5x2 otimizado."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from statistics import mean

from .custo import custo_hora, custo_noturno_relogio, fator_encargos, valor_hora_extra
from .demanda import demanda
from .modelos import Entrada
from .otimizador import ResultadoOtimizacao
from .regras import DIAS_POR_SEMANA_ESCALA, HORAS_SEMANAIS_ESCALA, SEMANAS_POR_MES
from .turnos import horas_noturnas_intervalo
from .validador import Violacao

RISCO_ACEITAVEL = 5
LIMITE_FALTAS_MES_POR_FUNCIONARIO = 8
LIMITE_HORAS_EXTRAS_DIA = 2


@dataclass
class Cenario:
    id: str
    nome: str
    custo_mensal: float
    horas_extras_mes: float
    horas_noturnas_mes: float
    cobertura_pct: float
    nota_risco: int
    motivos: list[str] = field(default_factory=list)
    estimativa: bool = False
    horas_sem_cobertura_mes: float = 0.0
    rotulo_horas: str = ""


def _base(entrada: Entrada) -> float:
    return sum(f.salario * fator_encargos(entrada.empresa.regime) for f in entrada.funcionarios)


def _noturno_atual(entrada: Entrada, teto: int) -> tuple[float, float]:
    horas = custo = 0.0
    for f in entrada.funcionarios:
        h = horas_noturnas_intervalo(f.turno_inicio, f.turno_fim) * DIAS_POR_SEMANA_ESCALA[f.escala] * SEMANAS_POR_MES
        horas += h
        custo += h * custo_noturno_relogio(f.salario, entrada.empresa.regime, teto)
    return horas, custo


def cenario_hoje(entrada: Entrada) -> Cenario:
    horas_not, custo_not = _noturno_atual(entrada, 44)
    return Cenario("hoje", "Situação de hoje (44h)", _base(entrada) + custo_not, 0.0, horas_not, 100.0, 0,
                   rotulo_horas="jornada contratada, sem horas extras")


def cenario_manter_6x1(entrada: Entrada, teto: int) -> Cenario:
    """Após a PEC as 2 folgas semanais são obrigatórias: o 6º dia vira descanso trabalhado, pago em dobro."""
    regime = entrada.empresa.regime
    horas_not, custo_not = _noturno_atual(entrada, teto)
    he_horas = he_custo = 0.0
    for f in entrada.funcionarios:
        if f.escala == "6x1":
            horas_dia = HORAS_SEMANAIS_ESCALA["6x1"] / DIAS_POR_SEMANA_ESCALA["6x1"]
            h = horas_dia * SEMANAS_POR_MES
            he_horas += h
            he_custo += h * custo_hora(f.salario, regime, teto) * 2
        elif f.escala == "5x2":
            h = max(0.0, HORAS_SEMANAIS_ESCALA["5x2"] - teto) * SEMANAS_POR_MES
            he_horas += h
            he_custo += h * valor_hora_extra(f.salario, regime, teto)
    return Cenario(
        "manter_6x1", "Manter a 6x1", _base(entrada) + custo_not + he_custo,
        he_horas, horas_not, 100.0, 10,
        ["Descumpre as 2 folgas semanais obrigatórias (PEC 221/2019): o 6º dia vira descanso "
         "trabalhado, pago em dobro, com alto risco de passivo trabalhista."],
        rotulo_horas="descanso trabalhado e horas extras",
    )


def cenario_5x2(entrada: Entrada, teto: int, otim: ResultadoOtimizacao, violacoes: list[Violacao]) -> Cenario:
    regime = entrada.empresa.regime
    esc = otim.escala
    semanas = esc.dias / 7
    por_mes = SEMANAS_POR_MES / semanas
    por_nome = {f.nome: f for f in entrada.funcionarios}

    horas_not = custo_not = 0.0
    for nome, dias in esc.turnos.items():
        f = por_nome[nome]
        for t in dias:
            if t is not None and t.horas_noturnas:
                horas_not += t.horas_noturnas
                custo_not += t.horas_noturnas * custo_noturno_relogio(f.salario, regime, teto)

    he_por_funcao: dict[str, list[float]] = defaultdict(list)
    for f in entrada.funcionarios:
        he_por_funcao[f.funcao].append(valor_hora_extra(f.salario, regime, teto))
    faltas_h = sum(otim.faltas.values())
    custo_faltas = sum(n * mean(he_por_funcao[fn]) for (fn, _d, _h), n in otim.faltas.items())

    dem = demanda(entrada)
    total_demanda = sum(
        n for d in range(esc.dias) for (_fn, ds, _h), n in dem.items() if ds == esc.data(d).weekday()
    )
    cobertura = 100.0 if total_demanda == 0 else 100.0 * (1 - faltas_h / total_demanda)

    # Hora extra é limitada a 2h por dia por funcionário: o que passa disso não pode ser coberto assim.
    faltas_dia: dict[tuple[str, int], int] = defaultdict(int)
    for (fn, d, _h), n in otim.faltas.items():
        faltas_dia[fn, d] += n
    funcao_de = {f.nome: f.funcao for f in entrada.funcionarios}
    excedente_h = 0
    for (fn, d), n in faltas_dia.items():
        escalados = sum(1 for nome, dias in esc.turnos.items() if funcao_de[nome] == fn and dias[d] is not None)
        excedente_h += max(0, n - LIMITE_HORAS_EXTRAS_DIA * escalados)

    motivos: list[str] = []
    faltas_mes = faltas_h * por_mes
    excedente_mes = excedente_h * por_mes
    faltas_mes_func = faltas_mes / len(entrada.funcionarios)
    if violacoes:
        nota = 10
        motivos += [f"{v.funcionario}: {v.regra} ({v.detalhe})" for v in violacoes]
    elif faltas_mes_func > LIMITE_FALTAS_MES_POR_FUNCIONARIO:
        nota = 6
        motivos.append(
            f"{faltas_mes:.0f}h por mês sem cobertura ({faltas_mes_func:.0f}h por funcionário): "
            "hora extra habitual. Recomenda-se reforço com tempo parcial (Kit Pro)."
        )
    elif faltas_h > 0:
        nota = 3
        motivos.append(f"{faltas_mes:.0f}h por mês sem cobertura, valorizadas a preço de hora extra pontual.")
    else:
        nota = 1

    if excedente_h > 0:
        motivos.append(
            f"{excedente_mes:.1f}h por mês excedem o limite de {LIMITE_HORAS_EXTRAS_DIA}h extras por dia por "
            "funcionário da função (inclusive em dias sem ninguém da função escalado): exigiriam trabalho em "
            "dia de descanso (pago em dobro) ou reforço/contratação. O custo mostrado é uma estimativa."
        )

    return Cenario(
        "5x2_otimizado", "5x2 otimizado",
        _base(entrada) + (custo_not + custo_faltas) * por_mes,
        faltas_mes, horas_not * por_mes, cobertura, nota, motivos,
        estimativa=faltas_h > 0,
        horas_sem_cobertura_mes=faltas_mes,
        rotulo_horas="horas sem cobertura valorizadas a preço de hora extra",
    )


def escolher_recomendado(cenarios: list[Cenario]) -> Cenario:
    aceitaveis = [c for c in cenarios if c.nota_risco <= RISCO_ACEITAVEL]
    if aceitaveis:
        return min(aceitaveis, key=lambda c: c.custo_mensal)
    return min(cenarios, key=lambda c: (c.nota_risco, c.custo_mensal))
