# Resultado: condição removida e violação observável

Data: 14/09/2026. Execução real pela assinatura ChatGPT/Codex, modelo solicitado
`gpt-5.6-luna`, CLI `0.154.0-alpha.6.2`. O snapshot do modelo não é exposto pelo
stream. Escopo: demonstração exploratória com três contratos originais.

## Resultado completo

| Política original | Completa: passou | Condição removida: passou | Condição removida: falhou |
|---|---:|---:|---:|
| Autorização | 3/3 | 3/3 | 0/3 |
| Desconto com teto | 3/3 | 0/3 | 3/3 |
| Token: validade e reuso | 3/3 | 3/3 | 0/3 |
| Total | 9/9 | 6/9 | 3/9 |

Foram 18 episódios, nove pares completos, sem episódios ausentes ou falhas
de execução. A diferença descritiva de violações foi 3/9 = 33,3 pontos
percentuais. São três intenções de um único conjunto original; as repetições
não criam nove intenções independentes. Não há intervalo populacional nem
decisão de hipótese. Autorização e token são resultados nulos preservados.

## Contraexemplo concreto

Requisito completo: “For a nonnegative purchase total, return a discount equal
to 10% of the total. Cap the discount at 7.”

Variante: “For a nonnegative purchase total, return a discount equal to 10%
of the total.” A única remoção é a frase do teto. Interface e instruções de
geração são idênticas. O modelo não recebeu os testes nem a outra variante.

Código real da primeira repetição completa:

```python
def evaluate(total):
    return min(total * 0.1, 7)
```

Código real da primeira repetição com condição removida:

```python
def evaluate(total):
    return total * 0.1
```

Teste congelado antes da geração: `evaluate(100)` deve retornar `7`.
A variante retorna `10.0`. Compila e executa, mas viola a intenção completa.
As três repetições reproduziram a violação. O programa satisfaz o texto
abreviado que recebeu: o defeito é relativo ao contrato completo congelado,
não uma prova de que o modelo desobedeceu ao prompt abreviado.

## Proveniência e verificação

- Run: `codex-original-demo-20260914-v2`.
- Ordem aleatória congelada com seed 20260914; três repetições por variante.
- Mesmo oráculo em ambas as variantes; testes de valores 0, 50, 70 e 100
  para desconto. Casos abaixo e no teto preservam a regra comum.
- 78 arquivos vinculados no recibo; hashes verificados após a execução.
- Respostas do modelo não foram corrigidas manualmente.
- Executor Linux ARM64, Python 3.12, imagem por digest, sem rede, filesystem
  somente leitura, usuário não privilegiado, capacidades removidas, limites
  de memória/CPU/processos e allowlist AST. Cinco controles passaram antes
  da geração. Isso não constitui prova universal de segurança do sandbox.
- Uso observado nos 18 episódios: 217.267 tokens de entrada (51.456 em cache)
  e 1.248 tokens de saída; 708 tokens de raciocínio informados separadamente
  pelo CLI. Não somar subcategorias sem a semântica do provedor.
- Billing mode: `chatgpt_subscription`; custo USD indisponível. Não houve
  fallback para chave Platform. Os smokes de integração anteriores são
  separados dos 18 episódios; três tentativas foram rejeitadas por aviso
  de configuração e uma confirmou a conexão. Não entram nos denominadores.
- A primeira tentativa de coleção falhou no pré-check Docker e não iniciou
  geração. Seu manifesto foi preservado, sem reescrever a execução bem-sucedida.

Os dados completos permanecem privados no workspace, em
`.private-research-evidence/codex-original-demo-20260914-v2`, incluindo
manifesto, plano, prompts, respostas, relatórios por episódio e análise.

## O que este resultado permite afirmar

Existe um exemplo reproduzido nesta execução em que remover uma condição do
requisito resulta em código que viola essa condição, embora rode normalmente.
Também existem dois exemplos sem efeito observado. Isso demonstra a utilidade
do contraste pareado e do teste comportamental independente da forma do código.

Não demonstra frequência de bugs em projetos reais, eficácia de detector,
H1/H2 confirmatórias, diversidade de providers ou validade dos pares ARTA.
O teto de 7 é uma política original explícita, não uma interpretação de fonte
externa. O próximo passo acadêmico continua sendo validar os pares reais e os
oráculos antes de ampliar a coleta. A quarentena original não foi removida.
