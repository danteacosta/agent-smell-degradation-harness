# Sonda de recuperação de regras — 2 de outubro de 2026

A coleta terminou: **69 candidatos, dois modelos e três respostas por candidato/modelo**, totalizando 138 pares e 414 respostas. A pergunta foi feita sem fornecer requisito, scaffold ou página. O objetivo foi medir se o modelo consegue recuperar a regra nesse contexto; não medir defeitos no código gerado.

| Modelo de geração | Recuperou a regra em pelo menos duas respostas | Não atingiu esse limiar | Inconclusivos |
|---|---:|---:|---:|
| `gpt-5.6-luna` | 22/69 | 47/69 | 0 |
| `gpt-5.6-sol` | 31/69 | 38/69 | 0 |

Em 17 candidatos os dois modelos atingiram o limiar; em 36 pelo menos um atingiu; em 33 nenhum atingiu. Esses denominadores são **candidatos**, não 69 obrigações independentes. Não atingir o limiar significa menos de duas respostas aceitas, não necessariamente desconhecer completamente a regra.

Cada resposta positiva precisou de dois julgamentos positivos: `gpt-6-astra` primeiro e `gpt-6-sol` somente após um primeiro “sim”. Um primeiro “não” encerrou a decisão. Os dois juízes acertaram os quatro controles de qualificação, totalizando oito chamadas. A coleta realizou **1.006 chamadas**: oito controles, 414 respostas e 584 julgamentos. Não houve falhas de chamada, julgamentos sem decisão ou pares ausentes. Os 244 segundos julgamentos não solicitados decorrem da rota condicional; não são dados faltantes.

A auditoria privada verificou **5.699 caminhos únicos por hash**. O [dataset público](../../data/memorization-probe-20261002/manifest.json) preserva [resultados](../../data/memorization-probe-20261002/results.json), [respostas como fornecidas aos juízes e julgamentos](../../data/memorization-probe-20261002/calls.json), [contabilidade](../../data/memorization-probe-20261002/accounting.json), [auditoria](../../data/memorization-probe-20261002/audit.json), [custódia](../../data/memorization-probe-20261002/custody.json) e [receipt público](../../data/memorization-probe-20261002/receipt.json). O [relatório por candidato/modelo](../../data/memorization-probe-20261002/report.md) permite examinar os casos individualmente.

O leitor pode recalcular a projeção sem acesso ao pacote privado:

```sh
python3 data/memorization-probe-20261002/verify.py --public data/memorization-probe-20261002
```

O verificador confere receipt, igualdade dos bytes públicos de `results.json` com o hash original registrado na custódia, prompts, identidade dos slots, rota dos julgamentos — incluindo respostas desconhecidas —, agregados e contagens. As respostas da sonda são publicadas como foram julgadas: `raw.strip()[:4000]`, com SHA e comprimentos do original. As capturas do CLI e os textos completos além desse limite permanecem privados. O verificador público testa consistência da projeção; não reconstrói os bytes privados truncados nem demonstra autenticidade externa apenas com um receipt fornecido junto dos dados. A exportação foi precedida de auditoria independente contra o pacote original e as fontes vinculadas.

## O que isso permite concluir

Existe recuperação da regra sem fornecer a referência, em parte dos candidatos e com diferenças entre modelos. Isso ajuda a investigar por que uma condição omitida pode reaparecer na implementação. **Não demonstra contaminação de pré-treinamento**: familiaridade, inferência e pistas na pergunta também podem explicar a resposta. Tampouco prova que uma condição não recuperada nesta sonda falhará no E2E.

Esta rodada não produziu novos E2Es e não confirma H1 ou H2. O rótulo congelado `memorized` foi preservado; sua interpretação operacional é recuperação sob esta pergunta e esta rota de julgamento. Os juízes são LLMs e os controles não substituem a auditoria humana prevista antes de uma afirmação confirmatória.

## Pendências antes da próxima geração

A [auditoria dos mappings da triagem](../../data/llm-screening-20261002/mapping-audit.json) mantém sete decisões pendentes: `rc-de652e658b99`, `rc-afa7beacea83`, `rc-4041140f2b5d`, `rc-6337ce108c4d`, `rc-e594b40135ff`, `rc-bd0b2995febc` e `rc-4da4940bc16c`. Esses mappings não foram corrigidos retrospectivamente para esta sonda.

Há também dois problemas de escopo da pergunta: Mealie `rc-60c42d4dd323` não fornece as quantidades concretas da regra numérica; Immich `rc-b6f382226c41` exige revisar se a pergunta e o predicado de caminho cobrem o mesmo escopo. Os resultados permanecem separados dessas decisões, sem reinterpretar uma resposta anterior como se uma pergunta revisada tivesse sido usada.

Os candidatos WeKan `rc-458cc4cba31a` e `rc-ebff8e70d1d7` contêm as mesmas quatro frases sobre o histórico na duplicação de quadros, adicionadas e depois removidas no mesmo arquivo. Precisam ser vinculados como a mesma obrigação antes de definir unidades independentes de análise.

A triagem admitiu candidatos em **sete projetos**. Aplicar o máximo de seis por projeto dá um teto de 36 candidatos, antes de resolver mappings e duplicações. O pré-registro exige pelo menos oito projetos e prevê outra rodada de triagem quando esse mínimo não é atingido. A seed `2026100203` está definida, mas a ordenação e o consumo do gerador aleatório da seleção final ainda precisam ser congelados; a prévia local não é uma seleção admitida. Nenhum caso deve ser trocado usando os resultados desta sonda como justificativa posterior.

O próximo passo é concluir mappings, direitos de uso das fontes e agrupamento de duplicações, congelar a seleção e a fronteira de informação, qualificar oráculos E2E independentes antes da geração e executar o desenho A/B/C previsto. Os dados da sonda ficam como covariável exploratória, preservando também resultados negativos.
