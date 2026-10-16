"""Contrato resultado.json v1.0 entre a skill de análise e a skill de identidade.

Sinais das comparações de custo mensal em cada cenário:
- ``diferenca_vs_hoje`` = custo de hoje - custo do cenário: POSITIVO significa economia.
- ``aumento_vs_hoje`` = custo do cenário - custo de hoje: POSITIVO significa que o custo sobe.
- ``economia_vs_manter_6x1`` = custo de manter a 6x1 - custo do cenário (0 para a própria 6x1).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .cenarios import RISCO_ACEITAVEL, Cenario
from .custo import custo_hora
from .modelos import DIAS, Entrada
from .regras import HORAS_SEMANAIS_ESCALA, Regras, feriados_nacionais, parametros_aplicados
from .turnos import Escala

VERSAO = "1.0"
CHAVES_OBRIGATORIAS = [
    "versao", "gerado_em", "modo", "horizonte_meses", "empresa", "parametros",
    "situacao_atual", "cenarios", "recomendado", "escala", "riscos",
    "plano_implantacao", "graficos", "faltas",
]


def _cenario_dict(c: Cenario, hoje: Cenario, manter: Cenario | None) -> dict:
    return {
        "id": c.id, "nome": c.nome,
        "custo_mensal": round(c.custo_mensal, 2),
        "custo_anual": round(c.custo_mensal * 12, 2),
        "diferenca_vs_hoje": round(hoje.custo_mensal - c.custo_mensal, 2),
        "aumento_vs_hoje": round(c.custo_mensal - hoje.custo_mensal, 2),
        "economia_vs_manter_6x1": None if manter is None else round(manter.custo_mensal - c.custo_mensal, 2),
        "cobertura_pct": round(c.cobertura_pct, 1),
        "horas_extras_mes": round(c.horas_extras_mes, 1),
        "horas_sem_cobertura_mes": round(c.horas_sem_cobertura_mes, 1),
        "rotulo_horas": c.rotulo_horas,
        "horas_noturnas_mes": round(c.horas_noturnas_mes, 1),
        "nota_risco": c.nota_risco, "motivos": c.motivos, "estimativa": c.estimativa,
    }


def _justificativa(rec: Cenario) -> str:
    if rec.nota_risco <= RISCO_ACEITAVEL:
        return f"Menor custo entre os cenários com risco jurídico até {RISCO_ACEITAVEL} (nota {rec.nota_risco})."
    texto = (f"Nenhum cenário ficou com risco até {RISCO_ACEITAVEL}; "
             f"foi escolhido o de menor risco (nota {rec.nota_risco}).")
    if rec.motivos:
        texto += " " + " ".join(rec.motivos)
    return texto


def montar_resultado(entrada: Entrada, regras: Regras, hoje: Cenario, cenarios: list[Cenario],
                     recomendado: Cenario, escala: Escala,
                     faltas: dict[tuple[str, int, int], int] | None = None) -> dict:
    regime = entrada.empresa.regime
    func = entrada.funcionarios
    anos = {escala.data(d).year for d in range(escala.dias)}
    feriados = {k: v for a in anos for k, v in feriados_nacionais(a).items()}

    linhas, feriados_trabalhados = [], 0
    for f in func:
        dias = []
        for d, t in enumerate(escala.turnos[f.nome]):
            dt = escala.data(d)
            nome_feriado = feriados.get(dt)
            if nome_feriado and t is not None:
                feriados_trabalhados += 1
            dias.append({"data": dt.isoformat(), "turno": t.rotulo() if t else None, "feriado": nome_feriado})
        semana_tipo = [
            {"dia_semana": DIAS[escala.data(d).weekday()], "turno": t.rotulo() if t else None}
            for d, t in enumerate(escala.turnos[f.nome][:7])
        ]
        linhas.append({"funcionario": f.nome, "funcao": f.funcao, "dias": dias, "semana_tipo": semana_tipo})

    manter = next((c for c in cenarios if c.id == "manter_6x1"), None)
    horas_semanais = sum(HORAS_SEMANAIS_ESCALA[f.escala] for f in func)
    lista_faltas = [
        {"funcao": fn, "data": escala.data(d).isoformat(), "hora": h, "pessoas": n}
        for (fn, d, h), n in sorted((faltas or {}).items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0]))
    ]

    riscos = [
        "Modo básico: parâmetros da CLT. A convenção coletiva da categoria pode prever condições diferentes; confira antes de implantar.",
        "Não reduza salário nem rebaixe jornada de quem já está contratado (CLT art. 468); mudanças de contrato só por acordo documentado.",
        "Premissa de demanda: a equipe de hoje atende os dias de pico; dias de movimento médio usam 90% e dias de movimento baixo 75% dessa presença. Valide com o empresário.",
    ]
    if feriados_trabalhados:
        riscos.append(
            f"{feriados_trabalhados} dia(s) de trabalho caem em feriado nacional: conceder folga compensatória ou pagar em dobro."
        )

    return {
        "versao": VERSAO,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "modo": "clt",
        "horizonte_meses": round(escala.dias / 7 / (52 / 12), 1),
        "empresa": {"nome": entrada.empresa.nome, "setor": entrada.empresa.setor,
                    "regime": regime, "cidade_uf": entrada.empresa.cidade_uf},
        "parametros": parametros_aplicados(regras),
        "situacao_atual": {
            "funcionarios": len(func),
            "custo_mensal": round(hoje.custo_mensal, 2),
            "custo_hora_medio_antes": round(sum(custo_hora(f.salario, regime, 44) for f in func) / len(func), 2),
            "custo_hora_medio_depois": round(sum(custo_hora(f.salario, regime, regras.teto_semanal) for f in func) / len(func), 2),
            "teto_semanal_aplicado": regras.teto_semanal,
            "horas_semanais_equipe": horas_semanais,
            "horas_mensais_equipe": round(horas_semanais * 52 / 12, 1),
        },
        "cenarios": [_cenario_dict(c, hoje, manter) for c in cenarios],
        "recomendado": {
            "id": recomendado.id,
            "justificativa": _justificativa(recomendado),
        },
        "escala": linhas,
        "riscos": riscos,
        "plano_implantacao": [
            "Validar a escala com o empresário e com a liderança de cada setor.",
            "Conferir a convenção coletiva da categoria.",
            "Comunicar os funcionários por escrito com antecedência.",
            "Formalizar acordos individuais necessários (compensação ou banco de horas).",
            "Implantar a nova escala na data de vigência do novo teto e acompanhar o primeiro mês.",
        ],
        "graficos": {},
        "faltas": lista_faltas,
    }


def validar_resultado(d: dict) -> list[str]:
    problemas = [f"chave obrigatória ausente: {k}" for k in CHAVES_OBRIGATORIAS if k not in d]
    if d.get("versao") != VERSAO:
        problemas.append(f"versão desconhecida: {d.get('versao')!r}")
    ids = {c.get("id") for c in d.get("cenarios", [])}
    if "recomendado" in d and d["recomendado"].get("id") not in ids:
        problemas.append("cenário recomendado não está na lista de cenários")
    return problemas


def salvar_resultado(d: dict, pasta: Path) -> Path:
    problemas = validar_resultado(d)
    if problemas:
        raise ValueError("; ".join(problemas))
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / "resultado.json"
    caminho.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho
