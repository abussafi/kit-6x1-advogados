import copy
import json
import re
from datetime import datetime
from pathlib import Path

import pytest

from kit6x1.cli import main
from kit6x1.conferencia import numeros_desconhecidos
from kit6x1.relatorio import MARCA_RESUMO, brl, gerar_relatorio

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def resultado(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("rel")
    assert main(["analisar", str(FIX / "restaurante_12.json"), "--saida", str(pasta), "--tempo", "10"]) == 0
    return pasta, json.loads((pasta / "resultado.json").read_text())


def test_brl():
    assert brl(39243.69) == "R$ 39.243,69"
    assert brl(-5876.27) == "R$ 5.876,27"
    assert brl(0.5) == "R$ 0,50"


def test_relatorio_tem_secoes_e_marca(resultado):
    _, r = resultado
    md = gerar_relatorio(r, {"aprovado": True, "ressalvas": ["Conferir convenção coletiva."]})
    for trecho in ("# Readequação 6x1", MARCA_RESUMO, "## Cenários", "## Onde falta gente",
                   "## Semana tipo", "## Riscos", "Conferir convenção coletiva.", "## Parâmetros"):
        assert trecho in md
    rec = next(c for c in r["cenarios"] if c["id"] == r["recomendado"]["id"])
    assert brl(rec["aumento_vs_hoje"]) in md and brl(rec["economia_vs_manter_6x1"]) in md


def test_relatorio_sem_numero_inventado(resultado):
    _, r = resultado
    assert numeros_desconhecidos(gerar_relatorio(r), r) == []


def test_cli_relatorio(resultado, tmp_path):
    pasta, _ = resultado
    saida = tmp_path / "relatorio-tecnico.md"
    assert main(["relatorio", str(pasta / "resultado.json"), "--saida", str(saida)]) == 0
    assert saida.read_text().startswith("# Readequação 6x1")


def _recomendado(r):
    return next(c for c in r["cenarios"] if c["id"] == r["recomendado"]["id"])


def _linha_recomendado(md, nome):
    return next(l for l in md.splitlines() if l.startswith(f"**{nome}**"))


def test_aumento_zero_diz_sem_variacao(resultado):
    _, r = resultado
    r = copy.deepcopy(r)
    rec = _recomendado(r)
    rec["aumento_vs_hoje"] = 0.0
    linha = _linha_recomendado(gerar_relatorio(r), rec["nome"])
    assert "sem variação de custo em relação a hoje" in linha
    assert "redução" not in linha and "aumento de" not in linha


def test_aumento_negativo_diz_reducao(resultado):
    _, r = resultado
    r = copy.deepcopy(r)
    rec = _recomendado(r)
    rec["aumento_vs_hoje"] = -5000.0
    linha = _linha_recomendado(gerar_relatorio(r), rec["nome"])
    assert "redução de R$ 5.000,00 por mês em relação a hoje" in linha
    assert "aumento de" not in linha


def test_economia_negativa_diz_a_mais_e_nao_economia(resultado):
    _, r = resultado
    r = copy.deepcopy(r)
    rec = _recomendado(r)
    rec["economia_vs_manter_6x1"] = -1234.5
    md = gerar_relatorio(r)
    linha = _linha_recomendado(md, rec["nome"])
    assert "custo de R$ 1.234,50 por mês acima de manter a 6x1" in linha
    assert "economia de" not in linha
    assert "+R$ 1.234,50 a mais" in md


def test_economia_positiva_aparece_na_frase(resultado):
    _, r = resultado
    md = gerar_relatorio(r)
    rec = _recomendado(r)
    assert f"e economia de {brl(rec['economia_vs_manter_6x1'])} por mês em relação a manter a 6x1" in md


def test_estimativa_do_recomendado_marca_frase(resultado):
    _, r = resultado
    r = copy.deepcopy(r)
    rec = _recomendado(r)
    rec["estimativa"] = True
    assert _linha_recomendado(gerar_relatorio(r), rec["nome"]).endswith("(estimativa)")
    rec["estimativa"] = False
    assert "(estimativa)" not in _linha_recomendado(gerar_relatorio(r), rec["nome"])


def test_loja_8_sem_numero_inventado(tmp_path):
    assert main(["analisar", str(FIX / "loja_8.json"), "--saida", str(tmp_path), "--tempo", "10"]) == 0
    r = json.loads((tmp_path / "resultado.json").read_text())
    assert numeros_desconhecidos(gerar_relatorio(r), r) == []


def test_nome_com_pipe_nao_quebra_tabela(resultado):
    _, r = resultado
    r = copy.deepcopy(r)
    r["escala"][0]["funcionario"] = "Ana | Silva"
    md = gerar_relatorio(r)
    assert "Ana \\| Silva" in md
    secao = md.split("## Semana tipo")[1].split("## Riscos")[0]
    tabela = [l for l in secao.splitlines() if l.startswith("|")]
    assert len(tabela) > 2
    assert len({len(re.findall(r"(?<!\\)\|", l)) for l in tabela}) == 1


def test_cabecalho_com_rotulos_legiveis(resultado):
    _, r = resultado
    md = gerar_relatorio(r, {"aprovado": True})
    cabecalho = md.splitlines()[2]
    assert "Setor: alimentação" in cabecalho and "Regime: Simples Nacional" in cabecalho
    assert "Revisor: aprovado" in cabecalho
    assert datetime.fromisoformat(r["gerado_em"]).strftime("%d/%m/%Y %H:%M") in md
    assert "Revisor: reprovado" in gerar_relatorio(r, {"aprovado": False})


def test_semana_tipo_e_horizonte_nomeiam_cenario_e_periodo(resultado):
    _, r = resultado
    md = gerar_relatorio(r)
    assert f"## Semana tipo — {_recomendado(r)['nome']}" in md
    assert f"nas primeiras {len(r['escala'][0]['dias']) // 7} semanas" in md
