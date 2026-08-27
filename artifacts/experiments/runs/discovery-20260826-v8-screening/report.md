# Requirements-smell validation round v8

## Em linguagem simples

Este experimento pega requisitos naturais do corpus ARTA e compara dois níveis de triagem: um baseline lexical, baseado em palavras/expressões, e um comparador linguístico contextual, que combina um vocabulário mais amplo com sinais de estrutura, como métricas, condições, atores, respostas explícitas e possíveis antecedentes de pronomes.

A comparação ainda não prova entendimento semântico: os rótulos usados nesta rodada são os marcadores do próprio ARTA e não uma anotação independente de especialistas. O comparador contextual é uma etapa intermediária, não um modelo LLM.

Importante: o comparador contextual desta rodada é uma análise exploratória
retrospectiva. Seus sinais foram definidos depois de inspecionar as falhas do
baseline e, por isso, esta rodada não deve ser lida como uma comparação
preditiva cega nem como evidência de superioridade. Na próxima rodada, os
sinais/prompt/modelo devem ser congelados usando apenas treino e calibração;
somente depois o conjunto de teste deve ser aberto.

## O que foi executado

- Casos processados: **144**, em **6 projetos**.
- Famílias: subjective_language, ambiguous_adjective_adverb, nonverifiable_term, vague_pronoun, uncertain_verb, polysemy.
- Cada família tem 12 positivos de fonte e 12 controles sem marcador; nesta configuração, os 144 registros de origem são distintos.
- Split por projeto: treino=ertms, keepass; calibração=cctns; teste=fun, gamma, peering.
- Texto original: executado a partir de um arquivo privado local e redigido dos artefatos versionados.
- Handoff de anotação: `annotation-manifest.jsonl` contém somente IDs, hashes e família; o texto precisa ser exportado localmente, sem rótulos ARTA.

## Resultado do baseline lexical no teste

A tabela CSV e o gráfico SVG mostram a concordância com os marcadores da fonte. Use os denominadores e os intervalos Wilson no JSON; eles são intervalos binomiais descritivos e não corrigem dependência entre requisitos do mesmo projeto.

| Família | TP | FP | TN | FN | Precisão | Recall | Avaliável |
|---|---:|---:|---:|---:|---:|---:|:---:|
| subjective_language | 3 | 0 | 6 | 5 | 1.0 | 0.375 | True |
| ambiguous_adjective_adverb | 0 | 0 | 7 | 9 | None | 0.0 | True |
| nonverifiable_term | 0 | 0 | 7 | 7 | None | 0.0 | True |
| vague_pronoun | 5 | 1 | 6 | 2 | 0.8333333333333334 | 0.7142857142857143 | True |
| uncertain_verb | 2 | 0 | 7 | 0 | 1.0 | 1.0 | True |
| polysemy | 0 | 1 | 6 | 5 | 0.0 | 0.0 | True |

## Comparador contextual (diagnóstico secundário)

A literatura indica que listas e dicionários precisam ser combinados com análise linguística, padrões de linguagem controlada ou representação contextual. Este comparador implementa apenas a parte auditável e offline dessa ideia. Ele pode rejeitar um falso alerta aparente quando existe um limite mensurável, ou elevar um alerta quando um pronome não tem antecedente local. Isso não substitui anotação humana nem avaliação com modelos reais.

| Família | TP | FP | TN | FN | Precisão | Recall |
|---|---:|---:|---:|---:|---:|---:|
| subjective_language | 6 | 0 | 6 | 2 | 1.0 | 0.75 |
| ambiguous_adjective_adverb | 7 | 0 | 7 | 2 | 1.0 | 0.7777777777777778 |
| nonverifiable_term | 6 | 1 | 6 | 1 | 0.8571428571428571 | 0.8571428571428571 |
| vague_pronoun | 2 | 0 | 7 | 5 | 1.0 | 0.2857142857142857 |
| uncertain_verb | 2 | 0 | 7 | 0 | 1.0 | 1.0 |
| polysemy | 4 | 1 | 6 | 1 | 0.8 | 0.8 |

## Auditoria dos erros

A auditoria automática contém 79 linhas redigidas, identificadas por hash e `case_id`. Ela registra a evidência lexical/contextual e separa `contextual_overreach` de `uncovered_or_contextual_miss`, mas deixa `semantic_error_category` pendente. Uma FN pode ser um smell sem pista do vocabulário; uma FP pode ser um uso legítimo que exige contexto de domínio. Portanto, a classificação semântica precisa de dois anotadores e adjudicação.

A leitura principal desta rodada é que ampliar o vocabulário ajuda a localizar candidatos, mas não resolve o problema: vários marcadores do corpus são relações de sentido, escopo ou estrutura que não aparecem como uma palavra fixa. O detector final deve produzir alerta, trecho/evidência, explicação, pergunta de esclarecimento e hipótese de correção; a geração de código deve ser avaliada apenas depois disso, com testes ocultos.

## Condições do agente

O artefato `agent_conditions.json` reaproveita o fixture comportamental v7 para comparar sem alerta, com alerta e com uma revisão hipotética perfeita. Isso é uma simulação/upper bound do pipeline; não é uma nova execução de agente nem uma chamada a modelo real.

## O que falta para relevância

- obter permissão escrita de redistribuição/transformação ou usar fontes explicitamente licenciadas;
- substituir os marcadores ARTA por rótulos binários independentes, com dois anotadores, amostra duplicada e adjudicação;
- executar pelo menos dois modelos reais, com prompts/versionamento, repetições, tokens, custo, latência e taxa de erro;
- comparar agente sem verificador, com alerta e com oportunidade real de revisão em requisitos novos;
- congelar o detector contextual antes do teste, usando somente treino/calibração, e
  repetir a comparação em projetos inteiramente mantidos fora dessa calibração;
- ampliar a diversidade de projetos e manter projetos inteiros fora da calibração.

**Status:** `blocked_until_external_validation`. O bundle está completo como triagem offline, mas bloqueado para evidência confirmatória.
