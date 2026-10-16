"""Escala 5x2 de menor custo com OR-Tools CP-SAT.

Custo minimizado (em centavos): horas faltantes cobertas com hora extra +
adicional noturno. Desempate: menor número máximo de domingos trabalhados.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean

from ortools.sat.python import cp_model

from .custo import custo_noturno_relogio, valor_hora_extra
from .demanda import demanda
from .modelos import Entrada, Funcionario
from .regras import Regras
from .turnos import Escala, Turno, respeita_interjornada, turnos_possiveis


class SemSolucao(Exception):
    pass


class TempoEsgotado(SemSolucao):
    """O solver parou por tempo sem provar inviabilidade nem achar escala."""


@dataclass
class ResultadoOtimizacao:
    escala: Escala
    faltas: dict[tuple[str, int, int], int]
    status: str


def _permitido(f: Funcionario, t: Turno, dia_semana: int) -> bool:
    if t.horas_noturnas and not f.noturno_permitido:
        return False
    if dia_semana == 6 and not f.domingo_permitido:
        return False
    return True


def _restringir(m: cp_model.CpModel, cond) -> None:
    if isinstance(cond, bool):
        if not cond:
            raise SemSolucao("restrição impossível de cumprir com os dados informados")
        return
    m.Add(cond)


def otimizar(entrada: Entrada, regras: Regras, inicio: date, semanas: int = 4,
             tempo_limite_s: float = 20.0) -> ResultadoOtimizacao:
    if inicio.weekday() != 0:
        raise ValueError("a data de início precisa ser uma segunda-feira")
    dias = semanas * 7
    regime = entrada.empresa.regime
    dem = demanda(entrada)
    m = cp_model.CpModel()

    opcoes: dict[tuple[str, int], list[Turno]] = {}
    x: dict[tuple[str, int, int], cp_model.IntVar] = {}
    for f in entrada.funcionarios:
        for d in range(dias):
            dsem = (inicio + timedelta(days=d)).weekday()
            fun = entrada.funcionamento.get(dsem)
            ops = [] if fun is None else [t for t in turnos_possiveis(fun) if _permitido(f, t, dsem)]
            opcoes[f.nome, d] = ops
            for t in ops:
                x[f.nome, d, t.inicio] = m.NewBoolVar(f"x_{f.nome}_{d}_{t.inicio}")
            if ops:
                m.Add(sum(x[f.nome, d, t.inicio] for t in ops) <= 1)

    def trabalha(nome: str, d: int):
        return sum(x[nome, d, t.inicio] for t in opcoes[nome, d])

    domingos = [d for d in range(dias) if (inicio + timedelta(days=d)).weekday() == 6]
    maior_domingos = m.NewIntVar(0, len(domingos), "maior_domingos")
    custo_noturno: list = []

    for f in entrada.funcionarios:
        for s in range(semanas):
            semana = range(s * 7, (s + 1) * 7)
            abertos = sum(1 for d in semana if opcoes[f.nome, d])
            alvo = min(regras.dias_trabalho_semana, abertos)
            _restringir(m, sum(trabalha(f.nome, d) for d in semana) == alvo)
        for d in range(dias - 1):
            for t1 in opcoes[f.nome, d]:
                for t2 in opcoes[f.nome, d + 1]:
                    if not respeita_interjornada(t1, t2, regras.interjornada_h):
                        m.AddBoolOr([x[f.nome, d, t1.inicio].Not(), x[f.nome, d + 1, t2.inicio].Not()])
        n = regras.domingo_folga_cada_semanas
        for w in range(len(domingos) - n + 1):
            _restringir(m, sum(trabalha(f.nome, d) for d in domingos[w:w + n]) <= n - 1)
        _restringir(m, maior_domingos >= sum(trabalha(f.nome, d) for d in domingos))
        centavos_noturno = round(100 * custo_noturno_relogio(f.salario, regime, regras.teto_semanal))
        for d in range(dias):
            for t in opcoes[f.nome, d]:
                if t.horas_noturnas:
                    custo_noturno.append(centavos_noturno * t.horas_noturnas * x[f.nome, d, t.inicio])

    por_funcao: dict[str, list[Funcionario]] = defaultdict(list)
    for f in entrada.funcionarios:
        por_funcao[f.funcao].append(f)
    he_centavos = {
        fn: round(100 * mean(valor_hora_extra(f.salario, regime, regras.teto_semanal) for f in fs))
        for fn, fs in por_funcao.items()
    }

    faltas: dict[tuple[str, int, int], cp_model.IntVar] = {}
    custo_faltas: list = []
    for d in range(dias):
        dsem = (inicio + timedelta(days=d)).weekday()
        for (funcao, ds, h), n in dem.items():
            if ds != dsem:
                continue
            cobertura = sum(
                x[f.nome, d, t.inicio]
                for f in por_funcao[funcao]
                for t in opcoes[f.nome, d]
                if h in t.horas_trabalhadas
            )
            falta = m.NewIntVar(0, n, f"falta_{funcao}_{d}_{h}")
            m.Add(falta + cobertura >= n)
            faltas[funcao, d, h] = falta
            custo_faltas.append(he_centavos[funcao] * falta)

    m.Minimize(sum(custo_faltas) + sum(custo_noturno) + maior_domingos)

    solver = cp_model.CpSolver()
    # Determinismo: semente fixa, 8 workers intercalados (interleave_search) e limite em tempo determinístico (não em relógio).
    solver.parameters.random_seed = 0
    solver.parameters.num_workers = 8
    solver.parameters.interleave_search = True
    solver.parameters.max_deterministic_time = tempo_limite_s
    st = solver.Solve(m)
    if st == cp_model.UNKNOWN:
        raise TempoEsgotado("tempo esgotado sem encontrar escala; aumente --tempo")
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise SemSolucao("nenhuma escala viável encontrada com as regras e os horários informados")

    turnos: dict[str, list[Turno | None]] = {}
    for f in entrada.funcionarios:
        linha: list[Turno | None] = []
        for d in range(dias):
            escolhido = next((t for t in opcoes[f.nome, d] if solver.Value(x[f.nome, d, t.inicio])), None)
            linha.append(escolhido)
        turnos[f.nome] = linha

    faltando = {k: solver.Value(v) for k, v in faltas.items() if solver.Value(v) > 0}
    return ResultadoOtimizacao(Escala(inicio, turnos), faltando, solver.StatusName(st))
