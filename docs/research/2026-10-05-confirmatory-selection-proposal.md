# Proposta: seleção da coleta confirmatória de H1a

Status: **proposta, não aprovada.** Nenhum requisito foi selecionado, nenhuma revisão de mapeamento começou e nenhuma chamada de modelo foi feita. A proposta só passa a valer depois de aprovada pelo orientador e registrada no pré-registro (seção 7). Até lá, o registro de decisões (`data/confirmatory-selection/selection-ledger.jsonl`) fica vazio.

## Desenho proposto

- 8 projetos × 5 requisitos, o menor desenho simulado acima de 0,80 de poder no cenário de estresse com efeito de cerca de 0,60 ([planejamento](2026-10-05-confirmatory-sample-size.md)).
- Os projetos são os 8 com admitidos provisórios na triagem de 05/10: Grist, Immich, Mattermost, Nextcloud, OpenProject, Paperless, WeKan e Zulip. Mealie teve zero admitidos.
- Decisão pelo teste exato de inversão de sinais por projeto junto com o IC por bootstrap de projetos, ambos bilaterais.

## Ordem congelada

`scripts/confirmatory_selection.py order` gerou `data/confirmatory-selection/selection-order-proposal.json`, com a ordem completa dos 162 admitidos provisórios:

- **Reserva antes de 2024.** Em cada projeto, vêm primeiro todos os admitidos da reserva (quadro registrado, 2025-01 a 2026-09) e depois todos os de 2024.
- **Semente fixa: 2026100506.** Dentro de cada projeto e janela, os candidatos são ordenados por ID e embaralhados com `random.Random(f"2026100506:{projeto}:{janela}")`. Um teste confere que a ordem publicada é reproduzida a partir dos resultados públicos da triagem.
- **Linhas sem decisão do painel ficam de fora**, porque não são admissões.

| Projeto | Reserva | 2024 | Na lista |
| --- | ---: | ---: | ---: |
| Grist | 10 | 9 | 19 |
| Immich | 4 | 9 | 13 |
| Mattermost | 11 | 0 | 11 |
| Nextcloud | 6 | 10 | 16 |
| OpenProject | 23 | 22 | 45 |
| Paperless | 3 | 7 | 10 |
| WeKan | 19 | 0 | 19 |
| Zulip | 19 | 10 | 29 |

## Regras do procedimento

1. **Ordem estrita.** Cada projeto é processado na ordem da lista. Um candidato só é decidido depois que todos os anteriores do mesmo projeto foram decididos.
2. **Duas decisões possíveis:** `qualified` ou `excluded`. Exclusão só com um dos motivos abaixo.
3. **Parada por meta.** Quando um projeto chega a 5 qualificados, os candidatos seguintes não são examinados.
4. **Parada por insuficiência.** Se a lista de um projeto acabar com menos de 5 qualificados, o projeto fica `insufficient` e o procedimento inteiro para (`stopped_insufficient`), com o registro do que aconteceu. Nada preenche a lacuna automaticamente: outro projeto, outra janela ou outro desenho seriam decisões novas, registradas como desvio.
5. **Registro só por acréscimo.** Cada decisão é uma linha nova no registro, com `seq`, `project`, `candidate_id`, `rank`, `action`, `reason` (quando houver exclusão), `duplicate_of` (para duplicatas), `decided_by`, `date` e `evidence` (caminho ou descrição da evidência). Nenhuma linha é editada nem apagada. `walk` reproduz o registro contra a ordem e recusa qualquer violação: pular posição, motivo fora da lista, lacuna de `seq`, decisão depois da meta ou falta de evidência.

Motivos permitidos de exclusão:

| Motivo | Quando |
| --- | --- |
| `duplicate_semantic` | afirma a mesma regra que um candidato de posição anterior (indicar em `duplicate_of`) |
| `overlaps_exploratory` | afirma a mesma regra que um dos 46 casos exploratórios, um dos 17 históricos ou um piloto (indicar em `duplicate_of`) |
| `mapping_invalid` | a regra do painel não é o que a mudança da documentação afirma |
| `not_constructible` | nenhuma página autocontida exercita a regra com uma observação que passa e uma que falha |
| `oracle_not_qualified` | o oráculo não passa nos seus controles autorados (páginas correta e incorreta) |
| `human_audit_exclude` | a auditoria humana cega excluiu o candidato; vale só para os candidatos da amostra de 20% |

## Ressalvas registradas

- **3 de 40 é o mínimo vindo de 2024**, e não uma previsão. Com os admitidos de hoje, entram só 2 do Paperless e 1 do Immich, mas cada exclusão nesses projetos puxa mais candidatos de 2024. O Paperless tem 10 na lista: se 6 caírem, ele fica insuficiente.
- **A janela é descritor e análise secundária.** As quatro covariáveis de H1b continuam as mesmas.
- **A sensibilidade sem 2024 não mantém o desenho.** Com o mínimo de hoje, ficaria com 37 requisitos distribuídos de forma desigual entre os projetos e sem o poder estimado de 8 × 5. Ela é descritiva.

## Antes de começar a percorrer as listas

- aprovação desta proposta e registro como desvio datado na seção 7;
- registro do pré-registro com as decisões da seção 8;
- auditoria humana da amostra de 20% (#176), porque `human_audit_exclude` depende dela.

Os passos seguintes, em ordem: revisão de mapeamento e de duplicatas, construção e qualificação dos oráculos (cada exclusão vira linha do registro), sonda de memória dos selecionados e congelamento de prompts, runtime e agenda antes da geração A/B/C.
