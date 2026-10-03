# Casos da seleção, lote 2: os 36 restantes

Status em 03/10: revisão de integração e qualificação em Docker concluídas para os 46 casos, com 360/360 controles autorados classificados como esperado. Falta congelar e executar as 552 gerações. Nenhum modelo foi chamado nesta revisão. A auditoria humana permanece pendente antes de afirmações confirmatórias.

Com este lote, os 46 requisitos selecionados (`data/requirement-selection/selection.json`) têm caso A/B/C: os 10 do lote 1 e 36 novos, seis por projeto em Grist, Mattermost, Nextcloud, OpenProject, WeKan e Zulip. Os specs estão em `scripts/selection_cases/specs_<projeto>.py`. O gerador entrou sem alteração; os novos specs foram acrescentados depois dos do lote 1, então as seeds e os arquivos do lote 1 continuam os mesmos.

## Como foram feitos

- O texto do braço A vem do snapshot da documentação no fim do frame (`current-doc-check.json`), não do commit. Cada config registra em `source` o arquivo do snapshot usado.
- O braço C é o A sem um único trecho contíguo, a frase da regra-alvo; isso é verificado em teste. O braço B reescreve o A inteiro com outras palavras, mantendo o significado.
- As regras do lote 1 valem aqui também: uma URL só, recarga como única navegação, estado observado no DOM renderizado pela página, pré-condição que falha como `interface_error`, duas fixtures e asserções-alvo separadas das de controle.
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

**Texto redundante omitido do A para que C não repetisse a regra** (A é uma adaptação localizada, acrescida de instruções da API sintética; não é uma transcrição integral da página):
- `grist-tutorial-fork-return`: a frase sobre a Direct URL, que repete a regra.
- `mattermost-playbook-task-markdown`: "Task descriptions support a limited form of Markdown".
- `openproject-auto-theme-contrast`: a regra aparece duas vezes e sai como um único trecho.
- `zulip-private-channel-access`: o texto de exclusividade. Por isso, "sem inscrição, sem acesso" não é testado.
- `wekan-field-order-independent`: a independência aparece três vezes; o caso pode discriminar pouco.

**Compromissos de scaffold ou de oráculo:**
- `openproject-invite-permission-basis`: a escolha é criada pelo modelo. O oráculo aceita a identidade semântica do valor ou um nome reconhecível; outro rótulo com o mesmo valor passa. A revisão corrigiu a confusão com adicionar um grupo: o alvo agora é um usuário convidado sob a base Group, conforme a fonte. Não avalia herança real de permissões.
- `zulip-resolved-notice-auto-read`: a implementação cria a configuração. O oráculo opera uma única configuração adicional visível, sem exigir o rótulo da frase removida, e aceita checkbox, select, switch ou botão com estado booleano acessível. Configurações ambíguas ou não identificáveis ficam não avaliáveis. O caso cobre ligado/desligado, não a modalidade somente tópicos não seguidos.
- `mattermost-anonymous-team-url`: a fixture 2 não tem asserção-alvo.
- `wekan-sync-local-edits` e `openproject-archived-project-selector`: a API expõe os campos que a regra usa (valores de origem, `archived`), o que é uma pista em C.
- `mattermost-playbook-task-markdown`: o HTML da tarefa é renderizado com `innerHTML`, sem sanitizar.

Esses pontos exigem tratamento antes do congelamento. Pistas remanescentes são parte do contexto experimental e não provam contaminação. A revisão dos oráculos foi separada dos resultados de geração, ainda inexistentes. O código inserido pode escrever no DOM; portanto os atributos do scaffold não constituem um canal de estado independente. A qualificação testa controles autorados, não todas as implementações válidas ou possíveis adulterações.

## Próximos passos

1. Incorporar a revisão e seus limites; os textos e oráculos foram revisados para coleta exploratória, sem substituir a auditoria humana.
2. Congelar os 46 configs, prompts e runtimes qualificados antes das chamadas. Qualquer alteração posterior exige novo pacote, sem substituir o anterior.
3. Coletar com `scripts/abc_case.py`: 46 × 3 braços × 2 modelos × 2 repetições = 552 chamadas, preservando recusas, erros, empates e falhas sem retry ou reparo.

## Revisão de integração

A revisão paralela de código e das fontes primárias encontrou e corrigiu falsos sucessos ou falsas falhas: menu invisível no Grist, limite implementado por botão desabilitado, texto de tradução divergente do texto visível e mensagens ocultas, lista de usuários filtrada legitimamente, rótulos alternativos e toggle acessível para avisos, conversão tardia no envio e ausência de link no Zulip. Os controles adversariais reproduziram as classificações incorretas antes das correções. O SHA incorreto dos seis casos Nextcloud foi corrigido; os seis projetos novos agora registram SHAs completos.

A fonte OpenProject foi conferida nas linhas 79/87/89. O caso antigo tratava de adicionar um grupo, um fluxo distinto nas linhas 47–55. O caso corrigido verifica seleção e persistência da base escolhida para a identidade correta; não demonstra herança de permissões nem cobre Group com convite por email.

As 35 fontes/contextos distintos dos 36 novos casos foram recuperados da API primária nos snapshots fixados. Os blobs Git e os hashes SHA-256 foram verificados. [Registro de fontes](../../data/requirement-selection/case-review-20261003/snapshot-source-verification.json) e [revisão dos braços](../../data/requirement-selection/case-review-20261003/arms-review.json) mantêm identidades, trechos removidos, hashes e limitações. A codificação independente de context_cue continua pendente nos casos não marcados explicitamente. A integração teve exposição a resultados anteriores da sonda; não é uma revisão cega.

Limites adicionais: o caso de canal privado testa o acesso positivo aos tópicos fornecidos e não toda a política de histórico compartilhado/protegido. No linkifier, linkText preenchido habilita o caminho de conversão e null representa a configuração desabilitada. As páginas são reconstruções sintéticas ancoradas na documentação open-source; não são execuções das aplicações completas. As evidências originais e diagnósticos permanecem separados.

## Qualificação final em Docker

[Manifesto verificável](../../data/requirement-selection/case-review-20261003/docker-qualification.json): 46 casos, 360 controles, imagem fixada `sha256:00d1265095773b7f8a12aa73e81d0bab75563cbd672dd0b5d91783ea1b6d4400`. Cada registro vincula config, scaffold, runner, qualificador, relatórios e hashes dos prints. Os JSONs dos relatórios e da qualificação estão publicados; os prints permanecem nos pacotes de custódia. Todos os hashes foram conferidos contra os arquivos finais. Rodadas de diagnóstico anteriores foram preservadas separadamente. Estes são controles feitos à mão, não resultados de H1.

## Fontes primárias consultadas

Documentação dos mantenedores, consultada em 03/10/2026 nos commits publicados no registro de fontes: [Grist Labs](https://github.com/gristlabs/grist-help), [Mattermost](https://github.com/mattermost/docs), [Nextcloud](https://github.com/nextcloud/documentation), [OpenProject](https://github.com/opf/openproject), [WeKan](https://github.com/wekan/wekan) e [Zulip](https://github.com/zulip/zulip). As fontes definem as obrigações e seus escopos, não demonstram causalidade dos smells. O registro vinculado acima identifica arquivo, URL fixada, blob e hash para cada caso. Essa consulta corrigiu o fluxo de convite do OpenProject e delimitou os caminhos de configuração e conversão do Zulip.
