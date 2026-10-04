# Context_cue v2: 46 requisitos codificados

Status: exploratório. Codificação realizada depois da coleta A/B/C, com os codificadores cegos às implementações, aos resultados E2E e à sonda. O pesquisador já conhecia resultados e a revisão do critério foi pós-coleta; isso não é uma nova pré-registração prospectiva dos E2Es.

A tentativa v1 que falhou permanece preservada. A v2 corresponde ao #161, commit `879efbc`, e foi congelada antes da primeira chamada deste painel. O critério exige uma pista que implique a condição e o comportamento da regra; a mera presença de elementos não conta.

## Execução e concordância

- 15/15 votos de qualificação corretos, em cinco controles e três modelos.
- 46/46 casos codificados; nove com pista, 37 sem pista, nenhum código desconhecido.
- 112 chamadas tentadas e válidas: 15 controles, 92 votos principais e cinco desempates. Sem retry ou reparo.
- Astra (`gpt-6-astra`) e Sol (`gpt-6-sol`) concordaram em 41/46 (89,1%); kappa de Cohen = 0,6461538462. Os cinco desacordos foram Astra=yes/Sol=no; Luna (`gpt-6-luna`) resolveu três como yes e dois como no.
- Matriz principal: 35 no/no, seis yes/yes, cinco yes/no e zero no/yes. Modelos do mesmo provedor não substituem uma auditoria humana independente.

## Codificação por projeto

| Projeto | Com pista | Sem pista |
| --- | ---: | ---: |
| grist | 0 | 6 |
| immich | 2 | 1 |
| mattermost | 0 | 6 |
| mealie | 1 | 1 |
| nextcloud | 3 | 3 |
| openproject | 1 | 5 |
| paperless-ngx | 1 | 4 |
| wekan | 0 | 6 |
| zulip | 1 | 5 |

## Cruzamento descritivo com os E2Es existentes

| Código | Regra violada em C | Regra mantida | Desconhecida |
| --- | ---: | ---: | ---: |
| Com pista (nove requisitos) | 14 | 20 | 2 |
| Sem pista (37 requisitos) | 91 | 53 | 4 |

Entre execuções avaliáveis, são 14/34 (41,2%) violações com pista e 91/144 (63,2%) sem pista. São contagens repetidas, não 178 requisitos independentes. Essa associação não demonstra que a pista causou a recuperação; características dos requisitos, modelos, projetos e contratos do scaffold também podem explicar a diferença.

O ajuste logístico misto de H1b, com interceptos de projeto e requisito e os quatro termos pré-especificados, ainda não foi executado. Esta tabela não o substitui. Qualquer análise que use estes códigos deve manter explícita a codificação pós-coleta e a auditoria humana pendente.

## Custódia e reprodução

Os recibos de congelamento e execução foram conferidos integralmente, assim como as identidades dos 46 casos, todos os votos e o vínculo de cada citação literal ao prompt C congelado. [Resultados e proveniência públicos](../../data/context-cue/20261004-v2/) contêm decisões, citações de material público e hashes. Capturas, comandos e pacotes privados continuam no Mac.

```sh
python3 scripts/selected46_report.py --results data/selection-abc-results/20261003 --context-cue data/context-cue/20261004-v2/results.json --json /tmp/selected46-cue.json --markdown /tmp/selected46-cue.md
```

O placar original sem códigos e os 46 results.json dos E2Es permanecem inalterados. O novo placar está separado no pacote v2; H1a e o controle B/A permanecem numericamente idênticos. A mudança no renderer apenas evita afirmar que todos os códigos estão ausentes quando eles foram fornecidos.

A coleta A/B/C continua com 79 degradações, 71 empates em sucesso, 22 em falha, 12 pares não avaliáveis e nenhuma melhora. H2 não foi testada.
