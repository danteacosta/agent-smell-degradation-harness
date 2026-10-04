# H1b: intervalos com quadratura adaptativa e perfil verificado

Status: exploratório, sem novas gerações. **Análise de sensibilidade**: o intercepto de projeto é fixado em 0. Isto não valida o modelo pré-registrado de dois interceptos; é o modelo reduzido com verossimilhança precisa. Usa as mesmas 178 linhas do `design.csv` da validação lme4 (#164). Script: `scripts/h1b_agq.py`. Saída: `data/selection-abc-results/20261003/h1b-agq.json`.

## Por que outro estimador

A validação no lme4 reproduziu os coeficientes do #163, mas o perfil falhou nos dois modelos: a busca encontrou uma deviance menor que a do próprio ajuste. Três coisas tornam o modelo pré-registrado difícil de perfilar:

1. **A variância de projeto fica na fronteira (0).** O ajuste pré-registrado é singular. Fixar essa variância em zero dá a mesma verossimilhança máxima de Laplace, mas a escolha é uma análise de sensibilidade: com outra aproximação ou outros dados a variância poderia sair da fronteira, e os intervalos abaixo não substituem os do modelo pré-registrado.
2. **Laplace é imprecisa aqui.** Há cerca de 4 execuções por requisito e o desvio-padrão do requisito fica perto de 5. Com os mesmos parâmetros, a log-verossimilhança de Laplace (1 nó) é −71,69, contra −69,80 na integração numérica direta. A quadratura de Gauss-Hermite adaptativa converge para esse valor: −69,8096 com 25 nós, que é o máximo do lme4, −69,8036 com 50 e −69,80348 com 100, igual à integração direta até 1e-5. O padrão adotado é 100 nós.
3. **`numeric` tem separação.** O termo é constante dentro de cada requisito, e as 16 execuções dos 4 requisitos numéricos violaram a regra. Quando β_numeric → +∞, esses quatro requisitos contribuem com verossimilhança 1, qualquer que seja o resto. O supremo do modelo completo é, então, exatamente o ajuste nos outros 42 requisitos sem o termo `numeric`. Os perfis dos demais termos são calculados ali, e `numeric` recebe só o limite inferior.

Convergência e perfil (corrigidos depois da revisão do #165):
- um ajuste só conta como convergido se o maior valor absoluto do gradiente numérico (diferenças centrais) for menor que 1e-3 e os parâmetros estiverem longe dos limites da busca; o sinal de sucesso do otimizador não entra na decisão;
- um limite de perfil só é reportado se todos os ajustes condicionais usados para cercá-lo e localizá-lo convergiram, e se a mudança de sinal se confirma em torno da raiz; caso contrário, o limite fica nulo com o motivo "refused";
- se algum ajuste condicional supera o ajuste completo, o modelo é reajustado a partir desse ponto e **todos** os intervalos são recalculados contra o novo máximo (até três vezes; depois disso, todos são recusados);
- um limite não encontrado é rotulado como "busca esgotada até |Δlog OR| = 15, sem mostrar que é infinito"; só `numeric` é "ilimitado (separação)", por argumento analítico.

Na saída final, os dois ajustes convergiram (gradiente máximo 2×10⁻⁷ e 1×10⁻⁶), nenhum reajuste foi necessário, e todos os limites finitos têm bracket confirmado.

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

- Com a verossimilhança correta, **nenhuma das três covariáveis estimáveis tem intervalo que exclua 1**. O intervalo de `memorized` [0,011; 0,98] do #163 muda para [0,015; 1,03] nesta análise de sensibilidade. A comparação muda também o tratamento do efeito de projeto e a otimização; ela não isola a causa dessa diferença.
- `numeric`: o limite inferior de 62 é o único resultado com intervalo inteiramente acima de 1. Ele vem de 4 requisitos e de uma separação completa. Deve ser lido como "todas as regras numéricas da amostra falharam em C", não como uma estimativa de tamanho de efeito.
- `derived_state` aponta contra a previsão de H1b, como você corrigiu no #164.
- Os intervalos muito largos refletem 42 a 46 requisitos com desfechos quase binários por requisito. Não fiz análise de poder, então não afirmo nada sobre poder.

## Conferência no lme4

Feita por você com `validate_agq.R` (`glmer(..., (1 | case), nAGQ = 25)`, mesmo contêiner do #164), no modelo reduzido de 42 requisitos:

- coeficientes reproduzidos; a log-verossimilhança difere da `agq25_check` deste script em 6×10⁻⁸;
- perfis do lme4 convergiram: `context_cue` [0,000029; 2,98], `derived_state` [0,0000054; 6,94], `memorized` [0,014; 1,035]. Os três incluem 1, como aqui. As diferenças podem refletir o número de nós e detalhes numéricos ou de otimização; a concordância é aproximada, não identidade de todos os limites.

Duas implementações independentes concordam, portanto, nos coeficientes e nos intervalos do modelo reduzido. O modelo pré-registrado, com intercepto de projeto, continua sem intervalos perfilados validados.

## Testes

`tests/test_h1b_agq.py` cobre sete pontos:
- a AGQ-100 coincide com a integração numérica direta, enquanto Laplace se afasta;
- num efeito simulado, os dois limites do perfil têm bracket, cobrem o valor verdadeiro e caem exatamente no ponto de corte de χ²(1);
- um termo separado recebe só o limite inferior;
- um otimizador que declara sucesso sem chegar ao ótimo é marcado como não convergido, pelo gradiente;
- um perfil cujos ajustes condicionais não convergem tem o limite recusado;
- um perfil iniciado de um ajuste de referência não convergente é recusado antes da busca;
- quando o máximo inicial é subótimo, a análise reajusta e recalcula os intervalos, que coincidem com os do ajuste correto.

Os testes são pulados quando `numpy`/`scipy` não estão instalados.
