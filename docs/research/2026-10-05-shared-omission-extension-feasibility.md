# Extensão de omissão compartilhada: viabilidade

Consulta em 05/10/2026 motivada pelo texto fornecido pelo pesquisador. Nenhuma nova chamada de modelo foi realizada. Há dois escopos possíveis: complementar a adequação E2E com código do próprio mutante, ou criar um experimento novo com agentes que usam ferramentas e policies. A escolha foi solicitada ao pesquisador antes de executar coleta dependente dela.

## Evidência externa verificada

**Tzafrir Rehan, Test-Driven AI Agent Definition (TDAD), arXiv:2603.08806**, submetido em 09/03/2026. Tipo: preprint, fonte primária. [Registro e abstract](https://arxiv.org/abs/2603.08806), [artefato indicado pelo autor](https://github.com/f-labs-io/tdad-paper-code). O abstract descreve geração de testes de especificações comportamentais, compilação de prompts e mutação semântica desses prompts. Isso impede apresentar mutation testing de evals de agentes como novidade genérica. Não foi feita reprodução do benchmark nem revisão completa de licença e dependências do artefato.

**Soneya Binta Hossain, Raygan Taylor e Matthew Dwyer, Doc2OracLL: Investigating the Impact of Documentation on LLM-Based Test Oracle Generation**, PACMSE 2(FSE), 2025, DOI 10.1145/3729354. Tipo: artigo científico publicado, fonte primária. [Texto da ACM](https://doi.org/10.1145/3729354). O estudo aborda documentação para geração de oráculos. A introdução apresenta o risco de incorporar comportamento defeituoso da implementação ao oráculo, atribuindo o problema a pesquisa anterior. O texto introdutório verificado não basta para alegar que Doc2OracLL demonstrou causalmente esse mecanismo em seu experimento. Não foram verificados os demais trabalhos mencionados no texto fornecido, nem a alegação de ausência de estudos semelhantes.

## Encaixe no experimento existente

O [resultado de adequação](2026-10-05-mutation-adequacy-results.md) compara testes gerados de requisito completo ou incompleto em 25 requisitos de oito projetos, com páginas já classificadas por oráculos. O braço com código recebeu uma página A correta, e não o mutante. Logo, não representa testar um PR defeituoso com sua própria descrição incompleta.

Uma extensão pequena pode selecionar, por regra e semente previamente congeladas, um mutante confirmado por requisito e gerar duas suítes a partir do pedido incompleto mais esse código. Seriam 50 chamadas adicionais. Reutilizar os controles e os alvos é viável, mas a comparação com braços coletados antes permanece exploratória e sujeita a diferença temporal. Uma comparação contemporânea das três fontes exigiria 150 chamadas novas, em lote separado e sem substituir o #180. Estes tamanhos são propostas, não coleta iniciada nem poder calculado.

A avaliação deve verificar quietude numa referência correta e alarmes nos mutantes e nas demais páginas corretas, preservando falhas de geração. Deve reportar tanto intenção de testar quanto discriminação condicionada, com pesos explícitos e agrupamento por projeto. A seleção prévia de páginas defeituosas não permite estimar a frequência geral de falsa confiança na população.

O escopo de agentes com ferramentas exigiria policies públicas com licença verificável, obrigações independentes, executor isolado e oráculos de ações/estado. Os números dos E2Es não podem ser apresentados como resultados desse novo domínio. Nenhum desses elementos foi congelado ou coletado nesta consulta.
