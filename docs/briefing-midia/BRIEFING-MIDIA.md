# Briefing: pacote de mídia do Kit 6x1 para advogados

Cole este arquivo inteiro como tarefa num agente de programação (Codex, Claude Code ou similar), com uma cópia deste repositório aberta. Veja `COMO-USAR.md`, nesta pasta.

---

## 1. Tarefa

Criar, dentro do repositório, a pasta `midia/` com um **pacote de mídia replicável**: peças que **qualquer advogado** possa publicar no próprio Instagram, LinkedIn e WhatsApp, com a própria marca, para informar empresários sobre o fim da escala 6x1.

As peças são **informativas**, não ofertas de serviço. O advogado usa para mostrar conhecimento sobre o tema, dentro das regras da OAB.

Entregar:

1. o texto de todas as peças, em Markdown;
2. modelos visuais em HTML/CSS que aceitam a marca do advogado por variáveis;
3. um script que exporta os modelos para PNG;
4. um `midia/README.md` explicando como personalizar e exportar.

**Não altere nada fora de `midia/`**, exceto acrescentar uma linha no `README.md` da raiz apontando para `midia/README.md`.

## 2. Público e tom

- **Quem publica:** o advogado, no perfil dele.
- **Quem lê:** donos de pequenas e médias empresas (comércio, alimentação, serviços) que hoje usam a escala 6x1.
- **Tom:** sóbrio, claro, sem jargão desnecessário, frases curtas. Português do Brasil.
- **Nunca:** promessa de resultado, "economize X%", "contrate", "agende sua consulta", preço, honorário, gratuidade como chamariz, caso real de cliente, superlativos ("o maior", "o melhor"), comparação com colegas.

## 3. Fatos que podem ser usados (e só estes)

Não acrescente nenhuma lei, número, data ou interpretação que não esteja nesta lista. Onde aparecer `[CONFIRMAR: …]`, mantenha o marcador exatamente assim. O advogado preenche depois da promulgação.

| # | Fato | Observação |
|---|---|---|
| F1 | A PEC 221/2019 foi aprovada no Senado em 14/10/2026, em dois turnos, por 75 votos a 1, com o mesmo texto aprovado pela Câmara em maio de 2026 | Use "Emenda Constitucional nº [CONFIRMAR: número]" quando se referir ao texto promulgado |
| F2 | Jornada normal de até 8 horas por dia | |
| F3 | Teto semanal de 42 horas a partir de 60 dias da publicação: [CONFIRMAR: data] | |
| F4 | Teto semanal de 40 horas 12 meses depois: [CONFIRMAR: data] | Hoje o teto é de 44 horas |
| F5 | Dois dias de repouso semanal remunerado, um preferencialmente no domingo. Não precisam ser seguidos | |
| F6 | O salário não pode ser reduzido. Pisos, férias, FGTS e 13º também não | |
| F7 | Continuam permitidos: compensação de jornada e banco de horas por acordo ou convenção coletiva, a escala 12x36 e os regimes especiais | |
| F8 | Domingo trabalhado sem folga compensatória é pago em dobro | |
| F9 | Conta: 44 ÷ 40 − 1 = 10%. A hora trabalhada fica cerca de 10% mais cara na etapa de 40h, e cerca de 4,8% na etapa de 42h (44 ÷ 42 − 1) | Para o mesmo salário |
| F10 | Hora extra custa no mínimo 50% a mais que a hora normal. Se for habitual, gera risco de passivo trabalhista | |
| F11 | Mudar horário, turno ou escala do empregado exige cuidado: a CLT, no art. 468, proíbe alteração do contrato que cause prejuízo ao empregado sem o consentimento dele | Use só nesse nível de generalidade |
| F12 | A convenção coletiva da categoria pode ter regras próprias e precisa ser conferida em cada caso | Vai no aviso de toda peça |
| F13 | Em simulações feitas com o Kit 6x1, a escala 5x2 dentro da lei pode **custar mais** que a escala de hoje, mas custar **menos** que manter a 6x1 cobrindo a diferença com hora extra | Nunca apresente a 5x2 como "economia" |

## 4. Peças

### 4.1 Carrosséis para o Instagram (1080 × 1350 px, de 6 a 8 telas)

**Regras:**

- A tela 1 é a capa, com título forte e curto.
- A última tela traz:
  - nome e OAB do advogado (`{{nome}}`, `{{oab}}`);
  - o aviso padrão (seção 5);
  - o crédito (seção 6).
- No máximo 35 palavras por tela.

