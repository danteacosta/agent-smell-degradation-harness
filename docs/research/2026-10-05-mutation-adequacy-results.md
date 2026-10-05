# Adequação por mutação: resultados exploratórios

Em 25 requisitos de oito projetos, as suítes escritas a partir da especificação completa detectaram mais perdas de regra que as escritas a partir do pedido incompleto. A diferença média foi de 78 pontos percentuais, com IC 95% por bootstrap de projetos de [66,7; 90,0] e p bilateral exato por projeto de 0,0078125. A comparação secundária com pedido incompleto mais código não satisfez a regra de decisão. Este estudo é exploratório; não confirma H1 nem testa H2.

## Coleta e integridade

O [pré-registro](../preregistration/2026-10-05-mutation-adequacy-preregistration.md) e as correções de custódia estavam em `cb02c80` antes da coleta. A execução única ocorreu em 05/10/2026, de 19:01:24 a 21:30:15 UTC, sem retry ou reparo. O testador foi `gpt-6-astra`, com dois testes gerados por fonte e requisito. As implementações vieram da coleta anterior de 46 requisitos: nenhuma implementação nova foi gerada.

Foram tentadas as 150 chamadas previstas: 149 produziram suítes e uma falhou na geração. Os três controles do runner passaram antes das chamadas. Dos 1.146 pares suíte/página planejados, 1.138 tiveram execução real e relatório de navegador; oito são registros de falha de geração, sem execução. Nenhum registro desses oito foi contado como teste bem-sucedido.

A conferência posterior validou o inventário de 5.756 arquivos do recibo, os hashes do pacote congelado, dos dois scripts, do runner, das suítes e das páginas. Também conferiu a cobertura exata do schedule, sem pares duplicados, e os vereditos contra os relatórios reais. A análise recalculada com o código congelado foi idêntica à publicada. [Verificação pública](../../data/mutation-adequacy/v1/verification.json), [manifesto público](../../data/mutation-adequacy/v1/frozen-manifest-public.json) e [resultados completos](../../data/mutation-adequacy/v1/results.json) preservam os números; respostas brutas, páginas e caminhos privados permanecem fora do repositório.

Os papéis das 191 páginas foram preservados: 81 mutantes confirmados pelo oráculo, 91 páginas A corretas, 17 páginas C recuperadas e duas C não confirmadas (falha mista e erro de navegador). As duas últimas entram somente na análise ingênua.

## Resultado por fonte

Um mutante só conta como detectado quando a suíte é utilizável e fica quieta na referência correta sorteada. Suítes inutilizáveis permanecem no denominador com escore zero. O escore principal dá peso igual a cada requisito após a média das suas duas suítes; não é a proporção agregada de execuções.

| Fonte da suíte | Suítes | Quietas na referência e utilizáveis | Inutilizáveis | Escore médio por requisito | Detecções confirmadas / pares com mutante |
| --- | ---: | ---: | ---: | ---: | ---: |
| Especificação completa | 50 | 43 | 0 | 0,840 | 137/162 |
| Pedido incompleto | 50 | 34 | 1 | 0,060 | 10/162 |
| Pedido incompleto + código correto | 50 | 37 | 0 | 0,665 | 100/162 |

A condição com código alcançou escore considerável: a previsão de que ambos os braços incompletos ficariam próximos de zero não se realizou. Estar quieta numa referência não garante que a suíte aceite outras implementações corretas.

## MA1 e MA2

| Comparação | Diferença média | IC 95% por projeto | p exato bilateral por projeto | Requisitos com diferença positiva / negativa / zero | Regra pré-definida |
| --- | ---: | --- | ---: | --- | --- |
| MA1: completa − incompleta | 0,780 | [0,667; 0,900] | 0,0078125 | 23 / 0 / 2 | Satisfeita neste estudo exploratório |
| MA2: completa − incompleta com código | 0,175 | [−0,032; 0,404] | 0,21875 | 9 / 3 / 13 | Não satisfeita |

