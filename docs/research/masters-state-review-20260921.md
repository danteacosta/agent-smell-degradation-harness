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
| StrictDoc SRS-110 | Exposição anterior comprovada; exportador histórico omite classificação sem UID/version; três controles e dois prints | Caso exposto; falha histórica de referência, sem efeito de LLM |
| StrictDoc SRS-163 | Fonte, três variantes propostas, rubrica, prompts e ensaio offline preparados | Sem coleta ou rótulos; escopo comando/campo não resolvido |

Fontes: [omissão e auditoria](masters-state-review-20260914.md),
[piloto de linguagem](codex-language-controls-results-20260914.md),
[piloto TodoMVC](../todomvc-exploratory-pilot.md),
[StrictDoc](2026-09-21-strictdoc-exposure-and-case-preparation.md).
Não somar essas contagens como uma única amostra independente.

## Avanço autônomo desta rodada

O [protocolo offline de critérios](2026-09-21-criteria-offline-protocol.md)
materializa nove posições propostas, com apenas uma variante por requisição,
ordem reproduzível e tabela administrativa inteiramente `not_attempted`.
As 54 células de cobertura ficam sem rótulo e sem evidência. Exercícios sintéticos
testam somente formato, erros e custódia; não alimentam resultados científicos.
O pacote preserva as fontes e os formulários anteriores e não contém um comando
de disparo. Não houve chamada nova de modelo nem consumo de chave API.

Foi corrigida a instrução operacional obsoleta que ainda mandava executar o
diagnóstico de fonte já encerrado. A coleção de 96 chamadas e seu gate falho
continuam preservados; nenhuma autorização histórica foi reutilizada.

## Próximas dependências reais

| Decisão ou ação | Material disponível | Dependência |
| --- | --- | --- |
| Mapear SRS-163 para a tarefa | Fonte e formulário separado | Resposta de revisor competente e independente |
| Avaliar reescrita/omissão | Três variantes e chave do custodiante | Revisão semântica da transformação |
| Resolver escopo e rubrica | Seis categorias e incerteza explícita | Adjudicação; não presumir oito obrigações |
| Dispor sobre direitos | Licença/NOTICE e revisão em branco | Decisão documentada de direitos/governança |
| Congelar protocolo de coleta | Molde, nove posições propostas e tabelas | Revisões acima e configuração/amostra finais |
| Executar e analisar | Rota Codex existente; contratos de erro e custódia preparados | Protocolo final e desfechos independentes |
| H1/H2 confirmatórias | Instrumentação, gates e formulários existentes | Amostragem, governança, anotação e análise registradas |

A configuração pretendida utiliza a assinatura ChatGPT via Codex, sem fallback
para chave. As coletas anteriores por API permanecem séries separadas. Ausência
de preço monetário exposto pelo CLI não significa custo zero.

Novas implementações devem ser guiadas por essas decisões. Mais chamadas,
checks de CI ou um juiz automático adicional não substituem validade semântica
nem tornam um caso exposto um teste independente.
