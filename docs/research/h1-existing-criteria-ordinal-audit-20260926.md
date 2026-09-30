# Auditoria ordinal secundária de critérios existentes — 26/09/2026

**Resultado:** o recorte sugere maior severidade após omissão nos pares
completos, mas **não decide H1**. Os limites que preservam todos os casos sem
rótulo abrangem zero. Esta é uma auditoria exploratória de artefatos já
gerados, não uma coleta confirmatória nem uma revisão humana.

## Desenho e custódia

O ponto de partida é a coleta fechada de [12 intenções em quatro projetos](criteria-expansion-results-20260921.md),
cujo recibo privado tem SHA-256
`5c72ebe1ab3cce7a09b804514680e3dc82c96b2a5cdb481a57b0cc928e8a7561`.
Antes desta nova avaliação, a seleção fixou a repetição 1 de A e C para cada
intenção e cada um dos dois geradores: **48 posições**, das quais duas já tinham
saída de geração inválida. As 46 saídas válidas receberam dois julgamentos
isolados, com `gpt-6-astra` e `gpt-6-sol`, totalizando **92 chamadas** pela
assinatura ChatGPT do Codex, sem chave de API nem GitHub Actions. Os julgadores
viram apenas critérios, IDs opacos e obrigações de referência; não receberam
braço, gerador, par ou desfecho E2E. A rubrica ordinal preexistente usa
`clean=0`, `minor=1`, `moderate=2`, `severe=3` e `not_visible` como abstenção.

Uma primeira versão do instrumento foi **encerrada**, não completada: 13
posições tentadas, uma falha de sandbox antes da resposta, sete JSONs válidos
e cinco respostas de formato inválido. Seu recibo separado é
`74dbe2fc0f51c844291d29cc9898f40e0a890b44b99fb4c727516f7234ccaedc`.
Nenhuma dessas respostas foi reparada ou transferida ao estudo seguinte. A
versão seguinte explicitou que todo campo `evidence` deve ser uma string e
passou **4/4 controles criados antes das chamadas de pesquisa**: ambos os
modelos reconheceram o exemplo completo e a omissão central. Esses controles
qualificam o formato e esses exemplos, não a validade semântica geral dos
rótulos. O segundo pacote teve **92/92 respostas em formato válido**, com
recibo privado SHA-256
`9b01a45ac1fc7996ea2725913dc56e5f567504d11cd34383ffbe7e8b50f2e878`.

## Desfechos sem preencher ausências

Os julgadores concordaram no rótulo ordinal em **39/46** artefatos e no rótulo
*mais todos os estados das obrigações* em **36/46**. A verificação adicional
do contrato de evidência por obrigação encontrou **26 citações não literais em 11 respostas**
(5 de Astra, 21 de Sol). Exigindo citações literais para `covered` e
`uncertain`, e texto vazio para `omitted`, restam **29/48** artefatos com
consenso estrito: 13 `clean` e 16 `moderate`. As duas gerações inválidas,
discordâncias, abstenções e citações inválidas permanecem sem severidade.

Só **9 das 24 células intenção × gerador** têm A e C com rótulos estritos.
Nelas, A−C vale −2 em oito células e 0 em uma; a média **−1,78** é descritiva
da seleção completa, não do conjunto planejado. Para as demais células,
atribuindo 0 a 3 a cada severidade desconhecida, o intervalo de identificação
do contraste médio A−C nas 24 células é **[−2,25; +0,125]**. É um limite por
ausência de informação, **não intervalo de confiança**. Por projeto:

| Projeto | Pares completos / 6 | Limites A−C |
| --- | ---: | ---: |
| CASS | 2 | [−2,00; 0,00] |
| RealWorld | 0 | [−2,67; +1,83] |
| StrictDoc | 4 | [−2,33; −0,83] |
| TodoMVC | 3 | [−2,00; −0,50] |

Sem a exigência de citação literal, haveria 36 rótulos de consenso, 13 pares
completos e limites globais [−2,125; −0,625]. **Não se usa essa análise mais
favorável como primária**: a instrução enviada aos julgadores pediu trechos
literais, e tratá-los como válidos depois de ver o resultado enfraqueceria a
trilha de evidência.

Os resultados públicos sem IDs de artefato estão em
[`data/h1-ordinal-audit/results-20260926.json`](../../data/h1-ordinal-audit/results-20260926.json).
Os códigos de coleta e análise estão em
[`scripts/h1_existing_artifacts_ordinal_audit.py`](../../scripts/h1_existing_artifacts_ordinal_audit.py)
e [`scripts/h1_ordinal_audit_results.py`](../../scripts/h1_ordinal_audit_results.py).
O modo `analyze` do coletor só conta rótulos preliminares; os números acima
vêm exclusivamente do segundo script, que valida citações e as 48 posições.
Após o selamento, o modo `--verify-sealed-receipt-sha256` desse script
recalcula os números sem escrever arquivos e confronta o inventário privado,
o resumo público e a análise privada com o recibo acima. A verificação
executada em 26/09/2026 passou. A regra de citação literal aplicada ao
desfecho verifica os trechos **por obrigação**; o campo narrativo `evidence`
do topo da resposta não compõe esse gate.
Prompts, saídas completas, captura por chamada, vínculo privado A/C e análise
detalhada ficam fora do Git em
`.private-research-evidence/h1-ordinal-audit-20260926-v3/`.

## Consequência para H1

Esta auditoria reutiliza saídas de quatro projetos escolhidos intencionalmente,
uma repetição por célula e dois julgadores do mesmo provedor, sem revisão humana.
Não estima a população de requisitos nem substitui a severidade adjudicada da
H1 registrada. O resultado de cobertura da coleta original continua evidência
exploratória mais completa para esse desfecho binário; converter cobertura em
severidade por regra automática também não resolveria a validade ordinal.

O próximo passo que realmente aproxima a resposta de H1 é congelar um conjunto
maior de intenções independentes com proveniência e licença, fixar a rubrica e
o tratamento de ausências antes da geração, obter adjudicação independente e
executar o estimando ordinal por intenção. Repetir o Kanboard E2E não satisfaz
essas condições.
