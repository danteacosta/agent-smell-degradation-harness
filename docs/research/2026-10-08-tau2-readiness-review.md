# Preparação do piloto τ²: medidas, bloqueios e revisão humana

Estado em 08/10/2026: preparação autorizada; inventário e desenho com Márcio ainda pendentes. Nenhuma coleta científica foi iniciada. Esta revisão propõe contratos para corrigir o rascunho antes do congelamento; não aprova o inventário, não muda os operadores e não autoriza execução.

## O que está verificado

O [PR #202](https://github.com/danteacosta/agent-smell-degradation-harness/pull/202) tem 83 testes locais aprovados e três verificações de CI aprovadas no commit 1db366e7300aac6ab4215dd6957168207c28da27. A tarefa v2 supervisionada completou; as três qualificações v3 não completaram. O transporte estruturado segue experimental. O [registro técnico](2026-10-07-tau2-subscription-bridge.md) preserva os resultados separados.

O inventário contém 32 trechos normativos, cinco controles e cinco exclusões. A política original confere com SHA-256 10dc0525421521208be39cee235bba84a16e2bcba9899eb93d92cd81d2f62fc4 e com o checkout τ² 4ce7c0397c1eb65c9bbe59aeacfe1ca44a1cd699. Correspondência textual e ausência de sobreposição não demonstram unidade semântica nem validade das inversões.

## Três erros reproduzidos na análise atual

Fonte conferida: [scripts/policy_adequacy.py](../../scripts/policy_adequacy.py), blob Git 8084759ec5d93cd7074ad23bfb11c8504e9b0fae. Todos os casos abaixo usam dados sintéticos, sem modelos, políticas alteradas em execução ou resultados do estudo.

| Contexto sintético | Saída atual | Contrato proposto antes da coleta |
| --- | --- | --- |
| Quatro A com reward=1; três N01 e três D01 com reward=null | R01 recebe omission_detected | Resultado ausente não confirma detecção; registrar ausência/falha técnica e manter a inferência pendente. |
| Quatro A com reward=1; nenhuma variante executada | candidates devolve 69 pares, cada um com duas repetições | Listar separadamente slots iniciais não executados; somente uma falha inicial válida pode iniciar confirmação. |
| Quatro A com reward=0; zero tarefas elegíveis | Todas as 32 regras recebem uncovered | Sem tarefas elegíveis, a cobertura é não estimável. Não classificar regras como descobertas sem avaliação elegível. |

A origem do primeiro erro é tratar not passed como falha científica mesmo quando a recompensa é ausente. O segundo nasce de juntar missing e unconfirmed em pending e usar pending como lista de repetições. O terceiro decorre de reduzir um conjunto vazio de confirmações a uncovered.

Cenários de aceitação para uma correção posterior:

1. Dada uma falha de infraestrutura ou uma avaliação ausente, quando a análise agrega resultados, então ela não aumenta detecções confirmadas nem fabrica recompensa zero.
2. Dado um slot inicial nunca tentado, quando candidates é chamado, então esse slot não aparece como confirmação; a ausência continua explícita.
3. Dada uma falha inicial válida e confirmações ainda incompletas, então somente as confirmações planejadas pendentes são identificadas. Uma tentativa técnica falhada permanece tentada; não habilitar retry por inferência.
4. Dado zero tarefas elegíveis, então a saída declara ausência de estimativa e denominador zero, sem concluir uncovered.
5. Dada uma sequência completa de avaliações válidas, então os limiares propostos de 3/4 e 2/3 permanecem iguais, até decisão explícita de desenho.

Antes de uma implementação, é preciso fixar o schema dos slots e estados: identificação única de variante/tarefa/tentativa, ordem inicial versus confirmação, falha técnica, avaliação concluída e resultado ausente. O leitor atual reduz resultados a variante, task_id, reward e termination_reason; não é suficiente para provar unicidade das tentativas ou reconstruir uma ordem a partir de arquivos arbitrários. A análise não deve interpretar a ordem de concatenação como identidade científica do slot.

## Medida observada e conclusão permitida

A medida automática atual é sensibilidade da recompensa da tarefa à mutação da política, para o agente, simulador e protocolo escolhidos. Uma inversão na política não demonstra que o agente violou a regra. Uma queda de recompensa também pode refletir outra alteração de comportamento, sem detecção da obrigação-alvo.

Para sustentar uma afirmação de adequação por regra, registrar separadamente:

| Campo | Evidência necessária |
| --- | --- |
| Oportunidade de aplicar a regra | Contexto da tarefa e condição de ativação da obrigação. |
| Violação da regra-alvo | Trajetória ou ação observável, comparada à política original. |
| Resposta do avaliador existente | Componentes efetivamente avaliados e recompensa, sem adicionar critérios ao benchmark. |
| Resultado técnico | Execução/eval concluída, ou motivo real de interrupção. |

Com isso, distinguir violação observada e reprovada, violação observada e aprovada, regra recuperada/não violada e caso não avaliável. Esses estados complementam a sensibilidade por operador. O tamanho e protocolo da inspeção humana ainda precisam ser decididos. Não presumir que uma amostra de trajetórias valida todas as regras.

Os nomes covered e uncovered precisam permanecer operacionais e condicionais ao agente enquanto essa evidência não existe. covered_but_omission_silent não identifica sozinho recuperação da regra; uma omissão pode não ter afetado o comportamento ou a tarefa pode não ter criado a oportunidade relevante.

## O avaliador realmente usado

No checkout fixado, EvaluationType.ALL respeita reward_basis da tarefa. As tarefas airline declaram DB e COMMUNICATE. Conferidas as 50 tarefas: todas declaram DB/COMMUNICATE e há 123 asserções de linguagem natural no total. A presença de nl_assertions no JSON não torna essas asserções parte da recompensa padrão. [O avaliador](https://github.com/sierra-research/tau2-bench/blob/4ce7c0397c1eb65c9bbe59aeacfe1ca44a1cd699/src/tau2/evaluator/evaluator.py) distingue ALL de ALL_WITH_NL_ASSERTIONS.

A lista actions é uma trajetória de referência para obter o estado de banco esperado; não é, por si só, uma exigência de reproduzir cada ação. Outra trajetória com o mesmo estado final pode passar. Isso é central para obrigações de processo, como obter confirmação antes de escrever: estado final correto não prova cumprimento da regra.

Manter o avaliador existente como objeto do estudo. Ativar asserções adicionais mudaria a suíte avaliada e exigiria outro desenho explícito; não fazê-lo para forçar detecção.

## Intervenção R03 parcialmente neutralizada pelo harness

A inspeção encontrou uma duplicação fora de policy.md: [AGENT_INSTRUCTION](https://github.com/sierra-research/tau2-bench/blob/4ce7c0397c1eb65c9bbe59aeacfe1ca44a1cd699/src/tau2/agent/llm_agent.py) manda escolher entre mensagem ao usuário e chamada de ferramenta e proíbe ambas no mesmo turno. Retirar R03 da política preserva essa instrução. Invertê-la cria conflito com a instrução externa. [A validação de mensagens](https://github.com/sierra-research/tau2-bench/blob/4ce7c0397c1eb65c9bbe59aeacfe1ca44a1cd699/src/tau2/agent/base_agent.py) também recusa conteúdo e tool_calls simultâneos.

Isso afeta a parte de R03 relativa à simultaneidade entre mensagem e ferramenta; não demonstra que toda a obrigação de serializar várias ferramentas seja imposta do mesmo modo. Não classificar ausência de efeito nessa parte como recuperação espontânea pelo modelo ou lacuna do avaliador.

Decisão proposta para revisão: separar as duas obrigações de R03 ou marcar a parte imposta pelo harness como não manipulável neste desenho. Não remover a instrução nem a validação upstream para fazer o mutante funcionar: isso mudaria mais que a política e violaria a intervenção proposta. Esta decisão e os denominadores permanecem pendentes.

## Pacote para revisão e decisões de construção

Foi preparado um pacote privado, com texto original e inversão de cada regra, campos vazios de decisão, cinco reescritas e cinco exclusões. Nenhuma aprovação foi preenchida. O pacote identifica o hash do inventário e da política.

Revisar com atenção trechos que contêm várias condições: R12 reúne a tabela de bagagens por categoria; R27 reúne alternativas de elegibilidade para cancelamento; R01 combina listar detalhes e obter confirmação; R03 combina serialização de ferramentas e exclusividade entre ferramenta e resposta. A revisão deve decidir se cada trecho é uma obrigação composta defensável ou precisa ser dividido. Não dividir automaticamente nem manter o denominador 32 após uma divisão.

Para cada item, registrar unidade semântica, efeito da retirada no contexto restante, duplicações, restrição da inversão à regra-alvo e exemplo de violação observável. Para controles, comparar exceções, quantificadores e modalidade. Só então congelar inventário, variantes, plano e denominadores.

## Sondagem de viabilidade proposta, ainda não executada

Uma amostra técnica por tipo de ação pode informar viabilidade sem iniciar a etapa científica. As cinco tarefas abaixo são uma proposta de engenharia, não amostra sorteada, não estimativa representativa de custo e não uma autorização de chamada.

| Tarefa | Ação presente na referência | Limite da qualificação |
| --- | --- | --- |
| 0 | Nenhuma ação obrigatória de referência; tarefa previamente usou leitura | Caminho de leitura/conversa; v2 completou, v3 ainda falha. |
| 8 | book_reservation | Escrita de nova reserva. |
| 11 | update_reservation_flights | Escrita de alteração de voo. |
| 12 | update_reservation_baggages | Escrita de bagagens. |
| 14 | cancel_reservation e book_reservation | Composição de cancelamento e nova reserva. |

Confirmado no tasks.json fixado: todas usam DB/COMMUNICATE. Seus arrays nl_assertions têm, respectivamente, 1, 4, 3, 2 e 5 itens; não estão ativados na recompensa padrão. Ferramentas de referência não garantem que a execução real vá usá-las.

Pré-condições: transporte qualificado, quota oficial recente sem controle de cursor, aprovação do orçamento e pasta/manifesto exclusivos por tentativa. Medir tempo total, latência de modelo, chamadas e tokens por papel, interrupções de quota/infraestrutura e conclusão real. Custo USD permanece indisponível. Um limite de chamadas pode censurar uma tarefa; isso não equivale a falha de política. Não extrapolar os 24,23 segundos da tarefa supervisionada para milhares de simulações.

## Auditoria do desenho pela skill benchmark-paper-template

| Pilar | Estado nesta preparação | Ajuste necessário |
| --- | --- | --- |
| Lacuna de avaliação | Pergunta sobre sensibilidade de suíte existente à política | Manter novidade como hipótese da revisão bibliográfica já documentada; esta etapa não fez nova busca. |
| Construção | Proveniência e 70 variantes verificáveis | Revisão humana e unidade da regra pendentes; pacote preparado. |
| Avaliação | Elegibilidade e confirmação propostas | Corrigir os três erros, fixar identidade dos slots e separar violação de resposta do avaliador. |
| Achados empíricos | Ausentes neste piloto | Não usar qualificações técnicas como resultados científicos. |
| Método companheiro | Fora de escopo | Não acrescentar geração de testes, produto ou treinamento para encerrar este piloto. |

Ordem de preparação: resolver contratos de análise; concluir revisão do inventário e desenho; qualificar transporte; autorizar sondagem de viabilidade; congelar e decidir orçamento da coleta. Essa extensão não deve deslocar a auditoria cega nem a confirmatória da dissertação.
