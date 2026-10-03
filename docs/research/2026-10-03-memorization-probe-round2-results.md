# Sonda de recuperação — rodada 2, 3 de outubro de 2026

A sonda dos 30 elegíveis de Zulip e Grist terminou: 180 respostas, três por regra e modelo. O critério congelado exige pelo menos duas respostas aceitas pelos dois juízes. Luna recuperou 8 de 30 regras e Sol recuperou 9 de 30. Nos demais pares, a regra não foi recuperada pelo critério; não houve casos inconclusivos, falhas de chamada ou julgamentos sem decisão.

| Modelo | Recuperou | Não recuperou | Inconclusivo |
| --- | ---: | ---: | ---: |
| gpt-5.6-luna | 8 | 22 | 0 |
| gpt-5.6-sol | 9 | 21 | 0 |

Os juízes gpt-6-astra e gpt-6-sol acertaram os oito controles previstos. Foram 414 chamadas: 180 respostas, 226 julgamentos e oito controles. O segundo juiz só é chamado após um “sim” do primeiro; 134 chamadas de segundo julgamento não estavam previstas nessa rota. Nenhuma chamada agendada ficou ausente e não houve retry ou reparo.

A auditoria independente do executor recalculou os 60 pares regra/modelo, conferiu o vínculo com a triagem e o executor congelados e verificou 2.342 caminhos de evidência por hash, contando arquivos aninhados uma vez. A projeção pública preserva exatamente os bytes de results.json e os rótulos originais. Publica a resposta como fornecida ao juiz (`raw.strip()[:4000]`), seu hash e comprimentos originais, mas não os captures privados do CLI nem os bytes completos truncados. Nenhuma resposta deste lote excedeu 4.000 caracteres. O verificador público confere a consistência dessa projeção; os hashes desses bytes privados são referências de custódia, não reconstrução pública independente.

Recuperar a regra sem receber requisito, scaffold ou página pode refletir familiaridade, inferência ou pistas da pergunta. Não prova contaminação de pré-treinamento, nem mede defeito E2E, nem confirma H1 ou H2. São 30 regras dos mesmos dois projetos, não 60 requisitos independentes. A primeira sonda (69 regras de sete projetos) continua separada; a mudança de contagens entre lotes não estima mudança de desempenho no mesmo corpus.

A [revisão dos mappings](2026-10-03-screening-round2-mapping-review.md) foi registrada antes de terminar a sonda e sem consultar seus outcomes. Ela sinaliza 15 candidatos, incluindo sete apoiados apenas em texto removido. Estes números da sonda não aprovam mappings nem autorizam selecionar casos pelo seu efeito. A seleção, o tratamento de remoções e duplicações e a definição do braço A continuam pendentes; qualquer mudança de regra exige compatibilizar a sonda da regra original com a nova definição.

## Reprodução pública

```sh
python3 data/memorization-probe-round2-20261003/verify.py --public data/memorization-probe-round2-20261003
```

[Pacote público](../../data/memorization-probe-round2-20261003/report.md) · [Auditoria por regra](../../data/memorization-probe-round2-20261003/audit.json) · [Contabilidade](../../data/memorization-probe-round2-20261003/accounting.json) · [Recibo](../../data/memorization-probe-round2-20261003/receipt.json).
