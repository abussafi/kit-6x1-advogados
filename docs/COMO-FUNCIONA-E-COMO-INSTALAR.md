# Kit 6x1 para advogados: como funciona e como instalar

**Versão 0.2.1.** Material gratuito para advogados, por Antonio Marcos Gonçalves Abussafi.

---

## 1. O que é

O Kit 6x1 é uma *skill* para o **Claude Code**, o assistente de IA da Anthropic que trabalha com arquivos no seu computador.

Ele ajuda o advogado a analisar a escala de trabalho de um cliente empresário diante do fim da escala 6x1 (PEC 221/2019). O teto semanal passa a ser de 42h na transição e de 40h depois, e as folgas semanais passam a ser duas, sem redução de salário.

Com os dados do cliente, o kit:

1. confere os dados informados e aponta erros e lacunas;
2. calcula cenários de escala e de custo com um motor de cálculo próprio. As contas são feitas por programa, não pela IA;
3. submete os cenários a um **revisor jurídico** automático, que tenta derrubar a solução antes que ela chegue ao cliente;
4. entrega um **relatório técnico** para o advogado, um **calendário da nova escala** e um **painel ao vivo** que mostra cada etapa no navegador.

O advogado decide em duas paradas: primeiro confirma as premissas, depois escolhe o cenário. Nada segue sem a sua confirmação.

## 2. Como funciona, passo a passo

| Etapa | Quem faz | O que acontece |
|---|---|---|
| Entrada dos dados | Você | Por formulário no navegador, por arquivo ou conversando com o Claude: empresa, horário de funcionamento e funcionários |
| Conferência | Agente "Analista de dados" | Valida os dados e aponta o que corrigir |
| **Parada 1** | Você | Confirma o teto (40h final ou 42h da transição), a data de início e a premissa de demanda |
| Cenários | Agente "Estrategista" + motor | Calcula os cenários: custo mensal, aumento em relação a hoje, economia em relação a manter a 6x1, cobertura e risco |
| Revisão | Agente "Revisor jurídico" | Confere a escala contra as regras e aprova ou reprova, com ressalvas |
| **Parada 2** | Você | Escolhe o cenário ou ajusta as premissas e recalcula |
| Relatório | Agente "Redator" | Monta o relatório técnico. O motor confere se todo número do texto bate com o cálculo |

**Regra central:** nenhum número sai da IA. Todo valor vem do motor de cálculo e é conferido automaticamente no relatório final.

## 3. Requisitos

- **Claude Code** com conta Claude em plano pago (Pro ou Max), usado pelo app Claude para desktop ou pelo Terminal.
- **Mac**. O kit foi testado no macOS. No Windows, ele só deve funcionar dentro do WSL, e isso não foi testado.
- **Python 3.10 ou superior.** Na primeira execução, o kit prepara sozinho um ambiente isolado. Leva cerca de 1 minuto e exige internet.

## 4. Instalação (cerca de 5 minutos)

O kit é instalado direto do GitHub: <https://github.com/abussafi/kit-6x1-advogados>.

1. **Abra o Terminal** (Aplicativos > Utilitários > Terminal) e rode os dois comandos abaixo, um de cada vez:

   ```
   claude plugin marketplace add abussafi/kit-6x1-advogados
   ```

   ```
   claude plugin install kit-6x1@kit-6x1-advogados
   ```

   Se você usa o Claude Code no Terminal, também pode digitar, dentro dele, `/plugin marketplace add abussafi/kit-6x1-advogados` e depois `/plugin install kit-6x1@kit-6x1-advogados`.
2. **Reinicie o Claude Code**: feche e abra o app, ou abra uma sessão nova no Terminal.
3. **Confira a instalação.** O comando abaixo deve listar `kit-6x1`:

   ```
   claude plugin list
   ```

**Permissões:** na primeira execução, o Claude Code pergunta se pode rodar o lançador do kit (`scripts/kit6x1`). Escolha a opção de permitir sempre para esse comando, para não ser interrompido a cada etapa.

## 5. Primeiro uso: teste com o exemplo

Antes de usar com um cliente, faça um teste com o caso de exemplo que vem no kit:

1. Crie uma pasta de teste, por exemplo `Teste 6x1`, e abra essa pasta no Claude Code.
2. Peça:

   > Faça a readequação 6x1 usando o arquivo de exemplo exemplos/loja_8.json do kit.

   Ou use o comando `/kit-6x1:readequacao-6x1` e escolha a opção de arquivo pronto.
3. Acompanhe o painel no navegador, responda às duas paradas e confira o relatório gerado.

O kit traz dois exemplos, ambos fictícios: `exemplos/loja_8.json` (loja com 8 funcionários) e `exemplos/restaurante_12.json` (restaurante com 12).

**Recomendação:** use o modelo **Opus** na sessão, porque é ele que conduz o processo. Os agentes usam Sonnet e Haiku automaticamente.

## 6. Uso com um cliente

1. Crie uma pasta para o cliente e abra-a no Claude Code.
2. Peça "faça a readequação 6x1 deste cliente".
3. Informe os dados pelo formulário que abre no navegador.
4. Ao final, você recebe dentro da pasta do cliente:
   - `readequacao-6x1/<data-hora>/relatorio-tecnico.md`: o relatório técnico;
   - o link do calendário da nova escala, que funciona enquanto o painel estiver aberto.

   Para reabrir o painel depois, peça ao Claude ou rode o comando que ele mostrar no fechamento.

## 7. Limites e cuidados

- **A convenção coletiva não é considerada.** Domingos, feriados, compensação, pisos e adicionais da categoria precisam ser conferidos por você.
- **Os resultados são estimativas técnicas** para apoiar o seu trabalho. Não substituem a análise jurídica do caso.
- **Datas da PEC:** confira a emenda promulgada e as datas de vigência antes de orientar o cliente.
- **Dados pessoais (LGPD):** o motor roda no seu computador, mas o que você digita na conversa é processado pela Anthropic. Prefira códigos (F01, F02…) a nomes de funcionários, e siga a política de dados do seu escritório.
- **Sigilo profissional:** use a sua conta e o seu computador. Não compartilhe as pastas de clientes.

## 8. Atualizar ou remover

- **Atualizar:** rode o comando abaixo e reinicie o Claude Code:

  ```
  claude plugin marketplace update kit-6x1-advogados
  ```

- **Remover:**

  ```
  claude plugin uninstall kit-6x1@kit-6x1-advogados
  ```

## Licença e atribuição

- **Código:** Apache License 2.0. Você pode usar, adaptar e redistribuir o kit, desde que:
  - mantenha os arquivos `LICENSE` e `NOTICE`;
  - indique o que alterou;
  - não use o nome do autor nem o do kit para promover versões modificadas.
- **Este guia:** CC BY 4.0, com atribuição a Antonio Marcos Gonçalves Abussafi.

## 9. Problemas comuns

| Sintoma | O que fazer |
|---|---|
| "Python 3 não encontrado" | Instale o Python 3.12 pelo site python.org, ou instale o `uv`, e tente de novo |
| A primeira execução demora | É normal: o kit está preparando o ambiente, cerca de 1 minuto |
| O Claude não encontra a skill | Rode `claude plugin list`. Se o kit não aparecer, refaça o passo 3 da instalação e reinicie o Claude Code |
| "Sem escala viável" | A equipe não cobre o horário de funcionamento com as novas regras. Revise os dados ou as premissas |
| O link do calendário não abre | O painel foi encerrado. Peça ao Claude para reabrir o painel |
