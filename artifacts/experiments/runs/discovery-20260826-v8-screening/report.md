# Requirements-smell validation round v8

## Em linguagem simples

Este experimento pega requisitos naturais do corpus ARTA e testa um baseline simples baseado em palavras/expressões. Ele serve para verificar se o pipeline consegue carregar dados, manter projetos separados, calcular métricas e deixar claro o que ainda não foi validado.

Ele não prova que o detector entende o requisito, porque os rótulos usados nesta rodada são os marcadores do próprio ARTA e não uma anotação independente de especialistas.

## O que foi executado

- Casos processados: **144**, em **6 projetos**.
- Famílias: subjective_language, ambiguous_adjective_adverb, nonverifiable_term, vague_pronoun, uncertain_verb, polysemy.
- Cada família tem 12 positivos de fonte e 12 controles sem marcador; nesta configuração, os 144 registros de origem são distintos.
- Split por projeto: treino=ertms, keepass; calibração=cctns; teste=fun, gamma, peering.
- Texto original: executado a partir de um arquivo privado local e redigido dos artefatos versionados.
- Handoff de anotação: `annotation-manifest.jsonl` contém somente IDs, hashes e família; o texto precisa ser exportado localmente, sem rótulos ARTA.

## Resultado do baseline no teste

A tabela CSV e o gráfico SVG mostram a concordância com os marcadores da fonte. Use os denominadores e os intervalos Wilson no JSON; eles são intervalos binomiais descritivos e não corrigem dependência entre requisitos do mesmo projeto.

| Família | TP | FP | TN | FN | Precisão | Recall | Avaliável |
|---|---:|---:|---:|---:|---:|---:|:---:|
| subjective_language | 3 | 0 | 6 | 5 | 1.0 | 0.375 | True |
| ambiguous_adjective_adverb | 0 | 0 | 7 | 9 | None | 0.0 | True |
| nonverifiable_term | 0 | 0 | 7 | 7 | None | 0.0 | True |
| vague_pronoun | 5 | 1 | 6 | 2 | 0.8333333333333334 | 0.7142857142857143 | True |
| uncertain_verb | 2 | 0 | 7 | 0 | 1.0 | 1.0 | True |
| polysemy | 0 | 1 | 6 | 5 | 0.0 | 0.0 | True |

## Condições do agente

O artefato `agent_conditions.json` reaproveita o fixture comportamental v7 para comparar sem alerta, com alerta e com uma revisão hipotética perfeita. Isso é uma simulação/upper bound do pipeline; não é uma nova execução de agente nem uma chamada a modelo real.

## O que falta para relevância

- obter permissão escrita de redistribuição/transformação ou usar fontes explicitamente licenciadas;
- substituir os marcadores ARTA por rótulos binários independentes, com dois anotadores, amostra duplicada e adjudicação;
- executar pelo menos dois modelos reais, com prompts/versionamento, repetições, tokens, custo, latência e taxa de erro;
- comparar agente sem verificador, com alerta e com oportunidade real de revisão em requisitos novos;
- ampliar a diversidade de projetos e manter projetos inteiros fora da calibração.

**Status:** `blocked_until_external_validation`. O bundle está completo como triagem offline, mas bloqueado para evidência confirmatória.
