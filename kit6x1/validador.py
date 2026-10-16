"""Conferência legal de qualquer escala, independente de quem a gerou."""
from __future__ import annotations

from dataclasses import dataclass

from .modelos import Entrada
from .regras import Regras
from .turnos import Escala, respeita_interjornada


@dataclass(frozen=True)
class Violacao:
    funcionario: str
    dia: int
    regra: str
    detalhe: str


def validar(escala: Escala, entrada: Entrada, regras: Regras) -> list[Violacao]:
    vs: list[Violacao] = []
    por_nome = {f.nome: f for f in entrada.funcionarios}
    semanas = escala.dias // 7

    for nome, dias in escala.turnos.items():
        f = por_nome[nome]
        for d, t in enumerate(dias):
            if t is None:
                continue
            if len(t.horas_trabalhadas) > regras.horas_dia:
                vs.append(Violacao(nome, d, "jornada_diaria", f"{len(t.horas_trabalhadas)}h no dia"))
            if t.horas_noturnas and not f.noturno_permitido:
                vs.append(Violacao(nome, d, "noturno_restrito", "escalado em horário noturno"))
            if escala.data(d).weekday() == 6 and not f.domingo_permitido:
                vs.append(Violacao(nome, d, "domingo_restrito", "escalado em domingo"))
            if d + 1 < len(dias) and dias[d + 1] is not None:
                if not respeita_interjornada(t, dias[d + 1], regras.interjornada_h):
                    vs.append(Violacao(nome, d + 1, "interjornada", f"menos de {regras.interjornada_h}h de descanso"))

        for s in range(semanas):
            semana = dias[s * 7:(s + 1) * 7]
            trabalhados = [t for t in semana if t is not None]
            if len(trabalhados) > regras.dias_trabalho_semana:
                vs.append(Violacao(nome, s * 7, "duas_folgas", f"{7 - len(trabalhados)} folga(s) na semana"))
            horas = sum(len(t.horas_trabalhadas) for t in trabalhados)
            if horas > regras.teto_semanal:
                vs.append(Violacao(nome, s * 7, "teto_semanal", f"{horas}h na semana"))

        n = regras.domingo_folga_cada_semanas
        domingos = [d for d in range(escala.dias) if escala.data(d).weekday() == 6]
        for w in range(len(domingos) - n + 1):
            janela = domingos[w:w + n]
            if all(dias[d] is not None for d in janela):
                vs.append(Violacao(nome, janela[-1], "domingo", f"nenhum domingo de folga em {n} semanas"))
    return vs
