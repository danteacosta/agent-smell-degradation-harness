# Execução exploratória τ² por assinatura: preparação de 09/10

Dante confirmou a revisão das 32 regras, inversões e cinco reescritas e a
aprovação do desenho com Márcio. Escolheu `gpt-6-astra` para agente e usuário;
Claude fica adiado. O inventário foi marcado `frozen`, sem alterar trechos,
operadores, tarefas ou ordem sorteada. O estudo continua exploratório e não
registrado na OSF.

## Qualificação técnica, fora da análise

Cinco tarefas da política original completaram via CLI oficial Codex, com
avaliação upstream e sem retries, API ou computer use:

| Tarefa | Chamadas | Recompensa | Encerramento |
| --- | ---: | ---: | --- |
| 0 | 9 | 1,0 | user_stop |
| 8 | 15 | 0,0 | user_stop |
| 11 | 15 | 1,0 | user_stop |
| 12 | 12 | 1,0 | user_stop |
| 14 | 20 | 1,0 | user_stop |

São 71 chamadas. A tarefa 8 terminou com transferência e recompensa zero;
terminar tecnicamente não implica resolver a tarefa. Foram exercitadas consulta,
alteração de voo, bagagem, cancelamento e nova reserva. Isso qualifica estes
percursos, sem garantir sucesso em todas as 50 tarefas. Uma tentativa anterior
parou na inicialização local antes de qualquer chamada; foi preservada como
falha de preparação, sem reutilização de slot científico.

O tempo acumulado de transporte foi 474 segundos, média aproximada de 95 por
tarefa. As cinco tarefas foram escolhidas por percurso, não aleatoriamente.
Extrapolar esse valor para 3.650 simulações iniciais daria cerca de 96 horas de
transporte, antes de confirmações e esperas por quota. É uma referência de
escala, não uma previsão de conclusão. Não há estimativa monetária inventada.

## Contrato de análise corrigido

A versão `policy-suite-adequacy-analysis/v2` exige identidade explícita de
variante, tarefa e tentativa. Rejeita duplicatas, slots desconhecidos e
recompensas inválidas. As regras 3/4 para elegibilidade e 2/3 para confirmação
permanecem; a confirmação exige três recompensas válidas. Resultado ausente
permanece técnico e não confirma detecção. Uma confirmação sem tentativa inicial
é rejeitada. Candidatos incluem apenas confirmações ainda não tentadas depois de
uma falha inicial válida. Zero tarefas elegíveis produz `not_estimable`.

A análise e os transportes passaram em 92 testes focados no runtime fixado;
compilação dos arquivos alterados e `git diff --check` também passaram. A revisão
independente cobriu aceitação, cenários, filosofia de testes, SOLID, legibilidade
e segurança. Dois cenários adicionais sugeridos na revisão foram incorporados.

## Limites de execução

O CLI não expõe snapshot exato do modelo, não fixa temperatura nem semente de
amostragem e não aplica teto estrito de tokens. A identificação registrada é a
solicitada, não um snapshot verificado. A semente do simulador vem do plano.
O envelope de ferramentas é textual e permanece em `tau2-subscription-json/v2`.
A configuração é exploratória, sem elegibilidade confirmatória.

A consulta pública oficial `account/rateLimits/read`, documentada no
[App Server do Codex](https://learn.chatgpt.com/docs/app-server), funcionou sem
iniciar turno de modelo. A execução verifica a quota antes de cada chamada.
Apenas a janela semanal foi exposta nesta qualificação; saiu de 89% para 87%
restante. A conta é compartilhada, portanto essa diferença não é uma medida
isolada do custo do experimento. Janela ausente, desconhecida, antiga, esgotada
ou reserva de 30% atingida interrompe a execução. Créditos adicionais não são
orçamento autorizado nem fallback.

Cada simulação terá no máximo 40 chamadas e 120 segundos por chamada, como na
sondagem. Atingir esses limites é interrupção técnica, preservada sem retry.
Recibos, respostas, políticas e trajetórias permanecem privados, vinculados por
hash ao manifesto da execução. As tarefas técnicas não entram no plano científico.
A primeira coleta será A, quatro tentativas nas 50 tarefas. As etapas seguintes
continuam condicionadas ao término anterior e à quota disponível.

## Inferência e limitações preservadas

Os nomes históricos das classes medem sensibilidade da recompensa a uma variante;
não demonstram, sozinhos, uma violação da regra alvo. A inspeção humana das
trajetórias permanece necessária. R03 também aparece numa instrução externa do
upstream: retirar a passagem da política não remove essa outra instrução. O
inventário aprovado é mantido, e essa limitação deverá constar do relato.
As asserções NL continuam fora da avaliação upstream ativada; nenhum juiz extra
foi acrescentado. Esta execução não altera H1/H2 nem inicia coleta confirmatória.
