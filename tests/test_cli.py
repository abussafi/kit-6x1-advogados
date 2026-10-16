import json
from pathlib import Path

from kit6x1.cli import main

FIX = Path(__file__).parent / "fixtures"


def test_ponta_a_ponta_restaurante(tmp_path, capsys):
    status = tmp_path / "status.json"
    rc = main(["analisar", str(FIX / "restaurante_12.json"), "--saida", str(tmp_path),
               "--teto", "40", "--status", str(status), "--tempo", "10"])
    assert rc == 0
    linha = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    d = json.loads(Path(linha["resultado"]).read_text())
    ids = [c["id"] for c in d["cenarios"]]
    assert ids == ["manter_6x1", "5x2_otimizado"]
    manter, c52 = d["cenarios"]
    assert manter["diferenca_vs_hoje"] < 0          # manter a 6x1 custa mais que hoje
    assert c52["custo_mensal"] < manter["custo_mensal"]  # 5x2 sai mais barato
    assert linha["economia_vs_manter_6x1"] > 0
    painel = json.loads(status.read_text())
    assert painel["recomendado"] is not None
    assert all(a["estado"] == "ok" for a in painel["agentes"])


def test_limite_do_plano_gratis(tmp_path, capsys):
    dados = json.loads((FIX / "loja_8.json").read_text())
    base = dados["funcionarios"][0]
    dados["funcionarios"] = [dict(base, nome=f"F{i}") for i in range(16)]
    p = tmp_path / "e.json"
    p.write_text(json.dumps(dados))
    assert main(["analisar", str(p), "--saida", str(tmp_path)]) == 2
    assert "15 funcionários" in capsys.readouterr().err


def test_entrada_invalida(tmp_path, capsys):
    dados = json.loads((FIX / "loja_8.json").read_text())
    dados["empresa"]["regime"] = "lucro"
    p = tmp_path / "e.json"
    p.write_text(json.dumps(dados))
    assert main(["analisar", str(p), "--saida", str(tmp_path)]) == 2
    assert "regime" in capsys.readouterr().err


def _rodar(args, capsys):
    rc = main(args)
    return rc, capsys.readouterr()


def test_arquivo_inexistente_sai_com_2(tmp_path, capsys):
    rc, out = _rodar(["analisar", str(tmp_path / "x.json"), "--saida", str(tmp_path)], capsys)
    assert rc == 2 and "não encontrado" in out.err


def test_json_ruim_sai_com_2(tmp_path, capsys):
    p = tmp_path / "e.json"
    p.write_text("{ ruim")
    rc, out = _rodar(["analisar", str(p), "--saida", str(tmp_path)], capsys)
    assert rc == 2 and "JSON" in out.err


def test_inicio_que_nao_e_segunda_sai_com_2(tmp_path, capsys):
    rc, out = _rodar(["analisar", str(FIX / "loja_8.json"), "--saida", str(tmp_path), "--inicio", "2027-01-05"], capsys)
    assert rc == 2 and "segunda-feira" in out.err


def test_semanas_menor_que_1_sai_com_2(tmp_path, capsys):
    rc, out = _rodar(["analisar", str(FIX / "loja_8.json"), "--saida", str(tmp_path),
                      "--plano", "pro", "--semanas", "0"], capsys)
    assert rc == 2 and "semanas" in out.err


def test_tempo_esgotado_sai_com_4_e_painel_final(tmp_path, capsys):
    status = tmp_path / "status.json"
    rc, out = _rodar(["analisar", str(FIX / "restaurante_12.json"), "--saida", str(tmp_path),
                      "--tempo", "0.001", "--status", str(status)], capsys)
    assert rc == 4 and "aumente --tempo" in out.err
    assert "tempo esgotado" in json.loads(status.read_text())["etapa"].lower()


def test_inviavel_sai_com_3_e_painel_final(tmp_path, capsys, monkeypatch):
    import kit6x1.cli as cli
    from kit6x1.otimizador import SemSolucao

    def falha(*a, **k):
        raise SemSolucao("nenhuma escala viável")
    monkeypatch.setattr(cli, "otimizar", falha)
    status = tmp_path / "status.json"
    rc, out = _rodar(["analisar", str(FIX / "loja_8.json"), "--saida", str(tmp_path), "--status", str(status)], capsys)
    assert rc == 3
    assert "sem solução" in json.loads(status.read_text())["etapa"].lower()


def test_painel_e_stdout_batem_com_resultado_json(tmp_path, capsys):
    status = tmp_path / "status.json"
    rc, out = _rodar(["analisar", str(FIX / "restaurante_12.json"), "--saida", str(tmp_path),
                      "--status", str(status), "--tempo", "10"], capsys)
    assert rc == 0
    linha = json.loads(out.out.strip().splitlines()[-1])
    d = json.loads(Path(linha["resultado"]).read_text())
    por_id = {c["id"]: c for c in d["cenarios"]}
    rec = por_id[linha["recomendado"]]
    assert linha["aumento_vs_hoje"] == rec["aumento_vs_hoje"]
    assert linha["economia_vs_manter_6x1"] == rec["economia_vs_manter_6x1"]
    painel = json.loads(status.read_text())
    for c in painel["cenarios"]:
        assert c["valor"] == next(x for x in d["cenarios"] if x["nome"] == c["nome"])["diferenca_vs_hoje"]
    assert painel["recomendado"]["valor"] == rec["diferenca_vs_hoje"]
    assert d["faltas"] and set(d["faltas"][0]) == {"funcao", "data", "hora", "pessoas"}


def _resultado_valido(tmp_path, capsys):
    pasta = tmp_path / "r"
    rc, _ = _rodar(["analisar", str(Path(__file__).parent / "fixtures" / "loja_8.json"),
                    "--saida", str(pasta), "--tempo", "10"], capsys)
    assert rc == 0
    return pasta / "resultado.json"


def test_relatorio_sem_revisao_avisa_e_segue(tmp_path, capsys):
    res = _resultado_valido(tmp_path, capsys)
    saida = tmp_path / "rel.md"
    rc, out = _rodar(["relatorio", str(res), "--revisao", str(tmp_path / "nao-existe.json"),
                      "--saida", str(saida)], capsys)
    assert rc == 0 and saida.is_file()
    assert "revisão" in out.err.lower() and "Traceback" not in out.err


def test_json_invalido_sai_com_2_sem_traceback(tmp_path, capsys):
    res = _resultado_valido(tmp_path, capsys)
    ruim = tmp_path / "ruim.json"
    ruim.write_text("{ ruim")
    rel = tmp_path / "rel.md"
    rel.write_text("texto")
    entrada = Path(__file__).parent / "fixtures" / "loja_8.json"
    casos = [
        ["relatorio", str(ruim), "--saida", str(tmp_path / "o.md")],
        ["relatorio", str(res), "--revisao", str(ruim), "--saida", str(tmp_path / "o.md")],
        ["conferir", str(ruim), str(entrada)],
        ["conferir", str(res), str(ruim)],
        ["conferir-numeros", str(rel), str(ruim)],
    ]
    for args in casos:
        rc, out = _rodar(args, capsys)
        assert rc == 2, args
        assert "JSON" in out.err and "Traceback" not in out.err, args
