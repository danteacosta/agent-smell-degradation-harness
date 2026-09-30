# Auditoria de smells nos dez requisitos históricos

## Critério

Uma mudança de requisito não é automaticamente um *requirement smell*. Para vincular um caso à literatura, exigimos um tipo nomeado e definido em fonte primária, um trecho específico do texto antigo que corresponda à definição e uma referência contemporânea para a obrigação. A confirmação no corpus ainda requer classificação independente, cega aos resultados E2E, e uma decisão explícita sobre aplicar taxonomias de casos de uso a documentação de produto. A distinção entre indício e defeito segue [Femmer et al.](https://arxiv.org/html/1611.08847).

**Estado: 6 candidatos vinculados a tipos publicados; 4 mudanças sem smell demonstrado; 0 smells confirmados por adjudicação independente.** Os 60 pares E2E originais continuam 11 melhoras, 44 empates e 5 desconhecidos, mas isso não é uma contagem de efeitos de smells validados.

## Candidatos vinculados à literatura

| Mudança e trecho antigo | Tipo publicado e localização do indício | Condição pendente | E2E original |
| --- | --- | --- | --- |
| [Nextcloud restore](https://github.com/nextcloud/documentation/commit/f9dff2cff30abeb81ad52fd1010023e5077f34e2): instrução de restaurar sem dizer o que ocorre se já há item com mesmo nome no destino. | **Incomplete System Behavior**, [Seki et al., apêndice, p. 17](https://arxiv.org/pdf/2009.01542): comportamento necessário não descrito. A lacuna proposta é o ramo de colisão na instrução de restauração. | Confirmar regra de nome e destino na revisão antiga; julgar se a taxonomia de caso de uso se transfere à documentação. | 2 melhoras, 4 empates. |
| [Kanboard subtarefa](https://github.com/kanboard/documentation/commit/85632cdaf1ff362bb9d4999628d0ad40422c923e): `has 3 different statuses`, depois `has 1 of 3 different statuses`. | **Omitted Word**, [Seki et al., apêndice, p. 13](https://arxiv.org/pdf/2009.01542): palavra omitida retira informação necessária e pode gerar ambiguidade. `1 of` explicita exclusividade. | Leitores independentes devem confirmar que o antigo realmente permitia estados simultâneos, em vez de mera concisão. | 1 melhora, 5 empates. |
| [Nextcloud retenção](https://github.com/nextcloud/documentation/commit/8b687e504b3f4360d15b3cd2c440c064fa1655e6): regra antiga de lixeira sem exceção da política administrativa. | **Incomplete System Behavior**, [Seki et al., p. 17](https://arxiv.org/pdf/2009.01542), se a exceção já integrava o comportamento exigido. O alvo é a regra de retenção. | Verificar configuração anterior; separar a nova frase do link administrativo que o braço novo também consultou. As duas páginas são um tratamento. | 3 melhoras, 1 empate, 2 desconhecidos. |
| [Paperless PDF original](https://github.com/paperless-ngx/paperless-ngx/commit/278ef3a364c4b8c0c914160756bfee1a6986e662): `never overwrite that document`. | **Negative Statements**, [Femmer et al., §3.2](https://arxiv.org/html/1611.08847): declaração de capacidade que o sistema não fornece. `never overwrite` é o indício localizado. | Julgar se a frase descreve a proibição no sentido do artigo e se a exceção valia na revisão antiga. A negativa não prova defeito sozinha. | 6 empates. |
| [Paperless barcode](https://github.com/paperless-ngx/paperless-ngx/commit/095ea3cbd3f8e1832f0247dd0a9f4d94a1929c51): instrução antiga de descartar a página separadora sem o ramo `retain`. | **Incomplete System Behavior**, [Seki et al., p. 17](https://arxiv.org/pdf/2009.01542), se a opção já era comportamento exigido. A lacuna está na instrução de divisão. | Verificar opção e semântica na revisão antiga; distinguir informação necessária de detalhe editorial. | 6 empates. |
| [Paperless novo usuário](https://github.com/paperless-ngx/paperless-ngx/commit/637efd5cb31cc26d2890079af5421dd14dbc3977): criação sem informar permissões iniciais e herança de grupo. | **Incomplete System Behavior**, [Seki et al., p. 17](https://arxiv.org/pdf/2009.01542), condicionado a esse default já ser obrigatório. O alvo é a instrução de criação. | Verificar política na revisão antiga; isolar o default do ajuste `UISettings View` do mesmo commit. | 6 empates. |

O tipo *Incomplete System Behavior* não tem um detector automático definido naquele artigo. Citá-lo não significa que um detector T0 possa encontrar uma ausência apenas no texto antigo; isso exige uma referência independente disponível naquele momento.

## Mudanças sem smell demonstrado

| Mudança | Razão para não rotular | E2E original |
| --- | --- | --- |
| [OpenProject progresso](https://github.com/opf/openproject/commit/603fdc4b97efe99bbaf1269f681735ac221e6b1a): `Work = Remaining` dava `100%`, corrigido para `0%`. | Valor factual incorreto. **Contradicted Sentences** de [Seki et al.](https://arxiv.org/pdf/2009.01542) exigiria localizar duas sentenças contraditórias no material antigo; o diff não demonstra isso. | 5 melhoras, 1 desconhecido. |
| [Kanboard busca](https://github.com/kanboard/documentation/commit/0f609e4909b9763b49d5b4316f081200b9b313ac): `assigne:me` para `assignee:me`. | Erro de exemplo executável, sem tipo publicado encontrado que corresponda precisamente ao typo. | 4 empates, 2 desconhecidos. |
| [Nextcloud transferência](https://github.com/nextcloud/documentation/commit/cb686c01fd73112e8baad6dee2f6f0706e255a46): `sharing ownerships` para `sharing settings and permissions ... to the new owner`. | Formulação imprecisa, mas não foi demonstrado referente ambíguo específico ou obrigação ausente segundo tipo nomeado. | 6 empates. |
| [Paperless perfil](https://github.com/paperless-ngx/paperless-ngx/commit/1ba6c31385b078e26b7e8fff1b0eaaec8487c411): `Users` passa a excluir explicitamente `My Profile`. | Delimitação de escopo possível, sem dois sentidos sustentáveis ou tipo publicado demonstrado. | 6 empates. |

Das 11 melhoras, **6 pares** vêm de três requisitos candidatos a smell publicado (restore, subtarefa, retenção) e **5 pares** do OpenProject sem smell demonstrado. Os seis pares são repetições aninhadas em três requisitos, não seis unidades independentes. Isso ainda não estima um efeito geral para H1 nem valida um detector H2.

## Fontes

- [Femmer et al., *Rapid Quality Assurance with Requirements Smells*](https://arxiv.org/html/1611.08847), artigo primário, 2016, consultado em 2026-09-30: define smell como indício localizado, sujeito a julgamento contextual, e cataloga *Negative Statements*.
- [Seki, Hayashi e Saeki, *Detecting Bad Smells in Use Case Descriptions*](https://arxiv.org/pdf/2009.01542), artigo primário, 2019, consultado em 2026-09-30: define *Omitted Word*, *Incomplete System Behavior* e *Contradicted Sentences*. O alvo original é descrição de casos de uso, não documentação de produto.
- [Veizaga, Shin e Briand, *Automated Smell Detection and Recommendation in Natural Language Requirements*](https://arxiv.org/html/2305.07097v2), artigo primário, 2023, consultado em 2026-09-30: *Incomplete condition* requer uma condição escrita sem ator ou verbo, portanto não rotula qualquer ramo inteiro ausente.

## Próximo passo de validação

Congelar as definições e entregar texto antigo mais referência contemporânea a avaliadores independentes, sem diff posterior ou resultado E2E. Registrar concordância, dissenso e exclusões antes de selecionar o subconjunto de H1. Para H2, avaliar o detector somente com informação disponível em T0 ou T1-T3.

## Downstream uses

- Corrige a classificação exploratória dos dez requisitos sem alterar os [resultados E2E](2026-09-30-natural-e2e-closure.md).
