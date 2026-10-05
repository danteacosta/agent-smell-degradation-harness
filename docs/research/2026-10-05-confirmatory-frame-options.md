# Quadro da coleta confirmatória: duas opções

Status original na preparação do quadro: sem chamadas de modelo. **Atualização de 05/10:** as duas triagens estão concluídas, conforme o [relatório](2026-10-05-confirmatory-screening-results.md); não houve geração A/B/C nova. A escolha do quadro é uma decisão para a reunião com o orientador. A triagem das duas opções pode rodar antes dela, porque é cega e não gera código.

## Opções

| | Reserva do quadro registrado | Janela 2024 |
| --- | --- | --- |
| Janela | 2025-01-01 a 2026-09-30, a mesma do pré-registro | 2024-01-01 a 2024-12-31 |
| Origem | candidatos do quadro atual que nunca entraram numa amostra de triagem | quadro novo, minerado com os mesmos filtros e caminhos |
| Candidatos | 693, em 8 projetos | 377, em 7 projetos |
| Amostra de triagem (≤ 30 por projeto) | 201 | 166 |
| Projetos | grist 28, immich 21, mattermost 20, nextcloud 104, openproject 174, paperless 12, wekan 97, zulip 237 | grist 22, immich 43, mealie 11, nextcloud 13, openproject 81, paperless 40, zulip 167 |
| A favor | mesma janela e mesmas regras; nada a justificar | requisitos mais antigos e independentes dos 46 |
| Contra | mesmos projetos dos 46; mealie se esgotou; paperless tem só 12 | maior chance de os modelos terem visto o texto (a sonda de memorização mede isso); Mattermost e Wekan quase não têm commits nos caminhos registrados em 2024, porque a documentação mudou de lugar (Mattermost só a partir de 2025-07) |

A recomendação original de 9 projetos × 4 requisitos foi retirada pelo [planejamento corrigido](2026-10-05-confirmatory-sample-size.md), que trata projetos como unidade de troca de sinais. O cenário de efeito próximo de 0,60 sugere 8 × 5 como sensibilidade, ainda sem aprovação metodológica. A triagem terminou com 95 admitidos provisórios na reserva e 67 em 2024. Mealie teve zero admitidos: as duas opções juntas cobrem oito projetos. A reserva sozinha tem só três candidatos admitidos no Paperless e quatro no Immich, insuficientes para 8 × 5; unir janelas também exige decisão prospectiva. Não há seleção ou coleta liberada por estes números.

## Arquivos

- `data/requirement-sampling/frame-2024-candidates.jsonl`: quadro da janela 2024, minerado com `scripts/mine_requirement_candidates.py --since 2024-01-01 --until 2024-12-31 --id-salt 2024-window:`. Os novos parâmetros não mudam o comportamento padrão.
- `data/requirement-sampling/screening-confirmatory-{reserve,w2024}-20261005.json`: amostras de triagem, sementes 2026100502 e 2026100503.
- `data/confirmatory-planning/frame-options.json`: contagens.
- `scripts/confirmatory_frame.py`: gera as duas amostras. `tests/test_confirmatory_frame.py` confere que nenhum candidato já foi triado e que os IDs da janela 2024 não colidem com os do quadro registrado.

## Triagem (no Mac)

```bash
bash scripts/run_confirmatory_screening.sh both      # ou reserve / w2024
```

Usa o mesmo painel e os mesmos controles das rodadas 1 e 2, sem retry. São cerca de 430 chamadas para a reserva e 370 para 2024.
