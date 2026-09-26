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


## Source/criteria-to-browser successor

The [frozen focus pilot](../research/focus-chain-results-20260922.md) adds one
retrospectively selected TodoMVC intent, not new project diversity. All52 eligible
code generations completed before browser feedback; two of54 planned positions
remain missing from an invalid upstream criterion. Direct-source omissions failed
focus6/6 versus0/6 complete and0/6 rewrite. Criteria-route omissions failed10/12;
two preserved focus. Complete criteria produced0 failures in10 executable outputs
(two missing of12 planned), and rewrite0/12. Every executable output passed the
six non-target assertions; all16 failures were selective initial-focus failures.
Nine authored controls qualified the instrument beforehand. A post-freeze review
identified an overstrict empty-list placement proxy; it did not fail in this
collection and is not used as the primary endpoint. Original scores stay frozen.
The preselected screenshot pair and externally observed active elements support
the local counterexample. Repetition does not create independent requirements;
route differences are not causal mediation and H1/H2 remain unconfirmed.

## Evidência E2E em seis projetos

A [matriz de evidências](../thesis/e2e-evidence-matrix-20260925.md) reúne
pilotos exploratórios separados de TodoMVC, RealWorld, Kanboard, Paperless-ngx,
Nextcloud e OpenProject. No sucessor de scaffold fixo em três projetos, houve
54 chamadas, 53 saídas executáveis e 11 falhas seletivas em C; todas as 17
saídas A avaliáveis e todas as 18 saídas B passaram. Esses totais pertencem
somente àquele sucessor, não a uma amostra combinada dos seis projetos.

Em 26 de setembro, um [segundo requisito do OpenProject](../research/openproject-remaining-pilot-20260926.md)
foi testado: 18/18 saídas avaliáveis, A e B com 3/3 acertos por modelo, C com
3/3 falhas seletivas por modelo. A obrigação omitida era derivar Remaining work
ao informar % Complete com Work já preenchido. Portanto, o piloto acrescenta
**diversidade de obrigações dentro de um projeto existente**, não um sétimo
projeto. A auditoria posterior de rótulos por LLM registrou discordâncias e
não substitui o oráculo de navegador nem validação humana.

Um [segundo requisito do Kanboard](../research/kanboard-duplicate-title-qualification-20260926.md)
foi testado na ação de duplicar uma tarefa, desta vez verificando se a cópia
mantém o título visível. As 18 gerações foram admitidas. No navegador
congelado, sete passaram, duas falharam apenas no título sob C e nove ficaram
sem avaliação porque os códigos usaram `crypto.randomUUID()`, indisponível na
origem da página de teste. Uma reavaliação diagnóstica **posterior ao
resultado**, com os mesmos artefatos e uma origem segura qualificada, obteve
16 acertos e as mesmas duas falhas em C, ambas no modelo Luna; Sol preservou
o título em C nas três repetições. Esse diagnóstico explica os casos
desconhecidos, mas não substitui o desfecho congelado. O total continua em
seis projetos; Kanboard e OpenProject agora têm duas obrigações distintas
cada um.

Uma [replicação nova e previamente congelada](../research/kanboard-duplicate-title-qualification-20260926.md#nova-replicação-prospectiva-com-origem-segura)
da mesma obrigação Kanboard executou outras 18 gerações e 18 avaliações E2E
com a origem segura qualificada antes da geração. Não houve caso desconhecido:
A e B passaram 6/6 cada; C passou 4/6 e falhou seletivamente 2/6. As duas
falhas ocorreram em Luna, com título da cópia alterado por um sufixo; Sol
recuperou o título em C nas três repetições. É uma replicação limpa do efeito
local e da heterogeneidade entre modelos, não nova diversidade de requisitos.

Uma [nova obrigação Paperless-ngx](../research/paperless-duplicate-consumption-20260926.md)
testou a aceitação padrão de uma cópia com o mesmo checksum. O primeiro lote
de 18 gerações revelou um desencaixe entre o arquivo entregue ao código e a
API do scaffold; nenhum caso passou, e esse lote permanece como falha de
instrumento. Após corrigir a interface, requalificar nove controles e
congelar outro lote antes de gerar código, houve **18/18 E2Es avaliáveis**.
A e B passaram 6/6 cada; C falhou apenas no alvo em 4/6 e passou em 2/6.
Luna concentrou três falhas C; Sol recuperou a obrigação em duas de três C.
Isto acrescenta diversidade de obrigações dentro dos seis projetos já
representados, sem estimar efeito populacional nem confirmar H1/H2.

Uma [nova obrigação RealWorld](../research/realworld-favorites-20260926.md)
testou a lista de artigos favoritados no perfil. O primeiro lote de 18
gerações expôs um contrato de dados incompleto no scaffold e permanece como
falha de instrumento, sem contraste causal. Um sucessor, com formato de dados
comum declarado, passou oito controles de navegador e três revisões LLM
antes do congelamento. Nas 18 novas gerações, **A, B e C passaram 6/6 cada**,
sem casos não avaliáveis. O contraste observado de falha-alvo C−A foi zero:
os modelos recuperaram a seleção de favoritos usando a rota e os campos do
scaffold, mesmo quando C omitiu a regra. Este resultado sem efeito observado
deve permanecer ao lado dos efeitos Paperless, OpenProject e Kanboard; não
prova equivalência nem confirma H1/H2. Agora são quatro obrigações novas
executadas no bloco planejado, restando sete.

A [ponte de persistência TodoMVC](../research/todomvc-persistence-bridge-20260926.md)
foi replicada prospectivamente com o seletor qualificado: 18 novas gerações,
17 saídas E2E avaliáveis, A e B com 6/6 passes cada, C com 5/6 passes e um
erro de interface. Não houve falha-alvo observada. O erro não é contado como
sucesso ou defeito. Essa replicação não acrescenta obrigação nova e não altera
as contagens dos pilotos anteriores.

Os experimentos demonstram que a omissão pode produzir defeito visível em
contextos distintos, mas há recuperações da informação omitida e diferenças
entre modelos. A seleção foi intencional, os scaffolds e datas diferem e as
repetições são aninhadas em requisitos. Não se estima efeito populacional.
O desfecho E2E é falha comportamental; H1 usa severidade ordinal adjudicada,
e H2 exige sinais anteriores ao código final em projetos de avaliação
separados. Nenhuma das duas hipóteses está confirmada.

## Auditoria ordinal secundária de H1

Uma [auditoria dos critérios já gerados](../research/h1-existing-criteria-ordinal-audit-20260926.md)
avaliou 48 posições predefinidas da coleta de 12 intenções e quatro projetos;
duas tinham geração inválida. Dois modelos julgaram as 46 saídas válidas com
uma rubrica ordinal preexistente, sem receber condição ou gerador. As 92
respostas tiveram formato válido, mas só 29 artefatos atenderam simultaneamente
ao consenso exato de severidade e estados das obrigações e à exigência de
citações literais. Nove das 24 comparações A–C ficaram completas. O contraste
A−C nessas nove foi −2 em oito e zero em uma; considerando todas as 24 e
mantendo os rótulos ausentes como 0–3, os limites são [−2,25; +0,125].
Portanto, o sinal exploratório é compatível com degradação, **mas não exclui
efeito nulo**. Julgadores do mesmo provedor, ausência de adjudicação humana,
quatro projetos intencionais e seleção de uma repetição impedem tratá-lo como
teste confirmatório de H1.
