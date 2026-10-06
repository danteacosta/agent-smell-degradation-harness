# Setup Antigravity por assinatura

## Contrato e plano

Setup autorizado após a avaliação #186. Adapter separado, sem alterar coletores congelados. Dado login Google oficial, quando enviado um prompt a um modelo Gemini explícito, então somente uma conclusão textual sem ferramentas pode ser aceita. Erro, autenticação por API, modelo divergente, ferramenta, stream incompleto ou timeout recusam a conclusão, sem retry. Evidência privada deve registrar tentativa, uso e hash do executável; não há preço USD inventado nem elegibilidade confirmatória.

Alternativas: Antigravity CLI usa a assinatura solicitada; Gemini CLI já instalado é outra integração, com quotas distintas; API exige billing separado. O setup segue Antigravity e preserva os resultados existentes.

Plano: instalar CLI oficial e verificar versão/catalogo; qualificar perfil sem ferramentas e login; escrever regressões de aceitação/recusa antes do adapter; implementar adapter e fumaça separada; verificar regressões Codex/memorização, privacidade, SOLID e recibos; abrir PR sem merge. Não iniciar a coleta de 150 chamadas.

CCE não tem índice neste worktree; descoberta seguiu arquivos exatos. Instalação oficial verificada por SHA-512 do manifesto, CLI 1.3.0. O instalador adicionou a pasta local bin aos perfis shell do usuário. O catálogo retornou `gemini-3.1-pro-low` e `gemini-3.1-pro-high`, sem comprovar saldo ou o plano contratado.

Fontes primárias, consultadas em 06/10/2026: [instalação](https://www.antigravity.google/docs/cli/install/), [headless](https://www.antigravity.google/docs/cli/headless/), [agentes sem ferramentas](https://www.antigravity.google/docs/subagents/) e [assinatura/overages](https://www.antigravity.google/docs/plans/). A seleção de Gemini impede usar um modelo OpenAI do catálogo. Crédito extra e limites não foram presumidos incluídos ilimitadamente.

## Resultado real do setup

O CLI foi instalado no Mac e retornou o catálogo. Foram realizadas **duas fumaças técnicas públicas**, sem requisitos, páginas, testes ou dados da pesquisa: uma para `tools: []`, outra para verificar se uma lista explícita `tools: [finish]` restringiria as capacidades. São qualificações de configurações diferentes, não repetição de chamada experimental. Ambas responderam corretamente pelo modelo declarado `gemini-3.1-pro-low`, sem chave de API. Nenhuma ferramenta foi chamada nos dois streams.

**As duas configurações expuseram 60 ferramentas**, inclusive navegação e leitura. Portanto, o setup de acesso funciona, mas **o runtime não está qualificado para coleta de pesquisa**. O catálogo e as respostas não comprovam qual plano está ativo, cota restante, ausência de créditos extras ou identidade de snapshot do backend. O backend não expõe aqui uma garantia auditável de fallback/retries internos.

O adapter não assume que um resultado recusado impeça ações: a validação do stream é posterior à execução. Por isso, exige antes de qualquer prompt uma qualificação textual sem ferramentas vinculada ao hash do executável. **Nenhum recibo válido foi criado com o CLI real.** Sem esse recibo, ele recusa antes de abrir o processo ou enviar o prompt; não é permitido usar o adapter para os 150 prompts privados nesta versão. O perfil alternativo também falhou, então não foi afrouxado o critério para aceitar as ferramentas.

A recusa cobre troca do modelo declarado, stream incompleto, erro, ferramentas expostas e mudança do executável. Só o texto do prompt é encaminhado; metadados/oráculo do request não são enviados. Configuração de autenticação por API é recusada no caminho real carregado pelo CLI; não há override para contornar essa checagem. Capturas usam permissões privadas. Há uma tentativa por chamada no adapter, sem afirmar que isso elimina retries internos do produto.

`agents/antigravity_cli.py` implementa o contrato separado; `scripts/antigravity_subscription_check.py` valida uma fumaça já existente **sem fazer chamadas**. Exemplo:

```sh
python scripts/antigravity_subscription_check.py --stream <stream-tecnico.jsonl> \
  --model gemini-3.1-pro-low --executable <agy>
```

O comando devolveu `qualified: false`, `research_collection_allowed: false` e exit 2 sobre a fumaça real. Não alterar os pacotes/coletores congelados para selecionar esse provider. Num protocolo novo, a integração pode usar `provider_factory` apenas depois de qualificação válida, quota/créditos verificados e contexto/retries do produto avaliados. O parâmetro `qualification_path` é um recibo privado, não autorização confirmatória.

### Verificação

Regressões offline cobrem aceitação textual em CLI falso, recusa antes do envio sem qualificação, API no HOME efetivo, ferramentas, mudança de modelo declarado, erro, timeout sem retry, mudança do binário e recibos exclusivos. Também foram executadas regressões Codex e memorização, compilação Python e `git diff --check`. A revisão de segurança encontrou a validação pós-execução e o caminho de configuração alternativo; o guard prévio e a checagem do HOME real foram adicionados após reproduzir essas lacunas.

Nenhum resultado científico foi coletado. Sem merge, seleção ou aprovação humana. Próximo bloqueio: obter uma forma oficial e verificável de desabilitar as capacidades/contexto no CLI, mantendo login da conta. Gemini CLI é alternativa com outra quota da mesma assinatura, ainda não integrada por este setup; API é uma alternativa com faturamento separado. Não houve troca silenciosa de produto nem ativação de overages.

## Alternativa solicitada: Claude Sonnet e Opus

O catálogo Antigravity também retornou `claude-sonnet-4-6` e `claude-opus-4-6-thinking`. Trocar apenas o modelo nesse CLI não resolve o problema de ferramentas; não foram feitas chamadas a esses modelos. O adapter Gemini não foi ampliado para aceitar essa troca silenciosamente.

Claude Code direto tem controle oficial `--tools ""`, configuração MCP estrita e sessões sem persistência. Contudo, ele não está instalado neste Mac, e a inspeção não encontrou cache de credenciais em arquivo. Não foi presumido que a assinatura Google dê acesso ao Claude Code direto: esse produto precisa de autenticação e entitlement próprios. A escolha entre os dois caminhos foi perguntada ao usuário antes de instalar outro produto ou gastar por API.

Fontes primárias: [CLI Claude Code](https://code.claude.com/docs/en/cli-reference), [autenticação](https://code.claude.com/docs/en/authentication) e [configuração de modelos](https://code.claude.com/docs/en/model-config), consultadas em 06/10/2026. A documentação é uma possibilidade de desenho, não prova de acesso local.
