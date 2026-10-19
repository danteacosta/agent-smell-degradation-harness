# τ² airline: snapshot histórico de 17/10/2026 às 11h

> **Escopo histórico:** os números e estados operacionais abaixo se referem somente à janela encerrada em 17/10/2026 às 11h de Maceió. Ordens humanas posteriores autorizaram uma retomada. Esta pasta não contém os resultados dessa continuação e não informa o estado atual da coleta ou da automação; eles dependem de nova síntese sanitizada verificada.

Naquela janela, a coleta foi encerrada por ordem humana em 17/10/2026 às 11h de Maceió (14h UTC), com zero execução ativa. A etapa 1 completou suas 1.221 tentativas iniciais na coorte fixa de 33 tarefas. A etapa 2 terminou com 65 das 1.056 deleções iniciais previstas: 58 recompensas positivas, quatro zeros e três resultados técnicos ausentes (`None`); 991 identidades nunca foram tentadas. O fechamento da janela não conclui o protocolo de pesquisa nem confirma uma relação causal entre alteração de política e falha.

Este documento e [stage2-aggregates.json](stage2-aggregates.json) substituem o snapshot intermediário das 08h. O [relatório da etapa 1](stage1-conclusions.md) e seus [agregados](stage1-aggregates.json) são registros históricos da entrega anterior à etapa 2; sua seção de próximos passos não constitui autorização de coleta atual. No fechamento daquela janela, a automação ficou pausada. Não foram reparados resultados `None`, executadas confirmações ou iniciadas novas tentativas na análise offline.

## Resultados observados

| Grupo | Tentativas | Recompensa positiva | Zero | None técnico | Com recompensa |
|---|---:|---:|---:|---:|---:|
| Baseline A nas mesmas 33 tarefas, quatro trials | 132 | 132 | 0 | 0 | 132 |
| Inversões N, 32 variantes × 33 tarefas | 1.056 | 1.007 | 25 | 24 | 1.032 |
| Reformulações B, cinco variantes × 33 tarefas | 165 | 162 | 0 | 3 | 162 |
| Etapa 1, N + B | 1.221 | 1.169 | 25 | 27 | 1.194 |
| Deleções D, prefixo parcial da etapa 2 | 65 | 58 | 4 | 3 | 62 |

Os 58 positivos de D representam **58/65 = 89,23% de todas as tentativas** e **58/62 = 93,55% das tentativas com recompensa**. Os quatro zeros correspondem a 4/65 = 6,15% de todas as tentativas ou 4/62 = 6,45% das válidas. Os três `None` representam 3/65 = 4,62%. Os denominadores com e sem resultados técnicos ausentes são explícitos; `None` não é tratado como zero nem removido silenciosamente.

O baseline original de 50 tarefas permanece separado: 200 tentativas, 152 positivos, 39 zeros e nove `None`. A regra de elegibilidade preexistente exigia quatro trials válidos e ao menos três positivos. Os 132 baselines são controles compartilhados (quatro trials × 33 tarefas). Cada comparação reutiliza os quatro trials A da tarefa; isso não acrescenta réplicas independentes. Tarefas reutilizadas entre variantes também não constituem observações independentes. Nas 33 tarefas selecionadas, os 132 resultados A observados foram positivos. As 17 tarefas restantes e os resultados históricos fora da coorte não são somados aos denominadores prospectivos. A restrição à coorte deixou 544 identidades D do plano original fora desta etapa; elas não fazem parte das 991 identidades elegíveis nunca tentadas.

## O que a etapa 2 acrescenta

O prefixo preservou a ordem, as seeds e os materiais congelados. Somente duas das 32 variantes D receberam tentativas:

| Variante | Tentativas | Positivos | Zeros | None técnicos | Planejadas na coorte |
|---|---:|---:|---:|---:|---:|
| D27 | 33 | 29 | 4 | 0 | 33 |
| D26 | 32 | 29 | 0 | 3 | 33 |

D27 completou sua coleta inicial na coorte; D26 ficou parcial. As outras 30 variantes não foram tentadas. A cobertura de tentativas da etapa 2 foi 65/1.056 = 6,16%, distribuída por apenas 2/32 variantes. O prefixo não oferece uma amostra representativa das deleções, mesmo tendo ordem fixada previamente. Não é válido extrapolar sua taxa de zeros para as 32 regras, comparar frequências N e D como se os grupos tivessem exposição equivalente ou interpretar as variantes não tentadas como silenciosas.

Os quatro zeros D ocorreram em tarefas cujos quatro baselines A correspondentes foram positivos. As inspeções privadas desses quatro casos já estavam registradas; esta entrega não repetiu inspeções nem selecionou novos exemplos. As diferenças observadas de diálogo e de sequência de operações impedem atribuir automaticamente cada zero à remoção de uma regra específica. Recompensa positiva também não demonstra cumprimento integral da política.

## Candidatos e limites das conclusões

A recomputação das funções congeladas `analyse` e `candidates` preservou os 25 pares candidatos N, distribuídos por 12 variantes e 14 tarefas. O protocolo propõe dois novos trials por par, totalizando 50 reruns N: **nenhum foi executado**. Os quatro zeros D geram quatro propostas de confirmação, oito reruns potenciais, também não executados. A saída de candidatos é um artefato analítico; não é uma fila autorizada para execução. Nenhum `None` foi transformado em candidato de reparo.

As 32 classes de regra continuam `incomplete`. Sem as confirmações exigidas, contagens de detecção confirmada iguais a zero não demonstram ausência de cobertura, efeito ou violação. Não houve confirmação humana de causalidade. H1/H2, o material de pesquisa e o protocolo congelado não foram modificados por esta síntese.

A evidência é exploratória e descritiva: uma observação inicial por par, tarefas reutilizadas entre variantes, conversas adaptativas e seleção por baseline forte. A coleta ocorreu em momentos diferentes; seeds preservadas não garantem determinismo do provedor. Não apresentamos significância estatística ou intervalos que pressupusessem independência não demonstrada. Os 65 `None` do registro histórico global permanecem ausências técnicas, dos quais 27 pertencem à coorte da etapa 1 e três à etapa 2; os demais pertencem ao histórico separado.

## Verificação e privacidade

A análise offline confere as identidades `variant/task/trial/seed` contra o plano original e rejeita duplicatas, identidades desconhecidas, trials ausentes ou booleanos e seeds alteradas ou booleanas. Ela usa o método congelado de análise, verifica hashes das fontes e evidências antes dos imports e reconfere os arquivos ao terminar. As 1.915 identidades históricas únicas têm tentativas e outcomes pareados. A recomputação fez zero chamada de modelo.

Os artefatos completos de linhas, candidatos, análise e recibos permanecem privados. Esta pasta contém apenas agregados e sínteses: sem trajetórias, mensagens, identificadores de conta/processo, caminhos locais ou capturas de CLI. A conclusão sustentada é limitada: houve candidatos iniciais de sensibilidade à política na coorte observada, enquanto a maior parte das deleções e todas as confirmações continuam sem coleta. Aquela janela encerrou a coleta então autorizada; ela não resolveu essas lacunas.
