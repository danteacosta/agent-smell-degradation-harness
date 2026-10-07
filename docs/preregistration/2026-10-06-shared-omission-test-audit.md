# Auditoria cega dos testes da omissão compartilhada (#184)

Status: protocolo congelado antes de qualquer suíte ser aberta. Exploratório e descritivo. Não altera os resultados publicados no #184 nem os reclassifica.

## Pergunta

O #184 mostrou que as suítes escritas a partir do pedido incompleto, com ou sem o código do mutante, quase não detectam a perda confirmada da regra. Esta auditoria pergunta **como** a perda escapou:

- **Grupo P (passes indevidos).** A suíte aprovou a referência correta e o mutante mostrado ao braço com código. O teste ignorou a regra, não chegou à condição dela, ou chegou e não verificou o que importa?
- **Grupo R (rejeição da referência).** A suíte reprovou a implementação correta. A asserção que falha exige a violação da regra omitida (o teste fixou o defeito), exige um detalhe que o requisito não determina, contradiz outra parte do requisito, ou o teste está quebrado?

## População

Fixada só a partir dos dados públicos (`scripts/test_omission_audit.py frame`, arquivo `data/shared-omission-e2e/v1/test-audit/audit-frame.json`), antes de abrir qualquer suíte:

| Grupo | Completa | Incompleta | Incompleta + código mutante | Total |
| --- | ---: | ---: | ---: | ---: |
| P: quieta na referência e no mutante mostrado | — | 35 | 17 | 52 |
| R: alarme (asserção ou erro) na referência correta | 11 | 11 | 30 | 52 |

Todas as suítes que cumprem cada critério entram; não há amostragem. A fonte completa não tem nenhuma suíte no grupo P. O grupo P usa o mutante mostrado ao braço com código (`selected_mutants`, semente 2026100508) também para a fonte incompleta, para que os dois braços sejam comparados na mesma página.

As 30 suítes do grupo R com código são o alvo principal. As da fonte incompleta e completa servem de comparação: sem elas, não se distingue "o código mudou a forma de errar" de "os testes erram assim em geral".

## Cegamento

- Os itens das três fontes são misturados e renomeados T001–T104 (semente 2026100609). A chave fica em `chave-privada.json`, no diretório privado, até o fim da adjudicação.
- A planilha mostra:
  - o requisito completo, com o trecho omitido entre `[[ ]]`;
  - o trecho isolado;
  - o código da suíte;
  - os nomes e resultados dos testes;
  - no grupo R, os testes que falharam na referência, com a mensagem.
- Nunca mostra o prompt recebido pelo testador nem o código que ele viu.
- O cegamento é imperfeito: uma suíte do braço com código pode citar ids ou funções do código mostrado. Por isso cada codificador registra, depois de codificar, um palpite sobre a fonte, e a taxa de acerto é publicada.
- Os codificadores não devem abrir `data/shared-omission-e2e/v1` nem o relatório do #184 antes de terminar.

## Livro de códigos

As definições literais estão em `CODES` no script e na aba de instruções. Se várias categorias se aplicam a testes diferentes, vale a primeira na ordem abaixo.

**Grupo P:**
1. `espera_violacao`
2. `assercao_insuficiente`
3. `nao_cria_condicao`
4. `nao_testa_regra`
5. `indeterminado`

**Grupo R:**
1. `exige_violacao_da_regra`
2. `contradiz_outra_parte`
3. `exige_detalhe_nao_especificado`
4. `teste_quebrado`
5. `indeterminado`

**Campos nos dois grupos:**
- `menciona_regra` (sim/não);
- `citacao`: trecho literal do código da suíte. O `score` recusa citação que não esteja na suíte. É obrigatória exceto em `nao_testa_regra` e `indeterminado`.
- `palpite_fonte`;
- `comentario`.

## Calibração (acrescentada em 06/10, antes de abrir qualquer suíte)

Antes da auditoria, os dois codificadores fazem uma calibração com 6 suítes de outro testador, o Claude Opus 4.6 (#190): 3 do grupo P e 3 do grupo R. Elas são sorteadas com semente 2026100612, só a partir dos dados públicos (`calibration-frame.json`).

- Cada codificador codifica as 6 suítes sozinho. Depois os dois discutem as divergências, só sobre o significado das categorias. A conversa não pode antecipar itens da auditoria.
- As suítes de calibração não entram no resultado, e o livro de códigos não muda depois dela. Se a discussão mostrar uma categoria ambígua, a ambiguidade e a decisão tomada são registradas antes de abrir a planilha da auditoria.
- Os itens ficam numerados C001–C006, numa planilha separada (`calibration-sheet`). Uma eventual auditoria posterior das suítes do Opus 4.6 exclui esses seis.

## Codificação e adjudicação

1. Dois codificadores humanos, sem acesso às respostas um do outro. O primeiro é o autor; o segundo é alguém indicado pelo orientador. Modelos não codificam.
2. Concordância bruta e kappa de Cohen por grupo, sobre os itens codificados pelos dois.
3. Divergências são resolvidas por discussão, numa terceira planilha (`--adjudicated`). Os rótulos individuais permanecem publicados ao lado do final.
4. Se o kappa de um grupo ficar abaixo de 0,40, o livro de códigos é revisado e o grupo é recodificado do zero. A primeira codificação e o motivo da revisão são publicados.

## O que será reportado

Por grupo e por fonte:
- contagem por categoria;
- número de requisitos e projetos por categoria;
- número de suítes que mencionam a regra.

As duas suítes do mesmo requisito não são independentes, e não há teste de hipótese.

Leituras fixadas antes de abrir as suítes:

- **Fixou o defeito.** "O braço com código fixou o comportamento defeituoso" só será afirmado se `exige_violacao_da_regra` for a categoria mais frequente entre as 30 suítes R com código, cobrindo pelo menos metade delas e aparecendo em requisitos de pelo menos quatro projetos. Também precisa ser rara nas suítes R da fonte incompleta.
- **Detalhe incidental.** Se a maioria das 30 for `exige_detalhe_nao_especificado`, a leitura é que o testador copiou detalhes incidentais do código mostrado, não a violação da regra.
- **Teste quebrado.** Se a maioria for `teste_quebrado`, a rejeição da referência é ruído de construção.
- **Grupo P.** A distribuição entre `nao_testa_regra`, `nao_cria_condicao` e `assercao_insuficiente` é comparada descritivamente entre as fontes incompleta e com código. Uma diferença de forma não é evidência causal do efeito do código.

## Custódia

- `sheet` roda no Mac sobre o diretório privado do estudo. Antes de montar a planilha, confere que os resultados privados são idênticos aos publicados.
- A planilha e os arquivos `.cjs` ficam no diretório privado.
- O `score` verifica o hash de cada suíte antes de aceitar citações.
- No repositório entram apenas:
  - o quadro;
  - a chave (depois da adjudicação);
  - os rótulos;
  - as concordâncias.

  O código das suítes, os prompts e as páginas continuam privados.

## Limites

- A população é condicionada a resultados já conhecidos.
- Há um único testador.
- As categorias descrevem a suíte, não a intenção do modelo.
- O autor do estudo é um dos codificadores; o segundo codificador e a publicação dos rótulos individuais reduzem, mas não eliminam, esse viés.
