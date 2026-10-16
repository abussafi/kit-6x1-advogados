"""Custo da hora, hora extra e adicional noturno."""
from __future__ import annotations

from .regras import ADICIONAL_HORA_EXTRA, ADICIONAL_NOTURNO, DIVISOR, FATOR_HORA_NOTURNA

FGTS = 0.08
# INSS patronal 20% + RAT 2% (referência) + terceiros 5,8%; no Simples (anexos I a III e V) não incide
ENCARGOS_PATRONAIS = {"simples": 0.0, "presumido_real": 0.278}
PROVISOES = 1 / 12 + 1 / 12 + 1 / 36  # 13º salário + férias + 1/3 de férias


def fator_encargos(regime: str) -> float:
    base = 1 + ENCARGOS_PATRONAIS[regime] + FGTS
    return base + PROVISOES * base


def custo_hora(salario: float, regime: str, teto: int) -> float:
    return salario * fator_encargos(regime) / DIVISOR[teto]


def valor_hora_extra(salario: float, regime: str, teto: int) -> float:
    return custo_hora(salario, regime, teto) * (1 + ADICIONAL_HORA_EXTRA)


def custo_noturno_relogio(salario: float, regime: str, teto: int) -> float:
    return custo_hora(salario, regime, teto) * (FATOR_HORA_NOTURNA * (1 + ADICIONAL_NOTURNO) - 1)
