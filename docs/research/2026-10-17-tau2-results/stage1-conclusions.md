> Relatório entregue antes do início da etapa 2. A seção “próxima etapa” registra o estado daquela entrega; o fechamento posterior está no [snapshot histórico das 11h](README.md).

# Conclusões da etapa 1: τ² airline

A coleta inicial da etapa 1 terminou. Na coorte fixa de 33 tarefas, as 1.221 identidades previstas foram tentadas uma única vez: 1.169 tiveram recompensa positiva, 25 tiveram recompensa zero e 27 ficaram sem recompensa por interrupção técnica (`None`). Não houve reparo ou repetição dos `None`. Esse fechamento da coleta inicial não equivale à conclusão da pesquisa, à confirmação dos candidatos ou à demonstração de defeitos causados por uma regra específica.

## Resultados e denominadores

| Grupo | Tentativas | Positivos | Zeros | None técnicos | Resultados com recompensa |
|---|---:|---:|---:|---:|---:|
| Baseline A, nas mesmas 33 tarefas, quatro trials | 132 | 132 | 0 | 0 | 132 |
| Inversões N, 32 variantes × 33 tarefas | 1.056 | 1.007 | 25 | 24 | 1.032 |
| Controles B, cinco variantes × 33 tarefas | 165 | 162 | 0 | 3 | 162 |
| Coorte da etapa 1, N + B | 1.221 | 1.169 | 25 | 27 | 1.194 |

Na coorte completa, positivos representam 95,74% das tentativas, zeros 2,05% e interrupções técnicas 2,21%. Para as inversões, os 25 zeros correspondem a 2,37% das 1.056 tentativas ou a 2,42% das 1.032 execuções que produziram recompensa. Os dois denominadores são apresentados porque excluir silenciosamente os `None` esconderia a perda de observação. Entre os controles, não houve zero nas 162 execuções com recompensa; três das 165 tentativas ficaram sem resultado técnico.

A elegibilidade foi determinada pelo baseline previamente fixado: quatro trials por tarefa e ao menos três resultados positivos, sem resultado ausente. No universo original de 50 tarefas, o baseline teve 200 tentativas, com 152 positivos, 39 zeros e nove `None`. As 33 tarefas selecionadas tiveram, neste conjunto observado, quatro positivos cada. Dez outras tarefas ficaram inelegíveis por desempenho e sete permaneceram sem elegibilidade resolvida por resultado técnico ausente. Essas 17 tarefas não entram no denominador principal de 1.221. Os resultados históricos preservados fora da coorte não foram somados a ela.

## O que o contraste com os baselines indica

Os 25 zeros ocorreram sob inversões de política em tarefas que os quatro baselines executaram com sucesso. Nenhum controle de reformulação produziu zero observado. Esse contraste é compatível com sensibilidade de parte das tarefas às variantes de inversão e fornece candidatos para investigação. Ele não permite, sozinho, afirmar que o benchmark detectou 25 violações de política ou que uma inversão causou cada falha.

Os candidatos se distribuem por 12 variantes e 14 tarefas. A contagem por variante é: N01 e N02, dois zeros cada; N04, um; N10, dois; N12, cinco; N14, dois; N16, um; N17, três; N20 e N23, um cada; N24, dois; N27, três. Uma mesma tarefa pode contribuir para mais de uma variante, portanto 25 pares não significam 25 tarefas independentes. Os controles não geraram candidatos nessa coorte.

A maior concentração observada foi N12, com cinco zeros em 33 tentativas e um `None`. N14 teve dois zeros e seis `None`, o maior número de interrupções técnicas entre as variantes N; qualquer comparação de sua frequência exige considerar essa perda. Não há base para ordenar variantes por importância causal apenas por essas contagens.

## O que os zeros significam: e o que ainda não está confirmado

A recompensa combina verificações de estado e de comunicação. As inspeções privadas dos zeros da coorte já estavam registradas em manifests exclusivos, com comparação aos quatro baselines da mesma tarefa. Elas mostraram que divergências de conversa podem acompanhar divergências de recompensa. Em um caso, a variante transferiu o atendimento; nos baselines, uma recusa levou o usuário a solicitar outra alteração que foi concluída. Em outro, o valor monetário final coincidiu, mas a estrutura das operações diferiu. Há também caso em que o baseline corrigiu uma resposta depois de o usuário continuar, enquanto a conversa da variante terminou antes. Esses exemplos descrevem diferenças observadas; não isolam seu mecanismo causal.

