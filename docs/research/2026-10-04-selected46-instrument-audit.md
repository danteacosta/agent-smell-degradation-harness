# Auditoria pós-hoc dos oito casos A e qualificação de context_cue

Data: 2026-10-04. Revisão não cega de código, prompts, runtimes e relatórios existentes. Não é avaliação independente de severidade nem confirmação de smells. Nenhum resultado, prompt, runtime ou pacote congelado foi alterado; nenhuma geração A/B/C foi repetida.

## Contrato desta revisão

Explicar falhas do braço completo sem presumir que sejam defeitos do oráculo. Distinguir violação do alvo, falha em controle não alvo e resultado desconhecido. Preservar as categorias observadas e propor mudanças apenas para um sucessor congelado. Conferir a apresentação estatística sem alterar os estimandos.

## Oito casos

A escolha foi pós-hoc: cumprimento do alvo em menos de três das quatro execuções A. Isso inclui desconhecidos; não significa duas falhas-alvo confirmadas em cada caso.

| Caso | Diagnóstico da inspeção A | Consequência prospectiva |
| --- | --- | --- |
| `grist-tutorial-restart` | Luna reinicia o slide sem restaurar dados originais; Sol cumpre. Regra e API necessárias estão explícitas. | Preservar defeitos observados; nenhuma falsa rejeição demonstrada. |
| `paperless-doc-title-placeholder` | Luna salva qualquer template, inclusive o placeholder proibido; Sol cumpre. | Preservar defeitos observados. |
| `zulip-reverse-linkifier-paste` | As quatro páginas registram conversão apenas em `onSend`, sem converter ao colar antes do envio. | Preservar falhas da jornada exigida, sem relaxar o endpoint. |
| `mealie-organize-food-permission` | As quatro páginas presumem uma lista de permissões; a fixture usa objeto booleano `organizeGroupData`, cujo contrato não está exposto. Duas têm TypeError e duas bloqueiam também o usuário autorizado. | Documentar tipos e chaves comuns aos três braços num novo pacote; os atuais continuam dois desconhecidos e duas falhas não alvo em A. |
| `wekan-member-same-org-team` | As páginas usam `organizations` ou `Organizations`/`Teams`; as fixtures usam `orgs`/`teams`, sem schema exposto ao modelo. Uma implementação também permite todos por uma expressão OR. | Explicitar schema comum em sucessor. O runner rejeita o comportamento produzido, mas a atribuição causal é limitada pelo contrato omitido. |
| `openproject-auto-theme-contrast` | As quatro páginas A acessam `mode`/`increaseContrast`; a fixture usa `colorScheme`/`contrast`. Todas registram `unknown theme`. | Explicitar schema comum. Preservar quatro desconhecidos em A, não chamá-los de quatro defeitos-alvo. |
| `openproject-filter-text-autoupdate` | O callback fornecido dispara `change`; as páginas não adicionam atualização por `input`. Três falham ao digitar; uma também envia IDs string onde a API espera números. | Explicitar evento e tipos comuns. Qualificar a jornada ao digitar e a pesquisa em campos distintos. |
| `openproject-invite-permission-basis` | Três páginas escolhem um grupo como principal embora A peça usuário ou email; presumem tipo `placeholder` em vez de `placeholder_user`. A quarta usa `prompt()` nativo, fora da interação que o runner opera. | Explicitar schema e interações suportadas em sucessor, ou qualificar adaptador de diálogo nativo. |

Cobertura: os 32 HTMLs A, prompts e relatórios correspondentes, os oito runtimes congelados, specs atuais e linhas A/C. Não foi demonstrada falsa rejeição do oráculo. A inspeção identifica mecanismos plausíveis e concretos, mas não separa causalmente todas as dificuldades do scaffold das escolhas do modelo.

Nos 32 pares desses oito casos: **quatro degradações, 19 empates e nove não avaliáveis**, nenhuma melhora. As degradações são as duas repetições Sol do Grist e as duas do Paperless. Não substituir a análise principal pela exclusão pós-hoc desses casos.

A evidência detalhada permanece no pacote privado `selected46-abc-20261003-reviewed/cases/`, com os recibos originais. [Resultados públicos por slot](../../data/selection-abc-results/20261003/) e [relatório completo](2026-10-04-selected46-results.md).

## Qualificação do painel context_cue

Tentativa privada `context-cue-panel-20261004-100949`: status `stopped_controls_failed`. Foram 12 chamadas de qualificação, sem retry, e **zero dos 46 casos codificados**.

| Controle | Esperado | Astra | Sol | Luna |
| --- | --- | --- | --- | --- |
| `ctl-cue-restated` | yes | yes | yes | yes |
| `ctl-cue-field-name` | yes | yes | yes | yes |
| `ctl-cue-none` | no | no | no | yes |
| `ctl-cue-knowledge-only` | no | no | no | no |

No controle que falhou, a regra omitida é fechar uma tarefa concluir suas subtarefas. O texto C apenas pede um botão Close que fecha a tarefa. O Luna inferiu a relação entre tarefa e subtarefas, embora o controle exija pista textual sobre a regra omitida. O gate funcionou conforme previsto; não houve substituição do juiz nem flexibilização retrospectiva do controle.

Astra e Sol acertaram seus quatro controles; isso não autoriza declarar completo um painel que exige qualificação também do desempate. `context_cue` permanece não codificado e o modelo ajustado H1b não foi executado. Uma nova tentativa precisa de decisão prospectiva documentada sobre o painel e novo pacote; preservar esta tentativa como falha operacional.

SHA-256 do resumo privado, contendo somente status e votos dos controles: `50f6ed22b73d03f5c2e9553afef65031679929891ccca5b7d560ceefa31e1c86`.

## Apresentação estatística

Corrigido o arredondamento do p-valor no placar: um valor Monte Carlo positivo próximo de 0,0002 aparecia como `0.000`. A regressão reproduziu o arredondamento antes da correção. Os resultados por slot, o JSON numérico, as estimativas e os intervalos permanecem iguais.

O escore pareado atribui 1 à piora, 0,5 ao empate e 0 à melhora, com média por requisito; não é porcentagem de gerações defeituosas. Um escore 0,5 não estabelece equivalência. O p-valor de troca de sinal tem uma hipótese adicional de sinais trocáveis entre requisitos; o bootstrap por projeto não comprova essa hipótese. Essas ressalvas não mudam os resultados exploratórios e não aprovam decisões confirmatórias pendentes.
