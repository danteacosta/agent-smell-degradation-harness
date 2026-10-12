# Rascunho: testador de outro provedor sobre a omissão compartilhada

Status: **rascunho para discussão com o orientador. Não congelado e não autoriza chamadas.** Só deve ser congelado depois da auditoria dos testes (`2026-10-06-shared-omission-test-audit.md`) e da verificação de custo e acesso pelo Codex.

## Motivação

No #180 e no #184, os geradores das implementações (gpt-5.6-luna e gpt-5.6-sol) e o testador (gpt-6-astra) vêm do mesmo provedor. A ausência de detecção pode ter duas explicações:

- **Omissão compartilhada:** a regra que não está no pedido também não chega aos testes, porque nenhum modelo a infere.
- **Mesmo modelo, mesmo erro:** uma família de modelos tende a falhar do mesmo jeito.

Um testador de outra família, com tudo o mais fixo, separa as duas explicações.

## O que fica fixo

- Os 25 requisitos de 8 projetos e as 191 páginas congeladas do #180/#184, com as mesmas categorias do oráculo.
- O mesmo mutante mostrado por requisito (`selected_mutants`, semente 2026100508).
- Os mesmos textos de prompt das três fontes, byte a byte. O manifesto deve registrar o hash de cada prompt congelado do #184 e o teste deve conferir a igualdade.
- O mesmo runner, a mesma imagem, os mesmos três controles de navegador antes da geração.
- Duas suítes por fonte e requisito, ordem sorteada, sem retry, sem reparo.
- O mesmo escore principal, com detecção só por suíte quieta na referência correta e peso igual por requisito.

## O que muda

- O modelo testador, de outra família e de outro provedor, escolhido antes do congelamento pelo levantamento do Codex. Nome e versão exata ficam no manifesto.
- A semente da ordem de chamadas: 2026100610.

## Hipóteses de replicação

- **RA1:** completa − incompleta > 0.
- **RA2:** completa − incompleta com código mutante > 0.

Para cada hipótese, o critério é o mesmo do #184: limite inferior do IC 95% por bootstrap de projetos acima de zero e p bilateral exato por troca de sinais por projeto < 0,05. Com 8 projetos, o menor p possível é 0,0078.

| RA1 e RA2 | Leitura |
| --- | --- |
| Ambas satisfeitas | A explicação "mesmo modelo, mesmo erro" perde força para esse contraste. |
| Nenhuma satisfeita | O efeito pode ser específico do testador; o #184 passa a ser descrito como dependente do modelo. |
| Só uma satisfeita | Reportar como replicação parcial, sem escolher a comparação depois. |

## Análises descritivas fixadas

- Escores por fonte e diferença em relação ao #184, por requisito. É descritivo: não é uma comparação randomizada entre testadores.
- Tabela de veredito na referência × veredito no mutante mostrado, por fonte. O padrão de interesse é reprovar a referência por asserção e aprovar o mutante mostrado: 23/50 no braço com código do #184, 0/50 na fonte incompleta.
- Se a auditoria dos testes do #184 sustentar `exige_violacao_da_regra`, as suítes R com código desta rodada entram numa extensão da mesma auditoria, com o mesmo livro de códigos.

## Custo e limites

- Cerca de 150 chamadas e cerca de 1.150 execuções no navegador.
- Os requisitos continuam selecionados por resultados conhecidos.
- Este estudo não confirma H1 nem testa H2.
- Uma replicação com outro testador não substitui requisitos novos.
