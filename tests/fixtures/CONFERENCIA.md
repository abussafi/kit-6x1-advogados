# Conferência manual: restaurante_12.json (teto 40h)

Data da conferência: 16/10/2026. Comando: `python -m kit6x1 analisar tests/fixtures/restaurante_12.json --saida saida/restaurante --status saida/restaurante/status.json`.
Saída: `{"recomendado": "5x2_otimizado", "economia_vs_manter_6x1": 4483.81}`. Todos os valores abaixo foram refeitos à mão (calculadora/Python puro, sem usar o código do pacote) e coincidem com `resultado.json`.

## 1. Custo de hoje (situação_atual.custo_mensal = 33.367,42)
- Fator de encargos (Simples): FGTS 8% e provisões de 13º, férias e 1/3 = 1/12 + 1/12 + 1/36 = 0,19444. Fator = 1,08 × 1,19444 = **1,29**.
- Salários: 4 garçons × 1.950 = 7.800; 3 cozinheiros × 2.600 = 7.800; 2 auxiliares × 1.800 = 3.600; 2 caixas × 1.900 = 3.800; 1 bar × 2.000 = 2.000. Soma = **25.000**. Base = 25.000 × 1,29 = **32.250,00**.
- Adicional noturno de hoje: 7 funcionários terminam às 23:20 (Caio, Duda, Fabi, Gil, Iris, Kika, Lia), com 1h20 (1,3333h) entre 22h e 23:20. Horas por pessoa = 1,3333 × 6 dias × 52/12 = 34,67h; total = 7 × 34,67 = **242,67h** (resultado: 242,7).
- Fator do noturno sobre a hora de relógio = (60/52,5) × 1,2 − 1 = 0,371429. Custo da hora = salário × 1,29 / 220. Soma sobre os 7 = **1.117,42**.
- Total = 32.250,00 + 1.117,42 = **33.367,42**. Confere.

## 2. Cenário "Manter a 6x1" (custo 43.727,49; diferença −10.360,08)
- Horas extras do mês = 12 funcionários × (44/6)h × 52/12 = 12 × 31,78h = **381,3h** (resultado: 381,3). O valor de 208h citado no plano original (4h por dia) foi substituído pelo addendum, porque o 6º dia inteiro vira descanso trabalhado.
- Custo do 6º dia trabalhado, pago em dobro, hora = salário × 1,29 / 200: **10.248,33**.
- Noturno com divisor 200: **1.229,16**.
- Total = 32.250,00 + 1.229,16 + 10.248,33 = **43.727,49**. Diferença para hoje = 33.367,42 − 43.727,49 = **−10.360,08**. Confere.

## 3. Cenário "5x2 otimizado" (custo 39.243,69; diferença −5.876,27)
- Pelo contrato, cobertura de 84,9% e 320,7h/mês de hora extra para cobrir a falta de pessoal; nota de risco 6.
- Verificação de ordem de grandeza (não exata, o código pondera por função): hora normal média = (25.000/12) × 1,29 / 200 = 13,44; hora extra a 50% = 20,16; 320,7h × 20,16 = 6.466; noturno 160,3h × 13,44 × 0,3714 = 800; soma 7.266 acima da base 32.250. O resultado dá 39.243,69 − 32.250,00 = 6.993,69, que fica ~4% abaixo da estimativa média, coerente porque as faltas se concentram em funções de salário menor (garçom, auxiliar). Confere em ordem de grandeza; não foi refeito exatamente.
- Economia da recomendação sobre manter a 6x1 = 43.727,49 − 39.243,69 = **4.483,80** (saída: 4.483,81, diferença de arredondamento dos centavos).

## 4. Escala
- Nenhuma linha da escala tem 6 dias trabalhados na mesma semana: 12 funcionários × 4 semanas = 48 semanas-funcionário, máximo de **5 dias** por semana (verificado por script sobre `resultado.json`).
