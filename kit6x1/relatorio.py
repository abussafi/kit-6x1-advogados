"""Relatório técnico em Markdown gerado só a partir do resultado.json (sem IA)."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from .modelos import DIAS

MARCA_RESUMO = "<!-- RESUMO -->"
_NOMES_DIA = {"seg": "segunda", "ter": "terça", "qua": "quarta", "qui": "quinta",
              "sex": "sexta", "sab": "sábado", "dom": "domingo"}


def brl(v: float) -> str:
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


_SETOR = {"alimentacao": "alimentação", "varejo": "varejo", "outro": "outro"}
_REGIME = {"simples": "Simples Nacional", "presumido_real": "Lucro Presumido/Real"}


def _sinal(v: float) -> str:
    return "+" if v > 0 else "−" if v < 0 else ""


def _cel(texto) -> str:
    return str(texto).replace("|", "\\|")


def _economia_tabela(v: float | None) -> str:
    if not v:
        return "—"
    return brl(v) if v > 0 else f"+{brl(-v)} a mais"


def _frase_recomendado(rec: dict) -> str:
    aum, eco = rec["aumento_vs_hoje"], rec["economia_vs_manter_6x1"]
    if aum > 0:
        var = f"aumento de {brl(aum)} por mês em relação a hoje"
    elif aum < 0:
        var = f"redução de {brl(aum)} por mês em relação a hoje"
    else:
        var = "sem variação de custo em relação a hoje"
    if eco and eco > 0:
        extra = f" e economia de {brl(eco)} por mês em relação a manter a 6x1"
    elif eco and eco < 0:
        extra = f" e custo de {brl(eco)} por mês acima de manter a 6x1"
    else:
        extra = ""
    frase = f"**{rec['nome']}** — custo de {brl(rec['custo_mensal'])} por mês, {var}{extra}."
    return frase + (" (estimativa)" if rec["estimativa"] else "")


def gerar_relatorio(r: dict, revisao: dict | None = None) -> str:
    sa, emp = r["situacao_atual"], r["empresa"]
    rec = next(c for c in r["cenarios"] if c["id"] == r["recomendado"]["id"])
    n_semanas = len(r["escala"][0]["dias"]) // 7
    revisor = ""
    if revisao and "aprovado" in revisao:
        revisor = " · Revisor: " + ("aprovado" if revisao["aprovado"] else "reprovado")
    out = [
        f"# Readequação 6x1 — {emp['nome']}",
        "",
        f"Setor: {_SETOR.get(emp['setor'], emp['setor'])} · Regime: {_REGIME.get(emp['regime'], emp['regime'])} · "
        f"{emp['cidade_uf']} · Teto aplicado: {sa['teto_semanal_aplicado']}h semanais" + revisor,
        "",
        "> Modo básico: parâmetros da CLT. A convenção coletiva da categoria pode prever condições diferentes; confira antes de implantar.",
        "",
        "## Resumo",
        "",
        MARCA_RESUMO,
        "",
        "## Situação atual",
        "",
        f"- Funcionários: {sa['funcionarios']}",
        f"- Horas contratadas por semana (equipe): {sa['horas_semanais_equipe']}h",
        f"- Custo mensal hoje: {brl(sa['custo_mensal'])}",
        f"- Custo médio da hora: {brl(sa['custo_hora_medio_antes'])} hoje → {brl(sa['custo_hora_medio_depois'])} com o novo teto",
        "",
        "## Cenários",
        "",
        "| Cenário | Custo mensal | Custo vs. hoje | Economia vs. manter a 6x1 | Cobertura | Risco |",
        "|---|---|---|---|---|---|",
    ]
    for c in r["cenarios"]:
        eco = _economia_tabela(c["economia_vs_manter_6x1"])
        out.append(f"| {_cel(c['nome'])}{' (estimativa)' if c['estimativa'] else ''} | {brl(c['custo_mensal'])} | "
                   f"{_sinal(c['aumento_vs_hoje'])}{brl(c['aumento_vs_hoje'])} | {eco} | "
                   f"{c['cobertura_pct']}% | {c['nota_risco']}/10 |")
    out += [
        "",
        "## Cenário recomendado",
        "",
        _frase_recomendado(rec),
        "",
        r["recomendado"]["justificativa"],
        "",
        "## Onde falta gente",
        "",
    ]
    agreg: dict[tuple[str, str], int] = defaultdict(int)
    for f in r["faltas"]:
        agreg[(f["funcao"], DIAS[date.fromisoformat(f["data"]).weekday()])] += f["pessoas"]
    if agreg:
        out += [f"Horas sem cobertura nas primeiras {n_semanas} semanas:", "",
                "| Função | Dia da semana | Horas sem cobertura no período |", "|---|---|---|"]
        for (fn, dia), h in sorted(agreg.items(), key=lambda kv: -kv[1])[:10]:
            out.append(f"| {_cel(fn)} | {_NOMES_DIA[dia]} | {h}h |")
    else:
        out.append(f"Nenhuma hora sem cobertura nas primeiras {n_semanas} semanas analisadas.")
    out += ["", f"## Semana tipo — {rec['nome']}", "",
            "| Funcionário | Função | " + " | ".join(_NOMES_DIA[d] for d in DIAS) + " |",
            "|---|---|" + "---|" * 7]
    for l in r["escala"]:
        cel = {x["dia_semana"]: (x["turno"] or "folga") for x in l["semana_tipo"]}
        out.append(f"| {_cel(l['funcionario'])} | {_cel(l['funcao'])} | " + " | ".join(cel.get(d, "—") for d in DIAS) + " |")
    out += ["", "## Riscos", ""] + [f"- {x}" for x in r["riscos"]]
    for c in r["cenarios"]:
        out += [f"- {c['nome']}: {m}" for m in c["motivos"]]
    if revisao and revisao.get("ressalvas"):
        out += ["", "## Ressalvas do Revisor jurídico", ""] + [f"- {x}" for x in revisao["ressalvas"]]
    out += ["", "## Plano de implantação", ""] + [f"{i}. {p}" for i, p in enumerate(r["plano_implantacao"], 1)]
    out += ["", "## Parâmetros aplicados", "", "| Regra | Valor | Origem |", "|---|---|---|"]
    out += [f"| {_cel(p['regra'])} | {_cel(p['valor'])} | {_cel(p['origem'])} |" for p in r["parametros"]]
    gerado = datetime.fromisoformat(r["gerado_em"]).strftime("%d/%m/%Y %H:%M")
    out += ["", f"_Gerado em {gerado} pelo Kit 6x1. Estimativas sujeitas à validação do advogado responsável._", ""]
    return "\n".join(out)
