# Kanboard: filtro Closed tasks

**Resultado exploratório prospectivo do sucessor:** 18/18 saídas avaliáveis;
A, B e C passaram 6/6 cada. A omissão da regra textual de recuperação no
filtro não produziu falha observável neste requisito. Isso é um resultado nulo
local, não prova ausência de efeito em outros requisitos.

A [fonte Kanboard](../../data/e2e-six-projects/sources/kanboard/tasks.md)
afirma que uma tarefa fechada deixa o quadro e pode ser encontrada no filtro
**Closed tasks**. O endpoint isola a segunda obrigação: a tarefa já começa
fechada; o navegador escolhe o filtro e exige que ela apareça. A vista inicial
do quadro, a identidade/título da tarefa e uma segunda fixture são controles.
A/B explicitam a recuperação; C conserva o contexto do filtro e omite essa
cláusula. A página comum oferece os registros e renderiza a lista; a decisão
de quais tarefas selecionar pertence ao código gerado. É uma réplica limitada
da interface, não o Kanboard original.

O **primeiro lote de 18 gerações** não informa o contraste: a página comum
fornecia `status: 'open'|'closed'` sem declarar o formato do registro. Várias
saídas supuseram `closed: boolean`; falhas misturadas apareceram em A, B e C.
Seu [pacote público separado](../../data/e2e-kanboard-closed-filter/instrument-failure-20260927/summary.json)
marca `instrument_failure: true` e preserva as 18 tentativas, recibo congelado
`ccf430c2fb285c357a3967bccf041f39a56d975e562df43847b1a5058880291f`
e recibo privado `543a495f635e72bb5227ddc61beeb7e9353bd6432fb4175394b3220c2ba21537`.
Não foi reparado nem reclassificado como evidência de C.

O sucessor adicionou apenas a declaração comum do formato
`{id, title, status: 'open'|'closed'}`, sem regra de filtragem. O oráculo passou
9/9 controles no Chromium fixado
`sha256:00d1265095773b7f8a12aa73e81d0bab75563cbd672dd0b5d91783ea1b6d4400`;
três revisores LLM independentes aceitaram a separação do alvo e a
equivalência A/B antes das gerações. A revisão automatizada não substitui
adjudicação humana. Fonte, braços, prompts, cronograma aleatório, runtime,
oráculo e imagem foram congelados no recibo
`f9d5703080bd9a717ff9f3a2fe90a976924aa9832e2fa99c625ba6bb3e4111be`.
Os 18 HTMLs foram gerados antes de testar no navegador, sem reparo ou retry.

| Modelo | A completa | B reescrita | C sem regra de recuperação |
| --- | ---: | ---: | ---: |
| `gpt-5.6-luna` | 3 passes | 3 passes | 3 passes |
| `gpt-5.6-sol` | 3 passes | 3 passes | 3 passes |

O [pacote público do sucessor](../../data/e2e-kanboard-closed-filter/results-20260927/summary.json)
preserva os 18 relatórios, prints e recibo
`0f252bf7d08114808494bc41fec00f441b67cd71ea7f1a58bd48c0ff326d97c5`;
o pacote privado integral tem recibo
`da474f78154618c0867800080ececb732ddc490e36560240a010455d9dbaab14`.
É plausível que o modelo tenha recuperado a regra a partir da opção visível
**Closed tasks** e do status explícito; isso é inferência, não teste isolado
dessa causa. Repetições do mesmo requisito não acrescentam diversidade.

Este é o **sétimo requisito novo executado** do bloco planejado; restam
quatro. A intervenção pertence à família operacional de conteúdo parcial:
foi removida uma cláusula de recuperação por filtro. Isso não valida uma
classificação de smells naturais. H1 ordinal e H2 continuam sem teste decisivo.
