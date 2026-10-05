# O que distingue as regras recuperadas das não recuperadas (exploratório, não cego)

Status: geração de hipóteses. Esta leitura foi feita **depois de ver os desfechos**, por quem conhecia o resultado de cada caso, e não é evidência de nada. Ela serve para propor uma covariável que possa ser codificada às cegas antes da coleta confirmatória. Nenhuma chamada de modelo foi feita.

## Os três grupos

Proporção de execuções C com a regra violada, por requisito, nos 46:

| Grupo | Requisitos | Observação |
| --- | ---: | --- |
| Sempre recuperada (C = 0) | 15 | A também passou em todos |
| Parcial (0 < C < 1) | 11 | — |
| Sempre violada (C = 1) | 20 | em 4 deles (`openproject-filter-text-autoupdate`, `openproject-invite-permission-basis`, `wekan-member-same-org-team`, `zulip-reverse-linkifier-paste`), A também falhou sempre: são casos de implementação difícil, e não de regra irrecuperável |

## Os descritores existentes separam pouco

| Descritor | Com | Sem |
| --- | --- | --- |
| `context_cue` (o texto de C implica a regra) | 9 requisitos, média de C 0,39 | 37 requisitos, 0,63 |
| `numeric` | 4, média 1,00 | 42, 0,54 |
| `derived_state` | 6, média 0,46 | 40, 0,60 |
| Palavras de restrição ou padrão no trecho (only, cannot, must, not, default…) | 23, média 0,65 | 23, 0,51 |

Nenhum descritor separa os grupos com nitidez. Os 15 recuperados são, em sua maioria, `context_cue = 0`. O painel de `context_cue` foi instruído a **não** contar conhecimento geral, então ele não captura recuperação por convenção.

## Leitura qualitativa

**Recuperadas:** em geral, a regra descreve o que uma implementação competente faria de qualquer jeito, dado o que a página e a API oferecem. Exemplos:
- apagar move para a lixeira quando existe `app.moveToTrash`;
- a conversa é criada se não existe;
- o seletor desabilitado some da caixa de mensagem;
- a busca por sugestões exclui quem já está inscrito;
- as mensagens aparecem traduzidas quando o canal tem tradução ativa.

**Sempre violadas:** em geral, a regra é uma escolha específica do produto, que nenhuma convenção imporia. Exemplos:
- restrições de permissão (só um superusuário concede o status, uma biblioteca tem um único dono, convidado precisa de pelo menos um canal);
- limites e listas (até 10, a extensão `.m2t`);
- padrões arbitrários ("Below" selecionado por padrão, página recolhida por padrão);
- exceções ("documentos com texto vazio são ignorados").

## Hipótese para a coleta confirmatória

**Convencionalidade:** uma implementação típica e competente do pedido C já satisfaria a regra, sem que ela fosse dita?

Diferente do `context_cue`, essa pergunta conta conhecimento geral de desenvolvimento, e não só o texto. A previsão é que regras convencionais sejam recuperadas e regras de escolha do produto não.

Para valer como teste, e não como leitura em retrospecto, a covariável precisa ser:
- definida e registrada antes da coleta, como covariável exploratória adicional, sem mudar as quatro de H1b;
- codificada às cegas para os 40 requisitos selecionados, antes de qualquer geração, de preferência por pessoas;
- acompanhada de controles autorados, como nos painéis atuais.

Codificar por LLM tem um risco de circularidade: um modelo julgaria o que modelos fazem por padrão.

Riscos desta leitura:
- viés de retrospecto: os exemplos foram escolhidos sabendo o resultado;
- a fronteira entre "convenção" e "escolha do produto" é subjetiva, e só a concordância entre codificadores cegos dirá se ela é codificável;
- 46 requisitos de 9 projetos é pouco para qualquer conclusão.
