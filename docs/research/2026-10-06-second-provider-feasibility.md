# Segundo provedor: acesso, orçamento e sonda offline

Verificado em 06/10/2026. Esta é uma avaliação de viabilidade, não uma coleta. Nenhum prompt experimental foi enviado a Google, Anthropic ou outro provedor. Foram consultadas documentação oficial e configuração local; os pacotes congelados não foram alterados.

## Decisão prática

**Há um caminho oficial para usar uma assinatura Google AI Pro/Ultra pelo CLI**, semelhante ao uso do Codex autenticado com ChatGPT. Isso não transforma a assinatura em saldo da Gemini API. O Gemini CLI instalado está configurado para `oauth-personal` e há cache OAuth; isso comprova configuração local, não validade atual do login, plano contratado, saldo ou autorização de um modelo específico. Não fiz inferência para testar esses pontos.

O Gemini CLI é a opção local mais próxima: pacote `@google/gemini-cli` **0.34.0**, instalado; Antigravity.app também está instalado, mas `agy` não foi encontrado no PATH. A documentação do Antigravity oferece execução headless com credenciais em cache e acesso ao CLI conforme o plano. Seria necessário verificar/instalar esse CLI e seu login separadamente; a sessão do aplicativo não foi presumida suficiente. Não foram extraídos tokens ou credenciais.

Para comparar famílias, selecionar explicitamente um modelo **Gemini**, registrando ID real e versão retornada; não usar o roteamento automático nem um modelo OpenAI eventualmente disponível no Antigravity. Gemini 3.1 Pro é candidato na assinatura; na API, o candidato de orçamento é `gemini-3.1-pro-preview`. `gemini-2.5-pro` é alternativa com ID estável e preço menor. Disponibilidade e identidade entre os produtos ainda precisam ser verificadas. Preview não garante snapshot imutável.

