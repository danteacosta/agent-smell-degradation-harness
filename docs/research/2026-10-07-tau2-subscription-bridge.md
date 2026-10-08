# τ²-bench com assinaturas Claude e ChatGPT

Estado: adaptador exploratório, validado localmente com respostas de replay. Nenhuma chamada de modelo ou simulação real foi executada. Não está qualificado para coleta.

O ponto de integração é a função de completion de [llm_utils.py no commit fixado](https://github.com/sierra-research/tau2-bench/blob/4ce7c0397c1eb65c9bbe59aeacfe1ca44a1cd699/src/tau2/utils/llm_utils.py). O wrapper substitui essa função somente durante um processo sequencial. As páginas de dados e o avaliador continuam no τ²-bench; o código upstream não é editado.

Cada turno leva o histórico completo, a política e os schemas das ferramentas ao CLI oficial em uma pasta temporária. O modelo devolve um envelope JSON com content e tool_calls; o wrapper o converte para a resposta esperada por LiteLLM. As ferramentas do CLI permanecem desabilitadas: o τ²-bench executa as ações no ambiente simulado. Cada chamada recebe uma pasta de evidência nova, privada; o transporte oficial exige autenticação salva por assinatura e não encaminha chaves de API.

Agente e usuário podem usar Claude ou Codex independentemente, com identificadores de modelo explícitos. O avaliador mantém o padrão ALL. Um julgador LLM não cadastrado provoca parada, sem fallback para API nem retirada silenciosa de critérios. Esse caso precisa de qualificação específica antes de escolher tarefas que o exijam.

## Uso

Em um ambiente Python 3.12 ou 3.13 com as dependências do τ²-bench fixado instaladas:

```sh
python -m scripts.tau2_subscription --tau2 /CAMINHO/tau2-bench --data /PASTA_PRIVADA/variantes/A
```

Esse comando verifica o checkout e os dados, sem carregar modelos ou gastar quota. A execução de uma tarefa exige --execute, --task-id, --agent-provider, --agent-model, --user-provider, --user-model, os caminhos dos CLIs usados, --quota, --out e --max-calls. Também exige --agent-windows e --user-windows com os nomes de TODAS as janelas expostas publicamente. Nada agenda lotes ou retoma automaticamente.

Antes da execução, ainda são necessárias revisão humana do inventário, definição com o orientador e autorização da sondagem. A adaptação técnica não libera o estudo.

## Quota e orçamento

--quota aponta para um JSON privado atualizado externamente com telemetria pública oficial. Ele NÃO descobre quota sozinho. Nunca preencher por estimativa, remover janelas expostas ou consultar credenciais/endpoints privados. Exemplo de formato (valores meramente ilustrativos):

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

O arquivo real precisa incluir subscription-user também e eventuais janelas por modelo. Os nomes devem coincidir com a lista declarada nos argumentos. Sem atualização pública confiável, o wrapper para; não assumir que um arquivo antigo continua válido. A amostra não pode ter mais de 60 segundos. Antes de cada chamada, exige cinco horas com saldo positivo e mais de 30% nas demais janelas, sem uso extra. --max-calls inclui os turnos dos dois participantes; não é quantidade de simulações.

A reserva é um limiar de parada antes da chamada, não garantia de saldo depois dela: o CLI não permite limitar tokens de saída e a telemetria pode atrasar. Esse limite precisa entrar na decisão de orçamento. Não houve qualificação da rotina externa de atualização nem consumo de quota neste desenvolvimento.

## Limites do método

O transporte serializa papéis e ferramentas em texto; não equivale a tool calling nativo. O CLI adiciona seu próprio contexto de execução. Semente e temperatura do τ² não são controláveis pela assinatura; valores recebidos ficam registrados como não aplicados. Uma comparação de modelos exige o mesmo protocolo e uma sondagem separada. Tempo, tokens e disponibilidade são custos observáveis; custo USD permanece null, nunca zero fictício.

Timeout, saída inválida ou falha do provedor deixam recibo e param sem nova chamada. Regra de confirmação do estudo é outra tentativa planejada, não retry automático do transporte. A versão atual executa uma única tarefa por processo; a orquestração das milhares de simulações e retomadas por reset continua pendente.

## Verificação

Testes locais cobrem histórico/ferramentas, resposta inválida, ausência de fallback, limite de chamadas, quota desatualizada/incompleta, restauração do hook e checkout com drift. Um teste adicional em tests/test_tau2_subscription_native.py usa o τ² e LiteLLM reais quando TAU2_CHECKOUT está configurado, ainda com transporte replay e sem chamada de modelo. Esse teste foi deixado explícito; não confundir testes da interface com qualificação end-to-end.
