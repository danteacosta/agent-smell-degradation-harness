# Casos da seleção, lote 1: Paperless, Immich e Mealie

Status: rascunho. Oráculos pré-qualificados localmente; falta a qualificação vinculante em Docker, a revisão dos braços B e C e a aprovação das decisões de seleção. Nenhum modelo foi chamado.

## Por que estes casos já

O sorteio com teto de seis só afeta projetos com mais de seis unidades. Paperless (5), Immich (3, com a exclusão proposta de `rc-afa7beacea83`) e Mealie (3) entram inteiros em qualquer resultado do sorteio, então estes casos podem ser montados antes da seleção sem olhar quem seria sorteado. A rodada 2 só acrescenta Zulip e Grist e não muda isso.

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
- O estado verificado vem da API da página (gravado e reconstruído após `reload`), não de texto que o código gerado pudesse escrever direto no DOM.
- A pré-condição de cada jornada falha como `interface_error` se a página chegar com estado alterado antes da ação.

## Controles de qualificação

68 controles em 10 casos: pelo menos uma referência e uma alternativa que passam, um mutante que falha só no alvo, um que falha só nos controles, um sem handler (`interface_error`) e um com erro de script (`browser_error`). Alguns casos têm controles extras para leituras legítimas diferentes da referência (por exemplo, desabilitar o checkbox de superusuário, remover `{{doc_title}}` em vez de recusar, escolher o primeiro dono) e para mutantes plausíveis (aceitar por MIME `video/*`, exigir Manage group).

Pré-qualificação local (Node e Playwright desta máquina, sem Docker): 68/68 controles classificados como esperado. Um ajuste foi feito durante a pré-qualificação: em `immich-path-search`, a asserção-alvo passou a exigir que o asset esteja incluído (a regra diz "inclui"), e a precisão ficou nas consultas de controle.

## Observações para codificar `context_cue`

Sem efeito nos oráculos; registradas para os codificadores cegos:

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
