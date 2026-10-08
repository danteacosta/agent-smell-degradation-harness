# τ²-bench com assinaturas Claude e ChatGPT

Estado: adaptador exploratório, validado no runtime fixado do τ²-bench com replay e uma chamada técnica pela assinatura ChatGPT. Nenhuma coleta do estudo foi executada. Claude e atualização automática de quota continuam pendentes; não está qualificado para coleta.

O ponto de integração é a função de completion de [llm_utils.py no commit fixado](https://github.com/sierra-research/tau2-bench/blob/4ce7c0397c1eb65c9bbe59aeacfe1ca44a1cd699/src/tau2/utils/llm_utils.py). O wrapper substitui essa função somente durante um processo sequencial. As páginas de dados e o avaliador continuam no τ²-bench; o código upstream não é editado.

Cada turno leva o histórico completo, a política e os schemas das ferramentas ao CLI oficial em uma pasta temporária. O modelo devolve um envelope JSON com content e tool_calls; o wrapper o converte para a resposta esperada por LiteLLM. As ferramentas do CLI permanecem desabilitadas: o τ²-bench executa as ações no ambiente simulado. Cada chamada recebe uma pasta de evidência nova, privada; o transporte oficial exige autenticação salva por assinatura e não encaminha chaves de API.

Agente e usuário podem usar Claude ou Codex independentemente, com identificadores de modelo explícitos. O avaliador mantém o padrão ALL. Um julgador LLM não cadastrado provoca parada, sem fallback para API nem retirada silenciosa de critérios. Esse caso precisa de qualificação específica antes de escolher tarefas que o exijam.

## Uso

Em um ambiente Python 3.12 (versão verificada: 3.12.14) com as dependências do τ²-bench fixado instaladas:

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

O arquivo real precisa incluir subscription-user também e eventuais janelas por modelo. Os nomes devem coincidir com a lista declarada nos argumentos. Sem atualização pública confiável, o wrapper para; não assumir que um arquivo antigo continua válido. A amostra não pode ter mais de 60 segundos. Antes de cada chamada, exige saldo positivo na janela de cinco horas quando ela é exposta e mais de 30% em todas as demais janelas expostas, incluindo a semanal, sem uso extra. --max-calls inclui os turnos dos dois participantes; não é quantidade de simulações.

A reserva é um limiar de parada antes da chamada, não garantia de saldo depois dela: o CLI não permite limitar tokens de saída e a telemetria pode atrasar. Esse limite precisa entrar na decisão de orçamento. A rotina externa de atualização não foi qualificada. A sondagem técnica Codex consumiu uma chamada, separada da análise do estudo.

## Limites do método

O transporte serializa papéis e ferramentas em texto; não equivale a tool calling nativo. O CLI adiciona seu próprio contexto de execução. Semente e temperatura do τ² não são controláveis pela assinatura; valores recebidos ficam registrados como não aplicados. Uma comparação de modelos exige o mesmo protocolo e uma sondagem separada. Tempo, tokens e disponibilidade são custos observáveis; custo USD permanece null, nunca zero fictício.

Timeout, saída inválida ou falha do provedor deixam recibo e param sem nova chamada. Regra de confirmação do estudo é outra tentativa planejada, não retry automático do transporte. A versão atual executa uma única tarefa por processo; a orquestração das milhares de simulações e retomadas por reset continua pendente.

## Verificação

Em 07/10/2026, 38 testes passaram, sem skips, com o checkout fixado 4ce7c0397c1eb65c9bbe59aeacfe1ca44a1cd699. Os testes nativos usaram τ²-bench 1.0.1, LiteLLM 1.82.6 e Python 3.12.14: conversão de ferramentas/uso/custo e uma tarefa airline com replay, execução real de ferramenta no ambiente e avaliação ALL. A tarefa mecânica não é um resultado científico nem demonstra sucesso na tarefa do benchmark. O preflight confirmou o commit e zero chamadas.

Uma sondagem separada por Codex CLI 0.157.0, modelo solicitado gpt-6-astra, retornou a ferramenta sintética esperada em uma única chamada por assinatura ChatGPT: 16.515 tokens de entrada, 26 de saída, 10,81 segundos e custo USD null. O snapshot do modelo não foi exposto. A telemetria pública disponível expunha apenas a janela semanal, com 93% restante; o gate foi corrigido e testado para exigir exatamente as janelas expostas, sem inventar a de cinco horas.

Claude CLI 2.1.285 confirmou autenticação claude.ai Pro. O comando oficial /usage falhou ao carregar o saldo. Nenhuma chamada de modelo Claude foi feita e não houve retry ou fallback. A compatibilidade ao vivo desse provedor permanece pendente.

O upstream importa dependências de voz mesmo no modo texto. O ambiente recebeu essas dependências, exceto PyAudio (exige PortAudio de sistema e não foi necessário para estes testes), sem editar o upstream. Há um aviso de depreciação de audioop; Python 3.13 não foi validado. Evidências e respostas da sondagem ficam privadas.
