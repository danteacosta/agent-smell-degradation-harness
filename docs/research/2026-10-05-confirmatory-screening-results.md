# Triagem das opções para a coleta confirmatória, 5 de outubro de 2026

As duas triagens terminaram. Dos 367 candidatos, 162 receberam admissão provisória, 203 foram excluídos e dois ficaram sem decisão. Estes números descrevem elegibilidade proposta por LLMs, não requisitos já selecionados, smells confirmados ou resultados E2E.

## Resultados preservados

| Opção | Candidatos | Admitidos provisórios | Excluídos | Sem decisão | Acordo | Desempate | Kappa primários | Pares primários válidos | Chamadas |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Reserva 2025–2026 | 201 | 95 | 105 | 1 | 180 | 21 | 0,808799 | 199 | 441 |
| Janela 2024 | 166 | 67 | 98 | 1 | 148 | 18 | 0,790594 | 165 | 368 |

Cada painel usou Astra e Sol como primários, Luna para desempate. Os seis controles de cada um dos três modelos passaram: 18/18 em cada opção. As 809 chamadas incluem 36 controles e 773 chamadas sobre candidatos. Não houve retry, reparo ou nova coleta nesta consolidação.

A reserva preserva duas chamadas primárias falhas e uma resposta de desempate inválida. A janela 2024 preserva uma chamada primária falha e uma resposta de desempate inválida. Os dois desempates inválidos permanecem `unresolved`, sem imputação.

| Projeto | Reserva | 2024 | Soma descritiva |
| --- | ---: | ---: | ---: |
| Grist | 10 | 9 | 19 |
| Immich | 4 | 9 | 13 |
| Mattermost | 11 | 0 | 11 |
| Nextcloud | 6 | 10 | 16 |
| OpenProject | 23 | 22 | 45 |
| Paperless | 3 | 7 | 10 |
| WeKan | 19 | 0 | 19 |
| Zulip | 19 | 10 | 29 |
| Mealie | 0 | 0 | 0 |
| Total | 95 | 67 | 162 |

A reserva tem admitidos em oito projetos; 2024, em seis. Mealie teve 11 candidatos avaliados e nenhum admitido. A soma continua cobrindo oito projetos, não nove, e não aprova a união dos quadros.

## Custódia e recálculo

Os arquivos públicos ficam em `data/llm-screening-confirmatory-{reserve,w2024}-20261005/`: resultado, controles, manifesto sem caminho do executável, auditoria, custódia e recibo público. Capturas brutas e streams do CLI continuam privados.

A auditoria somente leitura conferiu os inventários completos (2.856 arquivos na reserva e 2.384 em 2024), os recibos congelados e finais, o vínculo ao início da execução, os hashes das amostras públicas, a reconstrução das rotas, o parsing de cada voto válido e os placares. Não houve divergências. Os dados não foram editados para corrigir respostas inválidas.

A comparação entre opções não encontrou IDs repetidos, textos de mudança idênticos ou equivalentes após normalização de espaço/caixa, nem vínculos projeto/commit/arquivo repetidos. Também não encontrou regras-alvo admitidas literalmente iguais após normalização. Isso não exclui duplicação semântica: funcionalidades equivalentes precisam de revisão antes da seleção.

Há diferenças textuais entre votos favoráveis em 93 admitidos da reserva e 66 de 2024. Podem ser paráfrases ou regras diferentes. O exportador preserva o mapeamento que o painel escolheu, sem tratá-lo como consenso sobre a redação ou resolver semanticamente a diferença. As listas estão nos `audit.json`, com revisão pendente.

O recálculo detalhado por projeto e as verificações cruzadas estão em [screening-audit-20261005.json](../../data/confirmatory-planning/screening-audit-20261005.json). Os recibos públicos permitem verificar integridade; reabrir a custódia bruta requer os pacotes privados.

## O que estes números permitem preparar

O [planejamento corrigido](2026-10-05-confirmatory-sample-size.md) usa troca de sinais por projeto. Para efeito-alvo próximo de 0,60, 8 projetos × 5 requisitos foi o menor desenho simulado acima de 0,80 no cenário de estresse. Isso é sensibilidade de planejamento, não certificado de poder ou decisão aprovada.

A reserva triada sozinha ainda não preenche 8 × 5: Paperless tem três admitidos provisórios e Immich quatro. A união das duas opções oferece pelo menos cinco admitidos provisórios por projeto nos oito projetos, mas mudaria a janela do quadro e precisa de uma regra prospectiva aprovada. Mais triagem na reserva, outro desenho ou outro projeto também são decisões possíveis; nada foi sorteado ou coletado automaticamente.

Antes da próxima coleta faltam: escolher e registrar quadro, efeito-alvo e análise; revisar regras e duplicações; cumprir a auditoria humana aleatória de 20%; selecionar com procedimento congelado; preparar sonda e oráculos; qualificar navegação, escopo e controles; congelar prompts/runtime/schedule antes de gerar A/B/C. A sonda e os novos E2Es não foram iniciados nesta rodada.

## Estado científico

Os 46 requisitos A/B/C e os 17 casos do braço histórico continuam coleções exploratórias separadas. Esta triagem não acrescenta observações de H1a/H1b, não confirma smells e não testa H2. A reunião com o orientador e a auditoria humana continuam pendentes.
