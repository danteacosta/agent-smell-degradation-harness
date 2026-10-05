# Pré-registro: adequação por mutação de suítes de teste geradas por LLM

Data: 2026-10-05. Status: **registrado antes de qualquer geração de suíte.** Script: `scripts/mutation_adequacy.py`. Runner no Mac: `scripts/run_mutation_adequacy.sh`. Testes: `tests/test_mutation_adequacy.py`.

## 1. Pergunta

Uma suíte de testes escrita por um LLM a partir de um pedido incompleto percebe quando a implementação perdeu a regra que faltava no pedido? E uma suíte escrita a partir da especificação completa percebe?

O estudo amplia o diagnóstico de ancoragem de testes de 02/10 (3 requisitos, 0/11 contra 11/11) para todos os requisitos elegíveis da coleta dos 46, **sem gerar nenhuma implementação nova**.

## 2. Unidades e papéis

Tudo vem da coleta congelada de 03/10 (`data/selection-abc-results/20261003`). Os papéis são definidos pelo oráculo já registrado:

| Papel | Definição | Contagem |
| --- | --- | ---: |
| Correta | implementação do braço A com veredito `pass` | 91 |
| Mutante confirmado | implementação do braço C com veredito `target_only_failure`: perdeu a regra e o oráculo comprovou | 81 |
| Recuperada | implementação do braço C com veredito `pass`: o pedido omitia a regra, mas o agente a manteve | 17 |

Falhas mistas, falhas em A e desconhecidos não entram como mutantes confirmados. Nos 25 requisitos elegíveis, há também uma página C com falha mista e uma com erro de navegador: elas entram apenas como `unconfirmed` no escore ingênuo, que considera as 100 páginas C, sem mudar os 81 mutantes confirmados.

**Elegibilidade (mecânica):** pelo menos uma implementação correta e um mutante confirmado. São **25 requisitos em 8 projetos**.

**Implementação de referência:** uma correta por requisito, sorteada com `random.Random("2026100507:<caso>")`.

## 3. Suítes

Um modelo testador (padrão `gpt-6-astra`) escreve 2 suítes de cada fonte, por requisito, com as mesmas instruções do diagnóstico de 02/10:

| Fonte | O testador vê |
| --- | --- |
| `spec_complete` | o requisito completo (A) e a página base |
| `spec_incomplete` | o pedido incompleto (C) e a página base |
| `code_incomplete` | o pedido incompleto e a implementação de referência, como um revisor do PR veria |

São 25 × 3 × 2 = 150 chamadas, geradas uma vez, sem retry e sem reparo, em ordem sorteada com semente 2026100507. Os prompts são congelados com hash antes da primeira chamada.

## 4. Execução e medidas

Cada suíte roda contra todas as implementações corretas, mutantes e recuperadas do seu requisito, na imagem qualificada e sem rede (cerca de 1.100 execuções). O runner precisa reproduzir antes os controles autorados do diagnóstico de 02/10; se não reproduzir, nenhuma suíte gerada roda.

- **Suíte sólida:** fica quieta na implementação de referência.
- **Mutante morto:** uma suíte sólida dispara alarme nele (falha de asserção ou erro).
- **Escore de mutação de uma suíte:** mutantes mortos ÷ mutantes confirmados do requisito.
- **Escore do requisito para uma fonte:** a média das suas 2 suítes.
- **Suítes inutilizáveis** (falha de geração, suíte inválida ou erro do runner em qualquer execução da suíte) contam como não sólidas e não matam nada (intenção de testar).

## 5. Hipóteses e decisão

**MA1 (principal).** O escore de mutação de `spec_complete` é maior que o de `spec_incomplete`.

Estimador: a média, entre requisitos, da diferença de escore entre as duas fontes. É considerada suportada se as duas condições valem juntas:
- o limite inferior do IC 95% por bootstrap de projetos (4.000 reamostragens) fica acima de 0;
- o p bilateral do teste exato de inversão de sinais por projeto fica abaixo de 0,05.

Com 8 projetos, o menor p possível é 2/256 ≈ 0,0078.

**MA2 (secundária).** `spec_complete` tem escore maior que `code_incomplete`. Mesmo estimador e mesma regra.

**Previsão a partir do piloto:** `spec_complete` perto do teto; `spec_incomplete` e `code_incomplete` perto de zero, porque as suítes herdam a omissão do pedido.

**Descritivas, sem decisão:**
- **Fração de suítes sólidas por fonte.** Mede falsos alarmes contra implementações corretas.
- **Alarmes em implementações recuperadas e em outras corretas.** Uma suíte sólida não deveria disparar nelas.
- **Escore "ingênuo".** Trata todas as implementações de C como mutantes, sem confirmação do oráculo, e é comparado ao escore confirmado. As duas versões são reportadas com o mesmo peso por requisito e também como proporções agregadas, para não confundir mudança de rótulo com mudança de ponderação. Isso mostra quanto uma análise de mutação de especificação erraria se não verificasse que o mutante realmente viola a regra.
- **Requisitos com todos os mutantes mortos e com nenhum morto,** por fonte.

## 6. O que este estudo não é

- **Não é confirmatório para a tese principal.** As implementações e os vereditos do oráculo já eram conhecidos, e o autor sabe quais requisitos degradaram. O que é prospectivo é a geração das suítes e a sua execução.
- **O testador é do mesmo provedor que os geradores.** Um segundo provedor de testador é a extensão natural.
- **Cada fonte tem só 2 suítes por requisito.** A variação entre suítes fica mal estimada.
- **Os mutantes são "naturais".** São implementações reais de dois modelos sob o pedido incompleto, e não mutações sintéticas do código. Isso os aproxima do uso real, mas não cobre todos os modos de perder uma regra.

## 7. Desvios em relação ao diagnóstico de 02/10

- Suítes por requisito, e não por implementação. A fonte com código usa uma única implementação de referência, como uma suíte de regressão real.
- A fonte "código + especificação completa" foi retirada: no piloto ela empatou no teto com a especificação sozinha.
- Foi acrescentado o critério de suíte sólida (quieta na referência) antes de contar uma morte, como na análise de mutação clássica.

## 8. Como rodar (Mac)

Só depois do merge deste pré-registro:

```bash
bash scripts/run_mutation_adequacy.sh            # testador padrão: gpt-6-astra
```

O script:
1. roda os controles do runner;
2. localiza os 25 pacotes privados, comparando o hash dos `results.json` publicados;
3. congela os prompts;
4. gera as 150 suítes;
5. executa as cerca de 1.100 execuções;
6. copia para `data/mutation-adequacy/v1/` os resultados, os controles e o manifesto público, sem caminhos privados nem respostas brutas.

Ele recusa rodar de novo se a pasta da evidência já existir.

## 9. Verificações de integridade antes da geração

Correções feitas na revisão antes de qualquer chamada: cada página deve coincidir com o recibo de coleta e com o hash da página no relatório do oráculo, cujo hash está no resultado publicado. O runtime verifica os dois scripts Python, o runner e a imagem contra o congelamento; a execução também verifica cada suíte contra o hash registrado na geração. O runner remove seu contêiner nomeado se o cliente Docker atingir o timeout. Os pacotes e resultados antigos não foram alterados; para reproduzir a versão antiga do script compartilhado, usa-se seu commit original.

O plano continua com 150 chamadas; incluir os dois C não confirmados aumenta a execução de 1.134 para 1.146 pares suíte/página. Nenhuma dessas páginas é promovida a mutante confirmado.
