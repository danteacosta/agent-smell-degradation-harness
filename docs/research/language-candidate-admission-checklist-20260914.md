# Próxima etapa: admissão dos candidatos de linguagem

Rascunho operacional após o [piloto construído](codex-language-controls-results-20260914.md).
Não contém rótulos humanos, não admite casos ao corpus e não substitui o
charter de anotação confirmatória existente. Nenhum convite foi enviado.

## Preparação reproduzível dos formulários

Execute `python -m eval.language_review --output NOVO_DIRETORIO_PRIVADO --seed 20260914`.
O diretório pai deve existir. O comando gera seis formulários de quatro itens,
com um texto de cada grupo por formulário e dez textos únicos no conjunto.
Entregue a cada leitor somente um formulário; nunca a pasta inteira ou o
conteúdo de `custodian/`. Registre a atribuição e a exposição anterior antes de
congelar respostas individuais. Somente depois faça a revisão comparativa.

O recibo verifica os arquivos e mantém participantes e rótulos humanos em zero.
As 24 posições nos formulários não são novas observações nem uma recomendação
de tamanho amostral. Rubrica, independência, responsáveis e distribuição ainda
precisam ser definidos; a preparação não valida nem admite os candidatos.

## O que a revisão independente deve decidir

1. **Coordenação:** a frase sem parênteses admite os dois agrupamentos no
   contexto fornecido? A convenção de precedência lógica do público elimina
   a ambiguidade ou apenas favorece uma leitura? Justificar a categoria e
   registrar se a construção é artificial demais para o domínio pretendido.
2. **Pronome:** quais antecedentes de “it” são plausíveis? A frase permite
   referência à dupla ou ao vínculo? Não forçar a escolha entre somente
   remetente e destinatário: registrar leituras adicionais e decidir se a
   lista de alternativas precisa ser ampliada em uma coleta futura.
3. **Controles:** as duas redações preservam o comportamento em todo o domínio
   declarado? A forma complementar é um controle de redação suficiente ou
   exige um controle lexical distinto para estudar a categoria da literatura?
4. **Pistas e fidelidade:** os nomes de argumentos favorecem alguma leitura?
   A intervenção muda somente o trecho declarado? O oráculo representa a
   intenção do autor sem inventar informação ausente no requisito observado?

## Registro por candidato, antes de novas gerações

| Campo | Conteúdo a registrar |
|---|---|
| Identidade | ID opaco, origem construída ou natural, projeto/intenções e grupo dependente |
| Contexto disponível | Requisito observado, interface e todos os anexos efetivamente visíveis |
| Definição | Categoria proposta, fonte primária, trecho exato e operação aplicada |
| Comportamento | Intenção de referência, domínio, tabela prevista e alternativas plausíveis |
| Decisão | Aceitar, revisar ou rejeitar; justificativa textual; incerteza preservada |
| Proveniência | Identificador do anotador, versão da rubrica, data e hash do pacote |

Os anotadores devem avaliar o material sem os resultados, código gerado ou
preferências do modelo. Os exemplos deste piloto já estão públicos no relatório;
um leitor exposto a eles não deve ser tratado como cego a esses itens. A equipe
precisa registrar exposição prévia e recrutar casos novos quando necessário.
O pacote de admissão de requisitos e o pacote de julgamento de artefatos têm
finalidades distintas; não reutilizar rótulos de um como desfecho do outro.

Preservar decisões individuais antes da adjudicação. Resolver desacordos com
justificativa e versionar qualquer mudança de oráculo ou categoria. Uma revisão
posterior não altera retroativamente o manifesto nem torna o piloto confirmatório.
Qualquer ampliação de alternativas ou ablação das pistas exige nova configuração,
novo manifesto e resultados separados.

## Critério para avançar

Somente após revisar os candidatos, definir a população e unidade de amostragem,
registrar participantes e papéis independentes e congelar o protocolo deve-se
dimensionar nova coleta. A amostra precisa variar projetos e intenções; aumentar
repetições ou entradas de teste não substitui essa diversidade. Não estimar
poder usando os gêmeos deste piloto como projetos independentes.
