# Instruções para o Codex no Mac (5/10)

Este arquivo é para colar no Codex, ou para o Dante seguir à mão. Ele cobre só o que precisa do Codex CLI local. Não há geração A/B/C aqui: a coleta confirmatória só começa depois do registro do pré-registro.

## Regras que valem para tudo

- Nunca refaça uma chamada que falhou ou ficou inválida. Falha é desfecho e fica registrada.
- Não edite pacotes congelados (`frozen/`). Se um script recusar por deriva ou porque a pasta já existe, pare e informe.
- Evidência bruta dos provedores fica em `~/Documents/GitHub/.private-research-evidence`. No repositório entram só os arquivos públicos, como nos PRs anteriores.
- Se um controle autorado falhar, o painel para sozinho. Não ajuste prompts nem controles para fazer passar: informe e pare.

## Tarefa 1 concluída: instruções históricas, não executar novamente

As duas triagens e a consolidação pública terminaram em 05/10, com 809 chamadas preservadas. Consulte o [relatório final](2026-10-05-confirmatory-screening-results.md). O roteiro abaixo descreve a execução já realizada; não autoriza repetir chamadas.

Prompt para o Codex:

> No repositório agent-smell-degradation-harness, depois do merge do PR do quadro confirmatório (branch `study/confirmatory-frame`):
> 1. `git checkout main && git pull`.
> 2. Rode `bash scripts/run_confirmatory_screening.sh both` e espere terminar. Não interrompa e não faça retry.
> 3. Para cada opção (`reserve`, `w2024`), publique o resultado em `data/llm-screening-confirmatory-<opção>-20261005/` com o mesmo conjunto de arquivos e a mesma auditoria somente leitura usados no PR #147 (`results.json`, `controls.json`, `audit.json`, `custody.json`, `frozen-manifest.json`, `receipt.json`).
> 4. Escreva `docs/research/2026-10-05-confirmatory-screening-results.md` com, para cada opção: controles, admitidos por projeto, kappa e rotas (acordo ou desempate).
> 5. Abra um PR com isso. Não faça merge.
>
> Se os controles falharem em qualquer opção, publique só o `results.json` com `stopped_controls_failed`, descreva no PR e pare.

## Tarefa 2: depois da reunião, não agora

A sonda de memorização e a construção dos casos E2E dependem do quadro escolhido e do desenho (o 9 × 4 anterior foi retirado; o planejamento corrigido considera 8 × 5 sob hipóteses explícitas). Elas ficam para depois da decisão do orientador e do registro. Antes disso, não rode `run_memorization_probe.sh`, `abc_case.py` nem `run_historical_arm.sh` sobre candidatos novos.

## O que o Claude já fez (sem modelo)

- simulação de tamanho de amostra (#169);
- mineração do quadro de 2024 e amostras de triagem das duas opções (PR deste branch);
- planilha cega de auditoria humana dos painéis (PR separado);
- pauta da reunião e atualização do rascunho do artigo do workshop.
