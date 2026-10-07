# Omissão compartilhada: resumo entre testadores

Status: descritivo e exploratório. O script e a regra de inclusão foram escritos antes dos resultados dos testadores seguintes (Sonnet 5.5 e Opus 5.5, em execução em 06/10), para que acrescentar uma rodada não mude a forma de resumir.

## Regra

- Toda rodada avaliada publicada em `data/shared-omission-e2e` entra no registro `data/shared-omission-e2e/testers.json` e no resumo, qualquer que seja o resultado.
- Uma rodada cuja avaliação falhou entra no registro com o motivo e fica fora do resumo. É o caso da primeira avaliação dos Claude 4.6 sem Docker (#189).
- Nenhuma rodada é escolhida ou descartada depois de conhecido o resultado.
- Os testadores não são agregados entre si, e não se calcula teste entre eles. Eles compartilham páginas, requisitos e implementações e, dentro de um provedor, podem compartilhar família de modelo.
- O script recusa uma rodada com requisitos, páginas ou mutantes mostrados diferentes da primeira. Também recusa a rodada se a análise publicada não coincidir com a recomputação congelada.

## Estado com três testadores

| Testador | Provedor | Completo | Incompleto | Incompleto + código | MA1 [IC por projeto] | Suítes válidas (completo / incompleto / código) | Reprova a referência e aprova o mutante mostrado (completo / incompleto / código) |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| gpt-6-astra | OpenAI | 0,76 | 0,10 | 0,04 | 0,66 [0,50; 0,80] | 38 / 39 / 19 | 0 / 0 / 23 |
| claude-sonnet-4-6 | Anthropic | 0,40 | 0,05 | 0,00 | 0,35 [0,22; 0,47] | 26 / 22 / 17 | 4 / 5 / 27 |
| claude-opus-4-6 | Anthropic | 0,80 | 0,085 | 0,00 | 0,715 [0,56; 0,88] | 46 / 33 / 15 | 1 / 11 / 28 |

O p exato por projeto foi 0,0078 em todas as comparações MA1. Por requisito, o completo superou o incompleto nos três testadores em 9 dos 25 requisitos, em dois testadores em 11 e em um testador em 5. Nenhum requisito ficou sem a vantagem em todos.

## Como acrescentar uma rodada

1. Publicar a rodada no seu próprio PR, com protocolo congelado antes das chamadas.
2. Acrescentar a entrada ao registro, com status `evaluated` ou `failed_evaluation` e o motivo.
3. Rodar `python3 scripts/shared_omission_testers.py` e commitar o `testers-summary.json` regenerado.
4. O teste `tests/test_shared_omission_testers.py` confere que todas as rodadas avaliadas do registro aparecem no resumo.
