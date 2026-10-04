# H1b: regressão logística mista na coleta dos 46

Status: exploratório. A coleta tem `confirmatory_eligible: false`, e `context_cue` foi codificado depois da coleta (desvio na seção 7 do pré-registro). Os números vêm de `scripts/h1b_mixed_logit.py`, e a saída completa está em `data/selection-abc-results/20261003/h1b-mixed-logit.json`.

## Modelo (pré-registro, seção 5)

Violação da regra-alvo em cada execução C avaliável, com efeitos fixos `context_cue`, `numeric`, `derived_state` e `memorized` (do modelo da execução), e interceptos aleatórios por projeto e por requisito. A estimação usa a aproximação de Laplace da verossimilhança marginal, como o padrão do `glmer`. Os odds ratios vêm com intervalos de 95% de verossimilhança perfilada, sem correção de multiplicidade. As execuções com desfecho desconhecido ficam de fora: são 178 execuções, 105 violadas, 46 requisitos, 9 projetos.

## Resultado

| Termo | Odds ratio | IC 95% (perfil) | Observação |
| --- | ---: | --- | --- |
| `context_cue` | 0,010 | [≈0; 1,20] | inclui 1 |
| `numeric` | não finito | [47; ∞) | separação: as 16 execuções numéricas violaram; são só 4 requisitos |
| `derived_state` | 0,006 | [≈0; 2,41] | inclui 1 |
| `memorized` | 0,15 | [0,011; 0,98] | exclui 1 por pouco |

Desvio-padrão dos interceptos: requisito 4,8 (logit); projeto ≈ 0. Na sensibilidade sem `numeric`, `memorized` fica em 0,17 [0,011; 1,13] e passa a incluir 1. `context_cue` e `derived_state` mudam pouco.

## Como ler

- **A unidade que informa é o requisito.** O desvio-padrão de 4,8 diz que o resultado quase não varia entre as execuções do mesmo requisito: 20 dos 46 requisitos violaram em todas as execuções C e 15 em nenhuma. Os odds ratios condicionais ficam extremos e os intervalos, largos. Por isso, os limites inferiores perto de zero indicam falta de informação, não um efeito enorme.
- **Direções:** `context_cue`, `derived_state` e `memorized` apontam para menos violação, e `numeric` para mais. Só `memorized` tem um intervalo que exclui 1, e esse resultado não resiste à retirada de `numeric`. Com quatro requisitos, a separação em `numeric` é fraca como evidência, apesar de ser 16 de 16.
- **Nível do requisito (diagnóstico):**
  - com pista em C: 0,39 das execuções violadas em média, contra 0,63 sem pista (9 e 37 requisitos);
  - regra numérica: 1,00, contra 0,54 (4 e 42 requisitos);
  - `memorized`: 0,51 contra 0,63 (38 e 54 células requisito × modelo).

O ajuste pré-registrado não sustenta nenhum efeito de covariável com segurança. As direções observadas são compatíveis com H1b, mas este desenho, com 46 requisitos e desfechos quase binários por requisito, não tem poder para distinguir efeitos moderados. É o que o próprio pré-registro previa ("H1b is estimated, not powered for small effects").

## Validação do ajuste

Os testes em `tests/test_h1b_mixed_logit.py` cobrem três pontos:
- com variâncias aleatórias quase nulas, a verossimilhança coincide com a da regressão logística comum;
- num efeito simulado, a estimativa é recuperada com intervalo de perfil que o cobre;
- a separação é sinalizada em vez de estimada.

`numpy` e `scipy` não estão no lock base, e os testes são pulados quando faltam. Não houve comparação com `lme4`, porque não há R neste ambiente. Vale repetir o ajuste com `glmer` antes de qualquer texto final.
