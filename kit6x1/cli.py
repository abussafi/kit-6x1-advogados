"""Linha de comando: python -m kit6x1 analisar entrada.json --saida pasta."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .cenarios import cenario_5x2, cenario_hoje, cenario_manter_6x1, escolher_recomendado
from .modelos import DIAS, EntradaInvalida, carregar_entrada
from .otimizador import SemSolucao, TempoEsgotado, otimizar
from .regras import regras_clt
from .resultado import montar_resultado, salvar_resultado
from .status import AGENTES_SKILL, StatusWriter
from .validador import validar

LIMITE_GRATIS = 15
AGENTES = AGENTES_SKILL


class _SemPainel:
    def __getattr__(self, _nome):
        return lambda *a, **k: None


class _PainelParcial:
    """Painel em que agentes, fluxo e etapa são controlados por fora (hooks/orquestrador).

    O motor só acrescenta ao log; o texto da etapa fica com quem orquestra.
    """

    def __init__(self, writer: StatusWriter):
        self._w = writer

    def agente(self, *_a, **_k) -> None:
        return None

    def etapa(self, texto: str | None, log: str | None = None, fluxo: list | None = None) -> None:
        self._w.etapa(None, log=log)

    def __getattr__(self, nome):
        return getattr(self._w, nome)


def _args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="kit6x1")
    sub = p.add_subparsers(dest="comando", required=True)
    a = sub.add_parser("analisar")
    a.add_argument("entrada", type=Path)
    a.add_argument("--saida", type=Path, required=True)
    a.add_argument("--teto", type=int, default=40, choices=[40, 42])
    a.add_argument("--inicio", type=date.fromisoformat, default=date(2027, 1, 4))
    a.add_argument("--semanas", type=int, default=4)
    a.add_argument("--plano", choices=["gratis", "pro"], default="gratis")
    a.add_argument("--status", type=Path)
    a.add_argument("--tempo", type=float, default=20.0)
    a.add_argument("--agentes-externos", action="store_true")
    v = sub.add_parser("validar")
    v.add_argument("entrada", type=Path)
    s = sub.add_parser("status")
    s.add_argument("arquivo", type=Path)
    s.add_argument("--cliente")
    s.add_argument("--agente")
    s.add_argument("--estado", choices=["", "run", "ok", "fail"])
    s.add_argument("--nota", default="")
    s.add_argument("--etapa")
    s.add_argument("--log")
    s.add_argument("--fluxo")
    pn = sub.add_parser("painel")
    pn.add_argument("pasta", type=Path)
    pn.add_argument("--porta", type=int, default=8765)
    c = sub.add_parser("conferir")
    c.add_argument("resultado", type=Path)
    c.add_argument("entrada", type=Path)
    cn = sub.add_parser("conferir-numeros")
    cn.add_argument("relatorio", type=Path)
    cn.add_argument("resultado", type=Path)
    rl = sub.add_parser("relatorio")
    rl.add_argument("resultado", type=Path)
    rl.add_argument("--revisao", type=Path)
    rl.add_argument("--saida", type=Path, required=True)
    return p.parse_args(argv)


def _status(args: argparse.Namespace) -> int:
    fluxo = None
    if args.fluxo:
        try:
            fluxo = json.loads(args.fluxo)
        except ValueError as e:
            print(f"--fluxo não é um JSON válido: {e}", file=sys.stderr)
            return 2
    if args.agente and args.estado is None:
        print("--agente exige --estado.", file=sys.stderr)
        return 2
    w = StatusWriter.abrir(args.arquivo)
    if args.agente and args.agente not in [a["nome"] for a in w.dados["agentes"]]:
        print(f"Agente desconhecido: {args.agente}", file=sys.stderr)
        return 2
    if args.cliente:
        w.definir_cliente(args.cliente)
    if args.agente:
        try:
            w.agente_por_nome(args.agente, args.estado, args.nota)
        except KeyError:
            print(f"Agente desconhecido: {args.agente}", file=sys.stderr)
            return 2
    if args.etapa or args.log or fluxo is not None:
        w.etapa(args.etapa, log=args.log, fluxo=fluxo)
    return 0


def _analisar(args: argparse.Namespace) -> int:
    if args.inicio.weekday() != 0:
        print(f"A data de início ({args.inicio.isoformat()}) precisa ser uma segunda-feira.", file=sys.stderr)
        return 2
    if args.semanas < 1:
        print("O número de semanas (--semanas) deve ser pelo menos 1.", file=sys.stderr)
        return 2
    try:
        entrada = carregar_entrada(args.entrada)
    except EntradaInvalida as e:
        print("Entrada inválida:\n- " + "\n- ".join(e.erros), file=sys.stderr)
        return 2
    if args.plano == "gratis" and len(entrada.funcionarios) > LIMITE_GRATIS:
        print(f"A versão Grátis aceita até {LIMITE_GRATIS} funcionários. Use o Kit Pro.", file=sys.stderr)
        return 2
    semanas = 4 if args.plano == "gratis" else args.semanas
    args.saida.mkdir(parents=True, exist_ok=True)
    if args.status:
        args.status.parent.mkdir(parents=True, exist_ok=True)

    if not args.status:
        painel = _SemPainel()
    elif args.agentes_externos:
        w = StatusWriter.abrir(args.status)
        w.definir_cliente(entrada.empresa.nome)
        painel = _PainelParcial(w)
    else:
        painel = StatusWriter(args.status, entrada.empresa.nome, AGENTES)
    regras = regras_clt(args.teto, entrada.empresa.setor)

    painel.agente(0, "run", "validando entrada…")
    painel.etapa("Analista validando a entrada", log=f"{len(entrada.funcionarios)} funcionários", fluxo=[["orq", 0, "go"]])
    hoje = cenario_hoje(entrada)
    painel.agente(0, "ok", f"{len(entrada.funcionarios)} funcionários")

    painel.agente(1, "run", "testando cenários…")
    painel.etapa("Estrategista testando cenários", fluxo=[["orq", 1, "go"], [0, 1, "data"]])
    manter = cenario_manter_6x1(entrada, args.teto)
    painel.cenario(manter.nome, round(hoje.custo_mensal - manter.custo_mensal, 2))
    try:
        otim = otimizar(entrada, regras, args.inicio, semanas, args.tempo)
    except TempoEsgotado as e:
        painel.agente(1, "fail", "tempo esgotado")
        painel.etapa("Falha: tempo esgotado sem encontrar escala", log=str(e))
        print(str(e), file=sys.stderr)
        return 4
    except SemSolucao as e:
        painel.agente(1, "fail", "sem solução")
        painel.etapa("Falha: sem solução viável", log=str(e))
        print(str(e), file=sys.stderr)
        return 3
    painel.agente(1, "ok", f"otimizador: {otim.status}")

    painel.agente(2, "run", "conferindo regras…")
    painel.etapa("Revisor conferindo a escala", fluxo=[[1, 2, "data"]])
    violacoes = validar(otim.escala, entrada, regras)
    c52 = cenario_5x2(entrada, args.teto, otim, violacoes)
    painel.cenario(c52.nome, round(hoje.custo_mensal - c52.custo_mensal, 2))
    painel.agente(2, "ok" if not violacoes else "fail", f"{len(violacoes)} violação(ões)")

    cenarios = [manter, c52]
    rec = escolher_recomendado(cenarios)
    painel.agente(3, "run", "gravando resultado…")
    painel.etapa("Redator gravando o resultado", fluxo=[[2, 3, "data"]])
    d = montar_resultado(entrada, regras, hoje, cenarios, rec, otim.escala, otim.faltas)
    caminho = salvar_resultado(d, args.saida)
    painel.agente(3, "ok", "resultado.json")
    painel.recomendar(rec.nome, round(hoje.custo_mensal - rec.custo_mensal, 2), rec.nota_risco,
                      aumento_vs_hoje=round(rec.custo_mensal - hoje.custo_mensal, 2),
                      economia_vs_manter_6x1=round(manter.custo_mensal - rec.custo_mensal, 2))
    if args.agentes_externos:
        # o orquestrador é quem fecha a execução; o motor só registra o resultado no log
        painel.etapa(None, log=f"Cálculo concluído: {caminho}")
    else:
        painel.etapa("concluído", log=str(caminho), fluxo=[[3, "orq", "go"]])

    print(json.dumps({
        "resultado": str(caminho),
        "recomendado": rec.id,
        "economia_vs_manter_6x1": round(manter.custo_mensal - rec.custo_mensal, 2),
        "aumento_vs_hoje": round(rec.custo_mensal - hoje.custo_mensal, 2),
    }, ensure_ascii=False))
    return 0


def _validar(args: argparse.Namespace) -> int:
    try:
        e = carregar_entrada(args.entrada)
    except EntradaInvalida as exc:
        print(json.dumps({"ok": False, "erros": exc.erros}, ensure_ascii=False))
        return 2
    alertas = []
    if len(e.funcionarios) > LIMITE_GRATIS:
        alertas.append(f"{len(e.funcionarios)} funcionários: a versão Grátis aceita até {LIMITE_GRATIS}.")
    if any(f.escala == "12x36" for f in e.funcionarios):
        alertas.append("Há funcionários em 12x36: o modo básico ainda não modela essa escala; eles serão tratados como 5x2.")
    print(json.dumps({
        "ok": True, "empresa": e.empresa.nome, "setor": e.empresa.setor,
        "funcionarios": len(e.funcionarios),
        "dias_fechados": [DIAS[d] for d, f in sorted(e.funcionamento.items()) if f is None],
        "alertas": alertas,
    }, ensure_ascii=False))
    return 0


def _painel(args: argparse.Namespace) -> int:
    from .painel_servidor import servir
    servir(args.pasta, args.porta)
    return 0


class _JsonRuim(Exception):
    pass


def _ler_json(caminho: Path, rotulo: str):
    """Lê um JSON; em falha, avisa em português no stderr e levanta _JsonRuim."""
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Arquivo não encontrado ({rotulo}): {caminho}", file=sys.stderr)
    except (OSError, UnicodeDecodeError) as e:
        print(f"Não foi possível ler {rotulo} ({caminho}): {e}", file=sys.stderr)
    except json.JSONDecodeError as e:
        print(f"JSON inválido em {rotulo} ({caminho}): {e}", file=sys.stderr)
    raise _JsonRuim


def _conferir(args: argparse.Namespace) -> int:
    from .conferencia import conferir_resultado
    try:
        r = _ler_json(args.resultado, "resultado")
        _ler_json(args.entrada, "entrada")
    except _JsonRuim:
        return 2
    try:
        vs = conferir_resultado(r, args.entrada)
    except (ValueError, KeyError, TypeError) as e:
        msg = f"chave ausente: {e}" if isinstance(e, KeyError) else str(e)
        print(json.dumps({"ok": False, "violacoes": [], "erro": msg}, ensure_ascii=False))
        return 5
    print(json.dumps({"ok": not vs, "violacoes": [v.__dict__ for v in vs]}, ensure_ascii=False))
    return 0 if not vs else 5


def _conferir_numeros(args: argparse.Namespace) -> int:
    from .conferencia import numeros_desconhecidos
    try:
        r = _ler_json(args.resultado, "resultado")
    except _JsonRuim:
        return 2
    fora = numeros_desconhecidos(args.relatorio.read_text(encoding="utf-8"), r)
    print(json.dumps({"ok": not fora, "desconhecidos": fora}, ensure_ascii=False))
    return 0 if not fora else 5


def _relatorio(args: argparse.Namespace) -> int:
    from .relatorio import gerar_relatorio
    try:
        r = _ler_json(args.resultado, "resultado")
        rev = None
        if args.revisao:
            if args.revisao.is_file():
                rev = _ler_json(args.revisao, "revisão")
            else:
                print(f"Aviso: arquivo de revisão não encontrado ({args.revisao}); "
                      "o relatório sai sem as ressalvas do Revisor.", file=sys.stderr)
    except _JsonRuim:
        return 2
    args.saida.write_text(gerar_relatorio(r, rev), encoding="utf-8")
    print(json.dumps({"relatorio": str(args.saida)}, ensure_ascii=False))
    return 0


COMANDOS = {
    "analisar": _analisar, "validar": _validar, "status": _status, "painel": _painel,
    "conferir": _conferir, "conferir-numeros": _conferir_numeros,
    "relatorio": _relatorio,
}


def main(argv: list[str] | None = None) -> int:
    args = _args(argv)
    return COMANDOS[args.comando](args)
