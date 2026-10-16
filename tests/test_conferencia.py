import json
from pathlib import Path

import pytest

from kit6x1.cli import main
from kit6x1.conferencia import escala_do_resultado, numeros_desconhecidos, valores_brl

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def rodada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("rodada")
    assert main(["analisar", str(FIX / "loja_8.json"), "--saida", str(pasta), "--tempo", "10"]) == 0
    return pasta, json.loads((pasta / "resultado.json").read_text())


def test_escala_reconstruida(rodada):
    _, r = rodada
    esc = escala_do_resultado(r)
    assert esc.dias == 28 and set(esc.turnos) == {l["funcionario"] for l in r["escala"]}
    rotulos = [d["turno"] for d in r["escala"][0]["dias"]]
    assert [t.rotulo() if t else None for t in esc.turnos[r["escala"][0]["funcionario"]]] == rotulos


def test_conferir_ok_e_violacao(rodada, tmp_path, capsys):
    pasta, r = rodada
    assert main(["conferir", str(pasta / "resultado.json"), str(FIX / "loja_8.json")]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    for d in r["escala"][0]["dias"][:7]:
        d["turno"] = "09:00–18:00"  # 7 dias seguidos: viola as 2 folgas
    p = tmp_path / "r.json"
    p.write_text(json.dumps(r))
    assert main(["conferir", str(p), str(FIX / "loja_8.json")]) == 5
    assert any(v["regra"] == "duas_folgas" for v in json.loads(capsys.readouterr().out)["violacoes"])


def test_valores_brl():
    assert valores_brl("Custo R$ 39.243,69 e −R$ 5.876,27; também R$ 0,50.") == [39243.69, 5876.27, 0.5]


def test_numeros_desconhecidos():
    r = {"custo_a": 39243.69, "b": [{"economia_c": -5876.27}], "d": "texto"}
    assert numeros_desconhecidos("R$ 39.243,69 e R$ 5.876,27", r) == []
    assert numeros_desconhecidos("R$ 39.243,69 e R$ 1.000,00", r) == [1000.0]


def test_conferir_numeros_cli(rodada, tmp_path, capsys):
    pasta, r = rodada
    rel = tmp_path / "rel.md"
    custo = r["cenarios"][0]["custo_mensal"]
    rel.write_text(f"Custo: R$ {custo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    assert main(["conferir-numeros", str(rel), str(pasta / "resultado.json")]) == 0
    rel.write_text("Custo inventado: R$ 123.456,78")
    assert main(["conferir-numeros", str(rel), str(pasta / "resultado.json")]) == 5
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])["desconhecidos"] == [123456.78]


R_MIN = {"cenarios": [{"custo_mensal": 39243.69, "economia_vs_hoje": -5876.27}],
         "situacao_atual": {"teto_semanal_aplicado": 40, "horas": 44, "caps": 3}}


@pytest.mark.parametrize("texto,esperado", [
    ("Custa R$ 39 mil", ["R$ 39 mil"]),
    ("Custa R$ 1.234 no mês", ["R$ 1.234"]),
    ("Custa R$ 1.234,5 no mês", ["R$ 1.234,5"]),
    ("Custa 39 mil reais", ["39 mil reais"]),
    ("Custa BRL 2 mi", ["BRL 2 mi"]),
    ("Custa R$ 3k", ["R$ 3k"]),
    ("Custa R$ 1,5 milhões", ["R$ 1,5 milhões"]),
    ("Custa 500 reais", ["500 reais"]),
    ("Custa R$ 12.34,56", ["R$ 12.34,56"]),
])
def test_token_malformado_falha_fechado(texto, esperado):
    assert numeros_desconhecidos(texto, R_MIN) == esperado


def test_bem_formados_aceitos():
    assert numeros_desconhecidos("39.243,69 reais", R_MIN) == []
    assert numeros_desconhecidos("r$ -5.876,27", R_MIN) == []
    assert numeros_desconhecidos("-R$ 5.876,27 e brl 39.243,69.", R_MIN) == []
    assert numeros_desconhecidos("−R$ 5.876,27", R_MIN) == []
    assert numeros_desconhecidos("R$ 1.000,00 reais", R_MIN) == [1000.0]


def test_valores_brl_so_bem_formados():
    assert valores_brl("R$ 39 mil, R$ 1.234, R$ 10,00 e 5,50 reais") == [10.0, 5.5]


def test_so_valores_monetarios_na_whitelist():
    assert numeros_desconhecidos("Invento R$ 40,00", R_MIN) == [40.0]
    assert numeros_desconhecidos("R$ 44,00 e R$ 3,00", R_MIN) == [44.0, 3.0]


def test_whitelist_chaves_monetarias_profundas():
    r = {"x": {"aumento_vs_hoje": 10.5, "diferenca_total": [{"economia": -2.25}], "id": 7.77}}
    assert numeros_desconhecidos("R$ 10,50 R$ 2,25 R$ 7,77", r) == [7.77]


def test_conferir_erro_teto_invalido(rodada, tmp_path, capsys):
    pasta, r = rodada
    r = json.loads(json.dumps(r))
    r["situacao_atual"]["teto_semanal_aplicado"] = 38
    p = tmp_path / "r.json"
    p.write_text(json.dumps(r))
    assert main(["conferir", str(p), str(FIX / "loja_8.json")]) == 5
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False and out["violacoes"] == [] and out["erro"]


def test_conferir_numeros_cli_malformado(rodada, tmp_path, capsys):
    pasta, _ = rodada
    rel = tmp_path / "rel.md"
    rel.write_text("Economia de R$ 39 mil")
    assert main(["conferir-numeros", str(rel), str(pasta / "resultado.json")]) == 5
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])["desconhecidos"] == ["R$ 39 mil"]


@pytest.mark.parametrize("texto,esperado", [
    ("Economia de R$ +9.999,99", [9999.99]),
    ("Economia de R$+9.999,99", [9999.99]),
    ("Economia de +R$ 9.999,99", [9999.99]),
    ("Economia de 9.999,99 no mês", ["9.999,99"]),
    ("Sobra 123,45", ["123,45"]),
])
def test_porta_de_dinheiro_sinal_mais_e_numero_solto(texto, esperado):
    assert numeros_desconhecidos(texto, R_MIN) == esperado


def test_numero_solto_conhecido_aceito():
    assert numeros_desconhecidos("Total 39.243,69 e 5.876,27", R_MIN) == []
    assert numeros_desconhecidos("R$ +39.243,69", R_MIN) == []
    assert numeros_desconhecidos("R$ 39.243,69 (39.243,69)", R_MIN) == []


def test_numero_solto_nao_duplica_token_ja_casado():
    assert numeros_desconhecidos("R$ 1.000,00", R_MIN) == [1000.0]
    assert numeros_desconhecidos("R$ 12.34,56", R_MIN) == ["R$ 12.34,56"]
