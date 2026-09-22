# Síntese das evidências empíricas

Esta síntese reúne séries distintas. Não combina suas contagens em uma única
amostra nem substitui o protocolo confirmatório. O exportador `dissertation_bundle`
continua sendo uma demonstração sintética separada.

## Pergunta e unidade de análise

A pesquisa investiga perda de obrigações originadas em requisitos e a possibilidade
de observá-la antes do artefato final. Geração de critérios de aceitação é a tarefa
principal; código executável fornece verificações comportamentais complementares.
Uma obrigação ausente no artefato é avaliada contra a intenção completa congelada.
Um modelo pode obedecer ao requisito abreviado e ainda omitir essa obrigação.

Repetições de geração, entradas de teste, categorias de cobertura e votos de juízes
não são novas intenções independentes. Generalização entre projetos exige mais
fontes e uma separação prospectiva de desenvolvimento e avaliação.

## Achados reproduzíveis

| Série | Observação | O que permite afirmar |
| --- | --- | --- |
| Políticas de omissão, 18 gerações | Desconto: 3/3 completos passaram, 3/3 com teto omitido falharam; acesso e token sem contraste | Uma perda comportamental sob intervenção construída; não efeito geral de smells |
| Auditoria posterior, mesmos 18 códigos | 1.638 verificações; 393 violações do teto | Extensão do diagnóstico dos artefatos existentes, sem aumentar a amostra |
| Linguagem, 24 gerações | 12/12 explícitos passaram; coordenação reescrita 2/4 atende à intenção; as 4/4 reescritas de pronome não atendem a nenhuma das duas políticas; controles equivalentes passam | Sensibilidade nestas políticas construídas, com dependência entre intenções gêmeas |
| TodoMVC, qualificação | Referência 28/28, mutante manual 27/28, somente Escape falha | Oráculo detecta um defeito manual; prints e vídeos documentam o comportamento |
| TodoMVC, nove gerações | Nove erros de infraestrutura originais; reexecuções dos mesmos códigos após correção passaram 28/28 | Resultado nulo da omissão neste contexto; falhas originais preservadas |
| TodoMVC, contexto pós-hoc | Corpo sem reset: 28/28 com guarda, 27/28 sem guarda; dois corpos com reset passam em ambos | Contexto compensa aquela implementação; o corpo também aparece em uma reescrita |
| StrictDoc SRS-163, critérios | Links: completo 3/3, reescrita 3/3, omissão 0/3; consenso de três LLMs nas 54 categorias | Contraste local de cobertura, com divergência de escopo e erros auxiliares do painel |
| StrictDoc SRS-110 | Exposição anterior; exportador histórico oculta classificação sem UID/versão | Caso de desenvolvimento e referência inadequada para o contrato proposto |

O resultado da coleta de critérios SRS-163 é registrado na
[síntese corrente](../research/masters-state-review-20260921.md), com protocolo
separado e os desfechos efetivamente observados. Os recibos privados vinculam
fontes, chamadas, respostas e resultados; nenhum artefato histórico é substituído.

## Resultados negativos fazem parte da contribuição

Os estudos auxiliares de avaliadores mostram que aderência ao formato e
localização de citações não bastam para validade semântica. As comparações que
falharam seus gates continuam encerradas com esse resultado. Um painel novo não
requalifica retroativamente seus rótulos.

O resultado nulo do TodoMVC limita a explicação de que basta omitir a condição
para induzir um defeito. O diagnóstico posterior oferece uma explicação local
plausível e executável: a guarda do scaffold preserva a propriedade. A falha
aparece também em um corpo produzido pela reescrita; não é exclusiva da omissão.

## Correções analíticas e limites

A precisão média agora agrupa empates por limiar. O escore constante da
demonstração sintética com prevalência 0,5 produz AP 0,5, não 1,0. Isso corrige
um instrumento, sem produzir novo resultado empírico. Alpha de Krippendorff
agora trata corretamente marginais pareáveis, pesos por unidade e distância
ordinal; estimativas indefinidas não recebem confiabilidade perfeita.

Consenso automatizado é anotação exploratória, com votos preservados e
incerteza explícita. Concordância entre modelos do mesmo provedor não equivale
a validade contra especialistas. Não há resultado confirmatório de H1 ou H2,
e não foi demonstrado benefício empírico de alerta precoce ou utilidade para
usuários. Essas perguntas exigem observações prospectivas e desfechos adequados.

## Fontes internas e reprodução

- [Piloto de omissão](../research/codex-original-demo-results-20260914.md)
- [Auditoria dos mesmos códigos](../research/codex-original-demo-posthoc-audit-20260914.md)
- [Linguagem e controles](../research/codex-language-controls-results-20260914.md)
- [Piloto TodoMVC](../todomvc-exploratory-pilot.md)
- [Diagnóstico de contexto](../research/todomvc-context-diagnostic-20260921.md)
- [Triagem StrictDoc](../research/2026-09-21-strictdoc-exposure-and-case-preparation.md)
- [Correção de AP](../research/2026-09-21-ranking-metric-correction.md)
- [Correção de IRR](../research/2026-09-21-irr-correction.md)
- [Limites do consenso](../research/2026-09-21-llm-consensus-boundary.md)

- [Resultado do consenso SRS-163](../research/criteria-consensus-results-20260921.md)

## Ampliação exploratória: 12 requisitos, quatro projetos

A coleta executou 216 gerações (212 válidas, quatro inválidas) e 565 julgamentos
(539 válidos, 22 inválidos, quatro timeouts); 83 dos 648 julgamentos planejados
não foram realizados. A regra congelada encerrou a coleta sem repetição.
Os limites de perda de cobertura da obrigação omitida, C−A, são [−100; −16,67]
pontos percentuais no Luna e [−100; −25] no Sol, incorporando os desfechos
inconclusivos. São limites de ausência de informação condicionados à validade
dos rótulos do painel, não intervalos de confiança. B−A inclui zero nos dois
modelos e não comprova equivalência. Em C, há 47 ausências confirmadas e 25
alvos inconclusivos; nenhuma recuperação confirmada.

O resultado sustenta propagação de omissão em critérios neste corpus e protocolo.
Não comprova defeito executável novo, efeito geral dos smells ou H1/H2.
Consenso de LLMs, sem validação humana; a coleta anterior permanece separada.
[Resultados, proveniência e limitações](../research/criteria-expansion-results-20260921.md).
