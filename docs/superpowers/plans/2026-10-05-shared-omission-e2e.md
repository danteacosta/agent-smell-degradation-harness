# Plano da extensão E2E

Contrato e desenho aprovados pelo escopo escolhido pelo pesquisador: ver docs/preregistration/2026-10-05-shared-omission-e2e.md.

Arquitetura: adaptador novo reutiliza custódia, provedor, Docker e análise de mutation_adequacy sem editar seus arquivos congelados. O adaptador substitui somente o código recebido pelo testador, reidentifica e ordena as novas chamadas e vincula seu próprio hash ao manifesto. A variação isolada é a fonte de código. Não introduzir framework de experimentos.

- [ ] Regressão mínima: seleção determinística entre mutantes; prompt de código usa página mutante; não usa a correta.
- [ ] Implementar scripts/shared_omission_e2e.py com preparo, verificação, geração, execução e resumo público separado.
- [ ] Verificar alterações de script e preservação de schedule/páginas; executar regressões anteriores e smoke offline com recibos reais, sem chamadas.
- [ ] Revisão de segurança, SOLID, código e protocolo; commit/publicação antes de modelos.
- [ ] Qualificar Docker e congelar pacote novo; iniciar uma única coleta, mantendo o Mac acordado e monitorando até concluir.
- [ ] Conferir recibos/resultado e abrir PR separado de resultados, sem merge.

Verificação: pytest tests/test_shared_omission_e2e.py tests/test_mutation_adequacy.py tests/test_mutation_adequacy_integrity.py; py_compile; git diff --check; controles Docker. Falhar fechado em drift, pacotes ausentes ou controles inválidos. Sem API-key fallback e sem retry.
