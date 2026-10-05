# Tamanho da amostra confirmatória de H1a (simulação)

Status: planejamento, exploratório. Script: `scripts/confirmatory_power.py`. Saída: `data/confirmatory-planning/power.json` (semente 2026100501, 1.000 estudos simulados por célula, 1.000 reamostragens de bootstrap, 2.000 inversões de sinal). Nenhuma chamada de modelo.

## Como foi simulado

Cada estudo simulado sorteia projetos com reposição entre os 9 da coleta dos 46. Dentro de cada projeto sorteado, sorteia requisitos com reposição, e cada requisito mantém todos os seus pares A/C observados (2 modelos × 2 repetições, sem os desconhecidos). Dos 46 requisitos, 44 têm pelo menos um par avaliável. O estudo é analisado com o mesmo estimador do pré-registro (`paired_probability_of_superiority`).

Dois ajustes evitam que a simulação fique otimista demais:
- **Atenuação do efeito.** Cada par "C pior" vira empate com probabilidade q. q = 0 reproduz o efeito observado; q = 5/9 leva a cerca de 0,60; q = 0,8, a cerca de 0,55; q = 1 é a hipótese nula. Requisitos novos tendem a mostrar efeito menor que a amostra exploratória que motivou o estudo.
- **Ruído com inversões.** Os 172 pares A/C exploratórios não têm nenhum "C melhor". Reamostrados sozinhos, nunca produzem inversão e qualquer desenho pareceria com poder total. Por isso cada par é sorteado de novo, como pior ou melhor com 50% de chance cada, com probabilidade 0,047. Esse valor é a discordância entre duas redações do mesmo requisito completo (B contra A: 4 piores e 4 melhores em 172 pares). O cenário de estresse usa o triplo, 0,14.

Regras de decisão (fração de estudos que as satisfazem):
- **p:** valor p da inversão de sinais < 0,05;
- **IC:** limite inferior do IC 95% por bootstrap de projetos > 0,5.

## Resultado

Poder pela regra p (entre parênteses, pela regra IC). Ruído 0,047:

| Desenho (projetos × requisitos) | Requisitos | Efeito observado (≈0,74) | ≈0,61 | ≈0,55 | Nulo: taxa de falso positivo |
| --- | ---: | --- | --- | --- | --- |
| 4 × 4 | 16 | 0,98 (0,98) | 0,76 (0,86) | 0,29 (0,54) | 0,001 (0,03) |
| 6 × 4 | 24 | 1,00 (1,00) | 0,95 (0,96) | 0,55 (0,73) | 0,006 (0,06) |
| 8 × 3 | 24 | 1,00 (1,00) | 0,95 (0,97) | 0,56 (0,71) | 0,01 (0,05) |
| 8 × 4 | 32 | 1,00 (1,00) | 0,99 (0,99) | 0,71 (0,80) | 0,01 (0,03) |
| 9 × 4 | 36 | 1,00 (1,00) | 0,99 (1,00) | 0,81 (0,86) | 0,02 (0,04) |
| 12 × 4 | 48 | 1,00 (1,00) | 1,00 (1,00) | 0,93 (0,95) | 0,02 (0,03) |

Estresse, ruído 0,14:

| Desenho | ≈0,72 | ≈0,60 | ≈0,54 | Nulo |
| --- | --- | --- | --- | --- |
| 6 × 4 | 0,99 (0,99) | 0,82 (0,86) | 0,31 (0,48) | 0,03 (0,07) |
| 8 × 4 | 1,00 (1,00) | 0,91 (0,91) | 0,47 (0,57) | 0,03 (0,05) |
| 9 × 4 | 1,00 (1,00) | 0,95 (0,95) | 0,50 (0,60) | 0,04 (0,05) |
| 12 × 4 | 1,00 (1,00) | 1,00 (0,99) | 0,65 (0,70) | 0,04 (0,04) |

## Como ler

- **Se o efeito novo for parecido com o observado,** qualquer desenho com 6 ou mais projetos tem poder perto de 1. O tamanho só pesa se o efeito encolher.
- **Para um efeito de cerca de 0,60:** 9 projetos × 4 requisitos (36 requisitos) dão 0,99, ou 0,95 no cenário de estresse. 8 × 4 dá 0,99, ou 0,91 no estresse.
- **Para um efeito de cerca de 0,55,** nem 12 × 4 garante 0,80 no estresse. Para detectar um efeito tão pequeno seria preciso outro desenho, com mais repetições ou mais projetos.
- **A regra IC sozinha erra demais com poucos projetos.** No nulo, ela aceita entre 3% e 7% dos estudos, quando o esperado para um limite unilateral de 95% seria 2,5%. Com 4 a 6 projetos, o bootstrap de clusters é anticonservador. A regra p ficou abaixo de 5% em todos os desenhos, mas o estimador avisa que a permutabilidade entre requisitos do mesmo projeto não está demonstrada. Isso pesa na decisão 5 em aberto e sugere exigir as duas regras juntas, com no mínimo 8 projetos, como já pede a seção 3 do pré-registro.
- **Custo:** com A, B e C, cada requisito custa 12 chamadas; sem B, 8. O desenho 9 × 4 custa 432 chamadas com B ou 288 sem B, na mesma ordem das 552 da coleta dos 46.

Recomendação para levar ao orientador: **9 projetos × 4 requisitos**, decisão pelas duas regras juntas, com o efeito mínimo de interesse declarado em 0,60. Abaixo disso, o estudo não tem poder e o pré-registro deve dizer isso.

## Limitações

- A população reamostrada é a própria amostra exploratória: 9 projetos e desfechos quase de tudo ou nada por requisito. Se os requisitos novos forem mais heterogêneos, o poder cai.
- Mais de 9 projetos são simulados repetindo projetos observados, então a variação entre projetos fica subestimada nas colunas de 12 projetos.
- O ruído tem um único parâmetro (inversões simétricas) e não modela requisitos inteiros que se invertem.
- A média simulada (≈0,74) é um pouco maior que a estimativa amostral (0,725). Isso acontece porque o sorteio em dois estágios dá peso igual aos projetos.
