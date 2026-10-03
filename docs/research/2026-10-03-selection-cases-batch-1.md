# Casos da seleção, lote 1: Paperless, Immich e Mealie

Status: rascunho. A qualificação original de 68 controles passou no Docker em 3 de outubro de 2026. A revisão encontrou três lacunas adicionais; as fixtures foram corrigidas e a nova qualificação passou em 73/73 controles, no mesmo Docker congelado. A revisão dos braços B e C e a aprovação das decisões de seleção continuam pendentes. Nenhum modelo foi chamado para gerar estas páginas.

## Por que estes casos já

O sorteio com teto de seis só afeta projetos com mais de seis unidades. Paperless (5), Immich (3, com a exclusão proposta de `rc-afa7beacea83`) e Mealie (3) cabem inteiros sob o teto, desde que esses candidatos sejam mantidos após a aprovação dos mappings, tratamento das remoções e revisão de duplicações. Os casos podem ser preparados antes da seleção, mas ainda não estão admitidos. A rodada 2 só acrescenta Zulip e Grist e não muda isso.

Ficaram fora deste lote, até decisão: `rc-afa7beacea83` (exclusão proposta) e `rc-60c42d4dd323` (Mealie, remoção: depende da pergunta sobre o texto do braço A).

## Casos

| Caso | Candidato | Regra-alvo (omitida em C) | Asserções-alvo |
|---|---|---|---|
| `paperless-ai-suggestions-blank-text` | rc-84013890a131 | Documentos com texto processado vazio ou só espaços são pulados | Documentos em branco não entram na fila |
| `paperless-superuser-grant` | rc-806442660eb5 | Só um superusuário concede status de superusuário | Usuário não superusuário não consegue conceder |
| `paperless-custom-field-no-value` | rc-086a9d210266 | Sem valor, o campo só é adicionado e o valor existente fica intacto | Valor existente preservado |
| `paperless-own-profile` | rc-035e8af08cd7 | Permissões de User não são necessárias para editar o próprio perfil | Perfil salvo sem permissão de User |
| `paperless-doc-title-placeholder` | rc-9e198862b86e | `{{doc_title}}` não pode ser usado na atribuição de título | Template com `{{doc_title}}` não é salvo |
| `immich-m2t-upload` | rc-0ec1ac8f66bd | `.m2t` é extensão MP2T suportada | Arquivos `.m2t` aceitos |
| `immich-library-single-owner` | rc-c86728bbc029 | Biblioteca externa pertence a um único usuário | Nenhuma biblioteca com mais de um dono |
| `immich-path-search` | rc-b6f382226c41 | Parte de um nome de pasta encontra o asset (exemplo 3D_Printing) | `Printing`, `3D`, `Reports`, `2025` incluem o asset |
| `mealie-organize-food-permission` | rc-106bac72c813 | Criar comida exige Organize group data | Sem essa permissão, a comida não é criada |
| `mealie-planner-food-label` | rc-0f453b1f0a55 | Ingredientes também casam pela Food Label | Receitas com ingrediente rotulado entram no pool |

Cada caso tem duas fixtures com dados diferentes, asserções-alvo e de controle disjuntas, e o texto C é o A com exatamente um trecho contíguo removido (verificado em teste). Os textos A seguem a documentação no commit de origem, adaptados ao nome dos controles e da API da página.

## Navegação e escopo

A lição do estudo de ancoragem foi aplicada antes de qualquer geração:

- Cada página é um único documento em `http://localhost/`; a única navegação é `reload`, e qualquer outra requisição é abortada (CSP sem rede).
- Toda jornada usa só controles visíveis da página e só dados das fixtures; nenhuma jornada depende de um segundo usuário, de outra rota ou de estado fora do `localStorage` da página.
- Nas jornadas persistentes, o oráculo lê o estado renderizado após `reload`; as funções da página gravam os dados em `localStorage`. As jornadas de busca e pool de receitas verificam os resultados visíveis no DOM, sem exigir persistência. A admissão impede alterações fora do marcador, mas não impede que a inserção escreva no DOM; isso limita a força da evidência sobre estado interno.
- A pré-condição de cada jornada falha como `interface_error` se a página chegar com estado alterado antes da ação.

