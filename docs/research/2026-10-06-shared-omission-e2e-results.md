# Omissão compartilhada: E2Es com código do próprio mutante

Em 25 requisitos de oito projetos, os testes escritos com o requisito completo detectaram mais perdas de regra que os escritos com o pedido incompleto, inclusive quando este vinha acompanhado do código defeituoso. Os escores médios por requisito foram 0,760, 0,100 e 0,040, respectivamente. As duas comparações com o requisito completo satisfizeram a regra registrada de intervalo acima de zero e p abaixo de 0,05. É uma extensão exploratória sobre perdas já conhecidas, não confirmação de H1 nem teste de H2.

## Desenho e custódia

O [protocolo do #181](https://github.com/danteacosta/agent-smell-degradation-harness/blob/eec5110c4353dc5da3c6dc29f36be23bd2b090e9/docs/preregistration/2026-10-05-shared-omission-e2e.md) e o adaptador foram publicados em `eec5110` antes das novas chamadas. A chave legada `code_incomplete` nesta coleta significa pedido incompleto + código do **mutante confirmado selecionado**, explicitado por `code_context_role` no manifesto. Não é o código da referência correta fornecido no #180.

Os alvos permanecem as mesmas 191 páginas congeladas: 81 C com perda confirmada, 91 A corretas, 17 C recuperadas e duas C não confirmadas apenas no escore ingênuo. O código entregue ao testador vem de um mutante por requisito, sorteado com semente 2026100508 entre IDs ordenados; a referência correta anterior é mantida para avaliar elegibilidade. Nenhuma implementação nova foi gerada. O testador foi gpt-6-astra, duas suítes por fonte e requisito, com os três braços coletados juntos em ordem sorteada.

A execução única começou em 05/10 às22:33 e terminou em 06/10 às09:12 (America/Maceio). Houve suspensão do Mac por tampa fechada durante a madrugada e duas chamadas terminaram com TimeoutError. A suspensão foi inicialmente interpretada como bloqueio do runner, mas registros Sleep/Wake e o progresso posterior corrigiram esse diagnóstico. Não houve reinício, retry, reparo ou mudança do pacote congelado.

Foram tentadas as 150 chamadas: 148 suítes geradas e duas falhas de geração (uma completa e uma com código). Dos 1.146 pares planejados, 1.130 tiveram relatórios de execução real no navegador; 16 são placeholders das duas falhas, sem execução. Os três controles de navegador passaram antes da geração.

A conferência validou 5.723 arquivos do recibo, inventário congelado, hashes dos scripts/adapter/runner/páginas/suítes, IDs e cobertura do schedule, papéis e vereditos contra relatórios reais. Tanto a análise principal quanto a análise de quietude e discriminação recalculadas coincidiram com a publicação. [Verificação](../../data/shared-omission-e2e/v1/verification.json), [manifesto público](../../data/shared-omission-e2e/v1/frozen-manifest-public.json) e [resultados completos](../../data/shared-omission-e2e/v1/results.json). Páginas, prompts e respostas brutas permanecem privados.

## Escores e comparações registradas

Uma detecção só conta quando a suíte é utilizável e fica quieta na referência correta. Suítes que rejeitam a referência ou são inutilizáveis têm escore zero. O escore principal mantém todas as suítes no denominador: média das duas suítes por requisito, depois peso igual por requisito.

| Fonte | Suítes | Elegíveis | Inutilizáveis | Escore médio por requisito | Detecções / pares previstos com mutante |
| --- | ---: | ---: | ---: | ---: | ---: |
| Requisito completo | 50 | 38 | 1 | 0,760 | 118/162 |
| Pedido incompleto | 50 | 39 | 0 | 0,100 | 13/162 |
| Pedido incompleto + código mutante | 50 | 19 | 1 | 0,040 | 6/162 |

| Comparação | Diferença média | IC 95% por bootstrap de projetos | p bilateral exato por projeto | Requisitos com diferença positiva / negativa / zero | Critérios registrados |
| --- | ---: | --- | ---: | --- | --- |
| MA1: completa − incompleta | 0,660 | [0,500; 0,800] | 0,0078125 | 20 / 0 / 5 | Satisfeitos neste estudo exploratório |
| MA2: completa − incompleta com código mutante | 0,720 | [0,587; 0,828] | 0,0078125 | 20 / 0 / 5 | Satisfeitos neste estudo exploratório |

O bootstrap usa 4.000 reamostragens por projeto. O teste inverte conjuntamente os sinais dos requisitos de cada projeto; 0,0078125 é o menor p bilateral possível com oito projetos. Os pares suíte/página e as repetições não são unidades independentes. As hipóteses de troca de sinais por projeto e a quantidade pequena de projetos permanecem limites da inferência.

## Discriminação e falsos alarmes

A tabela condicionada inclui somente suítes elegíveis, mantendo numeradores e denominadores por papel. É descritiva e não substitui o escore principal.

| Fonte | Alarmes em mutantes confirmados | Falsos alarmes nas outras A corretas | Falsos alarmes nas C recuperadas |
| --- | ---: | ---: | ---: |
| Completa | 118/118 (100%) | 6/98 (6,1%) | 3/30 (10,0%) |
| Incompleta | 13/123 (10,6%) | 0/104 (0%) | 1/29 (3,4%) |
| Incompleta + código mutante | 6/66 (9,1%) | 0/48 (0%) | 0/7 (0%) |

Entre as suítes que aceitam a referência correta, os braços incompletos quase não detectam as perdas conhecidas. A fonte completa discrimina melhor neste conjunto. O baixo escore do braço com código tem duas partes: muitas suítes rejeitam a referência correta e, entre as elegíveis, a detecção também é baixa. Não cabe atribuir tudo a omissão ou a sobreajuste sem examinar os testes.

Considerando todas as suítes, os alarmes nas outras A corretas foram 37/132 (28,0%) na fonte completa, 26/132 (19,7%) na incompleta e 74/132 (56,1%) com código mutante. Nas C recuperadas foram 7/34 (20,6%), 6/34 (17,6%) e 25/34 (73,5%). Essas taxas agregadas incluem suítes não elegíveis; os placeholders permanecem no denominador previsto e não produzem alarmes observados.

O protocolo aceita alarmes de asserção e de erro. Nos relatórios reais, a fonte completa teve 182 de asserção e 35 de erro; a incompleta, 25 e 55; com código mutante, 181 e 10. Isso não prova que toda detecção identifica especificamente a obrigação-alvo.

## Quietude sobre o mutante selecionado

Cada fonte tem 50 pares previstos sobre os 25 mutantes selecionados. Quietude significa que a suíte executou e passou numa página cujo defeito já era confirmado pelo oráculo; falhas de geração não contam como quietude.

| Fonte | Quietude observada / pares previstos | Quietude entre pares de suítes elegíveis |
| --- | ---: | ---: |
| Completa | 0/50 (uma geração falhou) | 0/38 |
| Incompleta | 39/50 | 35/39 |
| Incompleta + código mutante | 41/50 (uma geração falhou) | 17/19 |

Esses passes indevidos demonstram falsa segurança operacional no recorte avaliado: o teste passa apesar da perda confirmada. Não medem confiança subjetiva do agente/usuário, nem prevalência populacional. Não foram calculados intervalos independentes sobre os 50 pares, pois compartilham requisitos e projetos.

## Escores sem confirmação e limites

Com peso igual por requisito, tratar todas as C como mutantes produz 0,625 em vez de 0,760 na fonte completa, 0,090 em vez de 0,100 na incompleta e 0,045 em vez de 0,040 com código mutante. Com ponderação agregada por pares, os valores confirmado/ingênuo são 0,728/0,625, 0,080/0,090 e 0,037/0,045. As páginas recuperadas e não confirmadas alteram os denominadores e os alarmes contados; não se deve atribuir as diferenças somente à capacidade da suíte.

Os 25 requisitos foram selecionados a partir de resultados conhecidos por terem uma A correta e uma C com perda confirmada. A implementação veio de gerações anteriores e não foi randomizada novamente. O protocolo e os prompts dos novos testes foram congelados antes das chamadas, mas isso não transforma a seleção em confirmatória. Há um provedor, um modelo testador e duas suítes por fonte, além dos limites do scaffold e da referência única.

O contraste completo versus incompleto reapareceu numa nova geração de testes sobre as mesmas páginas; isso não constitui uma amostra independente de requisitos. O código defeituoso não supriu a condição omitida neste desenho. Comparar numericamente o braço com código correto do #180 ao braço com código mutante desta rodada mistura contextos e datas; não foi uma comparação contemporânea randomizada e não estabelece isoladamente o efeito causal de trocar o código.

A evidência é compatível com omissões compartilhadas entre a geração de implementação e testes, com os limites acima. H1 permanece exploratória, H2 não foi testada e a auditoria humana continua pendente. Agentes com ferramentas e outro provedor não foram executados.

## Reproduzir o placar

No [código congelado eec5110](https://github.com/danteacosta/agent-smell-degradation-harness/tree/eec5110c4353dc5da3c6dc29f36be23bd2b090e9), confira os hashes do manifesto e use os JSON públicos desta publicação:

```python
import json
from pathlib import Path
from scripts import shared_omission_e2e as study

root = Path('data/shared-omission-e2e/v1')
results = json.loads((root / 'results.json').read_text())
manifest = json.loads((root / 'frozen-manifest-public.json').read_text())
assert study.ma.analyse(results['rows']) == results['analysis']
assert study.analyse_selected(results['rows'], manifest) == results['selected_mutant_analysis']
```

O recálculo público reproduz as estatísticas, não substitui a custódia privada dos relatórios completos. Não rode novamente o coletor para reproduzir o placar.