**Carrossel 1: "O que muda com o fim da 6x1"**

1. Capa: O que muda com o fim da 6x1. Resumo em 7 telas.
2. O que foi aprovado (F1).
3. 42 horas e depois 40 horas, com as datas `[CONFIRMAR]` (F3, F4).
4. Duas folgas por semana e até 8 horas por dia (F2, F5).
5. O salário não muda (F6).
6. O que continua valendo: 12x36, banco de horas, compensação por acordo, domingo em dobro (F7, F8).
7. Fecho: confira a convenção da sua categoria (F12), mais assinatura, aviso e crédito.

**Carrossel 2: "A hora do seu funcionário vai ficar 10% mais cara"**

1. Capa com a frase do título.
2. O mesmo salário vai pagar menos horas (F6, F4).
3. A conta: 44 ÷ 40 − 1 = 10% (F9). Mostrar como equação grande e limpa.
4. Na fase de 42h, cerca de 4,8% (F9).
5. "Vou cobrir com hora extra": custa no mínimo 50% a mais e, se for habitual, vira risco (F10).
6. O que fazer: rever a escala pelos horários de movimento, não pela soma de horas.
7. Fecho: assinatura, aviso e crédito.

**Carrossel 3: "Três caminhos para a sua escala"**

1. Capa: três caminhos para a sua escala depois da 6x1.
2. Caminho 1, manter tudo como está: deixa de ser possível acima do novo teto.
3. Caminho 2, manter a 6x1 e pagar a diferença em hora extra: custo alto e risco (F10).
4. Caminho 3, reorganizar a escala (por exemplo, 5x2) pelos horários de movimento.
5. A verdade incômoda (F13): reorganizar pode custar mais do que hoje, mas costuma custar menos que o caminho 2.
6. Cada empresa tem a sua conta: equipe, horário e convenção mudam o resultado (F12).
7. Fecho: assinatura, aviso e crédito.

**Carrossel 4: "Antes de mudar a escala, cuidado com isto"**

1. Capa com o título.
2. Mudar turno ou horário não é só uma decisão de gestão (F11).
3. A lei proíbe alteração que prejudique o empregado sem o consentimento dele (F11).
4. Boas práticas: comunicar com antecedência, registrar por escrito, ouvir a equipe.
5. Confira a convenção e os acordos coletivos (F12).
6. Fecho: assinatura, aviso e crédito.

**Carrossel 5: "Checklist dos 60 dias"**

1. Capa: checklist para os 60 dias da transição.
2. Levante a jornada atual de cada funcionário.
3. Mapeie os horários de pico de movimento.
4. Confira a convenção coletiva da categoria (F12).
5. Simule os cenários de escala e custo.
6. Comunique a equipe e registre as mudanças (F11).
7. Revise antes da etapa de 40 horas (F4).
8. Fecho: assinatura, aviso e crédito.

### 4.2 Posts únicos (1080 × 1350 px)

São 5 posts, com uma frase central cada, mais uma linha de apoio:

1. "44 → 42 → 40." Apoio: o novo teto semanal chega em duas etapas (F3, F4).
2. "Mesmo salário. Menos horas." Apoio: F6.
3. "Hora extra não é plano." Apoio: F10.
4. "Duas folgas por semana." Apoio: F5.
5. "A convenção da sua categoria pode mudar tudo." Apoio: F12.

### 4.3 Stories (1080 × 1920 px)

Uma sequência de 4 telas, com o conteúdo do carrossel 1 resumido e uma enquete sugerida no texto: "Sua empresa usa 6x1 hoje? Sim / Não". Não peça contato.

### 4.4 Roteiro de vídeo curto (Reels/Shorts, de 60 a 90 s)

- **Formato:** em Markdown, com colunas "tempo / fala / texto na tela".
- **Estrutura:**
  - gancho em 3 s ("A hora do seu funcionário vai ficar 10% mais cara");
  - a conta (F9);
  - o risco da hora extra (F10);
  - os três caminhos (carrossel 3);
  - fecho com o aviso F12.
- **Assinatura:** o advogado aparece falando, com o nome e a OAB na tela.

### 4.5 Texto para LinkedIn (de 300 a 450 palavras)

Mesmo conteúdo dos carrosséis 2 e 3, em prosa, com o aviso no fim.

### 4.6 Mensagem para a carteira de clientes (WhatsApp e e-mail)

Texto curto e informativo, **só para quem já é cliente do advogado**. Deve:

