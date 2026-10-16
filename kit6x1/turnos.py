"""Turnos de 8h com 1h de intervalo e a escala resultante."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .modelos import Funcionamento

DURACAO_TURNO = 9
_JANELAS_NOTURNAS = [(-2, 5), (22, 29), (46, 53)]


def horas_noturnas_intervalo(ini: float, fim: float) -> float:
    return sum(max(0.0, min(fim, b) - max(ini, a)) for a, b in _JANELAS_NOTURNAS)


@dataclass(frozen=True)
class Turno:
    inicio: int

    @property
    def fim(self) -> int:
        return self.inicio + DURACAO_TURNO

    @property
    def horas_trabalhadas(self) -> list[int]:
        intervalo = self.inicio + 4
        return [h for h in range(self.inicio, self.fim) if h != intervalo]

    @property
    def horas_noturnas(self) -> int:
        return round(sum(horas_noturnas_intervalo(h, h + 1) for h in self.horas_trabalhadas))

    def rotulo(self) -> str:
        return f"{self.inicio % 24:02d}:00–{self.fim % 24:02d}:00"


def turnos_possiveis(f: Funcionamento) -> list[Turno]:
    primeiro = int(f.abre)
    ultimo = max(primeiro, int(f.fecha) - DURACAO_TURNO)
    return [Turno(s) for s in range(primeiro, ultimo + 1)]


def respeita_interjornada(a: Turno, b: Turno, minimo_h: int = 11) -> bool:
    return 24 + b.inicio - a.fim >= minimo_h


@dataclass
class Escala:
    inicio: date
    turnos: dict[str, list[Turno | None]]

    @property
    def dias(self) -> int:
        return len(next(iter(self.turnos.values()))) if self.turnos else 0

    def data(self, d: int) -> date:
        return self.inicio + timedelta(days=d)