Fontes primárias: [Gemini CLI: quota e assinatura](https://geminicli.com/docs/resources/quota-and-pricing/), [Antigravity: planos](https://www.antigravity.google/docs/plans/), [Antigravity: autenticação](https://www.antigravity.google/docs/cli/install/) e [headless](https://www.antigravity.google/docs/cli/headless/).

## Tamanho medido dos prompts congelados

Medidas locais de texto Unicode e bytes UTF-8, sem `countTokens` remoto. Os 150 prompts do estudo de omissão compartilhada foram lidos sem modificação. Manifesto privado medido: SHA-256 `d1c7ddc5c69bf4068e7aa9c4428dcfbdd68ef08a441ca7d0da680f6bd0d8fc25`.

| Corpus / fonte | Prompts | Caracteres médios | Bytes médios | Caracteres totais |
| --- | ---: | ---: | ---: | ---: |
| Testador, completa | 50 | 4.677,20 | — | 233.860 |
| Testador, incompleta | 50 | 4.587,96 | — | 229.398 |
| Testador, incompleta + código mutante | 50 | 4.864,00 | — | 243.200 |
| Testador, total | 150 | 4.709,72 | 4.711,08 | 706.458 |
| Gerador, corpus A/B/C anterior | 552 | 3.876,28 | 3.877,71 | — |

O testador varia de 3.278 a 8.699 caracteres; o gerador de 2.447 a 7.644. Para o orçamento, **caracteres/4 é apenas uma aproximação**, não contagem de tokens Gemini: 1.177,43 tokens de entrada por chamada do testador e 969,07 do gerador. Uma faixa de caracteres/5 a caracteres/3 dá 942–1.570 e 775–1.292, respectivamente. Cabeçalhos internos do CLI, system prompts e ferramentas não estão incluídos.

Os 552 prompts do gerador vêm da coleta anterior dos 46 casos e servem apenas de proxy para o orçamento 8×5. **Os 40 casos confirmatórios não foram selecionados nem congelados por esta avaliação.** Medir seus prompts reais deve substituir essa proxy antes da execução.

Para reproduzir as medidas sem publicar o texto, passe ao Python apenas a pasta privada apropriada (`ROOT`), mantenha os pacotes intactos e agregue os comprimentos:

```python
import json, statistics
from pathlib import Path
root = Path(ROOT)  # study do testador, ou cases da coleta A/B/C
files = list((root / 'frozen/prompts').glob('*.txt'))
texts = [f.read_text() for f in files]
# Para o gerador: texts = [json.loads(f.read_text())['prompt']
#     for f in root.glob('*/frozen/requests/*.json')]
print(len(texts), statistics.mean(map(len, texts)),
      statistics.mean(len(t.encode('utf-8')) for t in texts),
      min(map(len, texts)), max(map(len, texts)))
```

## Preço por token e orçamento da API

Preços Standard em USD, entrada abaixo de 200 mil tokens, sem cache, batch, grounding ou ferramentas: Gemini 3.1 Pro Preview **US$2 por milhão de entrada e US$12 por milhão de saída**; Gemini 2.5 Pro **US$1,25 e US$10**, respectivamente. Por token: 0,000002/0,000012 e 0,00000125/0,000010. Saída faturada **inclui thinking**. Fonte: [tabela oficial Gemini API](https://ai.google.dev/gemini-api/docs/pricing).

Os cenários abaixo supõem 2.000, 4.000 ou 8.000 tokens faturáveis de saída por chamada, incluindo raciocínio. Não são saídas medidas de Gemini nem um teto garantido. Fórmula: `N × (entrada_média × preço_entrada + saída_faturável × preço_saída) / 1.000.000`.

| Modelo / coleta | Chamadas | Saída 2 mil | Saída 4 mil | Saída 8 mil |
| --- | ---: | ---: | ---: | ---: |
| 3.1 Pro Preview, testador | 150 | US$3,95 | US$7,55 | US$14,75 |
| 2.5 Pro, testador | 150 | US$3,22 | US$6,22 | US$12,22 |
| 3.1 Pro Preview, 8×5 A/B/C, 1 repetição | 120 | US$3,11 | US$5,99 | US$11,75 |
| 3.1 Pro Preview, 8×5 A/B/C, 2 repetições | 240 | US$6,23 | US$11,99 | US$23,51 |
| 3.1 Pro Preview, 8×5 A/B/C, 2 configurações × 2 repetições | 480 | US$12,45 | US$23,97 | US$47,01 |
| 2.5 Pro, 8×5 A/B/C, 2 repetições | 240 | US$5,09 | US$9,89 | US$19,49 |

Assim, 150 testes mais 240 gerações, com cenário de 4 mil tokens de saída, custariam aproximadamente **US$19,54 no 3.1** ou **US$16,11 no 2.5**. São dois estudos distintos; não devem compartilhar seleção, resultados ou recibos. Não estão incluídos controles novos, sondas/juízes, impostos, câmbio, Docker/energia ou eventual consumo maior de raciocínio. No 3.1, variar o proxy de entrada de caracteres/5 a caracteres/3 muda esse total central para cerca de US$19,37–19,81; a saída continua sendo a principal incerteza.

Na assinatura já contratada, o custo marginal pode ser zero **dentro da cota incluída**, mas não há preço por token que possa ser aplicado à cota como se fosse a API. O Antigravity permite overages com créditos, conforme configuração do usuário; não ativei nem autorizei gastos dessa natureza. Preços da API acima não estimam créditos Antigravity.

## Limites e acesso efetivo

O Gemini CLI publica limites diários de 1.000 requisições para conta individual, 1.500 para Google AI Pro e 2.000 para Ultra; também há limites por minuto e disponibilidade. Esses são limites publicados, **não o saldo verificado desta conta**. Um comando de agente pode emitir várias requisições ao modelo; 150 comandos não garantem 150 unidades de cota. A documentação orienta consultar `/stats model` para uso e limites. Google Workspace e Google AI Plus não devem ser tratados automaticamente como Pro/Ultra.

Antigravity tem cota baseada no trabalho do agente: Pro/Ultra recebem renovação a cada cinco horas até o limite semanal; a documentação não promete número fixo de prompts. Esses limites não são intercambiáveis com os do Gemini CLI.

Na API, RPM, TPM e RPD dependem de modelo, projeto e tier; o limite real deve ser lido no AI Studio. A API aplica limites por projeto e o RPD reinicia à meia-noite do Pacífico. Não confirmei billing ou quota da conta. Fonte: [limites oficiais Gemini API](https://ai.google.dev/gemini-api/docs/rate-limits).

Antes da coleta: registrar quotas efetivas, executar sequencialmente com margem para TPM/RPM, preservar cada falha sem retry e parar por falta de acesso. Não fazer fallback automático de modelo/provedor quando a quota terminar. O orçamento não garante execução ininterrupta.

## O adapter atual suporta?

**Não há integração pronta com a assinatura Google.** Os coletores de mutação e a sonda instanciam `CodexCLIProvider` por padrão. Aceitam injeção de `provider_factory` em Python, mas os wrappers atuais não selecionam Gemini/Antigravity. Trocar apenas o nome do modelo no shell não muda o provedor.

`agents/providers.py` contém `OpenAICompatibleProvider` com `base_url`, key, limite de saída e SDK com `max_retries=0`. A [compatibilidade oficial Gemini](https://ai.google.dev/gemini-api/docs/openai) oferece `https://generativelanguage.googleapis.com/v1beta/openai/`, **com Gemini API key**, sem usar a assinatura. Essa é uma base reaproveitável, não suporte experimental validado: o adapter sempre solicita `response_format=json_object`, enquanto o testador produz JavaScript bruto. É preciso resolver o contrato de saída, registrar thinking/usage/version e qualificar timeout, truncamento, erros e recibos. A lista do runtime em `agents/live.py` aceita openai/anthropic/deepseek, não Gemini.

Pelo CLI, falta um adapter próprio que use OAuth oficial, stdout JSON e processo novo por chamada, com ferramentas/MCP/memória/contexto externo desabilitados ou controlados. Também precisa impedir retries/fallbacks internos e registrar o modelo efetivo. Mesmo mantendo o prompt do usuário byte a byte, o system prompt do CLI difere do Codex: isso é uma limitação de comparação a declarar. Não extrair tokens da sessão para chamar endpoints internos.

**Recomendação:** usar a assinatura Google pelo CLI quando o acesso e a ausência de fallback puderem ser qualificados; usar a API se a necessidade de fixar modelo/contrato/recibos tornar o CLI inadequado. Nenhum adapter foi implementado ou coleta iniciada neste PR.

## Sonda de memorização: fumaça sem provedor real

Existem `scripts/memorization_probe.py` e `scripts/run_memorization_probe.sh`. Executei o fluxo Python completo `prepare → run(provider_factory=falso)` em diretório temporário novo, com duas regras artificiais, dois coders e dois juízes. O falso provider é a fixture determinística já usada em `tests/test_memorization_probe.py`.

Resultado: 12 sondas planejadas, quatro linhas finais (regra × coder), uma regra marcada como memorizada e uma não por coder, zero respostas sem julgamento. Foram escritos prompts congelados, tentativas/respostas locais, `results.json`, `receipt.json` e um resumo JSON. A qualificação dos juízes passou. **São dados de teste, não novos resultados científicos.**

Comandos de regressão executados:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_memorization_probe.py tests/test_memorization_public_dataset.py
bash -n scripts/run_memorization_probe.sh
```

Oito testes passaram. O wrapper shell foi verificado sintaticamente, mas **não executado com seu padrão Codex**, para não produzir chamadas reais. A prova ponta a ponta é do pipeline Python usado por ele, pela injeção de provider falso; não valida Gemini nem uma sessão real.

Para repetir o smoke offline, no ambiente Python do projeto:

```python
import json, runpy, tempfile
from pathlib import Path
from scripts import memorization_probe as probe
fixture = runpy.run_path('tests/test_memorization_probe.py')
root = Path(tempfile.mkdtemp(prefix='memorization-offline-smoke-'))
out = root / 'run'
probe.prepare(out, fixture['_panel'](root), ['fake-a', 'fake-b'],
              ['fake-j1', 'fake-j2'], Path('/bin/sh'))
summary = probe.run(out, provider_factory=fixture['_Provider'])
rows = json.loads((out / 'results.json').read_text())['rows']
assert len(rows) == 4
assert all(r['memorized'] == int(r['candidate_id'] == 'rc-known') for r in rows)
assert (out / 'receipt.json').exists()
(root / 'summary.json').write_text(json.dumps(summary, indent=2))
```

## Fontes e alcance da verificação

Todas as fontes externas acima são documentação técnica primária do Google/Gemini, acessada em 06/10/2026; servem para capacidade, preços e limites, não para validar hipóteses da dissertação. A inspeção local verificou presença/configuração do CLI e os contratos do código. Os tamanhos foram medidos dos pacotes privados sem publicá-los. Não há verificação online do plano individual, saldo, modelos concedidos ou qualidade de um segundo provedor.
