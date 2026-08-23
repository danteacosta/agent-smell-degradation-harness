# Pre-pilot corpus screening

Status: evidence screening only. No source below is admitted to the pre-pilot
until the exact redistributed text, license, project identity, hashes,
near-clone review, and manipulation check are recorded in the frozen corpus
manifest.

## Decision summary

The main acquisition risk is not finding public requirements. It is finding
requirements that can be redistributed and deliberately transformed into a
missing-condition variant while preserving an auditable project boundary.
"Publicly available" and "hosted on Zenodo" do not establish those rights.

The current screening found two promising CC-licensed critical-systems case
studies, several conditional sources, and three sources that must not be used
without additional permission. It does not yet support the 12-intent corpus.

## Screened sources

| Source | License evidence | Project structure | Task/oracle fit | Decision |
| --- | --- | --- | --- | --- |
| [SHARCS Tokeneer and LevelCrossing](https://doi.org/10.5258/SOTON/D2957) | Repository states Creative Commons Attribution for both archives and README | Two explicitly separated case studies | Strong if the archives expose natural-language requirements linked to the Event-B models | **Priority due diligence**; inspect and retain at most independently auditable requirements |
| [RailwayReq Corpus](https://doi.org/10.5281/zenodo.11263941) | MaRDI records CC BY 4.0 for the corpus | Railway-domain technical documents; project granularity still unclear | Strong constraint extraction, but the corpus is derived from PURE | **Conditional**; obtain curator confirmation that the CC license covers redistributed requirement text and transformations |
| [Explainability-needs elicitation dataset](https://doi.org/10.5281/zenodo.15793300) | Dataset states CC BY 4.0 and includes a license file | One elicitation study with multiple needs, not clearly multiple software projects | Useful for clarification or external-validity work; weaker for executable acceptance criteria | **Secondary only**; do not count as multiple projects without source evidence |
| [Generated explainability requirements from user reviews](https://doi.org/10.5281/zenodo.15839753) | Dataset states CC BY 4.0 | Derived/generated artifacts from one study | Useful for robustness, but generated requirements are not independent real source intents | **Exploratory only**; exclude from the primary pre-pilot corpus |
| [PURE v2](https://doi.org/10.5281/zenodo.7118517) | Record explicitly says the curators are unaware of license or IP rights on the underlying requirements; license field is blank | 79 documents | High topical relevance but unacceptable rights ambiguity | **Reject by default**; use only a separately licensed original document with provenance |
| [ARTA requirements-smell dataset](https://doi.org/10.5281/zenodo.4266727) | Public record exposes no license | 4,752 requirements from 24 projects | Relevant smells and project diversity | **Reject until written reuse and transformation permission is obtained** |
| [Software Requirements Data Set](https://doi.org/10.5281/zenodo.7897601) | Aggregates PURE, Hayes, Dalpiaz and web sources; per-record rights are not established by the landing page | Multiple mixed collections | Potentially useful for discovery | **Do not ingest as one licensed corpus**; trace every retained record to an independently licensed origin |

## Admission rule

A candidate intent is admitted only when all of the following are true:

1. the exact natural-language source is redistributable and allows the intended
   research transformation, or written permission is archived;
2. one stable project ID is defensible and is not inferred from a filename alone;
3. the requirement contains at least one independently auditable,
   test-relevant condition;
4. removing exactly that condition creates incompleteness without introducing
   ambiguity, inconsistency, unverifiability, or a changed underlying intent;
5. clean and defective texts, the removed constraint, license, source URL,
   retrieval metadata, and canonical hashes are recorded;
6. near-clones, paraphrases, excerpts from the same parent requirement, and
   cross-dataset duplicates remain in one project and source-intent group;
7. the record is not selected because a model or detector already failed on it.

## Minimum acquisition path

1. Inspect the two SHARCS archives first. They have the strongest current
   combination of explicit license, separate projects, and independent formal
   models that may support constraint auditing.
2. Contact the RailwayReq curator about derivative-use coverage before copying
   requirement text into the repository.
3. Contact the ARTA curator for explicit redistribution and transformation
   permission; its project diversity would be valuable if permission is granted.
4. Find at least three additional independently licensed project sources. Do
   not manufacture project diversity by treating documents, modules, or
   requirement sections as separate projects.
5. Construct more than 12 candidates, blind the manipulation review, and retain
   exactly 12 only after the license, clone, project, and manipulation gates.

If fewer than 12 eligible intents remain, the pre-pilot stays blocked. The
correct response is to acquire more sources or narrow the meeting request, not
to pad the corpus with paraphrases.

## Questions for the advisor

- Is a pre-pilot spanning critical systems and ordinary software preferable to
  a narrower but better-controlled critical-systems corpus?
- May written author permission supplement a missing machine-readable license?
- Should the pre-pilot require six projects now, or reserve that diversity gate
  for the 24-intent feasibility pilot while still preventing single-project
  dominance?
- Who can serve as the independent manipulation reviewer and adjudicator?
