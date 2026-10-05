# Braço histórico H: protocolo

Status: exploratório, pedido pelo orientador depois da coleta dos 46. Nenhuma chamada de geração H foi feita. Este documento congela a elegibilidade e a construção dos textos H antes dessas chamadas. Desvio registrado na seção 7 do pré-registro.

## Pergunta

Nos 46 requisitos, o texto que o projeto documentava **antes** do commit que escreveu a regra-alvo já produzia o defeito? A coleta dos 46 comparou A (documentação no fim da janela) com C (A menos a regra), e C é uma omissão construída. H é uma reconstrução controlada guiada pelo histórico: mantém o contexto moderno de A e altera o trecho da regra com base na documentação anterior. Não reproduz integralmente o requisito ou a documentação antiga. Quando H = C, as chamadas novas replicam a omissão construída em casos classificados pelo histórico; não demonstram o efeito do texto histórico integral.

O piloto de setembro (10 requisitos, 60 pares) encontrou 11 melhoras com o texto corrigido, 44 empates, 5 desconhecidos e nenhuma piora. Este estudo repete a pergunta nos 46, com os oráculos e as páginas congeladas da coleta atual.

## Etapa 1: triagem mecânica (feita, `data/historical-arm/classification.json`)

`python3 scripts/historical_arm.py classify --repos <clones>` lê só textos-fonte: o quadro de candidatos, a seleção, as configs dos casos e o git dos nove projetos. Nenhum resultado de execução é lido.

| Classe | Casos | Critério |
| --- | ---: | --- |
| `excluded_deletion` | 4 | o commit apagou texto: a versão antiga continha a regra |
| `excluded_moved` | 2 | o commit acrescentou texto que já estava na documentação do commit-pai (≥ 90% dos termos do trecho de C); a regra existia antes |
| `panel` | 40 | 17 adições e 23 modificações, decididas pela revisão |

Os dois casos movidos são `openproject-files-tab-attachments` e `zulip-subscribe-typeahead`. Em `nextcloud-mail-favorites-up`, só um passo genérico ("Visit mail settings") já existia, e o caso vai para a revisão.

Para cada caso da revisão, o script extrai do diff `commit^..commit` o lado antigo (contexto e linhas removidas, 25 linhas em torno das linhas do quadro, sem marcação).

**Correção do número preliminar.** Antes desta etapa eu tinha tratado 14 adições como "H = C" e calculado 0,714 com as execuções C existentes. Esse atalho não verificava se a documentação antiga já descrevia a funcionalidade. Em 12 dos 14, a regra é só de 4% a 89% do texto acrescentado no commit. Em alguns deles, como os favoritos do Mail, a seção inteira da funcionalidade entrou no mesmo commit. Nesses casos, o "texto antigo" não é uma regra com smell, e sim a ausência da funcionalidade. A revisão decide caso a caso. O número preliminar foi descartado.

## Etapa 2: revisão cega da documentação antiga (a rodar no Mac)

Os codificadores recebem três textos:
- FEATURE: o pedido sem a regra, isto é, o texto do braço C;
- RULE: o trecho que C retira;
- OLD DOCUMENTATION: o trecho anterior ao commit.

Eles não veem código gerado, resultados de oráculo, desfechos A/B/C nem nomes de modelos. Respondem a duas perguntas:

1. `feature_documented`: a documentação antiga já descreve a funcionalidade (sim ou não, com citação literal)?
2. `rule_status`, com citação literal, exceto em `absent`:
   - `same`: afirma a regra;
   - `vaguer`: afirma o comportamento de forma menos precisa, compatível com a regra mas sem determiná-la;
   - `absent`: não diz nada sobre o comportamento;
   - `different`: afirma um comportamento contrário, ou seja, o produto mudou.

A governança é a mesma do painel de `context_cue`:
- os codificadores são astra e sol, com luna como desempate;
- 5 controles autorados (um por rótulo, mais uma funcionalidade não documentada) precisam ser reproduzidos pelos três modelos, ou a execução para;
- citações não literais invalidam o voto;
- não há retry;
- o kappa é reportado nas duas perguntas.

A decisão final é a dos dois primários quando concordam nas duas perguntas; nos outros casos, decide o desempate. São cerca de 95 a 115 chamadas.

## Etapa 3: admissão e textos H (determinística, `build`)

| Decisão | Admissão | Texto H |
| --- | --- | --- |
| funcionalidade não documentada | não | — |
| `same` | não (sem diferença) | — |
| `different` | não (mudança de comportamento, não de especificação) | — |
| `absent` | sim | H = C |
| `vaguer` | sim | C integral, seguido de um novo parágrafo com a citação antiga literal; se a citação já aparece de forma contígua em C, normalizando somente espaços e caixa, H = C |

