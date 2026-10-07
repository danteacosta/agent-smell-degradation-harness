# Análise confirmatória H1a congelada antes dos dados

Status: proposta para o registro no OSF, escrita e testada antes de qualquer geração confirmatória. Não há chamadas de modelo. Nenhum número aqui é resultado.

## Por que existe

O pré-registro (seção 5) define o estimador; o [planejamento corrigido](2026-10-05-confirmatory-sample-size.md) trocou o teste por requisito pelo teste exato por projeto. Este script junta as duas coisas num único comando. Ele é rodado sobre dados sintéticos com três desfechos conhecidos, para que a análise e a regra de decisão fiquem fixadas antes de existir um dado real. Depois do registro, ele só pode mudar com um desvio registrado na seção 7.

## Entradas

- **Seleção:** a saída de `confirmatory_selection.py walk` (#177). Se o status não for `complete`, a análise devolve o status e nenhuma estimativa. Isso implementa a regra de parada: `stopped_insufficient` não é contornado na análise.
- **Desfechos:** uma linha por saída gerada, com estes campos:
  - `intent_id`, `project_id`, `model`, `replication`;
  - `arm`: A, B ou C;
  - `outcome`: pass, fail ou unknown;
  - opcionalmente `frame_option`: reserve ou w2024.

  A validação recusa slots ausentes ou duplicados, requisitos fora da seleção e requisitos no projeto errado.

## O que é reportado

| Item | Regra |
| --- | --- |
| H1a | Probabilidade de superioridade pareada C contra A, com pares não desconhecidos, repetições médias dentro do requisito e peso igual por requisito. IC 95% por bootstrap de projetos (4.000 reamostragens, semente 2026100611) e p bilateral exato por troca de sinais por projeto. |
| Decisão | **supported** se o limite inferior > 0,5 e p < 0,05. **reversal** se o limite superior < 0,5 e p < 0,05. Nos outros casos, **inconclusive**. |
| Desconhecidos | Pares observados (principal), e atribuição pior e melhor caso como limites, sem inferência. |
| Controle B | O mesmo estimando para B contra A; sinaliza efeito de redação se o IC excluir 0,5. |
| Exploratório | Por modelo, deixando um projeto de fora, por opção do quadro e sem a janela 2024. A análise sem 2024 é marcada como sensibilidade que não mantém o desenho 8×5. |

A regra bidirecional responde à decisão 5 da seção 8. Se o orientador preferir manter só a direção prevista, basta tratar `reversal` como `inconclusive` no registro. O script não precisa mudar.

Com oito projetos, o menor p possível é 2/256 = 0,0078. Um projeto com sinal contrário dobra esse valor (cerca de 0,016). O teste continua alcançando 0,05 com um ou dois projetos contrários pequenos, mas não com vários. Com quatro projetos ou menos, o teste não chega a 0,05, e o relatório diz isso.

## Ensaio com dados sintéticos

São oito projetos × cinco requisitos × dois modelos × duas repetições × três braços, ou seja, 480 slots, com 3% de desconhecidos. Os arquivos estão em `data/confirmatory-planning/analysis-dry-run/`.

| Cenário | Falha A / B / C | Estimativa | IC 95% | p por projeto | Decisão |
| --- | --- | ---: | --- | ---: | --- |
| Efeito | 0,08 / 0,10 / 0,55 | 0,744 | [0,712; 0,772] | 0,0078 | supported |
| Nulo | 0,20 / 0,20 / 0,20 | 0,507 | [0,468; 0,547] | 0,781 | inconclusive |
| Reversão | 0,55 / 0,55 / 0,10 | 0,260 | [0,223; 0,304] | 0,0078 | reversal |
| Seleção incompleta | — | — | — | — | stopped_insufficient, sem estimativa |

Os testes (`tests/test_confirmatory_analysis.py`) cobrem:
- os três cenários;
- braços idênticos (estimativa exatamente 0,5, p = 1);
- poucos projetos;
- a ordem dos limites de desconhecidos;
- as recusas de validação;
- a igualdade com os arquivos commitados.

## Fora deste script

- **H1b:** usa `scripts/h1b_agq.py`.
- **Efeito do instrumento (A0/C0) e H2:** o desenho 8×5 aprovado até agora só tem A/B/C.
- **Covariáveis, sonda de memorização e congelamento dos identificadores de modelo:** são pré-requisitos da coleta, não da análise.
