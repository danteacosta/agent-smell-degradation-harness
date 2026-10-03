# Decisões de seleção, versão 2: documentação no fim do frame

Status: proposta para aprovação. Nenhum resultado da sonda foi consultado. Nenhuma seleção vinculante foi executada.

## A decisão que destrava as outras

Muitas pendências das duas rodadas tinham a mesma raiz: o braço A é "a documentação atual do projeto", e não estava definido o que é "atual". A proposta define assim:

> Documentação atual = o último commit do branch padrão em ou antes de 2026-09-30T23:59:59Z, o mesmo limite do frame.

Consequências:

- Uma regra ausente desse snapshot é excluída, seja qual for o tipo da mudança (adição, modificação ou remoção). Isso responde à pergunta antiga sobre os candidatos de texto removido.
- Uma regra que saiu de uma página mas continua documentada em outra fica, e o texto do braço A vem do snapshot.
- O commit de origem continua sendo a forma de encontrar o candidato, mas não é a fonte do texto de A.

## Como foi verificado

`scripts/check_current_documentation.py` localiza o snapshot de cada um dos nove projetos e procura no snapshot cada frase adicionada ou removida dos 99 admitidos. A comparação usa a sequência de palavras: ignora markup, pontuação e alinhamento de tabela, e cobre todas as páginas de documentação do projeto, inclusive páginas que mudaram de lugar, como na migração da central de ajuda do Zulip. O resultado está em `data/requirement-selection/current-doc-check.json`.

33 candidatos não tiveram todas as frases encontradas literalmente. Procurei cada um deles no snapshot, sem acesso a resultados da sonda:

| Situação no snapshot | Candidatos |
|---|---|
| Regra ausente → excluir | rc-024102998dd2, rc-458cc4cba31a, rc-ebff8e70d1d7, rc-60c42d4dd323, rc-d3faa64f9193, rc-6337ce108c4d, rc-3c572449f134, rc-62e9d69be36f, rc-bf86d02f63c9, rc-3cd319371269, rc-c30a4162188a, rc-1590080019fb |
| Regra contradita → excluir | rc-302720d6856b (a documentação agora diz que as datas passam a ser determinadas por predecessoras ou filhas) |
| Só posição de controle, e desatualizada → excluir | rc-cb144c65d898 |
| Presente, reescrita ou movida → manter | rc-0dde4b87ef72, rc-0ec1ac8f66bd, rc-2c13970217ea, rc-24946f42bfc2, rc-393307131fc8, rc-4200f1dac6a9, rc-4aac15b7b503, rc-6be0f3992b4b, rc-7b485b51412f, rc-aac66a0af69a, rc-b49db6870ff5, rc-b7086f489030, rc-c044ebec7fe1, rc-c6aa48543d73, rc-d595b3b1510f, rc-dfb84383fb89, rc-e436521e462d, rc-e594b40135ff, rc-f33b2bf870e9, rc-fd348eb33246 |
| Só em texto alternativo de imagem → manter, com pergunta ao orientador | rc-882709afd891 |

## As 15 pendências da rodada 2

| Candidato | Proposta | Motivo curto |
|---|---|---|
| rc-3c572449f134 | excluir | Regra da caixa de busca ausente do snapshot |
| rc-dfb84383fb89 | manter | Presente em outra página ("You can always unsubscribe from any channel") |
| rc-62e9d69be36f | excluir | Ausente do snapshot |
| rc-bf86d02f63c9 | excluir | Ausente do snapshot |
| rc-7b485b51412f | manter | "Set default: Collapse" presente; o outro voto é outra obrigação |
| rc-3cd319371269 | excluir | Ficou só "deprecated"; "não suportado em novos documentos" saiu no mesmo dia |
| rc-f33b2bf870e9 | manter | "Up to 10 billing managers" presente, agora sem o qualificador getgrist.com |
| rc-c30a4162188a | excluir | Ausente do snapshot |
| rc-362ff82e3812 | manter | O oráculo deve testar o efeito da configuração, não só a existência do controle |
| rc-1590080019fb | excluir | O snapshot não afirma mais a regra; ela teria de ser inferida |
| rc-b7086f489030 | manter | O oráculo deve salvar a configuração e verificar quem consegue apagar |
| rc-aac66a0af69a | manter | Presente; a regra congelada inclui a consequência que o oráculo observa |
| rc-fd348eb33246 | manter | Presente; a regra congelada é a concessão positiva |
| rc-6be0f3992b4b | manter | Limite de 1GB presente; o oráculo não deve exigir um mecanismo específico |
| rc-cb144c65d898 | excluir | Só a posição de um controle (V2), que além disso mudou |

## Prévia não vinculante

Com estas decisões: 83 unidades antes do teto (grist 9, immich 3, mattermost 15, mealie 2, nextcloud 9, openproject 15, paperless 5, wekan 11, zulip 14). Com o teto de seis por projeto, são 46 requisitos em nove projetos, e não há falta. A lista sorteada não foi publicada.

Comando da seleção, depois da aprovação (`status: approved`, `approved_by`):

```sh
python3 scripts/select_requirements.py select \
  --screening data/llm-screening-20261002/results.json --screening data/llm-screening-round2-20261003/results.json \
  --frame data/requirement-sampling/frame-20261002.jsonl --frame data/requirement-sampling/frame-ext-20261002.jsonl \
  --decisions data/requirement-selection/decisions-proposed.json \
  --mapping-audit data/llm-screening-20261002/mapping-audit.json \
  --mapping-audit data/requirement-selection/round2-mapping-audit.json \
  --out data/requirement-selection/selection.json
```

## Efeito no lote 1

Com essa definição, os textos A do lote 1 devem vir do snapshot. A única mudança no nível da regra é no Immich: a linha MP2T agora também lista `.ts`, e o braço A de `immich-m2t-upload` deve incluir essa extensão antes do congelamento. As outras frases-alvo do lote 1 estão literalmente no snapshot.
