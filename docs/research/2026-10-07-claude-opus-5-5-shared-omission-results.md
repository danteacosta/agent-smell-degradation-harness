# Opus 5.5: omissão compartilhada nos E2Es

Nos mesmos 25 requisitos e oito projetos, o escore com requisito completo foi 0.940, contra 0.263 com pedido incompleto e 0.177 com pedido incompleto mais código do mutante mostrado. O resultado é exploratório; reutiliza as implementações OpenAI e não confirma H1 nem testa H2. A auditoria humana continua pendente.

Cada requisito recebe o mesmo peso. Uma suíte só mata um mutante se aprova a referência correta; suítes inválidas permanecem no denominador planejado. Repetições não são requisitos independentes.

## Execução e integridade

Foram 150 tentativas únicas deste modelo, 150 suítes prontas, 1146 relatórios reais de navegador e 0 placeholders de geração nos 1146 pares planejados. Nenhuma tentativa ou avaliação foi repetida. Recibos, hashes de entradas e importações foram conferidos; a análise foi regenerada com o código congelado e coincidiu exatamente. O arquivo de análise do mutante selecionado é derivado após o recibo da avaliação; seu conteúdo também foi recalculado e conferido, sem alterar o recibo original.

## Desvios operacionais

O protocolo 6fb02a2 foi publicado no [#191](https://github.com/danteacosta/agent-smell-degradation-harness/pull/191) antes das chamadas. A política autorizada permitiu consumir a janela de cinco horas até zero, preservando mais de 30% nas demais janelas; não houve API paga nem uso extra. O adaptador V2 e o parser V3 já estavam definidos antes desta coleta; não foram trocados durante ela.

- Etapa 000: início 06/10/2026 22:48:00, 0 tentativas anteriores; término 06/10/2026 23:22:48. Parou por perda de conexão StreamSuspended, com 127 tentativas no lote (126 prontas e uma falha), cota de cinco horas 23% e semanal 78%.
- Etapa 001: início 07/10/2026 06:33:53, 127 tentativas anteriores; término 07/10/2026 07:13:05. Continuou apenas os 173 slots não tentados, após autorização explícita em 07/10 e qualificação QUOTA_RESET_OK (cinco horas 100%, semanal 78%).

A retomada usou um novo pacote e o módulo versionado por hash claude55_stream_continuation.py: a exceção autoriza somente a parada 000 vinculada no manifesto. O pacote anterior permaneceu íntegro. A falha ficou tentada e não foi reclassificada. O novo módulo foi vinculado no manifesto antes da retomada, ainda sem commit no Git naquele instante; isso é um desvio operacional de publicação. Nenhum prompt, mutante, página, slot já tentado, oráculo ou script de análise mudou. A avaliação automática posterior não fez chamadas de modelo.

## MA1 e MA2

| Contraste | Diferença média | IC 95% bootstrap por projeto | p exato por projeto | Requisitos maior / menor / empate |
| --- | ---: | --- | ---: | --- |
| MA1: completa − incompleta | 0.6767 | [0.5805; 0.7895] | 0.0078125 | 20 / 0 / 5 |
| MA2: completa − incompleta+código | 0.7633 | [0.6282; 0.8826] | 0.0078125 | 21 / 0 / 4 |

O teste troca sinais por projeto. Com oito projetos, 0,0078125 é o menor p bilateral possível. Os intervalos e testes atendem ao critério exploratório registrado, sem substituir validação dos rótulos.

## Detecção e falsos alarmes

| Fonte | Suítes quietas na referência / 50 | Mutantes: alarme / pares elegíveis | Corretas: falso alarme / elegíveis | Recuperadas: falso alarme / elegíveis |
| --- | ---: | --- | --- | --- |
| spec_complete | 49 | 154/158 | 11/129 | 7/34 |
| spec_incomplete | 38 | 36/119 | 2/101 | 0/30 |
| code_incomplete | 33 | 23/100 | 5/85 | 0/28 |

| Fonte | Corretas: alarmes / observadas / planejadas | Recuperadas: alarmes / observadas / planejadas |
| --- | --- | --- |
| spec_complete | 14/132/132 | 7/34/34 |
| spec_incomplete | 29/132/132 | 3/34/34 |
| code_incomplete | 52/132/132 | 6/34/34 |

As taxas condicionais selecionam suítes quietas na referência; as incondicionais incluem todas as suítes. Falhas de geração não contam como resultados quietos. Erro de asserção/construção não é evidência de flakiness, que exigiria repetições próprias.

## Referência correta × mutante mostrado

| Fonte | Referência quieta / mutante alarme | Ambos quietos | Ambos alarme | Referência alarme / mutante quieto | Falha | Reversão por asserção |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| spec_complete | 47 | 2 | 1 | 0 | 0 | 0 |
| spec_incomplete | 14 | 24 | 6 | 6 | 0 | 4 |
| code_incomplete | 8 | 25 | 6 | 11 | 0 | 10 |

A reversão por asserção é compatível com fixar o comportamento mostrado, mas só a auditoria dos testes pode dizer se a asserção trata da obrigação-alvo. Não se assume exclusividade do braço com código.

| Fonte | Mutante mostrado quieto / 50 | Quieto entre elegíveis | Escore confirmado | Escore ingênuo | Suítes inutilizáveis / 50 |
| --- | --- | --- | ---: | ---: | ---: |
| spec_complete | 2/50 | 2/49 | 0.9400 | 0.8250 | 0 |
| spec_incomplete | 30/50 | 24/38 | 0.2633 | 0.1950 | 0 |
| code_incomplete | 36/50 | 25/33 | 0.1767 | 0.1350 | 0 |

O escore ingênuo trata toda página C como mutante; os dois escores acima usam a mesma ponderação por requisito. Implementações recuperadas não são defeitos confirmados. Não se ranqueiam modelos: páginas reutilizadas, dois testes por fonte e um provedor gerando código limitam a generalização. O braço requisito completo junto com código defeituoso não foi coletado aqui; permanece proposta no #183.

Dados: [results.json](../../data/shared-omission-e2e/claude55-v1/claude-opus-5-5/results.json), manifesto público e contabilidade descritiva na mesma pasta. Os resultados #184, #189 e #190 permanecem preservados.
