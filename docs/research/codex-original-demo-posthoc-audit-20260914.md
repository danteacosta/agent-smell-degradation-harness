# Auditoria posterior dos 18 artefatos salvos

Executada em 14/09/2026. Zero novas chamadas ao modelo. São os mesmos artefatos
do [experimento original](codex-original-demo-results-20260914.md), reexecutados
em uma grade maior. Os novos testes foram definidos após conhecer os resultados
originais, congelados antes desta reexecução e mantidos em evidência separada.

## Resultado

Cada célula abaixo reúne três artefatos da mesma variante; verificações são
entradas de teste, não episódios ou observações independentes.

| Política | Entradas por artefato | Completa: passou / verificações | Condição removida: passou / verificações | Falhas |
|---|---:|---:|---:|---:|
| Acesso | 2 | 6/6 | 6/6 | 0 |
| Desconto | 203 | 609/609 | 216/609 | 393 |
| Token | 68 | 204/204 | 204/204 | 0 |
| Total | — | 819/819 | 426/819 | 393 |

Foram 1.638 verificações, 18 artefatos reexecutados e nenhum erro de execução.
Em cada um dos três códigos de desconto com condição removida, todos os 131
valores acima de 70 retornaram mais de 7. Os 72 valores restantes passaram.
As 393 falhas são violações do teto, não diferenças isoladas de arredondamento.
Não houve falhas numéricas adicionais nos artefatos completos. Isso sustenta
que o defeito desses códigos não se limita à entrada 100 do teste original.

O resultado da coleta original continua sendo 9/9 variantes completas e 6/9
variantes com condição removida aprovadas. Não transformar 393 falhas em 393
novos defeitos independentes, nem usar a frequência da grade como prevalência.

## Grade e comparação numérica

Acesso: os dois valores Booleanos. Desconto: inteiros de 0 a 200 inclusive,
mais 69,99 e 70,01. Token: idades inteiras de 0 a 30 inclusive, mais 14,5,
14,999 e 15,001, todas cruzadas com `used=False` e `used=True`. Nenhuma entrada
negativa, fora do domínio declarado, foi adicionada.

O valor esperado do desconto foi congelado como `min(total * 0.1, 7)` em
Python. O executor existente compara por igualdade exata. Como expressões
matematicamente equivalentes podem arredondar de modo diferente, cada falha
foi inspecionada: entrada acima de 70, retorno numérico acima de 7 e esperado
igual a 7. Não se está validando uma convenção financeira de arredondamento.

## Evidência e revisão

O executor isolado existente passou seus cinco controles antes da reexecução.
Foram usados o mesmo digest da imagem Linux ARM64, ausência de rede, filesystem
somente leitura, usuário não privilegiado, capacidades removidas e limites de
recursos. Código do modelo não foi executado diretamente no host.

Os 78 hashes do recibo original foram verificados antes e depois e permanecem
iguais. O novo bundle privado é
`.private-research-evidence/codex-original-demo-20260914-posthoc-audit`, com
manifesto da grade, controle do executor, 18 relatórios, resumo e recibo.
`analysis-script.py` e `verification.json` preservam a análise e a checagem
suplementar sem reescrever o recibo inicial da auditoria.

SHA-256 do recibo da auditoria:
`36c4027be3e1bc0c11b12583524641bd6848436707cd1ea9a2ac5fdc34aef710`.
SHA-256 do script:
`3aebc965f7f509d23323e6c60d408f60009599618885ce893c8495e6e881705e`.

Uma segunda revisão por assistente verificou o
[plano](../superpowers/specs/2026-09-14-paired-evidence-followup-design.md)
e levou à explicitação da comparação numérica antes da execução. Não constitui
validação humana independente. A
[matriz de dez entradas da literatura](2026-09-14-smell-coverage-and-construct-validity.md)
separa cobertura bibliográfica de cobertura experimental; continuam sendo três
intenções, uma intervenção e uma configuração de modelo. H1/H2 não foram
testadas. As pistas da interface e os resultados nulos permanecem declarados.