## Controles de qualificação

A versão original tinha 68 controles em 10 casos; a versão corrigida tem 73: pelo menos uma referência e uma alternativa que passam, um mutante que falha só no alvo, um que falha só nos controles, um sem handler (`interface_error`) e um com erro de script (`browser_error`). Alguns casos têm controles extras para leituras legítimas diferentes da referência (por exemplo, desabilitar o checkbox de superusuário, remover `{{doc_title}}` em vez de recusar, escolher o primeiro dono) e para mutantes plausíveis (aceitar por MIME `video/*`, exigir Manage group).

Pré-qualificação local (Node e Playwright desta máquina, sem Docker): 68/68 controles classificados como esperado. Um ajuste foi feito durante a pré-qualificação: em `immich-path-search`, a asserção-alvo passou a exigir que o asset esteja incluído (a regra diz "inclui"), e a precisão ficou nas consultas de controle.

## Observações para codificar `context_cue`

Os identificadores científicos dos casos ficam nos metadados, fora do HTML fornecido ao modelo. Todas as páginas usam uma chave de armazenamento neutra. Pistas restantes do texto-fonte, sem efeito nos oráculos, ficam registradas para os codificadores cegos:

- `paperless-own-profile`: o braço C ainda diz que a permissão User cobre "outras contas", o que sugere a regra.
- `mealie-organize-food-permission`: o braço C mantém a linha da tabela "Organize group data: criar ... foods".
- `immich-path-search`: o braço C mantém "parte do caminho original"; o exemplo é o que falta.
- `immich-m2t-upload`: em C, a lista de extensões simplesmente não tem `.m2t`; recuperar a regra depende de conhecimento prévio.
- `immich-library-single-owner`: o scaffold usa caixas de seleção (permitem mais de um dono); é igual nos três braços.

## Como qualificar no Mac

```sh
bash scripts/qualify_selection_cases.sh
```

Roda `eval/fixtures/<caso>/qualify.py` com a imagem fixada para cada caso novo e grava a evidência fora do repositório. Depois disso, os configs em `data/abc-cases/` deixam de ser rascunho quando os braços B e C forem revisados e as decisões de seleção aprovadas. A coleta segue `scripts/abc_case.py` (duas repetições por braço e modelo: 120 chamadas para os 10 casos).

## Regenerar

`python3 scripts/build_selection_cases.py build` reescreve fixtures e configs a partir de `scripts/selection_cases/`; `check --work <dir>` repete a pré-qualificação local. Um teste garante que os arquivos versionados são exatamente os gerados pelas specs.

## Correções antes do congelamento

A revisão detectou vazamento artificial pelo identificador científico usado como chave de armazenamento no HTML. O teste reproduziu a pista nos dez prompts; as páginas agora usam a mesma chave neutra. Os nomes descritivos continuam apenas nos metadados externos.

O oráculo de superusuário aceitava um handler que bloqueava toda edição pelo usuário comum. Uma regressão no Docker reproduziu esse falso sucesso. A jornada agora testa primeiro uma edição válida de nome sem tentar conceder superusuário; o mutante é classificado como falha de controle. Isso permite recusar integralmente uma tentativa inválida de concessão, sem exigir atualização parcial desse formulário.

O oráculo de criação de alimentos recusava controles legitimamente desabilitados, ocultos ou removidos para o usuário sem permissão. Três regressões no Docker reproduziram o problema antes da correção e passaram depois dela. O ator autorizado continua exigindo controle único, visível e habilitado; IDs duplicados e ausência de handler permanecem erros de interface. Os novos controles de qualificação cobrem essas fronteiras.

Essas execuções qualificam o instrumento e não são gerações experimentais nem evidência de H1/H2. As evidências originais e corrigidas ficam em pacotes separados; nenhuma qualificação anterior é substituída.
