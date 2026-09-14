# Revisão do mestrado — 14/09/2026

## Estado atual após os PRs #53–55

Este quadro atualiza o diagnóstico inicial preservado abaixo. O PR #53 foi
mergeado em `509631b`, o #54 em `9fdf9a2` e o #55 em `e2b578d`. O último CI
aprovou 1.436 testes e nove subtestes, além do smoke do executor, replay e wedge.
A avaliação completa da `main` após o merge também passou. Esses checks
qualificam a entrega de engenharia; não validam hipóteses do mestrado.

| Frente | Executado e verificável | O que falta |
|---|---|---|
| Omissão controlada | 18 episódios originais; teto do desconto perdido em 3/3 reescritas. Acesso e token sem contraste. | Validade externa e revisão independente; não confundir omissão com categoria Paska validada. |
| Robustez dos artefatos | 1.638 entradas verificadas nos mesmos 18 códigos, sem novas gerações. | A grade não acrescenta intenções ou amostras independentes. |
| Ambiguidades e controles | 24 episódios separados; 12/12 textos claros passaram. Coordenação reescrita: 2/4 intenção, 2/4 alternativa. Pronome: 4/4 nenhuma das duas políticas. Controles: 8/8 entre ambos os braços. | Validar categorias, alternativas plausíveis e pistas da interface com revisores independentes. |
| Cobertura de smells | Dez entradas bibliográficas; exemplos executáveis de omissão, coordenação e pronome. | Ampliar casos/projetos e validar rótulos; não declarar dez smells comprovados. |
| Revisão humana | Formulários individuais preparados, sem resultados e com campos vazios; um texto por grupo. | Indicar revisores e adjudicador, revisar rubrica, registrar exposição e autorizar a distribuição. |
| H1 | Instrumento de pares e testes disponível. | Admissão semântica, amostragem por projeto/intenção, protocolo congelado e desfechos independentes. |
| H2 | Captura e análise de sinais T1–T3 disponíveis; gate histórico do avaliador falhou. | Qualificar rótulos/avaliador e medir detecção fora dos grupos usados no desenvolvimento, sem acesso a T4. |

Os [resultados do piloto de linguagem](codex-language-controls-results-20260914.md)
e o [roteiro de admissão](language-candidate-admission-checklist-20260914.md)
detalham a evidência e a próxima revisão. O comando `python -m eval.language_review`
reproduz o pacote de primeira leitura a partir do código versionado. Não
distribuir a pasta completa: isso exporia outras versões e induziria respostas.
O cadastro confirmatório continua bloqueado e não contém revisores ou labels
inventados. A revisão de candidatos não substitui o julgamento dos artefatos.

A proposta e o relatório do Drive foram atualizados, com conferência visual das
novas seções e preservação do texto anterior. Os decks agora contêm 13 e 14
slides, incluindo as injeções, os resultados e as limitações. PowerPoints e PDFs
foram exportados e conferidos. As menções a seis/sete slides, datas antigas ou
ausência de edição no diagnóstico inicial abaixo são fotografias anteriores.

As chamadas dos dois pilotos originais usaram a assinatura via Codex CLI.
Não misturar essa configuração com os experimentos históricos da API. O
exportador de revisão funciona offline e não consome nenhuma dessas cotas.

## Diagnóstico inicial, antes das atualizações desta sessão

PR #51 mergeado em `53dfb73`; PR #52 mergeado em `10db184`. A revisão do #52
encontrou e corrigiu um erro que repetia chamadas de juiz após falha de
persistência de evidência. Regressões passaram antes do merge. O CI de
`73236be` executou **1.406 testes e nove subtests**, todos aprovados, mais
os cinco controles do executor; auditoria de dependências, replay e wedge
também passaram. A adaptação Codex tem 16 testes próprios aprovados, gate
offline aprovado e o ensaio real documentado separadamente.

As tentativas de suíte completa no Mac e em Linux x86 emulado não ficaram
verdes: houve limites indisponíveis, identidade de snapshot e propriedade Git
do contêiner. Elas não são usadas como prova de aprovação. A evidência completa
dos PRs é o CI nativo acima. Nenhum controle foi afrouxado para esconder falhas.

O instrumento avançou mais do que a evidência científica. Há geração real,
captura temporal, rastreabilidade e recuperação de execução. Ainda não há
conclusão validada de H1/H2. Testes de software, chamadas de modelo e
concordância com respostas construídas não medem o efeito dos smells.

Um problema demonstrado está nos próprios oráculos históricos: exigir um
máximo de 1.000 usuários a partir de uma obrigação de capacidade de 1.000 muda
o contrato. GAMMA-002 e ERTMS-002 perderam o contraste na auditoria parcial.
NFR-002 e PEERING-001 mantiveram contraste em referências construídas, mas os
oráculos parciais também aceitam rejeição incondicional. Isso não demonstra
correção geral nem defeito produzido por LLM. O bloqueio de `eval.discovery`
live deve permanecer até a revisão semântica dos pares/oráculos.

## Documentos lidos no Drive

