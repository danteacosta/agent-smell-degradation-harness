# Coleta dos 46 requisitos selecionados: resultado completo

Status: exploratório (`confirmatory_eligible: false`). Os números abaixo vêm de `scripts/selected46_report.py` aplicado aos 46 `results.json` publicados em `data/selection-abc-results/20261003/`, e o placar completo está em `scoreboard.md` e `scoreboard.json` na mesma pasta. Antes de publicar, cada `results.json` foi conferido contra o hash registrado em `collection-progress.json` (46/46 iguais). Os pacotes privados (prompts, capturas e relatórios de navegador) continuam com a custódia original; só os resultados por slot estão aqui, e o caso Nextcloud mantém o pacote público completo do #153.

## Coleta

46 requisitos de 9 projetos × A/B/C × 2 modelos × 2 repetições = 552 execuções, todas tentadas uma vez, sem retry. Por categoria: 373 pass, 125 falha só no alvo, 26 falha mista, 8 falha só em controle, 16 erros de navegador e 4 saídas inválidas.

Para os estimandos, o desfecho é a regra-alvo:

- mantida: `pass` ou `non_target_only_failure`;
- violada: `target_only_failure` ou `mixed_failure`;
- desconhecida: o resto.

## Regra-alvo por modelo e braço

| Modelo | Braço | Mantida | Violada | Desconhecida |
| --- | --- | ---: | ---: | ---: |
| gpt-5.6-luna | A | 74 | 14 | 4 |
| gpt-5.6-luna | B | 74 | 13 | 5 |
| gpt-5.6-luna | C | 29 | 59 | 4 |
| gpt-5.6-sol | A | 81 | 8 | 3 |
| gpt-5.6-sol | B | 79 | 11 | 2 |
| gpt-5.6-sol | C | 44 | 46 | 2 |

## Estimandos pareados (pré-registro, seção 5)

Os pares casam requisito, modelo e repetição; as repetições são médias dentro do requisito. O intervalo é bootstrap por projeto, e o p-valor vem do teste de troca de sinal com 5.000 sorteios.

| Comparação | Observado | Pior caso | Melhor caso |
| --- | --- | --- | --- |
| H1a: C vs A | **0,725** [0,68; 0,78], p ≈ 0,0002; 172 pares, 44 requisitos, 9 projetos | 0,742 | 0,707 |
| Controle: B vs A | **0,500** [0,48; 0,52], p = 1,0; 172 pares, 45 requisitos | 0,524 | 0,486 |

- **C vs A:** 79 pioras com omissão, 93 empates e nenhuma melhora; 12 pares não avaliáveis. Pelo menos uma piora apareceu em 26 dos 46 requisitos, cobrindo os 9 projetos.
- **B vs A:** 4 pioras, 164 empates e 4 melhoras. Reescrever o texto sem remover a regra não produziu efeito; a diferença em C não vem só de mudar a redação.
- **Pior e melhor caso:** cada um põe todos os desconhecidos de um lado só. São limites determinísticos, sem intervalo.

Por modelo (exploratório): Luna 0,739 [0,71; 0,78], com 42 pioras e 42 empates; Sol 0,710 [0,65; 0,79], com 37 pioras e 51 empates. Nenhum dos dois teve melhora.

## Diagnóstico pós-hoc: casos em que A falha

Oito requisitos tiveram a regra mantida em menos de 3 das 4 execuções de A:

- grist-tutorial-restart
- mealie-organize-food-permission
- openproject-auto-theme-contrast
- openproject-filter-text-autoupdate
- openproject-invite-permission-basis
- paperless-doc-title-placeholder
- wekan-member-same-org-team
- zulip-reverse-linkifier-paste

Em vários deles, A e B falham juntos (por exemplo, `wekan-member-same-org-team` e `zulip-reverse-linkifier-paste` com 0/4 em A, B e C). Isso indica que o caso não mede a omissão: o oráculo ou o scaffold é mais exigente do que o texto completo, ou o comportamento é difícil mesmo com a regra. Três desses casos já estavam entre os pontos de revisão do lote 2: o convite do OpenProject, em que o oráculo encontra a opção pelo nome; o filtro do OpenProject, em que o scaffold só dispara o handler no evento `change`; e o linkifier do Zulip, por causa do nome do campo `linkText`.

Esses casos geram empates em falha, não pioras, e por isso não inflam H1a. Tirá-los, numa análise não pré-registrada e só diagnóstica, dá 0,748 [0,70; 0,80] em 38 requisitos. A conclusão não muda. Eles devem ser revistos antes de qualquer uso confirmatório.

## H1b, descritivo

Violação da regra em C por covariável, contando execuções; não há modelo ajustado.

| Covariável | Nível 1 | Nível 0 |
| --- | --- | --- |
| `numeric` | 16 violadas / 0 mantidas | 89 / 73 |
| `derived_state` | 11 / 13 | 94 / 60 |
| `memorized` (do modelo da execução) | 38 / 36 | 67 / 37 |
| `context_cue` | não codificado | — |

A direção de `memorized` é a esperada: a regra recuperada sem contexto é violada menos vezes. A de `numeric` também: as regras numéricas foram violadas em todas as execuções C. `derived_state` vai na direção contrária à hipótese. São contagens de execuções repetidas, não de requisitos independentes. O modelo misto de H1b só deve ser ajustado depois da codificação de `context_cue` (`bash scripts/run_context_cue_panel.sh`).

## O que isto permite dizer

Em 46 requisitos de 9 projetos, remover uma regra testável do requisito piorou o cumprimento da regra em 79 de 172 comparações pareadas e não o melhorou em nenhuma. A reescrita sem remoção não teve efeito. Isso é evidência exploratória ampla e consistente com H1a.

Ainda não é confirmação, por cinco motivos:

- a coleta tem `confirmatory_eligible: false`;
- a seleção e as covariáveis vieram de painéis de LLM, sem a auditoria humana de 20%;
- a revisão de integração dos casos não foi cega;
- oito casos mostram problemas de instrumento em A;
- o desfecho primário (oráculo de navegador ou rótulos ordinais) e a direção do teste continuam abertos para o orientador.

H2 não foi testada nesta coleta.
