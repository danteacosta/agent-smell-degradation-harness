# Seleção dos requisitos: procedimento congelado e decisões propostas

Status: proposta para revisão. Nenhuma seleção foi executada. A prévia local não é admissão.

## Procedimento

`scripts/select_requirements.py` transforma admissões da triagem em requisitos selecionados. Ordem fixada no script (o hash do script entra no resultado):

1. As unidades são os candidatos admitidos, menos os excluídos por decisão registrada.
2. Cada grupo de duplicação fica com uma unidade: o menor `candidate_id` lexicográfico. Os ids são hashes, então a escolha é cega a conteúdo e resultados.
3. Projetos em ordem alfabética. Um único `random.Random(2026100203)`. Projetos com mais de seis unidades chamam `rng.sample(ids_ordenados, 6)` uma vez; projetos com seis ou menos não consomem o gerador.
4. A seleção só vale com pelo menos 30 requisitos de pelo menos oito projetos. Caso contrário, o status é `blocked`, com o que falta.

O modo `select` recusa rodar se faltar decisão para algum mapping pendente da auditoria, se o arquivo de decisões não estiver `approved` ou se não declarar `probe_outcomes_consulted: false`. Resultados da sonda nunca são entrada. A seleção roda uma única vez, depois de todas as rodadas de triagem.

## Decisões propostas

Arquivo: [`data/requirement-selection/decisions-proposed.json`](../../data/requirement-selection/decisions-proposed.json). Proposta do assistente, sem consulta aos resultados por candidato da sonda. Precisa de aprovação (`status: approved`, `approved_by`).

Princípio: manter a regra do mecanismo congelado (primeiro voto favorável), salvo se falhar em V1 (a regra está no texto que o braço A usará) ou V2 (é um comportamento condicional com resultado observável, não só a presença ou o rótulo de um controle). Manter a regra congelada também mantém o alinhamento com a regra perguntada na sonda.

| Candidato | Proposta | Motivo |
|---|---|---|
| rc-de652e658b99 | manter | Favoritar, recarregar e aparecer em Starred; texto adicionado |
| rc-afa7beacea83 | excluir | Regra congelada é renomeação de rótulo (V2); o commit não traz regra de comportamento |
| rc-4041140f2b5d | manter | Só Remaining e Workspaces destacados, Home não; coincide com a intenção do commit |
| rc-6337ce108c4d | excluir | Regra congelada vem da frase removida (V1); o outro voto só afirma que um ícone existe (V2) |
| rc-e594b40135ff | manter | Cria a conversa se ainda não existir; condicional, muda outra entidade |
| rc-bd0b2995febc | manter | Lembrete opcional é o texto atual; a alternativa vem de frases removidas (V1) |
| rc-4da4940bc16c | manter | Campo aparece para admins com o recurso ativo; a alternativa exige segundo usuário |

Grupos de duplicação:

- `rc-458cc4cba31a` e `rc-ebff8e70d1d7`: as mesmas quatro frases sobre histórico na duplicação, adicionadas e removidas no mesmo dia.
- `rc-899c4d2472ad` e `rc-90d29a54a512`: mesmo commit e arquivo; as duas regras dizem que as ordens do cartão aberto e do minicard são independentes. Este grupo não estava na lista anterior; foi encontrado pelo modo `audit` (mesmo commit e arquivo). Os outros pares do mesmo commit foram lidos e são obrigações distintas.

## Prévia (não vinculante)

Com essas decisões: 65 unidades antes do teto (immich 3, mattermost 15, mealie 3, nextcloud 10, openproject 16, paperless 5, wekan 13); com o teto, 35 requisitos em sete projetos. Status: bloqueado por ter sete projetos, não oito. A lista sorteada não é publicada, para que nenhuma decisão pendente seja tomada olhando quem seria sorteado.

## Perguntas para o orientador

1. O braço A é "a documentação atual". Quatro admitidos são remoções (`rc-882709afd891`, `rc-2c13970217ea`, `rc-ebff8e70d1d7`, `rc-60c42d4dd323`), e outros tiram a regra de frases removidas. O braço A usa o texto anterior ao commit nesses casos, ou regras ausentes da documentação atual são excluídas?
2. `rc-458cc4cba31a` afirma uma regra que outro commit removeu no mesmo dia; numa leitura estrita, também sairia.
