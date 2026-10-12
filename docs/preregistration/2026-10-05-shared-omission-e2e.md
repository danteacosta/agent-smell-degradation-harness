# Extensão E2E: omissão compartilhada e código do próprio mutante

Status: protocolo prospectivo para novas suítes, após conhecimento do #180. Exploratório para a tese, sem confirmação de H1/H2. Autorização: pesquisador escolheu E2Es primeiro, sem implementar agentes com ferramentas.

## Contrato científico

São os mesmos 25 requisitos elegíveis em oito projetos e as mesmas 191 páginas do estudo de adequação, vinculadas aos resultados e recibos anteriores. Nenhuma implementação nova. Por requisito, selecionar um mutante confirmado entre os 81 com `Random("2026100508:<case>")` sobre IDs ordenados, sem examinar quais testes o mataram no #180. A referência correta anterior é mantida. A escolha do mutante é metadado privado e público, nunca label no prompt.

Coletar contemporaneamente duas suítes de cada fonte: requisito completo + scaffold; pedido incompleto + scaffold; pedido incompleto + código do mutante selecionado. São 150 chamadas novas do gpt-6-astra, sem retry/reparo, ordem sorteada com semente 2026100508, 1.146 pares planejados. As chamadas e falhas anteriores não são reaproveitadas nem substituídas. A chave legada `code_incomplete` é explicitamente rotulada no manifesto como código mutante, não referência correta.

## Desfechos e decisão

Preservar o estimador do estudo anterior: média de duas suítes por requisito, depois peso igual por requisito. Suíte utilizável e quieta na referência correta é elegível para matar um mutante. Falhas permanecem com zero no denominador. MA1 completa menos incompleta é principal; MA2 completa menos incompleta com código mutante é secundária. Suporte local exige conjuntamente bootstrap de projetos (4.000) com limite inferior acima de zero e teste bilateral exato de sinais por projeto p<0,05. Não remover projetos/requisitos ou mudar desfechos após resultados. MA2 não pode substituir MA1 se esta não sustentar a previsão.

Descritivo adicional: para o mutante selecionado, contar quietude observada da suíte e quietude entre suítes elegíveis. Esta é falsa segurança operacional perante perda já confirmada, não frequência populacional de falsa confiança nem prova psicológica de confiança. Relatar denominadores, erros/asserções, geração falha e taxas condicionadas e incondicionais de alarmes em outras A corretas e C recuperadas. Repetições não são unidades independentes.

## Custódia e aceitação

Given páginas vinculadas aos hashes publicados, When preparo o novo pacote, Then todos os prompts, papéis, selecionados e hashes de scripts/runner/imagem são congelados antes das chamadas. Mudança de código, página ou prompt deve impedir geração/execução. Given pacote já iniciado, When tento repetir, Then a execução é recusada. Given falha de geração, Then nenhum retry e nenhum sucesso fictício. Given mutante confirmado, Then o código enviado ao braço de código corresponde a esse mutante e nunca à referência correta. O teste de regressão deve comprovar essa fronteira.

Os três controles de navegador devem qualificar o runtime antes de qualquer chamada. Verificar 150 tentativas, relatórios reais versus placeholders e integridade ao terminar. Publicar somente resultados estruturados, manifesto sem caminhos e relatório, sem respostas/páginas privadas.

## Limites e ferramentas futuras

Seleção baseada em perdas conhecidas, oito projetos, um testador do mesmo provedor, duas suítes por fonte e scaffold simplificado permanecem limitações. O #180 continua separado. Para ferramentas, apenas registrar um desenho futuro: policies públicas/licenciadas, obrigações congeladas, ações/estado independentes e contraste entre evals completos/incompletos; não implementar ou executar esse domínio agora.
