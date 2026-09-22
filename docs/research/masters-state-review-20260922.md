# Estado do mestrado — piloto de foco e qualidade dos instrumentos

Há agora uma evidência comportamental local de propagação da omissão textual:
na rota direta, retirar a obrigação de foco produziu 6/6 falhas, enquanto completos
e reescritos passaram. Pela rota de critérios salvos, 10/12 omissões falharam e
duas preservaram foco. Os 52 códigos foram gerados antes dos testes; duas posições
sem critério válido continuam ausentes no denominador 54. Todas as demais
verificações passaram. O par de prints foi escolhido antes da coleta.

[Resultados, limites e prints](focus-chain-results-20260922.md) preservam os seis
estratos de configuração, os hashes, as ausências e os casos sem defeito. O caso
é um requisito TodoMVC já exposto, escolhido por viabilidade. Não confirma H1/H2
nem um efeito geral dos smells; também não é uma estimativa de mediação causal.
A limitação do teste auxiliar de lista vazia foi registrada, sem alterar o pacote.

[Correções de infraestrutura e medição](research-stack-audit-20260922.md) foram
integradas após CI: ARP 20, MergeWave 24 e RAG 16. O RAG tem contrato de métricas
versionado e baseline novo, com artefatos históricos preservados. A proposta e
o relatório do Drive distinguem checkpoints antigos do estado atual.

O avanço seguinte exige seleção prospectiva de novos requisitos/projetos e
oráculos derivados de cada fonte, com controles que também cubram implementações
corretas alternativas. Para H2, manter a comparação B3 versus B0 antes do artefato
final e a avaliação independente por projeto. Consenso automatizado não substitui
validação humana nem autoriza chamar este piloto de estudo confirmatório.

Integração desta etapa: [PR 67](https://github.com/danteacosta/agent-smell-degradation-harness/pull/67), condicionada ao CI do commit final.
