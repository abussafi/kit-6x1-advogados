import json
import os
import subprocess
import sys
from pathlib import Path

from kit6x1.status import StatusWriter

RAIZ = Path(__file__).resolve().parent.parent
HOOK = RAIZ / "scripts" / "hook_painel.py"


def _rodar(evento: dict, home: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, KIT6X1_HOME=str(home))
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(evento),
                          capture_output=True, text=True, env=env)


def _preparar(tmp_path):
    status = tmp_path / "rodada" / "status.json"
    StatusWriter.abrir(status)
    home = tmp_path / "home"
    home.mkdir()
    (home / "rodada-atual").write_text(str(status))
    return status, home


def test_start_e_stop(tmp_path):
    status, home = _preparar(tmp_path)
    assert _rodar({"hook_event_name": "SubagentStart", "agent_type": "kit-6x1:estrategista"}, home).returncode == 0
    d = json.loads(status.read_text())
    assert d["agentes"][1]["estado"] == "run"
    assert d["fluxo"] == [["orq", 1, "go"], [0, 1, "data"]]
    _rodar({"hook_event_name": "SubagentStop", "agent_type": "kit-6x1:estrategista",
            "last_assistant_message": "Cenários calculados."}, home)
    d = json.loads(status.read_text())
    assert d["agentes"][1]["estado"] == "ok"
    assert d["fluxo"] == [[1, "orq", "go"]]


def test_revisor_reprovado(tmp_path):
    status, home = _preparar(tmp_path)
    _rodar({"hook_event_name": "SubagentStop", "agent_type": "kit-6x1:revisor-juridico",
            "last_assistant_message": "  REPROVADO: interjornada."}, home)
    d = json.loads(status.read_text())
    assert d["agentes"][2]["estado"] == "fail"
    assert d["fluxo"] == [[2, 1, "back"]]


def test_ignora_outros_agentes_e_falta_de_ponteiro(tmp_path):
    status, home = _preparar(tmp_path)
    antes = status.read_text()
    assert _rodar({"hook_event_name": "SubagentStart", "agent_type": "Explore"}, home).returncode == 0
    assert status.read_text() == antes
    assert _rodar({"hook_event_name": "SubagentStart", "agent_type": "kit-6x1:redator"},
                  tmp_path / "vazio").returncode == 0
    assert _rodar({"x": 1}, home).returncode == 0


def test_hooks_json():
    h = json.loads((RAIZ / "hooks" / "hooks.json").read_text())["hooks"]
    for evento in ("SubagentStart", "SubagentStop"):
        assert h[evento][0]["matcher"] == "^kit-6x1:"
        assert "hook_painel.py" in json.dumps(h[evento][0]["hooks"])


def test_revisor_reprovado_com_markdown(tmp_path):
    status, home = _preparar(tmp_path)
    _rodar({"hook_event_name": "SubagentStop", "agent_type": "kit-6x1:revisor-juridico",
            "last_assistant_message": "**REPROVADO** x"}, home)
    d = json.loads(status.read_text())
    assert d["agentes"][2]["estado"] == "fail"
    assert d["fluxo"] == [[2, 1, "back"]]


def test_outro_agente_comecando_com_reprovado_fica_ok(tmp_path):
    status, home = _preparar(tmp_path)
    _rodar({"hook_event_name": "SubagentStop", "agent_type": "kit-6x1:analista-dados",
            "last_assistant_message": "REPROVADO é a palavra do revisor, não minha."}, home)
    d = json.loads(status.read_text())
    assert d["agentes"][0]["estado"] == "ok"
    assert d["fluxo"] == [[0, "orq", "go"]]
