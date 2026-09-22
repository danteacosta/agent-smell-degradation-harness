# Estado do mestrado — 21/09/2026

O instrumento produz artefatos, executa contratos e preserva evidências.
Existem exemplos de perda de obrigação em políticas construídas, mas ainda não
uma estimativa validada do efeito de categorias de smells em requisitos naturais.
A tarefa principal continua sendo geração de critérios de aceitação; código
executável é uma extensão comportamental.

## Evidências que podem ser apresentadas

| Frente | Evidência disponível | Limite da conclusão |
| --- | --- | --- |
| Omissão em políticas construídas | 18 gerações; teto de desconto perdido nas três versões com omissão; acesso e token sem contraste | Uma intervenção construída, não três categorias validadas |
| Reexecução de robustez | 1.638 verificações dos mesmos 18 códigos | Diagnóstico pós-hoc; não aumenta a amostra de intenções |
| Ambiguidade e reescrita | 24 episódios; textos explícitos 12/12; coordenação e pronome apresentam divergências; controles equivalentes preservados | Grupos dependentes; alternativas ainda sujeitas a revisão |
| TodoMVC: mutante manual | Referência 28/28; mutante 27/28, apenas Escape falha, com prints e vídeos | Sensibilidade do oráculo à mutação manual |
| TodoMVC: geração real | Nove gerações; após corrigir Acorn, nove reexecuções passaram 28/28 | Resultado nulo; nove erros originais de infraestrutura preservados |
| TodoMVC: diagnóstico de contexto | Três corpos salvos × dois scaffolds; o corpo sem reset passa com guard e falha apenas Escape sem guard | Pós-hoc; mesmo corpo em três omissões e uma reescrita, mas só um representante executado por contexto |
| StrictDoc SRS-110 | Exposição anterior comprovada; exportador histórico omite classificação sem UID/version; três controles e dois prints | Caso exposto; falha histórica de referência, sem efeito de LLM |
| StrictDoc SRS-163 | Nove critérios gerados e 27 julgamentos; links preservados em 3/3 completos, 3/3 reescritas e 0/3 omissões; 54 categorias unânimes | Uma intenção; divergência de escopo em 8/9 artefatos e dois erros auxiliares dos juízes; sem validação humana |

Fontes: [omissão e auditoria](masters-state-review-20260914.md),
[piloto de linguagem](codex-language-controls-results-20260914.md),
[piloto TodoMVC](../todomvc-exploratory-pilot.md),
[diagnóstico de contexto](todomvc-context-diagnostic-20260921.md),
[StrictDoc](2026-09-21-strictdoc-exposure-and-case-preparation.md).
Não somar essas contagens como uma única amostra independente.

## Avanço autônomo desta rodada

O [painel de critérios](criteria-consensus-results-20260921.md) terminou com
39 chamadas pela assinatura Codex, sem chave API: três calibrações, nove
artifatos e 27 julgamentos. Três modelos passaram pelos oito controles antes
da geração. O consenso foi unânime nas 54 células de cobertura: somente links
ficou ausente nas três respostas com essa obrigação removida. As outras cinco
categorias foram preservadas nos três braços.

A revisão independente conferiu os 258 arquivos do recibo, os 39 eventos de
uso e as 153 citações de suporte. Também identificou limites do painel:
divergência de escopo em oito artefatos e duas anotações auxiliares que chamam
links ausentes de acréscimos. Esses erros permanecem registrados. Não houve
reparo de votos, repetição de chamadas ou promoção a rótulo humano.

O protocolo offline anterior continua preservado como preparação histórica.
O sucessor tem autorização exploratória própria; a coleção de 96 chamadas
com gate falho continua encerrada. A [síntese empírica](../dissertation/EMPIRICAL_SYNTHESIS.md)
reúne estudos reais, resultados nulos e diagnósticos, separadamente do exportador
sintético. As correções de AP/IRR e validação já foram integradas nos três
repositórios após CI (harness #64, ARP #19 e RAG #15).

## O que está concluído e o que permanece aberto

| Frente | Estado atual | Limite ou dependência |
| --- | --- | --- |
| Piloto exploratório SRS-163 | Coleta, consenso fixo e reanálise concluídos | Uma intenção; labels de LLM, não validação humana |
| Mapeamento e transformação | Fonte pública verificada; três variantes congeladas e revisão técnica | Equivalência semântica independente ainda não certificada |
| Rubrica e escopo | Cobertura coletiva de seis categorias analisada | Fonte não resolve distribuição por comando; painel também diverge |
| Reprodução e integração | Código, testes, hashes, votos e capturas preservados | Aliases dos modelos não expõem snapshots imutáveis |
| Revisão humana e governança | Formulários preservados sem assinaturas fabricadas | Decisões de revisores, orientador e instituição quando aplicáveis |
| Validade externa e H1/H2 | Instrumentação e protocolos existentes | Novas fontes, separação por projeto, observações prospectivas e análise registrada |

A autorização de consenso automatizado encerrou a dependência operacional de
rótulos humanos para este piloto exploratório. Ela não modifica os requisitos
do estudo confirmatório nem demonstra benefício de alerta precoce ou utilidade
para usuários. Novas coletas devem usar seleção prospectiva de fontes e manter
candidatos rejeitados, sem escolher casos por produzir um efeito favorável.

A coleta usou ChatGPT via Codex, sem fallback para chave. Foram reportados
550.566 tokens de entrada e 14.698 de saída; preço monetário e snapshots de
resposta não estão disponíveis. As séries anteriores de API ficam separadas.

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
[Resultados, proveniência e limitações](criteria-expansion-results-20260921.md).
