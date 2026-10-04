# H1b: intervalos com quadratura adaptativa e perfil verificado

Status: exploratório, sem novas gerações. Usa as mesmas 178 linhas do `design.csv` da validação lme4 (#164). Script: `scripts/h1b_agq.py`. Saída: `data/selection-abc-results/20261003/h1b-agq.json`.

## Por que outro estimador

A validação no lme4 reproduziu os coeficientes do #163, mas o perfil falhou nos dois modelos: a busca encontrou uma deviance menor que a do próprio ajuste. Três coisas tornam o modelo pré-registrado difícil de perfilar:

1. **A variância de projeto fica na fronteira (0).** O ajuste é singular. Com essa variância em zero, o modelo sem o intercepto de projeto tem a mesma verossimilhança máxima, então o intercepto foi omitido.
2. **Laplace é imprecisa aqui.** Há cerca de 4 execuções por requisito e o desvio-padrão do requisito fica perto de 5. Com os mesmos parâmetros, a log-verossimilhança de Laplace (1 nó) é −71,69, contra −69,80 na integração numérica direta. A quadratura de Gauss-Hermite adaptativa converge para esse valor: −69,8096 com 25 nós, que é o máximo do lme4, −69,8036 com 50 e −69,80348 com 100, igual à integração direta até 1e-5. O padrão adotado é 100 nós.
3. **`numeric` tem separação.** O termo é constante dentro de cada requisito, e as 16 execuções dos 4 requisitos numéricos violaram a regra. Quando β_numeric → +∞, esses quatro requisitos contribuem com verossimilhança 1, qualquer que seja o resto. O supremo do modelo completo é, então, exatamente o ajuste nos outros 42 requisitos sem o termo `numeric`. Os perfis dos demais termos são calculados ali, e `numeric` recebe só o limite inferior.

O perfil agora tem verificações explícitas:
- cada ajuste condicional precisa convergir;
- um ponto do perfil acima do ajuste dispara um novo ajuste;
- um limite só é reportado com mudança de sinal confirmada (bracket);
- um limite ausente é rotulado como "não alcançado até |Δlog OR| = 15" ou, para `numeric`, "ilimitado (separação)".

## Resultado

Modelo completo (supremo em β_numeric, 42 requisitos, 162 execuções):

| Termo | Odds ratio | IC 95% (perfil, AGQ-100) | Previsão de H1b |
| --- | ---: | --- | --- |
| `context_cue` | 0,030 | [4,2×10⁻⁵; 2,97] | menos violação; inclui 1 |
| `derived_state` | 0,023 | [7,0×10⁻⁶; 6,91] | mais violação; a estimativa vai na direção contrária, e o intervalo inclui 1 |
| `memorized` | 0,159 | [0,015; 1,03] | menos violação; **inclui 1** |
| `numeric` | ilimitado | [62; ∞) | mais violação; só o limite inferior é identificado |

Desvio-padrão do intercepto de requisito: 4,90. Sensibilidade com os 46 requisitos e sem `numeric`: `context_cue` 0,040 [4,4×10⁻⁵; 5,63], `derived_state` 0,047 [1,7×10⁻⁵; 19,8], `memorized` 0,178 [0,016; 1,19].

Todos os limites finitos foram obtidos com bracket verificado e sem nenhum aviso. O teste confirma que, em cada limite, a deviance está no ponto de corte de χ²(1).

## Como ler

- Com a verossimilhança correta, **nenhuma das três covariáveis estimáveis tem intervalo que exclua 1**. O `memorized` [0,011; 0,98] do #163 era artefato da aproximação de Laplace; com integração adequada o intervalo vai a 1,03.
- `numeric`: o limite inferior de 62 é o único resultado com intervalo inteiramente acima de 1. Ele vem de 4 requisitos e de uma separação completa. Deve ser lido como "todas as regras numéricas da amostra falharam em C", não como uma estimativa de tamanho de efeito.
- `derived_state` aponta contra a previsão de H1b, como você corrigiu no #164.
- Os intervalos muito largos refletem 42 a 46 requisitos com desfechos quase binários por requisito. Não fiz análise de poder, então não afirmo nada sobre poder.

## Conferência no lme4

`data/selection-abc-results/20261003/lme4-validation/validate_agq.R` ajusta o mesmo modelo reduzido com `glmer(..., (1 | case), nAGQ = 25)` e tenta o perfil. Para comparar, a saída traz `agq25_check`: com 25 nós, log-verossimilhança −69,8096 e log-odds −3,488 (`context_cue`), −3,754 (`derived_state`) e −1,840 (`memorized`). Com `nAGQ = 25`, o lme4 deve reproduzir esses valores. Os intervalos de 100 nós podem diferir um pouco dos de 25.

Comando, no mesmo contêiner da validação:

```sh
docker run --rm --network none -v "$PWD/data/selection-abc-results/20261003/lme4-validation:/evidence" \
  h1b-lme4-validation:20261004 Rscript /evidence/validate_agq.R
```

## Testes

`tests/test_h1b_agq.py` cobre três pontos:
- a AGQ-100 coincide com a integração numérica direta, enquanto Laplace se afasta;
- num efeito simulado, os dois limites do perfil têm bracket, cobrem o valor verdadeiro e caem exatamente no ponto de corte de χ²(1);
- um termo separado recebe só o limite inferior.

Os testes são pulados quando `numpy`/`scipy` não estão instalados.
