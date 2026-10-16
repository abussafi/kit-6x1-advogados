# Como usar o briefing de mídia

O arquivo [`BRIEFING-MIDIA.md`](BRIEFING-MIDIA.md) é uma tarefa pronta para um agente de IA de programação (Codex, Claude Code ou similar). Com ele, o agente monta um **pacote de mídia sobre o fim da escala 6x1** que você publica no seu Instagram, LinkedIn e WhatsApp, com a sua marca:

- 5 carrosséis;
- 5 posts;
- stories;
- roteiro de vídeo curto;
- texto para LinkedIn;
- legendas;
- mensagem para a sua carteira de clientes.

## Para quem é

Para o advogado que quer informar empresários sobre a PEC 221/2019 sem começar do zero. As peças são **informativas** e foram escritas dentro do Provimento 205/2021 da OAB:

- sem oferta de serviço;
- sem promessa de resultado;
- sem preço.

## Passo a passo

1. **Copie o repositório.** No GitHub, clique em **Fork** (ou baixe o .zip em *Code → Download ZIP*) para ter a sua própria cópia.
2. **Abra a cópia no agente.**
   - **Claude Code:** abra a pasta do repositório.
   - **Codex:** conecte o seu fork.
3. **Envie a tarefa.** Copie todo o conteúdo de `BRIEFING-MIDIA.md` e cole como tarefa. O agente cria a pasta `midia/` com os textos, os modelos visuais e o script de exportação.
4. **Coloque a sua marca.** Abra `midia/marca.json` e preencha:
   - nome e OAB;
   - escritório (opcional);
   - cores, fontes e logotipo.

   Se tiver um logotipo, coloque o arquivo na pasta `midia/` com o nome indicado em `"logo"`.
5. **Gere as imagens.** Rode `python3 midia/exportar.py`. Os PNG prontos para postar ficam em `midia/saida/`.
6. **Confira antes de publicar** (veja abaixo).

## Antes de publicar, confira

- [ ] **Datas da lei.** Substitua todos os marcadores `[CONFIRMAR: …]` pelos dados do texto promulgado (número da emenda e datas de vigência). Não publique peças com o marcador.
- [ ] **Convenção coletiva.** Se você atende uma categoria específica, veja se a convenção dela muda alguma informação das peças.
- [ ] **Fatos.** Toda afirmação jurídica deve corresponder à tabela de fatos da seção 3 do briefing. Se o agente acrescentou algo que não está lá, apague.
- [ ] **OAB.** Leia cada peça procurando promessa de resultado, chamada para contratar, preço ou comparação com colegas. A seção 9 do briefing tem a lista completa.
- [ ] **Visual.** Confira se nenhum texto ficou cortado e se as cores têm contraste suficiente para leitura no celular.
- [ ] **Aviso e crédito.** Precisam estar na última tela de cada carrossel e em cada legenda.

## Pode mudar o briefing?

Pode. Os ajustes mais comuns:

- trocar a paleta padrão;
- reduzir o número de peças;
- mudar o público (por exemplo, só restaurantes).

Mantenha três coisas:

- a tabela de fatos;
- o aviso padrão;
- o crédito.

São eles que protegem você de erro jurídico e de problema com a OAB.

## Crédito e licença

Os textos das peças e este briefing estão sob a licença [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br). Você pode usar, adaptar e publicar, inclusive no seu perfil profissional, desde que mantenha o crédito:

> Conteúdo base: @abussafi · Kit 6x1 para advogados · CC BY 4.0

## Responsabilidade

O conteúdo é informativo e não substitui a análise do caso concreto. Quem publica é responsável por conferir as informações, as datas de vigência e a adequação às regras de publicidade da OAB.
