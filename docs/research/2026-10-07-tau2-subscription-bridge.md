# τ²-bench com assinaturas Claude e ChatGPT

Estado: adaptador exploratório, validado com replay, sondagens de um turno por ChatGPT e Claude e uma tarefa completa ao vivo com Sonnet 5.5 nos dois papéis. Nenhuma coleta do estudo foi executada. A atualização automática de quota Claude foi verificada em três turnos; a estabilidade do envelope JSON e a orquestração em lote continuam pendentes. Não está qualificado para coleta.

O ponto de integração é a função de completion de [llm_utils.py no commit fixado](https://github.com/sierra-research/tau2-bench/blob/4ce7c0397c1eb65c9bbe59aeacfe1ca44a1cd699/src/tau2/utils/llm_utils.py). O wrapper substitui essa função somente durante um processo sequencial. As páginas de dados e o avaliador continuam no τ²-bench; o código upstream não é editado.

Cada turno leva o histórico completo, a política e os schemas das ferramentas ao CLI oficial em uma pasta temporária. O modelo devolve um envelope JSON com content e tool_calls; o wrapper o converte para a resposta esperada por LiteLLM. O protocolo tau2-subscription-json/v2 normaliza tool_calls null como ausência de ferramentas somente quando content contém texto não vazio; respostas vazias, ferramentas desconhecidas e violações de tool_choice continuam causando parada. As ferramentas do CLI permanecem desabilitadas: o τ²-bench executa as ações no ambiente simulado. Cada chamada recebe uma pasta de evidência nova, privada; o transporte oficial exige autenticação salva por assinatura e não encaminha chaves de API.

Agente e usuário podem usar Claude ou Codex independentemente, com identificadores de modelo explícitos. O avaliador mantém o padrão ALL. Um julgador LLM não cadastrado provoca parada, sem fallback para API nem retirada silenciosa de critérios. Esse caso precisa de qualificação específica antes de escolher tarefas que o exijam.

## Uso

Em um ambiente Python 3.12 (versão verificada: 3.12.14) com as dependências do τ²-bench fixado instaladas:

```sh
python -m scripts.tau2_subscription --tau2 /CAMINHO/tau2-bench --data /PASTA_PRIVADA/variantes/A
```

Esse comando verifica o checkout e os dados, sem carregar modelos ou gastar quota. A execução de uma tarefa exige --execute, --task-id, --agent-provider, --agent-model, --user-provider, --user-model, os caminhos dos CLIs usados, --quota, --out e --max-calls. Também exige --agent-windows e --user-windows com os nomes de TODAS as janelas expostas publicamente. Nada agenda lotes ou retoma automaticamente.

Antes da execução, ainda são necessárias revisão humana do inventário, definição com o orientador e autorização da sondagem. A adaptação técnica não libera o estudo.

## Quota e orçamento

--quota aponta para um JSON privado com telemetria pública oficial. Sem --refresh-claude-quota, ele precisa ser atualizado externamente. Com a opção, o runner atualiza as rotas Claude a partir dos rate_limit_event capturados pelo CLI depois de cada chamada; a primeira chamada ainda exige uma amostra oficial recente. Nunca preencher por estimativa, remover janelas expostas ou consultar credenciais/endpoints privados. Exemplo de formato (valores meramente ilustrativos):

```json
{
  "sampled_at": 1791370000,
  "routes": {
    "subscription-agent": {
      "status": "allowed",
      "extra_usage": false,
      "windows": [
        {"name": "five_hour", "remaining_percent": 50, "reset_at": 1791383400},
        {"name": "weekly", "remaining_percent": 70, "reset_at": 1791600000}
      ]
    }
  }
}
```

O arquivo real precisa incluir subscription-user também e eventuais janelas por modelo. Os nomes devem coincidir com a lista declarada nos argumentos. Sem atualização pública confiável, o wrapper para; não assumir que um arquivo antigo continua válido. A amostra não pode ter mais de 60 segundos. Antes de cada chamada, exige saldo positivo na janela de cinco horas quando ela é exposta e mais de 30% em todas as demais janelas expostas, incluindo a semanal, sem uso extra. --max-calls inclui os turnos dos dois participantes; não é quantidade de simulações.

A reserva é um limiar de parada antes da chamada, não garantia de saldo depois dela: o CLI não permite limitar tokens de saída e a telemetria pode atrasar. Esse limite precisa entrar na decisão de orçamento. A rotina externa de atualização não foi qualificada. A sondagem técnica Codex consumiu uma chamada, separada da análise do estudo.

## Limites do método

O transporte serializa papéis e ferramentas em texto; não equivale a tool calling nativo. O CLI adiciona seu próprio contexto de execução. Semente e temperatura do τ² não são controláveis pela assinatura; valores recebidos ficam registrados como não aplicados. Uma comparação de modelos exige o mesmo protocolo e uma sondagem separada. Tempo, tokens e disponibilidade são custos observáveis; custo USD permanece null, nunca zero fictício.

Timeout, saída inválida ou falha do provedor deixam recibo e param sem nova chamada. Regra de confirmação do estudo é outra tentativa planejada, não retry automático do transporte. A versão atual executa uma única tarefa por processo; a orquestração das milhares de simulações e retomadas por reset continua pendente.

## Verificação

Em 07/10/2026, 38 testes passaram, sem skips, com o checkout fixado 4ce7c0397c1eb65c9bbe59aeacfe1ca44a1cd699. Os testes nativos usaram τ²-bench 1.0.1, LiteLLM 1.82.6 e Python 3.12.14: conversão de ferramentas/uso/custo e uma tarefa airline com replay, execução real de ferramenta no ambiente e avaliação ALL. A tarefa mecânica não é um resultado científico nem demonstra sucesso na tarefa do benchmark. O preflight confirmou o commit e zero chamadas.

Uma sondagem separada por Codex CLI 0.157.0, modelo solicitado gpt-6-astra, retornou a ferramenta sintética esperada em uma única chamada por assinatura ChatGPT: 16.515 tokens de entrada, 26 de saída, 10,81 segundos e custo USD null. O snapshot do modelo não foi exposto. A telemetria pública disponível expunha apenas a janela semanal, com 93% restante; o gate foi corrigido e testado para exigir exatamente as janelas expostas, sem inventar a de cinco horas.

Em 08/10/2026, a sondagem local por Claude CLI 2.1.285, modelo solicitado e retornado claude-sonnet-5-5, devolveu a ferramenta sintética esperada através de ClaudeCLIProvider e do generate real do τ² em uma única chamada pela assinatura normal. O recibo registra 2 tokens de entrada sem cache, 755 tokens de criação de cache, 45 de saída, 2,07 segundos e custo USD null. O envelope e os argumentos da ferramenta passaram na verificação; as ferramentas nativas do CLI estavam desabilitadas. Isso qualifica um turno do transporte, não uma tarefa completa nem o estudo. Antes dessa chamada, a UI oficial indicava 73% restante na sessão e 61% na semana, sem uso extra; esses valores são históricos e não autorizam chamadas futuras.

A tentativa de continuar a qualificação de tarefa completa em 08/10 não iniciou chamadas: o controle do Safari foi interrompido ao consultar a quota atual. O saldo antigo não foi renovado por estimativa. A próxima execução depende de leituras oficiais recentes em todos os turnos, mantendo o gate de 60 segundos e a reserva nas demais janelas. Não houve retry de modelo ou fallback para API.

O upstream importa dependências de voz mesmo no modo texto. O ambiente recebeu essas dependências, exceto PyAudio (exige PortAudio de sistema e não foi necessário para estes testes), sem editar o upstream. Há um aviso de depreciação de audioop; Python 3.13 não foi validado. Evidências e respostas da sondagem ficam privadas.

## Créditos e sondagem na nuvem

Dante autorizou priorizar os créditos de sessão na nuvem. A interface oficial mostrou US$ 100 de US$ 100 restantes, com expiração em 5 de novembro às 04:59 BRT. Foi criada uma sessão Cloud Sonnet 5.5, usando somente o repositório público remoto e uma ferramenta sintética lookup, sem envio de evidência privada, comandos, alterações de arquivos ou coleta. Uma resposta devolveu o envelope esperado e passou no parser do adaptador. A atualização do saldo mostrou US$ 99 restantes; a precisão desse mostrador não permite atribuir um custo exato de US$ 1 à chamada. O uso normal continuou em 27% na sessão e 39% na semana.

Essa sondagem qualifica a resposta sintética na UI, não o transporte ClaudeCLIProvider nem uma tarefa completa do τ². O caminho [oficial de nuvem](https://code.claude.com/docs/en/claude-code-on-the-web) é assíncrono: `claude -p --cloud SESSION` envia uma mensagem, retorna a identificação e sai sem aguardar a resposta; `stream-json` não é suportado nesse modo. Portanto, adicionar `--cloud` ao transporte atual não fornece a resposta nem os tokens exigidos pelo recibo. Uma integração de nuvem precisa de captura por turno pela interface oficial, sem endpoints privados, uso inventado ou fallback silencioso para a assinatura local. Até isso estar implementado e qualificado, não lançar lotes. A sessão técnica e seus screenshots estão preservados privadamente.


## Qualificação ao vivo de uma tarefa em 08/10/2026

Dante autorizou continuar pela assinatura normal. A UI oficial indicou 95% restante na sessão e 99% na semana, com uso extra desligado. A consulta foi atualizada antes de cada chamada. O harness privado supervisionado aguardava uma nova amostra posterior ao pedido de cada turno e então aplicava o gate original de 60 segundos; o limite total era de 20 chamadas, sem alterar a política original A nem o avaliador ALL.

Uma primeira execução parou na verificação de autenticação, antes de qualquer chamada de modelo: dentro do sandbox, o CLI não reconhecia a sessão salva. `claude auth status` fora do sandbox confirmou a assinatura Pro pelo caminho oficial, sem extração de credenciais. Uma nova execução com pasta exclusiva iniciou a tarefa airline 0, com Sonnet 5.5 nos papéis de agente e usuário.

O recibo contém três chamadas únicas: duas completaram o contrato do adaptador e uma falhou. O usuário simulado iniciou a conversa e o agente solicitou `get_reservation_details`, que foi executada pelo ambiente real do τ². Na terceira chamada, o Claude devolveu conteúdo textual não vazio, mas `tool_calls: null`, contrariando o envelope que exige uma lista. O parser rejeitou a resposta e a simulação encerrou com ValueError. Não houve nova chamada, retry ou fallback; não há resultado da tarefa nem avaliação ALL concluída.

A sondagem mostra funcionamento parcial do transporte e execução de ferramenta, mas **não qualifica uma tarefa completa**. A próxima revisão precisa decidir explicitamente se mantém o envelope estrito ou normaliza a ausência de ferramentas como lista vazia quando há conteúdo válido. Essa mudança de contrato deve ser testada antes de uma nova qualificação autorizada; não aceitar silenciosamente a saída nem remover critérios para terminar a tarefa. Os recibos, respostas e logs permanecem privados e fora da análise científica.


## Correção v2 e tarefa completa em 08/10/2026

A continuação foi autorizada por Dante depois da falha v1. A mudança de contrato foi reproduzida por testes antes da implementação: duas regressões falharam, depois os 40 testes do adaptador, runner, integração nativa, piloto e transporte Codex passaram sem skips. Apenas a normalização de ausência de ferramentas foi alterada; prompt, política, schemas e regras de quota ficaram iguais. O recibo identifica tau2-subscription-json/v2. A falha v1 permanece preservada e não foi reclassificada como sucesso.

Uma nova qualificação exclusiva da tarefa airline 0, fora da análise do estudo, usou Sonnet 5.5 nos papéis de agente e usuário pela assinatura normal. As seis chamadas completaram o contrato, uma tentativa cada, sem retries ou API fallback. O ambiente executou get_reservation_details; o usuário encerrou com user_stop e o avaliador upstream devolveu recompensa 1,0. O banco final coincidiu com a referência. O resultado não exigia ações de escrita nem asserções de linguagem natural; o componente COMMUNICATE registrou ausência de informação a verificar. Portanto, esta tarefa não qualifica julgadores LLM, ferramentas que alteram o banco, todos os tipos de avaliação ou outras tarefas/modelos.

Os recibos somam 12 tokens de entrada sem cache, 28.696 de criação de cache, 1.119 de leitura de cache e 1.044 de saída. A soma das latências dos seis processos de modelo foi 24,23 segundos, excluindo importação, espera por quota e avaliação. Custo USD permanece null. As observações públicas antes dos turnos mostraram 94–95% restante na sessão e 99% na semana; ao final, 94% e 99%, sem uso extra. O mostrador percentual arredondado não permite estimar consumo exato por tarefa.

A atualização de quota foi supervisionada pela interface oficial, não automática: antes de cada turno o harness aguardava uma amostra posterior ao pedido daquele turno, e o gate original exigia idade máxima de 60 segundos e todas as janelas expostas. Ainda falta qualificar atualização automática confiável e orquestração antes de qualquer lote. Os resultados e dados brutos ficam privados. Esta é evidência de viabilidade técnica em uma tarefa, não resultado científico de adequação da suíte.


## Atualização automática de quota Claude em 08/10/2026

A opção explícita --refresh-claude-quota lê o último rate_limit_event do stdout oficial, aceita allowed/allowed_warning sem uso extra e preserva todas as unifiedWindows, inclusive janelas por modelo. seven_day é normalizada para weekly. A data de leitura é o mtime da captura original; o parser não renova essa data ao reler um arquivo antigo. Capturas com mais de 60 segundos, percentuais inválidos, status bloqueado, uso extra ou eventos ausentes provocam parada. O gate seguinte mantém os mesmos limiares e exige correspondência com todas as janelas declaradas.

A atualização é atômica, com arquivo de modo 0600, e afeta somente aliases Claude da execução sequencial. Cada rota guarda sampled_at próprio; atualizar Claude não renova o saldo Codex. A captura quota-after.json de cada turno fica privada. Rotas Codex continuam exigindo atualização externa. O runner não adquire o saldo inicial sozinho, não agenda resets e não inicia lotes.

Os dois testes novos falharam antes da implementação. Após a correção e a cobertura de integração do transporte, 43 testes passaram sem skips; git diff --check passou. A revisão de limites confirmou ausência de credenciais/endpoints privados, preservação de janelas extras e isolamento da data das rotas. Nenhuma política experimental foi alterada.

Uma qualificação técnica adicional usou Sonnet 5.5 nos dois papéis, política A, orçamento de 20 chamadas e uma única amostra inicial da UI oficial. Depois disso, não houve atualização manual entre turnos: três chamadas produziram três capturas de quota com 94% restante na sessão e 99% na semana, sem uso extra. Duas respostas passaram no envelope; a terceira foi texto puro, sem JSON, e o parser parou com JSONDecodeError. Não houve retry, resultado concluído ou avaliação dessa tentativa. Isso valida o caminho de atualização nos três turnos observados, mas expõe uma limitação de formato que impede liberar lotes. A tarefa anterior com quota supervisionada completou; as duas tentativas permanecem separadas e fora da análise científica.

Próximo passo técnico: avaliar saída estruturada pelo CLI oficial, com contrato e testes próprios, sem aceitar texto arbitrário como uma ação nem usar chamadas de reparo automáticas. Ainda é necessário qualificar tarefas com ações de escrita e outros caminhos de avaliação antes de ampliar o uso.