- [Proposta atual](https://docs.google.com/document/d/1sio6UiAciypbKGu7mbs8nlQJv2xvc3t888SvaShmB2w/edit), modificada em 14/09.
- [Relatório operacional](https://docs.google.com/document/d/1wSv-khPmRusFKwk4PO02qmbY6eg1MTjJ0QGHTlZuzuI/edit), modificado em 14/09.
- [Resumo visual](https://docs.google.com/presentation/d/1Hn01BrWVuRbUx5mClA4xU-hgEl3Mzae1G-Fc_L8iGvs/edit), seis slides.
- [Estado até 24/08](https://docs.google.com/presentation/d/12RNMJdRPOPUb9CxlUJTsRyeJpuhj2781DNxqsZD4gIE/edit), sete slides.

Avaliação de conteúdo/estrutura extraídos pelos conectores; sem inspeção
visual renderizada. Os arquivos nativos não foram alterados.

### Proposta

A formulação atual é defensável: testa perda de restrição causada pelo requisito,
mantém critérios de aceitação como tarefa primária e código como extensão
comportamental. A separação T1–T3/T4 e a possibilidade de resultado negativo
estão explícitas. A própria proposta reconhece que H1/H2 não foram testadas.

O resumo informa que v4/v5 fizeram 48 chamadas de desenvolvimento, com 23/24
vetores por versão, e falharam o gate conjunto: sob observação parcial, uma
condição ausente não autoriza concluir que ela se perdeu. Não substituir
essa limitação por percentuais globais de acerto do juiz.

O cabeçalho ainda diz 08/09, embora contenha atualizações de 14/09. Registros
históricos repetem estados superados; conservar a proveniência em apêndice e
manter uma tabela principal com executado, validado e pendente evitaria
leituras contraditórias.

### Relatório operacional

Está mais atualizado que os slides: descreve o pré-piloto corrigido (240
artefatos, 1.296 chamadas, US$0,194731), a limitação dos labels, a auditoria
de oráculos e a recuperação de geração/julgamento/publicação do PR #52.
Esses valores foram lidos do documento; não foi refeita a conciliação dos
ledgers históricos privados nesta revisão.

Separar os denominadores: intenções independentes, variantes, repetições,
artefatos e chamadas. O cabeçalho permanece em 08/09 e a seção de repositório
aponta main 76403a1, anterior aos merges desta sessão.

### Apresentações

As duas mostram no slide 6 **370 testes**, **3 gates**, ausência de dois
providers e execução de 120 episódios como próximo passo. Essa fotografia
não corresponde aos documentos atuais. Substituição recomendada:

> Pré-piloto exploratório executado; validade semântica ainda pendente.
> Duas configurações já foram exercitadas. O gate do avaliador falhou.
> Próximo: validar pares/oráculos e medir violações com testes comuns congelados.
> H1/H2 permanecem sem conclusão.

No slide 3, “reuso fica silenciosamente permitido” é um exemplo ilustrativo,
não uma consequência garantida. Usar “pode deixar de testar ou impedir reuso”
até haver artefato real com entrada, esperado e observado. O slide 2 do resumo
também apresenta propagação como inevitável; ajustar para hipótese de risco.

O slide 7 do deck histórico registra a orientação de mostrar cerca de dez
pares clean/smell com resultados. O ensaio original desta sessão é menor e
não cumpre essa meta de corpus: serve para mostrar o tipo de evidência.
Não ampliar para dez inventando origem ou aprovação.

## Experimento que responde à pergunta

Congelar antes da geração: intenção completa, uma condição removida, interface
igual, testes comuns e condição-alvo. Entregar ao modelo somente uma variante.
Preservar código, prompt, configuração, repetição, entrada do teste, esperado,
observado e erros. Reportar também nenhum efeito e efeito reverso. Não mudar
o teste depois de observar a resposta nem tratar crash/timeout como perda semântica.

`eval.codex_demo` usa três políticas **originais**, três repetições, um modelo
solicitado e 18 episódios. O desconto tem teto explícito de 7 na versão completa,
para não atribuir expectativa arbitrária a uma fonte real. A execução usa Linux
ARM64 nativo em contêiner, imagem congelada, usuário não privilegiado, sem rede
e com limites. É demonstração exploratória de código gerado; não corpus natural,
confirmação de H1 ou avaliação de detecção H2.

Para cumprir a orientação acadêmica com os pares reais: revisar a semântica de
todos os candidatos antes de selecionar os aprovados, congelar a revisão,
coletar repetições em configurações identificadas e distinguir demonstração
de uma violação do tamanho/generalização do efeito.

## Cota Codex

A alternativa suportada é a autenticação ChatGPT do **Codex CLI**. A cota não
vira crédito da API Platform. O adaptador exige esse login, remove chaves do
ambiente filho, desativa ferramentas e não tem fallback pago. O CLI não expõe
snapshot confiável nesse stream nem o teto estrito de tokens da API; o
adaptador registra essas limitações. Consumo da assinatura não é custo API
medido igual a zero. Não misturar esses episódios com a configuração API anterior.

Fontes oficiais: [autenticação](https://learn.chatgpt.com/docs/auth),
[modo não interativo](https://learn.chatgpt.com/docs/non-interactive-mode),
[configuração](https://learn.chatgpt.com/docs/config-file/config-reference).
