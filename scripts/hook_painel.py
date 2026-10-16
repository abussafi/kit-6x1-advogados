"""Hook SubagentStart/SubagentStop: acende os agentes do Kit 6x1 no painel ao vivo.

Só usa a biblioteca padrão e o módulo kit6x1.status (sem dependências externas).
Nunca deixa o hook falhar: qualquer erro termina em silêncio com código 0.
"""
from __future__ import annotations  # o python3 do sistema pode ser 3.9

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

NOMES = {"analista-dados": "Analista de dados", "estrategista": "Estrategista",
         "revisor-juridico": "Revisor jurídico", "redator": "Redator"}


def _status_atual() -> Path | None:
    home = Path(os.environ.get("KIT6X1_HOME", Path.home() / ".kit6x1"))
    ponteiro = home / "rodada-atual"
    if not ponteiro.is_file():
        return None
    caminho = Path(ponteiro.read_text(encoding="utf-8").strip())
    return caminho if caminho.is_file() else None


def main() -> None:
    from kit6x1.status import AGENTES_SKILL, StatusWriter

    evento = json.load(sys.stdin)
    tipo = str(evento.get("agent_type", ""))
    if not tipo.startswith("kit-6x1:") or tipo.split(":", 1)[1] not in NOMES:
        return
    caminho = _status_atual()
    if caminho is None:
        return
    nome = NOMES[tipo.split(":", 1)[1]]
    i = [n for n, _ in AGENTES_SKILL].index(nome)
    w = StatusWriter.abrir(caminho)
    if evento.get("hook_event_name") == "SubagentStart":
        w.agente_por_nome(nome, "run", "trabalhando…")
        fluxo = [["orq", i, "go"]] + ([[i - 1, i, "data"]] if i > 0 else [])
        w.etapa(f"{nome} trabalhando", fluxo=fluxo)
    elif evento.get("hook_event_name") == "SubagentStop":
        msg = str(evento.get("last_assistant_message", "")).strip()
        reprovou = (tipo.split(":", 1)[1] == "revisor-juridico"
                    and msg.lstrip("*_#> \t\n").upper().startswith("REPROVADO"))
        if reprovou:
            w.agente_por_nome(nome, "fail", "reprovou")
            w.etapa("Revisor reprovou: volta ao Estrategista", log=msg[:200], fluxo=[[i, 1, "back"]])
        else:
            w.agente_por_nome(nome, "ok", "concluído")
            w.etapa(f"{nome} concluiu", fluxo=[[i, "orq", "go"]])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # o painel é acessório: nunca interromper a sessão
        pass
    sys.exit(0)
