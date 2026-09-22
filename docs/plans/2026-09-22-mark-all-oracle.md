# TodoMVC Mark all browser oracle

Acceptance: the same trusted browser controller must accept an explicit-reset
implementation and a derived-state implementation that removes the empty master;
it must reject a target-only stale-master mutant and a non-target individual-sync
mutant under exact assertion IDs. Both fixtures begin with two active todos.
The target is the checked state after clearing completed, conditional on bulk
selection and clear actually working. If either prerequisite fails, mark target
not evaluable; report the independent non-target failure instead. No empty-list
geometry, internal state, exact CSS or implementation choice is required.

The generator's common public interface names selectors and a neutral initial
fixture (`window.initialTodos`), not the post-clear checked state. The controller
runs in an offline bounded Docker image, fresh context per scenario. HTML and
browser reports remain separate; category classification rejects malformed,
duplicate or inconsistent reports. Authored fixture controls and image identity
must pass before adding a case to an experimental schedule. This oracle is
instrument preparation, not an empirical outcome.
