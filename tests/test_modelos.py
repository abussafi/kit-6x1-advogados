import json
from pathlib import Path

import pytest

from kit6x1.modelos import EntradaInvalida, carregar_entrada

FIX = Path(__file__).parent / "fixtures"


def test_carrega_restaurante():
    e = carregar_entrada(FIX / "restaurante_12.json")
    assert e.empresa.setor == "alimentacao"
    assert len(e.funcionarios) == 12
    assert e.funcionamento[0].abre == 11.0
    assert e.funcionamento[4].fecha == 24.0  # sexta fecha à meia-noite
    caio = next(f for f in e.funcionarios if f.nome == "Caio")
    assert caio.turno_inicio == 15.0
    assert caio.turno_fim == pytest.approx(23 + 20 / 60)


def test_dia_fechado_vira_none(tmp_path):
    dados = json.loads((FIX / "loja_8.json").read_text())
    dados["funcionamento"]["dom"] = None
    p = tmp_path / "e.json"
    p.write_text(json.dumps(dados))
    assert carregar_entrada(p).funcionamento[6] is None


def test_erros_listados(tmp_path):
    dados = json.loads((FIX / "loja_8.json").read_text())
    dados["empresa"]["setor"] = "padaria"
    dados["funcionarios"][0]["salario"] = 0
    dados["funcionarios"][1]["nome"] = "Ana"
    p = tmp_path / "e.json"
    p.write_text(json.dumps(dados))
    with pytest.raises(EntradaInvalida) as exc:
        carregar_entrada(p)
    erros = exc.value.erros
    assert any("setor" in m for m in erros)
    assert any("salário" in m for m in erros)
    assert any("repetido" in m for m in erros)


def _base():
    return json.loads((FIX / "loja_8.json").read_text())


def _erros_de(tmp_path, dados):
    p = tmp_path / "e.json"
    p.write_text(json.dumps(dados))
    with pytest.raises(EntradaInvalida) as exc:
        carregar_entrada(p)
    return exc.value.erros


@pytest.mark.parametrize("salario", ["1950", "abc", True, None])
def test_salario_nao_numerico_vira_erro(tmp_path, salario):
    dados = _base()
    dados["funcionarios"][0]["salario"] = salario
    assert any("salário" in m for m in _erros_de(tmp_path, dados))


def test_dia_de_funcionamento_nao_objeto_vira_erro(tmp_path):
    dados = _base()
    dados["funcionamento"]["seg"] = "09:00-19:00"
    erros = _erros_de(tmp_path, dados)
    assert any(m.startswith("seg:") and "objeto" in m for m in erros)


def test_funcionario_nao_objeto_vira_erro(tmp_path):
    dados = _base()
    dados["funcionarios"][0] = "Ana"
    assert any("deve ser um objeto" in m for m in _erros_de(tmp_path, dados))


@pytest.mark.parametrize("turno", ["11:00", "10:00-11:00-12:00", "10:00-10:00", "25:99-10:00", 1500])
def test_turno_invalido_vira_erro(tmp_path, turno):
    dados = _base()
    dados["funcionarios"][0]["turno"] = turno
    assert any("turno inválido" in m for m in _erros_de(tmp_path, dados))


def test_turno_atravessa_meia_noite_continua_valido(tmp_path):
    dados = _base()
    dados["funcionarios"][0]["turno"] = "22:00-02:00"
    p = tmp_path / "e.json"
    p.write_text(json.dumps(dados))
    f = carregar_entrada(p).funcionarios[0]
    assert (f.turno_inicio, f.turno_fim) == (22.0, 26.0)


@pytest.mark.parametrize("abre, fecha", [("10:00", "10:00"), ("25:99", "10:00"), ("09:00", "24:00")])
def test_horario_de_funcionamento_invalido_vira_erro(tmp_path, abre, fecha):
    dados = _base()
    dados["funcionamento"]["seg"] = {"abre": abre, "fecha": fecha, "pico": "medio"}
    assert any("horário de funcionamento inválido" in m for m in _erros_de(tmp_path, dados))


@pytest.mark.parametrize("conteudo", ["{ nao é json", "[1, 2]", '{"empresa": 3, "funcionamento": {}}',
                                      '{"empresa": {}, "funcionamento": []}', '{"empresa": {}, "funcionarios": 5}'])
def test_entrada_malformada_vira_entrada_invalida(tmp_path, conteudo):
    p = tmp_path / "e.json"
    p.write_text(conteudo)
    with pytest.raises(EntradaInvalida):
        carregar_entrada(p)


def test_arquivo_inexistente_vira_entrada_invalida(tmp_path):
    with pytest.raises(EntradaInvalida) as exc:
        carregar_entrada(tmp_path / "nao_existe.json")
    assert "não encontrado" in exc.value.erros[0]