`build` grava `data/historical-arm/admission.json` e uma config derivada por caso em `data/historical-arm/cases/`. O painel vincula a classificação e as configs a hashes congelados; `build` recusa mudanças nos textos revisados e exige citações válidas. Os dois modelos primários devem ser distintos. A config derivada tem os braços A, B, C e H, `collect_arms: ["A", "H"]` e uma semente nova. O `build` se recusa a sobrescrever textos H já construídos, e a etapa 4 se recusa a rodar com `data/historical-arm/` fora do git.

Limitações conhecidas:
- o contexto moderno pode oferecer pistas que não existiam antes do commit; H não é o texto histórico integral;
- quando H vem de uma citação antiga, perde as dicas de API que estavam no trecho da regra, como C;
- a citação vem do codificador que decidiu, e não de uma escolha humana;
- a regra pode estar descrita em outro arquivo da documentação antiga. A triagem só procura o texto acrescentado no commit, e a revisão vê apenas o trecho do arquivo alterado.

## Etapa 4: coleta A + H contemporânea (no Mac)

Para cada caso admitido: 2 modelos × 2 repetições × 2 braços = 8 chamadas, no mesmo pacote. A é coletado de novo para que a comparação não misture datas, já que os modelos podem mudar entre a coleta de 3/10 e esta. As páginas congeladas, os oráculos e a imagem Docker são os da coleta dos 46. Os pacotes ficam em `historical-arm-v1` e os resultados em `data/historical-arm-results/v1`, sem timestamp variável: reiniciar o comando não repete slots já tentados. Uma tentativa interrompida sem resultado final exige diagnóstico, sem retry automático.

## Análise

- **Principal (exploratória):** probabilidade pareada de H ser pior que A, com pares por requisito × modelo × repetição, bootstrap por projeto e teste de inversão de sinais. É o mesmo estimador de H1a, com limites de pior e melhor caso para os desconhecidos.
- **Separada por construção:** `absent` (réplica de C selecionada pelo histórico) e `vaguer` (o texto antigo efetivamente presente).
- **Diagnósticos:**
  - a violação em A agora contra A em 3/10, para medir deriva;
  - nos casos `absent`, a violação em H agora contra C em 3/10.

## Como rodar

```bash
bash scripts/run_historical_arm.sh panel      # revisão + build; depois commit de data/historical-arm/
bash scripts/run_historical_arm.sh collect    # A + H; publica em data/historical-arm-results/v1/
```

## Testes

`tests/test_historical_arm.py` cobre:
- a classificação publicada: 46 linhas, nenhum campo de desfecho, prompts cegos;
- a construção de H nos três caminhos;
- a exigência de citações literais;
- um painel falso que passa pelos controles e gera 40 configs coletáveis só com A e H, com slots distintos dos da coleta original;
- a parada quando um controle falha;
- os agendamentos das configs antigas, que ficam idênticos;
- o pareamento A × H.

## Qualificação de 04/10: primeira parada

O painel com Astra/Sol e Luna como desempate tentou os 15 controles e parou antes de codificar qualquer caso. Astra e Sol acertaram os cinco controles; Luna produziu uma citação não contígua em `ctl-hist-same`, rejeitada pela regra literal já congelada. Não houve admissão nem geração A/H. SHA-256 do resultado privado: `0535804e8bf3d71f9aa13b0570d78828a52d644e3ac0ffc7e7006f361518b527`.

A próxima qualificação mantém os textos, os cinco controles e o critério, substituindo apenas o desempatador por `gpt-6.1-sol`, distinto dos dois primários. A troca é exploratória e ocorre sem decisões dos 40 casos. A rodada anterior permanece preservada; não se reexecutam seus slots.

A segunda qualificação tentou 15 controles, com dez respostas válidas dos primários e cinco rejeições de API para `gpt-6.1-sol`: o modelo não é suportado nesta assinatura pelo CLI. Zero casos foram codificados. SHA-256 do resultado privado: `ce6d31af82953b38c814cdb2b571da2e6bd6bdde7822c16fb9162317764013da`. Depois de consultar o catálogo local do CLI, a próxima qualificação usa `gpt-5.6-terra` como desempate; esse modelo é listado pelo runtime e é distinto de Astra/Sol e dos geradores Luna/Sol 5.6 da coleta original. Textos, controles e critério permanecem idênticos.

## Revisão dos H antes do congelamento

A primeira construção dos seis `vaguer` ampliava a deleção para sentenças completas. A revisão independente encontrou perda de APIs e regras não alvo em WeKan e Paperless. Nenhuma geração A/H havia ocorrido. A construção passa uniformemente a **C + passagem histórica literal**, em parágrafo separado, preservando todo C byte a byte; não inclui nova instrução interpretativa. A posição da passagem e a duplicação de contexto são limitações da reconstrução. Os votos do painel permanecem intactos.

Em 05/10, a revisão das fontes colocou Paperless `custom-field-no-value` e Nextcloud `mail-favorites-up` em quarentena. O painel original continua com 19 admitidos; o conjunto operativo tem 17 (12 absent, cinco vaguer) e 136 chamadas, conforme [relatório da admissão](2026-10-05-historical-panel-admission.md). A revisão é não cega e não substitui votos ou auditoria humana.
