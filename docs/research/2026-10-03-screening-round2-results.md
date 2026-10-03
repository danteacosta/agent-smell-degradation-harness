# Rodada 2: candidatos elegíveis em nove projetos

A extensão da triagem terminou em 3 de outubro de 2026. Dos 60 candidatos de Zulip e Grist, **30 foram considerados elegíveis e 30 excluídos**, sem decisões não resolvidas. A rodada anterior tinha 69 elegíveis em sete projetos; juntas, as rodadas têm **99 candidatos elegíveis em nove projetos**. Isso remove o déficit de projetos da triagem, mas não constitui a seleção final nem confirma que os candidatos sejam requirement smells.

| Projeto novo | Avaliados | Elegíveis | Excluídos |
|---|---:|---:|---:|
| Zulip | 30 | 19 | 11 |
| Grist | 30 | 11 | 19 |

## Como o painel decidiu

Os modelos `gpt-6-astra` e `gpt-6-sol` deram os votos primários; `gpt-6-luna` resolveu divergências. Cada modelo acertou seis controles autorados, totalizando **18/18 decisões corretas** antes dos candidatos. Houve 53 acordos e sete desempates. O kappa dos votos primários foi **0,7661469933184855**, calculado sobre 60 pares com dois votos válidos.

Foram **145 chamadas**: 18 controles, 120 votos primários e sete desempates. Não houve falhas, votos inválidos ou retries. O painel recebeu projeto, arquivo e frases alteradas; não recebeu a sugestão do assistente nem resultados de experimentos anteriores. Uma mudança histórica e uma admissão do painel não substituem o vínculo à literatura de smells nem a validação da obrigação.

## Dados e custódia

Os [resultados públicos](../../data/llm-screening-round2-20261003/results.json) mantêm exatamente os bytes dos resultados privados. A [auditoria](../../data/llm-screening-round2-20261003/audit.json) recalculou os totais e as rotas sem divergências. Foram verificados **941 caminhos privados por hash**; o inventário inclui os 67 arquivos do pacote congelado, que não devem ser somados novamente. A [custódia](../../data/llm-screening-round2-20261003/custody.json) vincula os receipts e resultados originais. O [receipt público](../../data/llm-screening-round2-20261003/receipt.json) cobre a projeção publicada.

Capturas do CLI, streams brutos e caminho do executável permanecem privados. Hashes fornecidos junto dos dados permitem conferir consistência; por si só, não demonstram autenticidade externa. Os nomes dos modelos são os solicitados ao provedor, sem verificação independente do snapshot interno.

## O que ainda falta

Os 30 elegíveis têm redações diferentes de regra-alvo entre votos favoráveis. Isso não significa 30 conflitos semânticos: paráfrases devem ser separadas de diferenças de condição e escopo antes do congelamento dos casos.

As decisões do [procedimento de seleção](2026-10-02-selection-procedure.md) permanecem propostas. Ainda faltam aprovação dos mappings, tratamento das remoções, revisão de duplicações entre as duas rodadas e a seleção congelada, uma única vez, com teto de seis requisitos por projeto. Nenhuma lista sorteada foi consultada nesta coleta.

A sonda dos novos elegíveis é um pacote separado. Ela mede recuperação da regra sem fornecer o requisito; não é um E2E. Cada caso finalmente selecionado ainda requer fonte e licença verificáveis, fixture, oráculo independente, qualificação de navegação e escopo e congelamento anterior à geração A/B/C. Esta triagem não confirma H1 ou H2. A auditoria humana prevista continua necessária antes de qualquer afirmação confirmatória.
