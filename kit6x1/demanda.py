"""Demanda mínima por função, dia da semana e hora.

Premissas (aparecem no relatório e podem ser ajustadas):
1. A escala de hoje foi dimensionada para os dias de pico. A presença média
   atual de cada função em cada hora é a demanda dos dias de pico "alto".
2. Dias de movimento médio precisam de 90% dessa presença; dias de movimento
   baixo, de 75%.
3. Presença conta só o tempo efetivamente trabalhado: o intervalo é descontado
   proporcionalmente (ex.: 6x1 de 44h = 7h20 trabalhadas num turno de 8h20).
4. Hora parcial conta proporcionalmente: um funcionário que trabalha só parte
   de uma hora soma apenas essa fração do seu peso nela (ex.: turno de
   15h às 23h20 soma 1/3 do peso às 23h).
5. Havendo presença em uma hora de funcionamento, a demanda é de pelo menos 1.
6. A demanda é arredondada pela regra comum (0,5 sobe): 2,5 vira 3, e não 2
   como no arredondamento bancário do Python.
"""
from __future__ import annotations

import math
from collections import defaultdict

from .modelos import Entrada
from .regras import DIAS_POR_SEMANA_ESCALA, HORAS_SEMANAIS_ESCALA

FATOR_ESCALA = {"6x1": 6 / 7, "5x2": 5 / 7, "12x36": 1 / 2}
AJUSTE_PICO = {"baixo": 0.75, "medio": 0.9, "alto": 1.0}


def _fator_efetivo(turno_inicio: float, turno_fim: float, escala: str) -> float:
    horas_dia = HORAS_SEMANAIS_ESCALA[escala] / DIAS_POR_SEMANA_ESCALA[escala]
    return min(1.0, horas_dia / (turno_fim - turno_inicio))


def arredondar_demanda(v: float) -> int:
    """Arredondamento comum (0,5 sobe), com mínimo de 1 para demanda positiva."""
    return max(1, math.floor(v + 0.5))


def demanda(entrada: Entrada) -> dict[tuple[str, int, int], int]:
    presenca: dict[tuple[str, int], float] = defaultdict(float)
    for f in entrada.funcionarios:
        peso = FATOR_ESCALA[f.escala] * _fator_efetivo(f.turno_inicio, f.turno_fim, f.escala)
        for h in range(0, 30):
            overlap = max(0.0, min(h + 1, f.turno_fim) - max(h, f.turno_inicio))
            if overlap > 0:
                presenca[(f.funcao, h)] += peso * overlap

    saida: dict[tuple[str, int, int], int] = {}
    for dia, fun in entrada.funcionamento.items():
        if fun is None:
            continue
        for (funcao, h), media in presenca.items():
            if not (fun.abre <= h < fun.fecha):
                continue
            if media > 0:
                saida[(funcao, dia, h)] = arredondar_demanda(media * AJUSTE_PICO[fun.pico])
    return saida
