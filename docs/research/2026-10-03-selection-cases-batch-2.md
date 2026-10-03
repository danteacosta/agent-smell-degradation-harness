# Casos da seleção, lote 2: os 36 restantes

Status: rascunho. Oráculos pré-qualificados localmente; faltam a qualificação em Docker, a revisão dos braços e o congelamento. Nenhum modelo foi chamado.

Com este lote, os 46 requisitos selecionados (`data/requirement-selection/selection.json`) têm caso A/B/C: os 10 do lote 1 e 36 novos, seis por projeto em Grist, Mattermost, Nextcloud, OpenProject, WeKan e Zulip. Os specs estão em `scripts/selection_cases/specs_<projeto>.py`. O gerador entrou sem alteração; os novos specs foram acrescentados depois dos do lote 1, então as seeds e os arquivos do lote 1 continuam os mesmos.

## Como foram feitos

- O texto do braço A vem do snapshot da documentação no fim do frame (`current-doc-check.json`), não do commit. Cada config registra em `source` o arquivo do snapshot usado.
- O braço C é o A sem um único trecho contíguo, a frase da regra-alvo; isso é verificado em teste. O braço B reescreve o A inteiro com outras palavras, mantendo o significado.
- As regras do lote 1 valem aqui também: uma URL só, recarga como única navegação, estado lido da API da página, pré-condição que falha como `interface_error`, duas fixtures e asserções-alvo separadas das de controle.
- Os casos com `oracle_requirement` mudam a configuração pela página e observam o efeito: `zulip-resolved-notice-auto-read` (aviso lido ou não lido conforme a configuração) e `openproject-files-tab-attachments`.

## Pré-qualificação local

349/349 controles, nos 46 casos, foram classificados como esperado (Node e Playwright locais, sem Docker). Os 36 casos novos têm de 6 a 11 controles cada, com referência, leitura alternativa correta, mutante do alvo, mutante de controle, sem handler e erro de script. A suíte rápida passou; uma falha intermitente em `test_codex_cli.py`, sem relação com este lote, passou ao repetir.

## Pontos para a revisão dos braços e oráculos

Os casos foram montados por agentes, um por projeto, com o lote 1 como referência; eu integrei e conferi. Os construtores registraram compromissos que pedem decisão humana antes do congelamento:

**Texto que ainda sugere a regra em C** (vai para a codificação de `context_cue`):
- Nextcloud: a senha de dispositivo ("does not save the plain password"), a lixeira (C ainda descreve a lixeira, restaurar e excluir permanentemente), favoritos (o nome da configuração "Sort favorites up") e a conversa do calendário ("will also appear in the list of conversations").
- Grist: `grist-tutorial-restart` mantém "Be sure to save changes … prior to clicking this"; `grist-context-menu-shortcut` mantém os atalhos vizinhos com Shift+F10.
- WeKan: `wekan-home-multi-drop` mantém "a one-board drag continues to set Home normally".
- Mattermost: `mattermost-anonymous-team-url` mantém o contraste "If your system admin has not enabled anonymous URLs".

**Texto omitido do A para que C não repetisse a regra** (o A deixa de ser a página literal):
- `grist-tutorial-fork-return`: a frase sobre a Direct URL, que repete a regra.
- `mattermost-playbook-task-markdown`: "Task descriptions support a limited form of Markdown".
- `openproject-auto-theme-contrast`: a regra aparece duas vezes e sai como um único trecho.
- `zulip-private-channel-access`: o texto de exclusividade. Por isso, "sem inscrição, sem acesso" não é testado.
- `wekan-field-order-independent`: a independência aparece três vezes; o caso pode discriminar pouco.

**Compromissos de scaffold ou de oráculo:**
- `openproject-invite-permission-basis`: o código gerado precisa criar a escolha de Group/Placeholder, e o oráculo a encontra pelo nome. Um rótulo incomum conta como falha no alvo.
- `zulip-resolved-notice-auto-read`: qualquer controle no scaffold revelaria a regra, então a implementação cria o próprio controle, nomeado na frase removida. Sem ele, o alvo falha.
- `mattermost-anonymous-team-url`: a fixture 2 não tem asserção-alvo.
- `wekan-sync-local-edits` e `openproject-archived-project-selector`: a API expõe os campos que a regra usa (valores de origem, `archived`), o que é uma pista em C.
- `mattermost-playbook-task-markdown`: o HTML da tarefa é renderizado com `innerHTML`, sem sanitizar.

Nenhum destes impede a coleta, mas cada um deve ser aceito, ajustado ou registrado como covariável antes do congelamento.

## Próximos passos

1. Revisar os braços B e C e os pontos acima. Para mudar um caso, edite o spec e rode `python3 scripts/build_selection_cases.py build`; o teste garante que os arquivos versionados batem com os specs.
2. Qualificar em Docker no Mac: `bash scripts/qualify_selection_cases.sh`, que roda todos os casos com `candidate_id`.
3. Congelar os 46 configs e coletar com `scripts/abc_case.py`: 46 × 3 braços × 2 modelos × 2 repetições = 552 chamadas.
