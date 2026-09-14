# Piloto de ambiguidades e controles equivalentes

Coleta original executada em 14/09/2026: 24 episódios, seis políticas construídas,
duas variantes e duas repetições por política. Os casos formam quatro grupos:
dois pares de intenções dependentes e dois controles. Não são seis projetos
independentes nem casos naturais admitidos por anotação humana.

## Resultado observado

| Grupo | Texto claro: atende intenção | Texto reescrito: atende intenção | Interpretação da reescrita |
|---|---:|---:|---|
| Coordenação, duas intenções gêmeas | 4/4 | 2/4 | 2 intenção prevista; 2 somente alternativa |
| Pronome, duas intenções gêmeas | 4/4 | 0/4 | 4 não atendem nenhuma das duas políticas |
| Controle de limiar equivalente | 2/2 | 2/2 | 2 intenção prevista |
| Controle Booleano equivalente | 2/2 | 2/2 | 2 intenção prevista |

Todos os 24 episódios foram executados, sem substituições, chamadas adicionais
ou falhas de provedor/execução. O denominador planejado foi preservado. O campo
legado `defective` identifica a variante reescrita, inclusive controles que
preservam significado; não significa que todo texto dessa variante é defeituoso.
Não se calcula efeito agregado de smells misturando controles e ambiguidades.

## Injeções e contraexemplos executáveis

### Coordenação: remoção de parênteses

As intenções explícitas são `(a or b) and c` e `a or (b and c)`. Os textos claros
usam essas mesmas expressões em linguagem natural, com parênteses. Ambas as
reescritas são exatamente:

> Return True exactly when flag a is true or flag b is true and flag c is true. Otherwise return False.

A interface `evaluate(a, b, c)` e os tipos Booleanos permanecem iguais. Nos
quatro episódios reescritos, o código gerado usa `a or (b and c)`. Para a intenção
`(a or b) and c`, a entrada `(True, False, False)` deveria retornar `False`, mas
retorna `True`. Isso ocorreu nas duas repetições. Para a outra intenção, a mesma
escolha passou. As oito combinações Booleanas foram verificadas por artefato
contra ambas as políticas, congeladas antes da coleta.

O contraste demonstra perda de informação sobre o agrupamento pretendido.
Não implica que a interpretação escolhida seja linguisticamente impossível:
ela corresponde à alternativa predefinida. Os gêmeos compartilham o mesmo prompt
reescrito e não são observações independentes de domínios distintos.

### Pronome: substituição do ator por “it”

Texto claro do remetente: “A sender is paired with a receiver. Return True
exactly when the sender is enabled. Otherwise return False.” A intenção gêmea
troca somente “the sender” por “the receiver”. Ambas as reescritas usam “it”.
A interface continua `evaluate(sender_enabled, receiver_enabled)`; os nomes
preservam pistas dos dois atores.

As quatro reescritas geraram `sender_enabled and receiver_enabled`. Esse código
não implementa nenhuma das duas políticas congeladas. Para a intenção do
remetente, `(True, False)` deveria retornar `True`, mas retorna `False`; para a
do destinatário, o contraexemplo é `(False, True)`. Todas as quatro combinações
Booleanas foram verificadas contra as duas políticas.

“Nenhuma” significa nenhuma das duas políticas testadas, não ausência de qualquer
interpretação possível da frase. O modelo introduziu uma conjunção adicional;
não se deve relatar esse resultado como simples escolha do ator alternativo.

### Controles que preservam significado

Limiar: “return True exactly when x is at least 5; otherwise False” foi reescrito
como “return False exactly when x is less than 5; otherwise True”. Domínio:
inteiros de −1 a 10, inclusive. Controle Booleano: resposta verdadeira quando
`enabled` é verdadeiro foi reescrita como resposta falsa quando é falso, com
resposta complementar no outro caso. Domínio: ambos os valores Booleanos.

Os oito artefatos dos controles passaram, incluindo quatro reescritos. Esses
controles de resposta complementar não são defeitos injetados nem positivos
humanamente validados da categoria “negative statements”. Preservam um resultado
nulo importante: a alteração da redação não produziu falha nesses casos.

## Protocolo, integridade e custo

Perfil `language_controls_v1`, seed `20260914`, duas repetições, modelo
`gpt-5.6-luna`, raciocínio baixo, via Codex CLI autenticado na assinatura ChatGPT.
Sem fallback para chave da API. O CLI não expõe um snapshot imutável exato do
modelo. O uso consome a cota da assinatura; custo em dólares não informado não
significa custo zero. Foram registrados 293.159 tokens de entrada, dos quais
75.008 em cache, 1.360 de saída e 738 de raciocínio reportados separadamente.

Manifesto, ordem aleatória, prompts, testes pretendidos e alternativos e hashes
de quatro arquivos de implementação foram congelados antes das chamadas. O
modelo recebeu somente seu prompt, sem oráculos, IDs dos gêmeos ou classificação.
O executor Linux ARM64 isolado foi qualificado antes da geração; nenhum código
gerado foi executado diretamente no host.

Bundle privado: `.private-research-evidence/codex-language-controls-20260914-v1`.
Verificação posterior confirmou 142 arquivos do recibo, quatro hashes de fonte
e 24 prompts/agendamentos e rederivou as classificações dos relatórios brutos.
SHA-256 do recibo:
`1c0b9af57c88b1c7a4ac68d90b3f1adb659298d2cbd248c36537061679cadcb6`.
`verification.json` e `verification-script.py` são evidências suplementares,
preservadas sem reescrever o recibo original.

## Alcance para o mestrado

Este piloto acrescenta evidência executável em duas famílias de ambiguidade,
além do [piloto anterior de omissão](codex-original-demo-results-20260914.md).
As coletas têm intervenções e denominadores diferentes e permanecem separadas.
São casos originais construídos, revisados por assistente. Não substituem
validação humana independente, admissão de corpus, diversidade de projetos ou
estimativa populacional. Duas repetições por célula não sustentam inferência
confirmatória. H1/H2 continuam não testadas.

O resultado sustenta a utilidade do protocolo pareado para revelar divergências
comportamentais em relação à intenção conhecida e distinguir uma interpretação
alternativa de código que não atende nenhuma política prevista. O próximo passo
é validar os candidatos com anotadores independentes e expandir os grupos de
projetos/intenções antes de um estudo confirmatório.

Implementação e critérios: [desenho](../superpowers/specs/2026-09-14-language-controls-pilot-design.md)
e [plano](../superpowers/plans/2026-09-14-language-controls-pilot.md).
Verificação de engenharia: 52 testes focados passaram, compilação dos módulos
passou e `git diff --check` passou; o CI nativo do PR é o gate de integração.
