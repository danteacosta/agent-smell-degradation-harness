# Validação externa do ajuste de H1b

## Escopo e resultado

Reavaliação numérica dos mesmos 178 registros C avaliáveis, de 46 requisitos e nove projetos. Nenhuma geração nova, alteração de desfecho ou chamada a modelo. A saída original do #163 permanece preservada. O CSV público replica a seleção e a codificação de `design()` do estimador próprio.

Foi executado `glmer` com família binomial, `nAGQ=1`, interceptos por projeto e requisito, os quatro preditores e otimizador `bobyqa` (`maxfun=200000`). Também foi ajustada a sensibilidade sem `numeric`. O ambiente usa R 4.3.3 e lme4 1.1-35.1; o pacote inclui a receita Docker e o ID da imagem usada. A execução dos ajustes não teve rede.

| Modelo | log-verossimilhança lme4 | OR context_cue | OR derived_state | OR memorized |
| --- | ---: | ---: | ---: | ---: |
| Completo | -71,43412 | 0,00983 | 0,00618 | 0,14995 |
| Sem numeric | -76,37827 | 0,00804 | 0,00983 | 0,16608 |

Os coeficientes reproduzem as estimativas do #163. No modelo completo, `numeric` recebe um coeficiente de aproximadamente 24,89; sob separação, esse valor finito do otimizador não estabelece uma estimativa finita identificada. O desvio-padrão por requisito foi 4,758 no modelo completo e 5,456 na sensibilidade; o de projeto foi zero nos dois. Ambos retornaram aviso de ajuste singular.

## Intervalos ainda não validados

`confint(..., method="profile", parm="beta_")` falhou nos dois modelos, detectando nova deviance menor durante a busca: diferença de 0,0000493 no completo e 0,00117 sem `numeric`, contra tolerância padrão de 1e-9. As mensagens completas estão no JSON. Não foi relaxada a tolerância para obter um intervalo conveniente.

Portanto, esta comparação valida aproximadamente os coeficientes e a verossimilhança; não valida os ICs nem a afirmação de que `memorized` exclui 1. O estimador próprio também precisa distinguir esgotamento da busca finita de limite comprovadamente infinito, verificar convergência dos ajustes condicionados e recusar limites sem bracket válido. Essas correções de implementação permanecem pendentes; o relatório original agora explicita o estado provisório dos ICs.

A direção de `derived_state` é contrária à previsão de H1b. A falta de precisão não demonstra, por si, baixo poder para efeitos moderados: seria necessária uma análise específica de poder. H1a e os desfechos E2E não mudam. Esta reavaliação continua exploratória.

## Reprodução e custódia

Arquivos em `data/selection-abc-results/20261003/lme4-validation/`: `design.csv`, `validate.R`, `Dockerfile`, `lme4-validation.json` e `provenance.json` com hashes SHA-256 e commit de origem. O Dockerfile usa repositórios apt mutáveis; o ID registrado identifica a imagem efetivamente executada, mas uma reconstrução futura pode instalar versões diferentes.

```sh
docker build -t h1b-lme4-validation:20261004 data/selection-abc-results/20261003/lme4-validation
docker run --rm --network none -v "$PWD/data/selection-abc-results/20261003/lme4-validation:/evidence" h1b-lme4-validation:20261004 Rscript /evidence/validate.R
```

## Fontes primárias consultadas

- [lme4: glmer](https://lme4.github.io/lme4/reference/glmer.html): `nAGQ=1` usa aproximação de Laplace. Usar a mesma família de aproximação não garante os mesmos resultados de otimização.
- [lme4: confint.merMod](https://lme4.github.io/lme4/reference/confint.merMod.html): distingue intervalos por perfil, Wald e bootstrap. Esta validação tentou o perfil, preservando a falha.
- [lme4: convergence](https://lme4.github.io/lme4/reference/convergence.html): orienta inspeção de avisos e comparação de otimização. O código de saída do otimizador não elimina singularidade ou instabilidade do perfil.

Fontes consultadas em 04/10/2026. A documentação online pode corresponder a uma versão diferente da usada; versões efetivamente executadas estão no JSON.
