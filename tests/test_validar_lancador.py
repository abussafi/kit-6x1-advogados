import json
import os
import subprocess
import sys
import sysconfig
from pathlib import Path

from kit6x1.cli import main

RAIZ = Path(__file__).resolve().parent.parent
FIX = RAIZ / "tests" / "fixtures"
LANCADOR = RAIZ / "scripts" / "kit6x1"

# uv falso: cria o venv apontando para o Python do teste e não toca a rede.
FAKE_UV = """#!/usr/bin/env bash
if [ "$1" = "venv" ]; then
  dir="${@: -1}"
  mkdir -p "$dir/bin"
  ln -sf "__PY__" "$dir/bin/python"
  exit 0
fi
if [ "$1" = "pip" ] && [ "$2" = "install" ]; then
  if [ -n "${FAKE_UV_FALHA:-}" ]; then echo "falha simulada" >&2; exit 1; fi
  exit 0
fi
echo "uv falso: comando não suportado: $*" >&2
exit 2
"""


def test_validar_ok(capsys):
    assert main(["validar", str(FIX / "loja_8.json")]) == 0
    d = json.loads(capsys.readouterr().out)
    assert d["ok"] is True
    assert d["funcionarios"] == 8
    assert d["setor"] == "varejo"
    assert d["dias_fechados"] == []


def test_validar_erros(tmp_path, capsys):
    dados = json.loads((FIX / "loja_8.json").read_text())
    dados["empresa"]["regime"] = "lucro"
    p = tmp_path / "e.json"
    p.write_text(json.dumps(dados))
    assert main(["validar", str(p)]) == 2
    d = json.loads(capsys.readouterr().out)
    assert d["ok"] is False and any("regime" in e for e in d["erros"])


def test_validar_alertas(tmp_path, capsys):
    dados = json.loads((FIX / "loja_8.json").read_text())
    base = dados["funcionarios"][0]
    dados["funcionarios"] = [dict(base, nome=f"F{i}") for i in range(16)]
    dados["funcionarios"][0]["escala"] = "12x36"
    dados["funcionamento"]["dom"] = None
    p = tmp_path / "e.json"
    p.write_text(json.dumps(dados))
    assert main(["validar", str(p)]) == 0
    d = json.loads(capsys.readouterr().out)
    assert d["dias_fechados"] == ["dom"]
    assert any("15" in a for a in d["alertas"])
    assert any("12x36" in a for a in d["alertas"])


def test_lancador_usa_python_informado():
    py = RAIZ / ".venv" / "bin" / "python"
    if not py.exists():
        py = Path(sys.executable)
    env = dict(os.environ, KIT6X1_PYTHON=str(py))
    r = subprocess.run([str(LANCADOR), "validar", str(FIX / "loja_8.json")],
                       capture_output=True, text=True, env=env, cwd="/")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["ok"] is True


def test_primeira_execucao_sem_rede_marca_ambiente_pronto(tmp_path):
    fake = tmp_path / "fakebin"
    fake.mkdir()
    uv = fake / "uv"
    uv.write_text(FAKE_UV.replace("__PY__", sys.executable))
    uv.chmod(0o755)
    dados = tmp_path / "dados"
    env = {k: v for k, v in os.environ.items() if k != "KIT6X1_PYTHON"}
    # Um symlink para o python do venv não encontra o pyvenv.cfg, então o site-packages
    # do venv (com o ortools) é exposto via PYTHONPATH.
    site = sysconfig.get_paths()["purelib"]
    env.update(PATH=f"{fake}{os.pathsep}{os.environ['PATH']}", CLAUDE_PLUGIN_DATA=str(dados),
               PYTHONPATH=f"{site}{os.pathsep}{os.environ.get('PYTHONPATH', '')}")
    cmd = [str(LANCADOR), "validar", str(FIX / "loja_8.json")]

    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd="/")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["ok"] is True
    assert (dados / "venv" / ".pronto").exists()
    assert not (dados / ".lock").exists()

    # Ambiente sem marcador (instalação interrompida) não pode ser aceito.
    (dados / "venv" / ".pronto").unlink()
    env["FAKE_UV_FALHA"] = "1"
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd="/")
    assert r.returncode != 0
    assert not (dados / "venv" / ".pronto").exists()
    assert not (dados / ".lock").exists()


def test_manifesto_do_plugin():
    m = json.loads((RAIZ / ".claude-plugin" / "plugin.json").read_text())
    assert m["name"] == "kit-6x1"
    assert m["version"]