A regra exige conjuntamente limite inferior acima de zero e p abaixo de 0,05. O bootstrap usa 4.000 reamostragens de projetos e o teste inverte conjuntamente os sinais dos requisitos de cada projeto. Com oito projetos, 0,0078125 é o menor p bilateral possível. A inferência depende das hipóteses de troca de sinais por projeto; as repetições e os testes em várias páginas não são unidades independentes.

## Falsos alarmes e tipos de alarme

As taxas abaixo são descritivas agregadas de pares suíte/página, incluindo suítes que falharam na referência. Não são estimativas independentes por execução. Na fonte incompleta, os placeholders de geração permanecem no denominador previsto; não geram alarmes observados.

| Fonte | Alarmes nas outras páginas A corretas | Alarmes nas C recuperadas |
| --- | ---: | ---: |
| Completa | 23/132 (17,4%) | 7/34 (20,6%) |
| Incompleta | 36/132 (27,3%) | 10/34 (29,4%) |
| Incompleta + código | 79/132 (59,8%) | 21/34 (61,8%) |

O braço com código teve mais alarmes sobre implementações que o oráculo classificou como corretas, limitando sua utilidade prática. A própria fonte completa também não foi livre de falsos alarmes.

Na execução real, a fonte completa teve 158 alarmes de asserção e 43 de erro; a incompleta, 36 e 58; a fonte com código, 217 e 25. Esses números incluem todos os papéis de página. O protocolo aceita ambos os tipos para uma detecção elegível; não se deve interpretar toda detecção como uma asserção que identificou especificamente a regra-alvo.

## Escore ingênuo versus confirmado

A análise ingênua trata todas as 100 páginas C como mutantes, inclusive as 17 recuperadas e as duas não confirmadas. A comparação abaixo usa a mesma ponderação por requisito em ambos os escores.

| Fonte | Confirmado, média por requisito | Ingênuo, média por requisito | Confirmado, proporção agregada | Ingênuo, proporção agregada |
| --- | ---: | ---: | ---: | ---: |
| Completa | 0,840 | 0,720 | 0,846 | 0,720 |
| Incompleta | 0,060 | 0,075 | 0,062 | 0,075 |
| Incompleta + código | 0,665 | 0,610 | 0,617 | 0,610 |

Ignorar a confirmação altera tanto o denominador quanto as páginas cujos alarmes contam. O escore ingênuo pode diminuir ou aumentar: na fonte incompleta ele aumentou. Portanto, um escore baixo sem oráculo não basta para culpar a suíte por deixar passar defeitos.

## Limites e próximo passo

Os 25 requisitos foram selecionados mecanicamente por terem ao menos uma A correta e uma C com perda confirmada, a partir de resultados já conhecidos. Isso restringe a conclusão a esse conjunto elegível. São oito projetos, um provedor e duas suítes por fonte; a quietude em uma única referência não estabelece validade geral da suíte. O cegamento do testador aos labels não elimina o conhecimento prévio dos autores.

A evidência sustenta MA1 neste desenho: fornecer a regra completa ao testador melhora a detecção das perdas já confirmadas. Não sustenta MA2 nem uma afirmação de que ler código necessariamente atrapalha. Antes de extrapolar, vale replicar com outro provedor e auditar asserções e alarmes em implementações corretas. A auditoria humana, a seleção confirmatória e as decisões de H1/H2 continuam pendentes e não foram aprovadas por esta execução.

## Recalcular sem chamadas

No commit da coleta, ou com os hashes dos scripts conferidos contra o manifesto, os resultados públicos bastam para recalcular a análise:

```python
import json
from pathlib import Path
from scripts.mutation_adequacy import analyse

results = json.loads(Path('data/mutation-adequacy/v1/results.json').read_text())
assert analyse(results['rows']) == results['analysis']
```

Isso reproduz a análise, mas não substitui a custódia privada das páginas, suítes e relatórios completos de navegador. Não execute o coletor novamente para reproduzir esta tabela.
