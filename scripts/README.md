# Scripts: o que está ativo e o que é histórico

São 85 scripts Python e 8 de shell. A maioria é de uso único: cada um congelou, rodou ou auditou um piloto específico, e o hash dele está registrado nos pacotes daquele piloto. **Não edite scripts históricos.** Mudar um byte faz a verificação do pacote correspondente falhar (`runtime drift`). Isso inclui os caminhos fixos do Mac (`/Users/...`, `/opt/homebrew/bin/codex`) que aparecem em cerca de 25 deles. Para um script novo, use as variáveis `EVIDENCE_ROOT` e `PYTHON` dos runners `.sh`, ou passe `--executable`, em vez de fixar caminhos.

## Pipeline atual (outubro)

| Etapa | Script | Runner no Mac |
| --- | --- | --- |
| Minerar candidatos da documentação | `mine_requirement_candidates.py` | — |
| Quadros e amostras de triagem da coleta confirmatória | `confirmatory_frame.py` | — |
| Triagem por painel de LLM | `llm_screening_panel.py` | `run_llm_screening*.sh`, `run_confirmatory_screening.sh` |
| Seleção dos 46 exploratórios | `select_requirements.py`, `check_current_documentation.py` | — |
| Seleção confirmatória (proposta: ordem, registro, parada) | `confirmatory_selection.py` | — |
| Sonda de memória | `memorization_probe.py` | `run_memorization_probe.sh` |
| Casos A/B/C (fixtures, configs, qualificação) | `build_selection_cases.py`, `selection_cases/` | `qualify_selection_cases.sh` |
| Gerar e executar um caso | `abc_case.py` (usa `persistence_collection.py` e `kanboard_duplicate_collect.py` como bibliotecas) | — |
| Placar e H1a | `selected46_report.py` | — |
| H1b | `h1b_agq.py` (atual), `h1b_mixed_logit.py` (Laplace, mantido por registro) | — |
| `context_cue` | `context_cue_panel.py` | `run_context_cue_panel.sh` |
| Braço histórico | `historical_arm.py`, `historical_evidence.py` | `run_historical_arm.sh` |
| Ancoragem de testes | `test_anchor_experiment.py` | `run_test_anchor.sh` |
| Poder | `confirmatory_power.py` | — |
| Auditoria humana | `human_audit_sheet.py`, `screening_audit_sample.py` | — |
| Omission Bench | `omission_bench.py` | — |

## Históricos (setembro e começo de outubro): não editar

Pilotos e revisões por caso, substituídos pelo `abc_case.py` genérico:
- `kanboard_*`, `nextcloud_*`, `openproject_*`, `paperless_*`, `realworld_*`, `todomvc_*`;
- `six_project_e2e_*`, `three_project_scaffold_*`, `persistence_collection.py` (este último também é biblioteca do pipeline atual).

Os configs migrados em `data/abc-cases/` (campo `migrated_from`) apontam para eles, e `tests/test_abc_case.py` confere que o caso genérico reproduz cada coletor antigo.

Estudos anteriores de critérios, juízes e anotação:
- `criteria_consensus.py`, `criteria_expansion.py`, `focus_chain.py`, `behavioral_expansion.py`;
- `h1_existing_artifacts_ordinal_audit.py`, `h1_ordinal_audit_results.py`, `judge_controls.py`;
- `prepare_*`, `run_llm_panel.py`, `merge_llm_panel.py`, `validate_*`, `freeze_corpus_manifest.py`;
- `run_exploratory_llm_judged_prepilot.py`, `run_native_provider_smoke.py`.

Escopo de H2, sem dados coletados: `check_feature_plane_mutation_gate.py`, `check_split_mutation_gate.py`.

Utilitários: `dependency_bundle.py`, `reproduce_evidence.py`, `audit_existing_e2e_results.py`, `multi_obligation_candidates.py`.

## Regra para scripts novos

Um script novo que chama modelo deve ter:
- congelamento antes da execução, com hashes dos prompts e do runtime;
- execução única, sem retry;
- uma pasta de saída nova e fora do repositório para a evidência bruta;
- um teste com provedor simulado.

Siga `abc_case.py` ou `context_cue_panel.py` como modelo.
