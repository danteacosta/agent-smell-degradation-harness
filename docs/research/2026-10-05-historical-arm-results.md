# Braço histórico H: coleta concluída

Foram concluídas 136/136 chamadas novas, com A e H coletados contemporaneamente em 17 requisitos de oito projetos. Esses 17 são um subconjunto dos 46, não requisitos adicionais. Houve 25 pioras em H, 27 empates com a regra cumprida, 13 empates com a regra violada, 0 melhoras e 3 pares não avaliáveis. A piora apareceu em 8 requisitos de 6 projetos. O resultado é exploratório.

## O que foi comparado

A usa a regra completa. Em 12 casos, H é exatamente C, a omissão construída, selecionada por revisão do histórico. Nos outros cinco, H preserva C e acrescenta uma passagem literal antiga classificada pelo painel como mais vaga. H mantém contexto moderno e não representa a documentação antiga integral. As páginas são implementações geradas em scaffolds controlados, avaliadas no navegador; não são versões históricas dos produtos originais.

## Resultado separado por construção

| Construção | Requisitos | H pior | Empate cumprido | Empate violado | H melhor | Não avaliável |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H=C: regra ausente | 12 | 24 | 13 | 8 | 0 | 3 |
| H=C+passagem antiga: regra mais vaga | 5 | 1 | 14 | 5 | 0 | 0 |


As construções não são tratamentos intercambiáveis. H=C replica a omissão construída sob uma seleção guiada pelo histórico. Os resultados de H=C+passagem antiga não isolam o efeito da citação, pois C não foi coletado contemporaneamente nesses cinco casos. Um empate em sucesso não prova recuperação causada pela citação.

## Por requisito

| Requisito | Projeto | Construção | Piora | Empate cumprido | Empate violado | Melhora | Não avaliável |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `grist-page-default-collapse` | grist | omissão | 4 | 0 | 0 | 0 | 0 |
| `grist-suggestions-open-copy` | grist | passagem antiga | 0 | 4 | 0 | 0 | 0 |
| `immich-library-single-owner` | immich | omissão | 4 | 0 | 0 | 0 | 0 |
| `immich-m2t-upload` | immich | omissão | 4 | 0 | 0 | 0 | 0 |
| `mattermost-anonymous-team-url` | mattermost | omissão | 3 | 1 | 0 | 0 | 0 |
| `mattermost-timezone-default-automatic` | mattermost | omissão | 0 | 4 | 0 | 0 | 0 |
| `nextcloud-device-password-once` | nextcloud | passagem antiga | 1 | 2 | 1 | 0 | 0 |
| `openproject-filter-text-autoupdate` | openproject | passagem antiga | 0 | 0 | 4 | 0 | 0 |
| `openproject-invite-permission-basis` | openproject | omissão | 0 | 0 | 2 | 0 | 2 |
| `paperless-doc-title-placeholder` | paperless-ngx | omissão | 1 | 0 | 3 | 0 | 0 |
| `paperless-superuser-grant` | paperless-ngx | omissão | 4 | 0 | 0 | 0 | 0 |
| `wekan-field-order-independent` | wekan | omissão | 0 | 4 | 0 | 0 | 0 |
| `wekan-swimlane-below-default` | wekan | omissão | 4 | 0 | 0 | 0 | 0 |
| `wekan-sync-local-edits` | wekan | passagem antiga | 0 | 4 | 0 | 0 | 0 |
| `wekan-week-number-immediate` | wekan | omissão | 0 | 4 | 0 | 0 | 0 |
| `zulip-gif-picker-disabled` | zulip | passagem antiga | 0 | 4 | 0 | 0 | 0 |
| `zulip-reverse-linkifier-paste` | zulip | omissão | 0 | 0 | 3 | 0 | 1 |


## Estimativa e modelo

