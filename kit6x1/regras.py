"""Regras da CLT e da PEC 221/2019 usadas no modo básico (sem convenção coletiva)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

DIVISOR = {44: 220, 42: 210, 40: 200}
HORAS_SEMANAIS_ESCALA = {"6x1": 44, "5x2": 44, "12x36": 42}
DIAS_POR_SEMANA_ESCALA = {"6x1": 6, "5x2": 5, "12x36": 3.5}
SEMANAS_POR_MES = 52 / 12
ADICIONAL_HORA_EXTRA = 0.5
ADICIONAL_NOTURNO = 0.2
FATOR_HORA_NOTURNA = 60 / 52.5
DOMINGO_FOLGA_CADA_SEMANAS = {"varejo": 3, "alimentacao": 7, "outro": 7}


@dataclass(frozen=True)
class Regras:
    teto_semanal: int
    setor: str
    dias_trabalho_semana: int = 5
    horas_dia: int = 8
    interjornada_h: int = 11

    @property
    def divisor(self) -> int:
        return DIVISOR[self.teto_semanal]

    @property
    def domingo_folga_cada_semanas(self) -> int:
        return DOMINGO_FOLGA_CADA_SEMANAS[self.setor]


def regras_clt(teto_semanal: int, setor: str) -> Regras:
    if teto_semanal not in DIVISOR:
        raise ValueError(f"teto semanal deve ser 44, 42 ou 40 (recebido {teto_semanal})")
    if setor not in DOMINGO_FOLGA_CADA_SEMANAS:
        raise ValueError(f"setor desconhecido: {setor}")
    return Regras(teto_semanal, setor)


def parametros_aplicados(r: Regras) -> list[dict]:
    domingo_origem = (
        "Lei 10.101/2000, art. 6º, parágrafo único" if r.setor == "varejo"
        else "Portaria MTP 671/2021 (atividades autorizadas a trabalhar aos domingos)"
    )
    return [
        {"regra": "Jornada semanal máxima", "valor": f"{r.teto_semanal}h", "origem": "PEC 221/2019"},
        {"regra": "Jornada diária máxima", "valor": f"{r.horas_dia}h", "origem": "CF art. 7º, XIII (redação da PEC 221/2019)"},
        {"regra": "Folgas semanais", "valor": "2", "origem": "PEC 221/2019"},
        {"regra": "Divisor mensal", "valor": str(r.divisor), "origem": "Proporcional ao teto semanal"},
        {"regra": "Interjornada", "valor": f"{r.interjornada_h}h", "origem": "CLT art. 66"},
        {"regra": "Intervalo intrajornada", "valor": "1h acima de 6h", "origem": "CLT art. 71"},
        {"regra": "Hora extra", "valor": "50%", "origem": "CF art. 7º, XVI"},
        {"regra": "Adicional noturno", "valor": "20%, 22h às 5h, hora de 52min30s", "origem": "CLT art. 73"},
        {"regra": "Domingo de folga", "valor": f"ao menos 1 a cada {r.domingo_folga_cada_semanas} semanas", "origem": domingo_origem},
        {"regra": "Convenção coletiva", "valor": "não considerada (modo básico)", "origem": "Conferir a convenção da categoria antes de implantar"},
    ]


def _pascoa(ano: int) -> date:
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def feriados_nacionais(ano: int) -> dict[date, str]:
    fixos = {
        (1, 1): "Confraternização Universal",
        (4, 21): "Tiradentes",
        (5, 1): "Dia do Trabalho",
        (9, 7): "Independência do Brasil",
        (10, 12): "Nossa Senhora Aparecida",
        (11, 2): "Finados",
        (11, 15): "Proclamação da República",
        (11, 20): "Dia Nacional de Zumbi e da Consciência Negra",
        (12, 25): "Natal",
    }
    f = {date(ano, m, d): nome for (m, d), nome in fixos.items()}
    f[_pascoa(ano) - timedelta(days=2)] = "Sexta-feira Santa"
    return f
