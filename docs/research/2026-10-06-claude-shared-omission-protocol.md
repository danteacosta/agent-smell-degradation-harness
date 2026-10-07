# Replicação exploratória: omissão compartilhada com Claude

Autorização: executar pelo Claude Sonnet/Opus e parar em 30% de cota restante. Não é coleta confirmatória nem substituição de dados anteriores. Usa as mesmas 25 regras, oito projetos, páginas, prompts, fontes e seleção de mutantes do protocolo eec5110. O braço com código continua recebendo o mutante confirmado, nunca a referência correta.

Plano/contrato: importar o script histórico sem alterações; verificar os recibos e páginas; qualificar novamente os três controles Docker; copiar os 150 prompts byte a byte para cada modelo em pacotes novos; congelar script/adapter/CLI/modelos/ordem intercalada e limite; executar uma tentativa por slot; avaliar as suítes no mesmo runner e analisar cada modelo separadamente. Dois modelos × 150 chamadas = 300, até o limite autorizado. Os 1.146 pares por modelo incluem implementações corretas, mutantes e recuperadas.

Aceitação BDD: dado saldo válido acima de 30%, quando uma chamada termina, preservar resposta e quota observada; dado saldo de 30% ou menor em qualquer janela, janela expirada, quota ausente/inválida ou uso extra, recusar a próxima chamada e registrar progresso. Não estimar cota por tokens. Uma falha ambígua de geração interrompe o lote para inspeção, sem retry. Slot não tentado não vira falha gerada. Nenhuma mudança em prompts/resultados privados anteriores ou scripts congelados.

Limite operacional: a quota é observada nos eventos `rate_limit_event` do CLI, conferidos nas qualificações locais (17% usado em cinco horas e 3% semanal). A parada ocorre entre chamadas; uma chamada em curso e uso concorrente de outras sessões podem atravessar o limiar. Portanto não se promete reserva exata de 30%. Ausência de novo sinal implica parada. Recibo inicial deve ter menos de 15 minutos e as janelas não podem ter expirado. Consulta UI estava sem sessão; nenhum token foi extraído para chamar endpoint privado.

Validação: testes de saldo no limiar, valores inválidos/ausentes, uso extra, janela expirada, ordenação e ausência de repetição; regressões dos adapters; controles de navegador antes da coleta. Revisão de privacidade e código antes de congelar. As respostas, suites e caminhos das páginas permanecem privados; publicação posterior apenas agregados/recibos sanitizados por modelo.

A comparação principal replica requisito completo versus pedido incompleto; comparação secundária usa pedido incompleto+código do mutante. Preservar MA1/MA2, ponderação igual por requisito, bootstrap e teste exato por projeto, discriminação e alarmes falsos com denominadores. Auditoria humana e H1/H2 não são aprovadas por esta execução.

Referências técnicas: [status line e cota oficial](https://code.claude.com/docs/en/statusline), [limites compartilhados](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work). O campo documentado da status line difere do formato observado em stream-json; o parser desta execução registra a evidência de compatibilidade com CLI 2.1.285 e falha fechado.

Pré-lançamento: 51 testes passaram; controles reais do Docker 3/3 qualificados. Revisão encontrou que janelas adicionais eram descartadas; corrigido para exigir as duas observadas e validar todas as janelas expostas, incluindo a cota específica de modelo. Raiz do pacote criada explicitamente 0700.
