# Auditoria de requisitos antes do merge: rascunhos para validação

Atualizado em 07/10/2026. Pitch, post e roteiro são rascunhos internos. Não houve publicação, entrevista ou validação comercial. Este documento atualiza o [protocolo de piloto](product-pilot.md) e o [recorte de mercado de setembro](research/2026-09-24-premerge-requirement-audit-market-check.md).

## Pitch para entrevistas

Times que usam agentes de código implementam e testam a partir de tickets. Uma obrigação da especificação pode desaparecer do ticket, e os testes produzidos a partir dele podem herdar essa omissão. Queremos validar uma auditoria antes do merge que compare a referência escrita com a implementação e os testes, apontando regras violadas e regras sem cobertura, com evidência para o revisor.

A promessa está **a validar**. Precisamos medir, por regra, a detecção de uma perda confirmada e os falsos alarmes em implementações corretas ou recuperadas. Um comentário plausível do auditor não basta para contar uma detecção. O uso inicial proposto é em modo de observação, com decisão humana e registro de tempo de revisão, retrabalho e alertas descartados.

## Evidência que pode entrar na conversa

Adequação de mutação confirmada, com peso igual por requisito; um mutante só conta como detectado quando o teste permanece quieto na referência correta:

| Testador observado | Requisito completo | Pedido incompleto | Pedido incompleto + código do mutante mostrado |
| --- | ---: | ---: | ---: |
| Astra, estudo #184 | 0,760 | 0,100 | 0,040 |
| Sonnet 4.6, estudo #190 | 0,400 | 0,050 | 0,000 |
| Opus 4.6, estudo #190 | 0,800 | 0,085 | 0,000 |
| Sonnet 5.5, estudo #195 | 0,860 | 0,170 | 0,060 |
| Opus 5.5, estudo #196 | 0,940 | 0,263 | 0,177 |

