# Adequação de uma suíte de avaliação existente à política escrita do agente (τ²-bench, airline) — rascunho

**Estado:** rascunho, não registrado. Nenhuma chamada de modelo foi feita. A execução depende da reunião com o orientador, da revisão humana do inventário de regras e da qualificação do transporte escolhido (seção 7). É um estudo exploratório separado da coleta confirmatória 8 × 5 e não altera nenhum protocolo congelado.

## 1. Pergunta

Quando um agente conversacional segue uma política escrita, a suíte de avaliação que já existe para ele percebe a perda de cada regra?

O estudo mede **cobertura regra por regra de uma suíte pronta**. Não gera testes novos. Também não usa a política para escrever avaliações, como fazem ferramentas e estudos anteriores.

## 2. Por que este estudo

- **Continuidade com a dissertação.** A RQ1 mostrou que retirar uma obrigação do pedido leva à violação. A RQ2 mostrou que testes escritos a partir do pedido incompleto não percebem essa violação; nesse ponto, ela replica Haeri e Ghelichi (2026) em jornadas de navegador. Este estudo troca o objeto: em vez de testes gerados, examina uma suíte escrita por humanos, a das 50 tarefas do τ²-bench, diante da política que o agente recebe.
- **Antecedentes.** [Cao (2026)](https://arxiv.org/abs/2609.14400) identificou 15 lacunas na política airline, das quais só 7 são exercitadas pelas tarefas. [Rabinovich et al. (2026)](https://arxiv.org/abs/2603.29665) mostram que 8–17% das trajetórias pulam uma checagem exigida e ainda assim terminam no estado correto. Nenhum dos dois retira ou inverte regras para medir quais delas a suíte detecta. A [busca de 07/10/2026](../product-market-kit-20261007.md) não encontrou ferramenta que faça isso.
- **Hipótese de produto.** É a demonstração pública da auditoria proposta: dada uma política e a suíte que a equipe já usa, quais regras podem se perder sem que nenhuma avaliação falhe?

## 3. Material congelado

- τ²-bench no commit `4ce7c0397c1eb65c9bbe59aeacfe1ca44a1cd699`, domínio airline, 50 tarefas, `policy.md` com SHA-256 `10dc0525…2fc4`. O código do τ²-bench não é alterado: cada variante é uma raiz de dados própria, selecionada por `TAU2_DATA_DIR`. Só o `policy.md` muda; os demais arquivos são links para o original.
- Inventário em `data/policy-adequacy/tau2-airline/rules-draft.json`: 32 regras normativas, cada uma um trecho exato de linhas da política, e 5 exclusões justificadas (meta-regras, avisos sobre a API e o bloco de identificação duplicado).
- Para cada regra:
  - **Dxx — retirada:** as linhas da regra são removidas, como no braço C.
  - **Nxx — inversão:** as linhas são substituídas por um texto que autoriza a violação. Exemplos: "Basic economy flights can be modified"; trocar um valor como $50 por $150.
- **Controles Byy:** cinco reescritas com o mesmo sentido (como o braço B), para estimar quanto o ruído da simulação passa pela regra de confirmação.
- `scripts/policy_adequacy.py validate` confere hash, texto e não sobreposição. `build` gera as 70 raízes. `plan` gera a ordem sorteada (semente 2026100701).

**Antes de qualquer chamada:** Dante revisa o inventário. A revisão confirma três coisas:

1. cada trecho é uma regra só;
2. cada inversão viola a regra sem mudar outras;
3. cada reescrita preserva o sentido.

Mudanças nessa revisão são registradas, e o arquivo passa a `frozen` com hash.

## 4. Execução

- **Etapa 1:** a política original (A) em 4 tentativas nas 50 tarefas; depois as 32 inversões e as 5 reescritas, uma vez cada, nas 50 tarefas. São 2.050 simulações.
- **Etapa 2:** as 32 retiradas, uma vez cada, nas 50 tarefas. São 1.600 simulações. Só roda se a etapa 1 terminar e o orçamento permitir. A ordem já está fixada.
- **Confirmação:** toda falha numa tarefa elegível é repetida mais 2 vezes (`candidates` lista quais).
- Uma tentativa por slot, sem retry. Falhas de infraestrutura ficam registradas como tais.
- O agente e o simulador de usuário usam modelos fixados por identificador exato. A semente de cada lote vem do plano.

## 5. Análise (fixada antes dos resultados)

- **Tarefa elegível:** passa em pelo menos 3 das 4 execuções de A. Só tarefas elegíveis podem detectar algo.
- **Detecção confirmada** de uma variante numa tarefa: falha na primeira execução e em pelo menos 2 das 3 execuções (a primeira e as duas repetições).
- **Regra coberta** sob um operador: pelo menos uma tarefa confirma a detecção.
- **Classes por regra:**
  - `omission_detected`: a inversão e a retirada são detectadas;
  - `covered_but_omission_silent`: só a inversão é detectada; o agente provavelmente recupera a regra sem tê-la no texto, ou a retirada não muda o comportamento;
  - `omission_detected_violation_not`: só a retirada é detectada (esperado como raro);
  - `uncovered`: nenhuma tarefa detecta a violação explícita;
  - `incomplete`: há confirmações pendentes.
- **Ruído:** detecções confirmadas nos controles B, sobre pares controle × tarefa elegível.
- **Relato:** contagens por classe e por seção da política, sempre com os denominadores. Não há teste de hipótese: as regras não são uma amostra, e o estudo descreve uma suíte específica.

## 6. O que o estudo pode e não pode mostrar

- **Pode mostrar:** quais regras desta política, para este agente e este simulador, podem ser violadas sem que as 50 tarefas falhem.
- **Não pode mostrar:**
  - que uma regra não coberta é de fato violada em produção;
  - que outras suítes têm a mesma cobertura;
  - que uma ferramenta comercial encontraria essas lacunas com baixo custo.
- **"Não coberta" depende do agente.** Um agente que ignora a inversão porque o modelo já "sabe" a regra faz uma regra coberta parecer não coberta. Para separar os dois casos, uma amostra das execuções sem detecção é inspecionada por um humano, que verifica se o agente de fato violou a regra.
- **Ameaças:**
  - o simulador de usuário é um modelo de linguagem;
  - as tarefas foram revisadas pelos mantenedores do τ²-bench e o histórico de correções é público;
  - a inversão é um mutante mais forte que uma omissão real;
  - Cao (2026) mostra lacunas na política que podem confundir o que conta como violação.

## 7. Viabilidade e custo (a decidir)

- O caminho upstream chama modelos via LiteLLM e requer chave de API. A alternativa local em `scripts/tau2_subscription.py` conecta os CLIs oficiais de Claude e Codex por assinatura, sem fallback para API. O adaptador foi testado offline; a compatibilidade com o runtime completo e a sondagem real ainda precisam de qualificação. Veja [protocolo e limitações](../research/2026-10-07-tau2-subscription-bridge.md).
- Na assinatura, semente e temperatura não são controláveis e o envelope de ferramentas é serializado em texto. As quotas precisam de atualização externa a partir de telemetria pública oficial; o wrapper para com amostra velha, janela ausente ou reserva atingida. A reserva é um limiar antes da chamada, sem garantia de saldo após uma chamada sem teto de tokens.
- O custo por simulação não é conhecido. Antes da etapa 1, uma sondagem de viabilidade roda A em 5 tarefas para medir tokens e tempo. Essas execuções ficam fora da análise.
- Escala total: cerca de 2.050 simulações na etapa 1, mais confirmações; 1.600 na etapa 2.
- **Decisões em aberto:**
  - quais modelos usar para o agente e para o usuário;
  - qual orçamento;
  - se a etapa 2 entra;
  - se o estudo vira capítulo, apêndice ou trabalho futuro.

