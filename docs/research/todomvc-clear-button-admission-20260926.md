# TodoMVC Clear completed: instrumento adiado

A [especificação fixada](../../data/criteria-expansion/sources/todomvc/app-spec.md)
diz que **Clear completed** remove os itens concluídos e deve ficar oculto
quando não há itens concluídos. O candidato A/B mantém as duas condições; C
omite somente a visibilidade. O E2E começa com um item concluído e outro
ativo, clica no botão e observa a visibilidade resultante, a remoção do
concluído e a preservação do ativo em duas fixtures.

Na primeira versão do scaffold, o próprio método `removeCompleted` fazia a
remoção. Um revisor LLM corretamente apontou que o controle não alvo não era
implementado pelo código gerado. Esse parecer foi preservado com recibo
`2cdbc19df22524dc476ba0001af5e80f06bc8f887808d8a8d3e630bca18afcb7`.

A versão seguinte expõe apenas `setTodos`: o handler gerado precisa remover
os concluídos e decidir se oculta o botão. O oráculo passou **7/7 controles**
no Chromium fixado: duas implementações corretas, mutante alvo, mutante não
alvo, botão oculto antes da ação, handler ausente e erro de script. Recibo
privado da qualificação:
`26bab5ce33fde926fe88e1fafd8bb8fb624d437c7c90be22dd3b23e2211e7333`.

O gate de revisão científica ainda **não passou**. O mesmo julgador Luna
rejeitou a segunda formulação alegando que a condição sem itens concluídos
não era testada, apesar da remoção pós-clique, e rejeitou a terceira porque
C omitiria a obrigação alvo — justamente a manipulação planejada. Esses
pareceres, potencialmente inconsistentes, estão preservados separadamente:
`9002e06cf147e99ef154add5b3df78d1535bcd291602b28dadf0ff9216ef3820`
e `9708496277dd0012413ce6c74dea7d434e7bc754bfd9b45ad99523319f95af43`.
Não há unanimidade nem base para contornar o gate após ver esses votos.

**Nenhuma geração experimental foi feita para este candidato.** O instrumento
permanece disponível para uma revisão independente do endpoint ou do próprio
procedimento de adjudicação. Ele não aumenta a contagem de obrigações
executadas e não é evidência para H1/H2.