Fontes: [Astra #184](https://github.com/danteacosta/agent-smell-degradation-harness/pull/184), [4.6 #190](https://github.com/danteacosta/agent-smell-degradation-harness/pull/190), [Sonnet 5.5 #195](https://github.com/danteacosta/agent-smell-degradation-harness/pull/195) e [Opus 5.5 #196](https://github.com/danteacosta/agent-smell-degradation-harness/pull/196). Os resultados 5.5 ainda estão em PRs separados, sem merge. Cada modelo recebeu 150 slots; Sonnet 5.5 preserva uma falha de geração, sem repetir a tentativa. Os relatórios registram a interrupção de conexão e a continuação autorizada dos slots não tentados.

Os 5.5 repetiram a diferença entre referência completa e pedido incompleto neste desenho, mas seus escores com código foram maiores que os de 4.6. No braço com código, a combinação “alarme de asserção na referência correta e quietude no mutante mostrado” ocorreu em 24/50 suítes Sonnet 5.5 e 10/50 Opus 5.5. Isso descreve esses testadores e contextos; não permite dizer universalmente que trocar de modelo não resolve.

São estudos exploratórios sobre os mesmos 25 requisitos de oito projetos, com páginas e mutantes reutilizados e um provedor gerando código. Repetições e modelos não acrescentam projetos independentes. Não são uma avaliação de produto em PRs reais, um ranking de modelos, nem confirmação de H1/H2. A auditoria humana continua pendente.

A afirmação sustentada é que **testes escritos a partir de um pedido incompleto podem herdar a omissão**. Ler o requisito completo junto com código defeituoso não foi avaliado neste braço de 25 requisitos. O diagnóstico de três requisitos/11 falhas não comprova o resgate pela ferramenta proposta; essa lacuna pertence à [proposta fatorial #183](https://github.com/danteacosta/agent-smell-degradation-harness/pull/183), que permanece aberta e não foi lançada.

## Post de mercado — rascunho, não publicado

Um PR pode passar nos testes e ainda perder uma regra que estava na especificação. Quando o ticket omite a regra, os testes gerados a partir dele podem repetir a lacuna.

Em estudos exploratórios com 25 requisitos de oito projetos, os testadores observados detectaram mais mutantes quando receberam a referência completa. Sonnet e Opus 5.5 também mostraram esse contraste. Os números variam entre modelos e contextos; usamos as mesmas páginas e não medimos uma ferramenta comercial em equipes reais.

Estamos investigando uma auditoria antes do merge que use a referência escrita para apontar regras violadas ou sem cobertura. A utilidade ainda precisa ser validada: quanto detecta, quantos alertas errados produz e quanto trabalho acrescenta ou evita para o revisor.

## Duas hipóteses de mercado

A hipótese principal são equipes usando agentes de código, com especificação escrita, tickets e revisão de PR. Procuramos episódios em que uma regra se perdeu e a suíte ficou verde, além de exemplos em que os testes ou a revisão já resolveram bem o problema.

A segunda hipótese são equipes com agentes conversacionais que precisam obedecer a uma política externa, como regras de atendimento. Uma resposta pode parecer aceitável e contrariar uma obrigação escrita. É uma analogia de mercado: esta bateria não traz evidência direta sobre agentes conversacionais. O piloto de normalização de traces descrito no protocolo continua uma possibilidade separada, sem prioridade comercial estabelecida.

## Roteiro de entrevistas

Começar pelo processo atual, antes de apresentar a proposta. Pedir casos próprios e permitir que a pessoa diga que não enfrenta o problema.

1. Onde ficam as regras que a implementação ou o agente deve seguir? Como elas chegam ao ticket, prompt, testes e revisão?
2. Conte o último caso em que uma regra escrita se perdeu. Para equipes de código: o PR estava verde? Para equipes conversacionais: qual política foi contrariada e em qual resposta?
3. Como o problema foi descoberto, por quem e em que momento? Houve casos em que a revisão ou os testes detectaram a perda antes de causar retrabalho?
4. Que evidência distingue a regra violada de um falso alarme? Pode mostrar um exemplo anonimizado de comportamento correto que uma checagem rejeitou?
5. Qual foi o custo em horas, atraso, incidente ou suporte? Quantos episódios semelhantes ocorreram no último mês ou trimestre?
6. Qual solução já usam? O que funciona e o que exige trabalho manual? Onde um novo alerta atrapalharia?
7. Quem revisaria o alerta, quem adotaria a ferramenta e quem aprovaria ou pagaria? Qual orçamento ou ferramenta concorreria por esse gasto?
8. Após descrever a promessa a validar: faria sentido um piloto em modo de observação? Que resultado mínimo justificaria continuar, e que taxa de alertas errados seria inaceitável?

Registrar frequência com janela e denominador, custo observado separadamente de estimativas, usuário separadamente de comprador e relatos negativos junto dos positivos. Não chamar erro de construção de teste “flaky”: instabilidade exige repetição própria, ausente desta bateria.

## Critérios para um futuro piloto

Congelar as regras e a referência antes da avaliação. Uma pessoa deve adjudicar a perda e o comportamento correto/recuperado independentemente do alerta. Relatar detecção de perda confirmada e falsos alarmes por regra, com denominadores e casos incertos separados; medir também tempo de revisão, retrabalho e custo. Começar sem bloquear merge e comparar com o processo atual. Nenhum desses resultados comerciais está demonstrado agora.

## Artefatos localizados e pendências

Foram localizados os documentos de piloto, limite tese/produto, roadmap e recorte de mercado no repositório. Buscas no Drive por pitch, mercado, entrevistas, kit, omissão, pre-merge e ancoragem encontraram documentos acadêmicos ou materiais de outros projetos; não identificaram um pitch/kit correspondente. Nenhum arquivo Drive foi editado. Este rascunho concentra os materiais para revisão futura.

As entrevistas, o piloto comercial, a calibração humana e a proposta fatorial permanecem pendentes. Este documento não autoriza mensagens, publicação de posts, novas chamadas ou coleta adicional.
