# Emenda de limite, autorizada durante a coleta

Em 06/10/2026, depois do início, o usuário autorizou: “pode zerar a de 5 horas”. A reserva das demais janelas continua em 30%, incluindo a semanal e quaisquer janelas específicas de modelo. Uso extra não é autorizado. A parada ocorre entre chamadas; uma chamada pode cruzar o limiar, e limite/erro remoto interrompe sem retry.

O pacote anterior e seus scripts e recibos ficam intactos. Depois da parada original por quota, uma continuação explicitamente autorizada copia uma visão vinculada por hashes, conserva os slots concluídos e só tenta aqueles sem recibo de tentativa anterior. Não repete falhas, não muda textos, ordem, fontes ou modelos. Um novo manifesto registra a emenda e a origem de cada importação. Não é restart do coletor congelado nem nova replicação independente; integra o mesmo lote interrompido.

Contrato BDD: com 1% da janela de cinco horas e >30% nas demais, permite o próximo slot; com 0%, reserva semanal atingida, janela expirada ou informação ausente, impede. Toda tentativa anterior é excluída da fila, inclusive se tiver falhado; falha ou recibo ambíguo anterior impede preparar esta continuação. Diretório novo e marcador exclusivo impedem uma segunda execução.

Testes de política/schedule e regressões passam. Preparação verificará hashes de scripts/CLI/páginas e suites prontas. Só executar Docker depois dos 300 slots concluídos. Slots ainda não tentados são pendentes, não falhas de geração. Alteração pós-início precisa constar no relatório exploratório.

Verificação: 53 testes passaram nesta sessão, compilação e diff check aprovados. A revisão identificou e corrigiu a falta de frescor no lançamento da continuação: timestamp de quota congelado e recusa após 15 minutos antes de qualquer tentativa.
