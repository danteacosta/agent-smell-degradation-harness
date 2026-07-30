# Agent-smell benchmark V4

V4 is a versioned metadata layer over the local paired-requirement seed. Each record documents its source, license, immutable source hash, intent-preservation review, injected manipulation, one-defect review, natural-variant status, and contamination note.

The dataset remains offline-first. It does not claim that the seed is representative of production requirements or that its synthetic variants are naturally occurring. `natural_variant` is false unless separately documented natural-source evidence is added.

Executable and reference-based scores are primary benchmark evidence. Human annotation, adjudication, and any LLM judge are independent label-plane evidence and must not leak into feature-plane extraction.
