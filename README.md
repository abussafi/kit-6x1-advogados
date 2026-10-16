# Kit 6x1 para advogados

Skill para o **Claude Code** que apoia o advogado na readequação da escala de trabalho de um cliente ao fim da escala 6x1 (PEC 221/2019). A PEC prevê 42 horas semanais na transição, 40 horas depois, duas folgas semanais e nenhuma redução de salário.

Com os dados do cliente, o kit:
- confere a entrada;
- calcula cenários de escala e custo com um motor determinístico (as contas são feitas por programa, não pela IA);
- submete os cenários a um revisor jurídico automático;
- entrega um **relatório técnico**, o **calendário da nova escala** e um **painel ao vivo**.

O advogado decide em duas paradas: primeiro confirma as premissas, depois escolhe o cenário.

> Material técnico de apoio. Não constitui parecer jurídico, não substitui a análise do caso concreto e não considera convenções ou acordos coletivos. Confira o texto da emenda constitucional promulgada e as datas de vigência antes de orientar o cliente.

## Requisitos

- Claude Code em plano pago da Claude (Pro ou Max), pelo app para desktop ou pelo Terminal.
- macOS. No Windows, só pelo WSL, e esse caminho não foi testado.
- Python 3.10 ou superior. Na primeira execução, o kit prepara um ambiente isolado em cerca de 1 minuto.

## Instalação

No Terminal, rode um comando de cada vez:

```bash
claude plugin marketplace add abussafi/kit-6x1-advogados
```

```bash
claude plugin install kit-6x1@kit-6x1-advogados
```

Depois, reinicie o Claude Code. Para conferir se o kit foi instalado:

```bash
claude plugin list
```

Na primeira execução, o Claude Code pergunta se pode rodar o lançador do kit (`scripts/kit6x1`). Permita sempre para esse comando, para não ser interrompido a cada etapa.

## Primeiro uso

1. Crie uma pasta de teste e abra-a no Claude Code. A recomendação é usar o modelo Opus.
2. Peça: *"Faça a readequação 6x1 usando o arquivo de exemplo exemplos/loja_8.json do kit"*. Também dá para usar o comando `/kit-6x1:readequacao-6x1`.
3. Acompanhe o painel no navegador, responda às duas paradas e leia o relatório técnico gerado na pasta.

Os exemplos fictícios ficam em [`exemplos/`](exemplos). O passo a passo completo está em [`docs/COMO-FUNCIONA-E-COMO-INSTALAR.md`](docs/COMO-FUNCIONA-E-COMO-INSTALAR.md).

## Atualizar e remover

Para atualizar, rode o comando abaixo e reinicie o Claude Code:

```bash
claude plugin marketplace update kit-6x1-advogados
```

Para remover:

```bash
claude plugin uninstall kit-6x1@kit-6x1-advogados
```

## Material de mídia para divulgar

Em [`docs/briefing-midia/`](docs/briefing-midia) há um briefing pronto para um agente de IA (Codex, Claude Code ou similar) montar, com a sua marca, um pacote de carrosséis, posts, stories, roteiro de vídeo e legendas sobre o fim da 6x1. O conteúdo é informativo e foi escrito dentro do Provimento 205/2021 da OAB. Leia antes o [`COMO-USAR.md`](docs/briefing-midia/COMO-USAR.md).

## Cuidados com dados

O motor roda no seu computador, mas o texto digitado na conversa é processado pela Anthropic. Prefira códigos (F01, F02…) a nomes de funcionários e siga a política de dados e de sigilo do seu escritório.

## Licença e atribuição

- **Código:** [Apache License 2.0](LICENSE). Você pode usar, adaptar e redistribuir o kit, inclusive em contexto profissional, desde que:
  - mantenha os arquivos `LICENSE` e [`NOTICE`](NOTICE);
  - indique os arquivos que alterou;
  - não use o nome do autor nem o nome do kit para promover versões modificadas.
- **Documentação** (este README e a pasta `docs/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br), com atribuição a Antonio Marcos Gonçalves Abussafi.

Autor: **Antonio Marcos Gonçalves Abussafi**.
