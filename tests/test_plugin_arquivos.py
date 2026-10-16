import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
AGENTES = {"analista-dados": "haiku", "estrategista": "sonnet", "revisor-juridico": "sonnet", "redator": "haiku"}


def _frontmatter(p: Path) -> dict:
    texto = p.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    assert m, f"{p} sem frontmatter"
    return dict(l.split(": ", 1) for l in m.group(1).splitlines() if ": " in l)


def test_agentes_com_modelo_certo():
    for nome, modelo in AGENTES.items():
        fm = _frontmatter(RAIZ / "agents" / f"{nome}.md")
        assert fm["name"] == nome
        assert fm["model"] == modelo
        assert fm["description"]


def test_skill():
    p = RAIZ / "skills" / "readequacao-6x1" / "SKILL.md"
    fm = _frontmatter(p)
    assert fm["name"] == "readequacao-6x1"
    assert len(fm["description"]) <= 1024
    corpo = p.read_text()
    for trecho in ("kit-6x1:analista-dados", "kit-6x1:estrategista", "kit-6x1:revisor-juridico",
                   "kit-6x1:redator", "--agentes-externos", "conferir-numeros", "aumento_vs_hoje",
                   "${CLAUDE_PLUGIN_ROOT}/scripts/kit6x1"):
        assert trecho in corpo


def test_marketplace():
    m = json.loads((RAIZ / ".claude-plugin" / "marketplace.json").read_text())
    assert m["plugins"][0]["name"] == "kit-6x1"
