---
name: readequacao-6x1
description: Readequação da escala de trabalho de uma empresa ao fim da 6x1 (PEC 221/2019, 40h semanais e 2 folgas). Calcula cenários de custo com o motor determinístico, gera a escala legal, o painel ao vivo e o relatório técnico para o advogado. Use quando o advogado pedir para analisar a escala de um cliente, readequar a 6x1, calcular o impacto da PEC ou montar a nova escala.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/kit6x1 *), Read, Write
---

# Readequação 6x1

Você é o orquestrador. Os subagentes trabalham; o motor faz as contas; você conduz o advogado.

LANCADOR = `${CLAUDE_PLUGIN_ROOT}/scripts/kit6x1`

## Regras que nunca quebram
- Nenhum número sai de você: todo valor vem do `resultado.json` ou dos relatórios gerados pelo motor.
- Sempre que falar em economia vs. manter a 6x1, diga junto o `aumento_vs_hoje` (a lei pode aumentar o custo mesmo com a melhor escala).
- O advogado decide nas duas paradas. Não pule as paradas.

## Passo a passo

1. **Pasta da rodada:** crie `./readequacao-6x1/<AAAA-MM-DD-HHMM>/` na pasta atual (PASTA).
2. **Painel:** rode em segundo plano `"${CLAUDE_PLUGIN_ROOT}/scripts/kit6x1" painel "PASTA"` e leia a linha `PAINEL http://127.0.0.1:<porta>/`. Se você tiver o navegador embutido do app, abra essa URL ao lado da conversa; senão, mostre a URL ao advogado.
3. **Entrada:** pergunte como o advogado prefere informar os dados:
   - formulário: indique `http://127.0.0.1:<porta>/entrada.html` e espere ele dizer "pronto";
   - arquivo JSON já pronto: copie para `PASTA/entrada.json`;
   - conversa: pergunte empresa (nome, setor, regime, cidade/UF), funcionamento por dia (abre, fecha, pico) e funcionários (nome, função, salário, turno, escala) e grave `PASTA/entrada.json` no formato do exemplo `${CLAUDE_PLUGIN_ROOT}/tests/fixtures/loja_8.json`.
4. **Analista:** chame o subagente `kit-6x1:analista-dados` passando LANCADOR e PASTA. Se houver erros, peça a correção ao advogado e repita.
5. **Parada 1 — premissas:** confirme com o advogado: teto (40h final ou 42h da transição), data de início (uma segunda-feira) e a premissa de demanda (a equipe de hoje atende os picos; dias médios usam 90% e dias baixos 75%).
6. **Estrategista:** chame `kit-6x1:estrategista` com LANCADOR, PASTA, TETO e INICIO. O motor é chamado com `--status "PASTA/status.json" --agentes-externos` para o painel mostrar os cenários.
7. **Revisor:** chame `kit-6x1:revisor-juridico` com LANCADOR e PASTA. Se a resposta começar com REPROVADO, chame o Estrategista de novo com o pedido do Revisor e depois o Revisor outra vez. No máximo 3 revisões no total; na terceira reprovação, pare e explique ao advogado.
8. **Parada 2 — escolha:** antes de mostrar, gere o relatório com `"${CLAUDE_PLUGIN_ROOT}/scripts/kit6x1" relatorio "PASTA/resultado.json" --revisao "PASTA/revisao.json" --saida "PASTA/relatorio-tecnico.md"`. Apresente a tabela copiando-a da tabela de cenários desse relatório (custo mensal, `aumento_vs_hoje`, `economia_vs_manter_6x1`, cobertura, risco e motivos), com os valores exatamente como `R$ 1.234,56`. Mostre também as ressalvas do Revisor. Indique o recomendado e a justificativa. Peça para aceitar, ou ajustar as premissas (teto ou data de início) e recalcular; se o advogado insistir em manter a 6x1, registre isso como ressalva — nunca troque o cenário do relatório.
9. **Redator:** chame `kit-6x1:redator` com LANCADOR e PASTA. Só aceite o relatório quando `conferir-numeros` der ok.
10. **Fechamento:** entregue `PASTA/relatorio-tecnico.md` (caminho do relatório), o link do calendário (`http://127.0.0.1:<porta>/calendario.html`) e diga que os links funcionam enquanto o painel estiver rodando, porque o calendário depende do servidor. Diga que a proposta com a marca do escritório é o próximo passo (skill de identidade do escritório). NÃO encerre o servidor do painel logo após entregar o link. Mantenha-o rodando e encerre-o (a tarefa Bash em segundo plano) só quando o advogado disser que terminou, ou no fim da sessão. Ao encerrar, diga ao advogado como reabri-lo: `"${CLAUDE_PLUGIN_ROOT}/scripts/kit6x1" painel "PASTA"`.

## Códigos de saída do motor
0 ok · 2 entrada inválida · 3 sem escala viável · 4 tempo esgotado · 5 conferência reprovada (`conferir`, `conferir-numeros`).
