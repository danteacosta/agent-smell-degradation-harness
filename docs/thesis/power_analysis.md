# Confirmatory Power Analysis

The confirmatory unit is the source-intent cluster, not the 5 repeated episodes. The minimum design therefore provides 12 intent clusters and at least 3 project clusters. Replications improve within-intent precision but do not create independent degrees of freedom.

Before data collection, choose a practically meaningful ordinal delta `d`, target power `0.80`, two-sided alpha `0.05`, and the planned cluster-level sign-flip test. The signed cluster contrasts and bootstrap procedure are then fixed; changing `d`, alpha, or the clustering unit after seeing outcomes is prohibited.

The preregistered calculation is implemented by `protocol.power.estimate_sign_flip_power` (Monte Carlo seed, cluster count, standardized effect, alpha, and simulation count are exported). `protocol.power.sensitivity_table` produces the effect-size grid for the methods appendix; it does not consume observed labels or outcomes.

The repository exports the exact design counts and split manifest. If the achieved number of independent intents or projects is below the preregistered minimum, the result is labelled pilot/descriptive and no confirmatory claim is made.

The current seven-intent seed is intentionally insufficient and must not be padded. A later revision must record the achieved effect-size sensitivity table and the rationale for the final cluster count in the run manifest.