A recomputação de `analyse` e `candidates` encontrou 25 pares candidatos, todos N. O protocolo existente propõe dois novos trials por candidato, totalizando 50 reruns potenciais. Eles são apenas uma fila produzida pela análise: **não foram executados e não estão sendo iniciados nesta entrega**. A ausência dessas confirmações não será convertida em confirmação positiva ou negativa.

As 32 classificações de regra continuam `incomplete`. As deleções D ainda não foram coletadas nesta etapa e os candidatos N não passaram pelo critério de repetição do protocolo. Os campos de detecções confirmadas retornam zero por falta de evidência confirmatória suficiente; isso não prova ausência de cobertura ou ausência de efeito. Nenhuma violação, detecção ou causalidade foi confirmada por humano.

## Falhas e incertezas

Os 27 `None` da coorte: 24 em N e três em B: continuam ausências técnicas, separados de sucesso e de falha científica. O histórico contém interrupções por transporte ou limite local, ambiente de execução, quota/capacidade e prazo/interrupção. O rótulo genérico de parada do supervisor não permite atribuir uma causa específica a todos os casos sem diagnóstico individual; por isso não apresentamos uma distribuição causal inventada. No encerramento anterior ao 056, a guarda recusou um snapshot oficial cujo reset já havia vencido; o resultado ausente foi preservado. O 056 finalizou seus 21 inéditos com 21 positivos e nenhum novo `None` ou zero.

A análise é exploratória e descritiva. Há uma observação inicial por par variante/tarefa, conversas adaptativas e o mesmo conjunto de tarefas repetido entre variantes; as contagens não são amostras independentes. Os baselines e as variantes foram coletados em momentos distintos, e os recibos não expõem uma versão imutável do modelo. As seeds do plano foram preservadas, mas isso não garante determinismo do provedor. Não foi calculado um intervalo binomial ou teste de significância que pressupusesse independência não demonstrada.

A seleção de 33 tarefas com baseline forte restringe a interpretação a essa coorte do domínio airline. Sucesso em recompensa não demonstra cumprimento integral da política; ausência de zero não demonstra que uma regra seja dispensável. Materiais, ordem, seeds, a duplicação preexistente de R03 e o filtro de elegibilidade foram preservados, sem alteração de recompensas ou denominadores.

## Conclusão e próxima etapa

A etapa 1 encontrou **25 falhas iniciais candidatas sob inversão, contra nenhum zero observado nos controles**, numa coorte em que os 132 baselines correspondentes foram positivos. A maioria das inversões manteve a recompensa positiva. Isso sustenta investigar a sensibilidade e os pontos cegos das tarefas, mas ainda não sustenta a tese causal de que remover ou inverter uma regra específica produza um defeito confirmado.

A análise offline foi recomputada com identidade `variant/task/trial`, rejeição de duplicatas e de variantes/tarefas/trials desconhecidos, e preservação de todos os resultados ausentes. Os hashes de fontes e evidências congeladas foram conferidos antes dos imports. Nenhuma chamada de modelo foi feita pela recomputação.

A próxima etapa autorizada é a coleta inicial das deleções D: 32 variantes × 33 tarefas, total de 1.056 identidades no plano original. Ela exige novo supervisor, testes RED/GREEN, revisão independente, freeze e guardas oficiais frescas. A coleta será limitada pela guarda financeira então vigente e pelo prazo histórico de 17/10/2026 às 08:00 de Maceió, o que ocorrer primeiro. Um novo HTTP429 continua exigindo parada e nova decisão humana. Não serão reparados `None` nem iniciada coleta confirmatória adicional. O fechamento integral das 1.056 tentativas não é prometido dentro dessa janela.

## Artefatos desta entrega

[Agregados sanitizados](stage1-aggregates.json). As linhas por identidade, a análise completa, os candidatos e os recibos de verificação permanecem privados. Trajetórias, mensagens e identificadores operacionais não fazem parte desta síntese.