O estimador pareado, com peso por requisito e 0,5 para empate, é 0.683824. Esse número não é uma taxa de falhas. O intervalo exploratório por projeto é [0,585; 0,813]; os extremos determinísticos para resultados desconhecidos ficam em [0,669; 0,699]. O grupo H=C tem estimativa 0,750, contra 0,525 para H=C+passagem antiga. O campo técnico `valid_for_inference` do estimador verifica somente a quantidade de projetos; não aprova a inferência científica. O p-valor gerado não é usado como confirmação, pois o esquema de troca entre requisitos dependentes de projeto não foi validado. Os intervalos por projeto e os limites de sensibilidade estão em [`h-vs-a.json`](../../data/historical-arm-results/v1/h-vs-a.json); são análises exploratórias, sem autorização para inferência confirmatória. As repetições do mesmo requisito não são unidades independentes.


| Modelo | H pior | Empate cumprido | Empate violado | H melhor | Não avaliável |
| --- | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-luna | 13 | 12 | 7 | 0 | 2 |
| gpt-5.6-sol | 12 | 15 | 6 | 0 | 1 |


## Execução e custódia

Os 17 oráculos passaram em 130 controles no Docker antes das gerações. Todas as 136 solicitações foram congeladas antes da primeira chamada, sob o commit `1200272a99849b03bfd8ade4b8f3b929f4d7ad22`. Foram preservados 136 retornos, 132 resultados avaliáveis para a regra alvo e 266 vínculos de prints. Os recibos cobrem 1893 arquivos verificados. Cada slot foi tentado uma vez, sem retry, reparo ou substituição de resultado.

A execução começou em um processo e foi distribuída em até três processos, cada um responsável por casos completos para reduzir a latência. Um processo liberado assumiu o caso Nextcloud ainda não iniciado. Essa mudança de orquestração foi registrada fora dos inputs congelados; não alterou prompts, slots, modelos, repetições ou ordem interna de cada caso.

Os pacotes privados, retornos completos e prints permanecem no Mac. Os resultados públicos mantêm categorias, identificadores e hashes dos relatórios e prints. [`audit-summary.json`](../../data/historical-arm-results/v1/audit-summary.json) liga os resultados aos recibos e contém contagens por requisito, projeto, construção e modelo. [`cohort-frozen.json`](../../data/historical-arm-results/v1/cohort-frozen.json) registra o congelamento anterior à coleta.

Os três pares desconhecidos permanecem separados: dois no convite OpenProject (um H altera o scaffold congelado; um A tem exceção de DOM) e um no linkifier Zulip. Nesse par do Zulip, A tem timeout ao clicar em Send e H tem erros de console, embora parte da jornada produza observações e prints. Não foi possível avaliar a obrigação com o contrato do oráculo. Os quatro resultados individuais não avaliáveis formam três pares; nenhum foi reexecutado.

## Limites e conclusão

A coleta fornece evidência local sobre a perda de uma obrigação nas páginas geradas, principalmente pela omissão construída. Não demonstra que todos os textos antigos eram smells, que o commit corrigiu um bug de requisito, ou que omissão e redação vaga têm o mesmo efeito. Os rótulos da triagem são decisões de LLM, não validação humana nem confirmação do vínculo com literatura de smells.

A seleção e o desenho foram preparados após conhecer os resultados dos 46. Há um único provedor, dois modelos e poucos requisitos por projeto. O contexto moderno, a posição da citação e a duplicação de informação limitam a reconstrução. Empates em falha incluem problemas do próprio A e não evidenciam degradação causada por H.

Os diagnósticos A atual versus A anterior e, onde H=C, H atual versus C anterior ficam separados em `h-vs-a.json`. Não substituem a comparação A/H contemporânea nem os resultados anteriores congelados. H2 continua sem teste decisivo; esta coleta não fecha o desfecho ordinal de qualidade nem a auditoria humana de 20%.

A próxima decisão científica é auditar a admissão e os mappings, especialmente os casos mais vagos, antes de chamar essas mudanças de smells históricos confirmados. A coleta dos 46 e os 60 pares históricos continuam separados.
