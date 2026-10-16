"""Conferências independentes: escala do resultado.json e números citados no relatório."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .modelos import carregar_entrada
from .regras import regras_clt
from .turnos import Escala, Turno
from .validador import Violacao, validar

_SUFIXO = r"(?:\s*(?:milh[õo]es|milh[ãa]o|mil|mi|bi|k)\b)"
_TOKEN = re.compile(
    r"(?:(?:R\$|BRL)\s*[-−+]?\s*(?P<n1>[\d.,]*\d)(?P<s1>" + _SUFIXO + r"?)"
    r"|(?<![\w.,])(?P<n2>\d[\d.,]*\d|\d)(?P<s2>" + _SUFIXO + r"?)\s+reais\b)",
    re.IGNORECASE,
)
_SOLTO = re.compile(r"(?<![\w.,])(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}(?![\d,]|\.\d)")
_BEM_FORMADO = re.compile(r"^(\d{1,3}(\.\d{3})*|\d+),\d{2}$")
_CHAVES_MONETARIAS = ("custo", "economia", "aumento", "diferenca")


def escala_do_resultado(resultado: dict) -> Escala:
    linhas = resultado["escala"]
    inicio = date.fromisoformat(linhas[0]["dias"][0]["data"])
    turnos = {
        l["funcionario"]: [Turno(int(d["turno"][:2])) if d["turno"] else None for d in l["dias"]]
        for l in linhas
    }
    return Escala(inicio, turnos)


def conferir_resultado(resultado: dict, entrada_caminho: Path) -> list[Violacao]:
    entrada = carregar_entrada(entrada_caminho)
    regras = regras_clt(resultado["situacao_atual"]["teto_semanal_aplicado"], resultado["empresa"]["setor"])
    return validar(escala_do_resultado(resultado), entrada, regras)


def _tokens(texto: str) -> list[tuple[str, float | None]]:
    """(texto bruto, valor) por token monetário; valor None se malformado."""
    saida = []
    for m in _TOKEN.finditer(texto):
        num = m.group("n1") or m.group("n2")
        suf = m.group("s1") or m.group("s2")
        if suf or not _BEM_FORMADO.match(num):
            saida.append((m.group(0).strip(), None))
        else:
            saida.append((m.group(0).strip(), float(num.replace(".", "").replace(",", "."))))
    return saida


def _soltos(texto: str) -> list[str]:
    """Números no formato de dinheiro sem símbolo (9.999,99 ou 12,50) fora de tokens monetários."""
    ocupado = [m.span() for m in _TOKEN.finditer(texto)]
    return [m.group(0) for m in _SOLTO.finditer(texto)
            if not any(a <= m.start() < b for a, b in ocupado)]


def valores_brl(texto: str) -> list[float]:
    return [v for _, v in _tokens(texto) if v is not None]


def _centavos(obj, chave_monetaria: bool = False) -> set[int]:
    """Centavos de folhas numéricas cuja chave começa por custo/economia/aumento/diferenca."""
    if isinstance(obj, bool):
        return set()
    if isinstance(obj, (int, float)):
        return {round(abs(obj) * 100)} if chave_monetaria else set()
    if isinstance(obj, dict):
        achados: set[int] = set()
        for k, v in obj.items():
            achados |= _centavos(v, str(k).lower().startswith(_CHAVES_MONETARIAS))
        return achados
    if isinstance(obj, list):
        achados = set()
        for v in obj:
            achados |= _centavos(v, chave_monetaria)
        return achados
    return set()


def numeros_desconhecidos(texto: str, resultado: dict) -> list[float | str]:
    conhecidos = _centavos(resultado)
    desconhecidos: list[float | str] = [bruto if v is None else v for bruto, v in _tokens(texto)
                                        if v is None or round(v * 100) not in conhecidos]
    for bruto in _soltos(texto):
        if round(float(bruto.replace(".", "").replace(",", ".")) * 100) not in conhecidos:
            desconhecidos.append(bruto)
    return desconhecidos
