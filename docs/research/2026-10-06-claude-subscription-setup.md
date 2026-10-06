# Claude Code por assinatura: Sonnet e Opus

## Contrato aprovado e plano

Após o usuário confirmar assinatura Claude Pro/Max, o caminho escolhido é Claude Code direto. A assinatura Google não é reutilizada. Modelo explícito Sonnet ou Opus, autenticação OAuth Claude first-party por assinatura, ferramentas e MCP desabilitados, contexto novo, nenhuma chave de API ou credencial extraída. O setup não inicia a coleta científica.

Aceitação: dado CLI falso autenticado pela assinatura, quando uma conclusão textual de um modelo explícito termina com uso válido e zero ferramentas, então retorna texto e grava metadados privados. Sem login, API, troca de modelo, ferramenta, falha, captura incompleta ou timeout: recusar sem retry do adapter. Invariantes: não alterar prompts/resultados congelados, não encaminhar metadados/oráculos, não substituir provedor por falta de quota; não transformar custo API equivalente em cobrança da assinatura.

Plano: instalar Claude Code oficial; abrir login Claude subscription; testar falhas antes do adapter; implementar fronteira separada reutilizável; qualificar cada modelo com texto público quando houver login; registrar resultados e limites, verificar regressões/privacidade/SOLID e publicar PR sem merge. A etapa humana de login, se necessária, não pode ser inventada.

CLI instalado pelo instalador oficial, SHA-256 conferido contra manifesto, versão stable 2.1.285. Não havia login local; o fluxo oficial `claude auth login --claudeai` foi aberto. O adapter será independente dos scripts congelados; o protocolo de segundo provedor precisa de manifesto e recibos próprios antes da coleta.

Fontes primárias, consultadas em 06/10/2026: [CLI](https://code.claude.com/docs/en/cli-reference), [autenticação](https://code.claude.com/docs/en/authentication), [modelos](https://code.claude.com/docs/en/model-config). `--bare` não serve aqui: essa opção não lê OAuth/keychain e exigiria outra autenticação. Usamos controles explícitos compatíveis com a assinatura.

## Qualificação técnica concluída

Login oficial confirmado com `authMethod: claude.ai`, first-party, assinatura Pro. Sonnet `claude-sonnet-4-6` e Opus `claude-opus-4-6` responderam `SETUP_OK`, cada um em uma chamada pública, com zero ferramentas e zero servidores MCP. Os IDs observados nas respostas coincidiram com os solicitados. [Recibo público sanitizado](2026-10-06-claude-technical-smokes.json). Não são resultados científicos; nenhuma coleta foi iniciada.

A leitura do Keychain exige as variáveis locais USER/LOGNAME, além de HOME. O adapter conserva apenas variáveis de localização/identidade do sistema e configurações de segurança fixas; não conserva chaves API, endpoints, proxies nem tokens OAuth exportados. Não extrai credenciais. A execução no sandbox do Codex não acessou o login; o teste autorizado fora dele funcionou.

O adapter `agents.claude_cli.ClaudeCLIProvider` implementa o contrato `ProviderRequest`, só encaminha `prompt` e deixa os coletores congelados intactos. Usa ferramentas vazias, MCP estrito vazio, safe mode, fontes de configuração vazias, hooks desabilitados, diretório temporário e sessão sem persistência. Recusa políticas gerenciadas locais conhecidas, autenticação API, erros, ferramentas e troca de modelo. Captura privada exclusiva, limite de 2 MB e timeout com encerramento do grupo de processos. O executável é identificado por SHA-256 antes/depois. Os controles reduzem o contexto ambiental; não constituem um sandbox contra falhas do próprio CLI.

Retry é zero no adapter e nas opções documentadas do CLI, incluindo retry não streaming e fallback de transporte. Nenhum modelo alternativo é configurado. Não há promessa de imutabilidade do serviço: cada lote precisa congelar a versão do CLI e os IDs, conservar recibos e requalificar. [Variáveis oficiais](https://code.claude.com/docs/en/env-vars). Preço USD fica desconhecido: assinatura possui limites e pode ter uso extra habilitado na conta; login por assinatura não garante chamadas ilimitadas nem custo incremental zero.

Para repetir **apenas uma qualificação técnica**, com uma pasta nova e pai existente:

```bash
python3 scripts/claude_subscription_check.py \
  --executable "$HOME/.local/bin/claude" --model claude-sonnet-4-6 \
  --evidence-directory /caminho/privado/qualificacao-nova
```

Para Opus, use `claude-opus-4-6`. A ferramenta não inicia os 150 testes ou o desenho 8×5. Antes disso falta protocolo/manifesto específico de segundo provedor, qualificação dos controles do experimento e congelamento; não se substitui o provedor dentro de pacotes existentes. Evidência bruta contém respostas e identificadores da sessão e deve continuar privada.

## Verificação e revisão

41 testes de integração/regressão passaram nesta sessão (Claude, Antigravity, Codex e sonda de memorização), incluindo checker ponta a ponta com processo falso. Compilação Python e `git diff --check` passaram. Revisões independentes de contrato/código e segurança não encontraram bloqueadores para publicar este setup. O adapter não é qualificação científica e não autoriza alterar a seleção/auditoria humana.
