"""Entrada do empresário: leitura e validação do entrada.json."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DIAS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
SETORES = {"varejo", "alimentacao", "outro"}
REGIMES = {"simples", "presumido_real"}
PICOS = {"baixo", "medio", "alto"}
ESCALAS = {"6x1", "5x2", "12x36"}


class EntradaInvalida(ValueError):
    def __init__(self, erros: list[str]):
        super().__init__("; ".join(erros))
        self.erros = erros


@dataclass(frozen=True)
class Funcionamento:
    abre: float
    fecha: float
    pico: str


@dataclass(frozen=True)
class Funcionario:
    nome: str
    funcao: str
    salario: float
    turno_inicio: float
    turno_fim: float
    escala: str
    noturno_permitido: bool = True
    domingo_permitido: bool = True


@dataclass(frozen=True)
class Empresa:
    nome: str
    setor: str
    regime: str
    cidade_uf: str


@dataclass(frozen=True)
class Entrada:
    empresa: Empresa
    funcionamento: dict[int, Funcionamento | None]
    funcionarios: list[Funcionario]


def _hora(texto: str) -> float:
    h, m = texto.strip().split(":")
    hora, minuto = int(h), int(m)
    if not (0 <= hora <= 23 and 0 <= minuto <= 59):
        raise ValueError(texto)
    return hora + minuto / 60


def _intervalo(abre: str, fecha: str) -> tuple[float, float]:
    a, f = _hora(abre), _hora(fecha)
    if f == a:
        raise ValueError("início igual ao fim")
    if f < a:
        f += 24
    return a, f


def carregar_entrada(caminho: Path | str) -> Entrada:
    try:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise EntradaInvalida([f"arquivo não encontrado: {caminho}"]) from None
    except (OSError, UnicodeDecodeError) as e:
        raise EntradaInvalida([f"não foi possível ler o arquivo {caminho}: {e}"]) from None
    except json.JSONDecodeError as e:
        raise EntradaInvalida([f"JSON inválido em {caminho}: {e}"]) from None
    if not isinstance(dados, dict):
        raise EntradaInvalida(["o arquivo de entrada deve conter um objeto JSON na raiz"])
    erros: list[str] = []
    for chave in ("empresa", "funcionamento"):
        if chave in dados and not isinstance(dados[chave], dict):
            erros.append(f"{chave}: deve ser um objeto")
    if "funcionarios" in dados and not isinstance(dados["funcionarios"], list):
        erros.append("funcionarios: deve ser uma lista")
    if erros:
        raise EntradaInvalida(erros)

    emp = dados.get("empresa", {})
    if emp.get("setor") not in SETORES:
        erros.append(f"setor inválido: {emp.get('setor')!r} (use {sorted(SETORES)})")
    if emp.get("regime") not in REGIMES:
        erros.append(f"regime tributário inválido: {emp.get('regime')!r} (use {sorted(REGIMES)})")
    empresa = Empresa(emp.get("nome", ""), emp.get("setor", ""), emp.get("regime", ""), emp.get("cidade_uf", ""))

    funcionamento: dict[int, Funcionamento | None] = {}
    for i, dia in enumerate(DIAS):
        d = dados.get("funcionamento", {}).get(dia)
        if d is None:
            funcionamento[i] = None
            continue
        if not isinstance(d, dict):
            erros.append(f"{dia}: horário de funcionamento deve ser um objeto")
            continue
        if d.get("pico") not in PICOS:
            erros.append(f"{dia}: pico inválido {d.get('pico')!r} (use {sorted(PICOS)})")
        try:
            a, f = _intervalo(d["abre"], d["fecha"])
        except (AttributeError, KeyError, TypeError, ValueError):
            erros.append(f"{dia}: horário de funcionamento inválido")
            continue
        funcionamento[i] = Funcionamento(a, f, d.get("pico", "medio"))

    funcionarios: list[Funcionario] = []
    vistos: set[str] = set()
    for i, f in enumerate(dados.get("funcionarios", []), start=1):
        if not isinstance(f, dict):
            erros.append(f"funcionário #{i}: deve ser um objeto")
            continue
        nome = f.get("nome", f"#{i}")
        if nome in vistos:
            erros.append(f"funcionário {nome}: nome repetido (use apelidos diferentes)")
        vistos.add(nome)
        sal = f.get("salario")
        salario_ok = isinstance(sal, (int, float)) and not isinstance(sal, bool)
        if not salario_ok:
            erros.append(f"funcionário {nome}: salário deve ser um número")
        elif sal <= 0:
            erros.append(f"funcionário {nome}: salário deve ser maior que zero")
        if f.get("escala") not in ESCALAS:
            erros.append(f"funcionário {nome}: escala inválida {f.get('escala')!r}")
        try:
            ini, fim = _intervalo(*f["turno"].split("-"))
        except (AttributeError, KeyError, TypeError, ValueError):
            erros.append(f"funcionário {nome}: turno inválido (use HH:MM-HH:MM)")
            continue
        funcionarios.append(Funcionario(
            nome=nome, funcao=f.get("funcao", ""), salario=float(sal) if salario_ok else 0.0,
            turno_inicio=ini, turno_fim=fim, escala=f.get("escala", ""),
            noturno_permitido=f.get("noturno_permitido", True),
            domingo_permitido=f.get("domingo_permitido", True),
        ))

    if not funcionarios:
        erros.append("nenhum funcionário informado")
    if erros:
        raise EntradaInvalida(erros)
    return Entrada(empresa, funcionamento, funcionarios)