- avisar que a mudança foi aprovada e resumir F3 a F6;
- dizer que vale a pena revisar a escala antes das datas.

Não oferecer serviço com preço nem prometer resultado. Duas versões: WhatsApp (até 600 caracteres) e e-mail (com assunto).

### 4.7 Legendas

Uma legenda pronta para cada carrossel e post, com:

- de 80 a 150 palavras;
- no máximo 5 hashtags, escolhidas entre: #escala6x1 #direitodotrabalho #pec221 #gestaodepessoas #empresarios;
- o aviso padrão no fim.

## 5. Aviso padrão (obrigatório na última tela e nas legendas)

> Conteúdo informativo. Não substitui a análise do caso concreto. A convenção coletiva da categoria pode ter regras próprias.

## 6. Crédito (obrigatório na última tela, em letra pequena)

> Conteúdo base: @abussafi · Kit 6x1 para advogados · CC BY 4.0

O texto das peças fica sob a licença CC BY 4.0. Acrescente `midia/LICENSE-MIDIA.md` com o texto da licença e a regra de atribuição.

## 7. Identidade visual (o advogado aplica a marca dele)

Modelos em HTML/CSS com variáveis num arquivo único, `midia/marca.json`:

```json
{
  "nome": "Dra. Nome Sobrenome",
  "oab": "OAB/SP 000.000",
  "escritorio": "",
  "cor_primaria": "#1F2A44",
  "cor_secundaria": "#C9A227",
  "cor_fundo": "#F5F3EE",
  "cor_texto": "#1F2A44",
  "fonte_titulo": "Playfair Display",
  "fonte_texto": "Inter",
  "logo": "logo.png"
}
```

**Regras visuais:**

- **Paleta padrão neutra**, como a acima. Não use as cores, fontes ou o logotipo de Abussafi, nem de nenhum escritório real.
- **Fontes:** só Google Fonts. Contraste mínimo WCAG AA.
- **Hierarquia:** título grande (de 64 a 88 px na capa) e corpo de no mínimo 36 px no carrossel.
- **Margens:** de no mínimo 80 px.
- **Elementos:** no máximo 1 ícone ou forma por tela. Nada de banco de imagens nem fotos de pessoas.
- **Logotipo:** se `logo` estiver vazio, a peça funciona sem ele.
- **Campos vazios:** se `escritorio` estiver vazio, não aparece.

## 8. Estrutura de arquivos

```
midia/
├── README.md                  como personalizar e exportar, passo a passo para leigo
├── LICENSE-MIDIA.md
├── marca.json                 variáveis da marca
├── textos/
│   ├── carrosseis.md          as 5 sequências, tela a tela
│   ├── posts.md
│   ├── stories.md
│   ├── roteiro-video.md
│   ├── linkedin.md
│   ├── mensagem-clientes.md
│   └── legendas.md
├── modelos/                   HTML/CSS que leem marca.json e textos estruturados
│   ├── carrossel.html
│   ├── post.html
│   └── story.html
├── dados/                     conteúdo estruturado (JSON) usado pelos modelos
├── exportar.py                gera os PNG em midia/saida/ (Playwright ou Chrome headless)
└── saida/                     PNG gerados (no .gitignore, exceto os exemplos)
    └── exemplo/               1 carrossel exportado com a marca padrão, para mostrar o resultado
```

`exportar.py` precisa:

- rodar com `python3 midia/exportar.py`;
- instalar o que faltar com instruções claras;
- gerar um PNG por tela, com nomes como `carrossel-1-tela-01.png`.

## 9. Critérios de aceite

- [ ] Toda afirmação jurídica corresponde a um fato da seção 3. Nenhum fato novo.
- [ ] Todos os marcadores `[CONFIRMAR: …]` foram preservados.
- [ ] O aviso padrão e o crédito aparecem em toda última tela e em toda legenda.
- [ ] Nenhuma ocorrência de: "economize", "garantido", "contrate", "agende", "consulta grátis", "R$", "honorário", "melhor", "maior".
- [ ] Nome e OAB vêm de `marca.json` em todas as peças visuais.
- [ ] Nenhuma cor, fonte ou logotipo de escritório real.
- [ ] `python3 midia/exportar.py` gera todos os PNG sem erro, e os PNG de exemplo foram conferidos visualmente (texto sem cortar, contraste legível).
- [ ] O `midia/README.md` explica, para quem nunca programou, como trocar a marca, editar um texto e exportar.
- [ ] Nada fora de `midia/` foi alterado, além da linha no README da raiz.
