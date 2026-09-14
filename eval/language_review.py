"""Export draft first-reading forms, without models, results or human labels.

Give each reader only one form. Custody files and other forms are not part of
that handoff. Prior exposure must be recorded; exporting proves no blinding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random

from eval import language_controls


INSTRUCTIONS = """# Primeira leitura de requisitos — formulário individual

Somente este formulário deve ser entregue a este leitor. Não consulte outros
formulários, o mapeamento ou os resultados antes de registrar sua interpretação.
Registre exposição prévia aos exemplos, às outras versões ou aos resultados;
não se presume cegamento de quem já os conhece.

Para cada item, descreva a regra entendida, outras leituras plausíveis, contexto
ausente e confiança, justificando sua leitura. Não implemente o código: as
instruções de implementação abaixo são parte do contexto original observado.
A ausência de informação pode permanecer inconclusiva.

Rascunho ainda não distribuído. Não é anotação confirmatória de H1/H2.
"""

GUIDE = """# Revisão de candidatos — preparação offline

Entregue a cada leitor somente um par de arquivos Markdown/JSON em forms/.
Nunca entregue a pasta inteira: versões diferentes do mesmo grupo podem induzir
interpretações. custodian/ é material exclusivo do responsável. Registre a
atribuição e a exposição prévia e congele respostas individuais antes de uma
revisão comparativa da intenção, intervenção e categoria.

São seis formulários com quatro itens cada, um por grupo, e dez textos únicos.
As redações dos grupos de ambiguidade aparecem duas vezes; cada redação dos
controles aparece três vezes. As 24 posições não são participantes nem novas
observações experimentais. Participantes, independência, rubrica e distribuição
continuam pendentes; nenhum rótulo humano é criado.

Os textos vêm do perfil original language_controls_v1. Não há resultados de
modelo ou gabaritos nos formulários. Os exemplos são construídos e já tiveram
resultados publicados; a exposição anterior precisa ser declarada. Isto não
admite casos ao corpus, não estima poder estatístico e não valida H1/H2.

receipt.json é escrito por último e registra os hashes de todos os outros
arquivos. Sua ausência indica exportação incompleta. Cada nova revisão deve
usar um diretório novo; não sobrescreva formulários ou respostas existentes.
"""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def prepare_review(inventory: list[dict], seed: int = 20260914) -> dict[str, bytes]:
    """Prepare the supported original profile before any filesystem mutation."""
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if len(inventory) != 6 or len({c['id'] for c in inventory}) != 6:
        raise ValueError('unsupported original language profile')
    groups = {}
    for case in inventory:
        if any(not isinstance(case.get(k), str) or not case[k].strip()
               for k in ('id', 'cluster', 'clean', 'defective', 'scaffold')):
            raise ValueError('profile fields must contain text')
        for arm in ('clean', 'defective'):
            prompt = case[arm] + case['scaffold']
            groups.setdefault(case['cluster'], {}).setdefault(prompt, []).append(
                {'case_id': case['id'], 'arm': arm})
    sizes = {cluster: len(texts) for cluster, texts in groups.items()}
    if sizes != {'coordination_twin': 3, 'pronoun_twin': 3,
                 'threshold_control': 2, 'boolean_control': 2}:
        raise ValueError('unsupported original language profile shape')

    rng = random.Random(seed)
    items, by_cluster, custody = {}, {}, []
    for cluster, texts in sorted(groups.items()):
        prompts = sorted(texts)
        rng.shuffle(prompts)
        by_cluster[cluster] = []
        for prompt in prompts:
            item_id = 'R-' + _sha(f'{seed}:{len(items)}'.encode())[:12]
            items[item_id] = {
                'item_id': item_id, 'observed_requirement_and_interface': prompt,
                'interpretation': None, 'other_plausible_interpretations': None,
                'missing_context': None, 'confidence': None, 'rationale': None,
            }
            by_cluster[cluster].append(item_id)
            custody.append({'item_id': item_id, 'cluster': cluster,
                            'prompt_sha256': _sha(prompt.encode()), 'mapping': texts[prompt]})

    files, assignments = {}, []
    for number in range(6):
        selected = [ids[(number + offset) % len(ids)]
                    for offset, ids in enumerate(by_cluster.values())]
        rng.shuffle(selected)
        form_id = 'FORM-' + chr(65 + number)
        rows = [items[item_id] for item_id in selected]
        form = {'schema_version': 'candidate-interpretation-review/v1',
                'status': 'draft_not_distributed', 'form_id': form_id,
                'reviewer_id': None, 'prior_exposure_declared': None, 'items': rows}
        files[f'forms/{form_id}.json'] = _json(form)
        markdown = INSTRUCTIONS
        for row in rows:
            markdown += (f"\n## {row['item_id']}\n\n```text\n"
                         + row['observed_requirement_and_interface']
                         + '\n```\n\nInterpretação:\nOutras leituras plausíveis:\n'
                         + 'Contexto ausente:\nConfiança e justificativa:\n')
        files[f'forms/{form_id}.md'] = markdown.encode()
        assignments.append({'form_id': form_id, 'item_ids': selected})

    files['custodian/inventory.json'] = _json(inventory)
    files['custodian/manifest.json'] = _json({
        'schema_version': 'candidate-review-custody/v1', 'seed': seed,
        'status': 'not_for_annotators', 'profile': 'language_controls_v1',
        'items': custody, 'assignments': assignments, 'reviewer_assignments': [],
        'inventory_sha256': _sha(files['custodian/inventory.json']),
        'source_sha256': {Path(p).name: _sha(Path(p).read_bytes())
                          for p in (__file__, language_controls.__file__)},
    })
    files['README.md'] = GUIDE.encode()
    files['receipt.json'] = _json({
        'schema_version': 'draft-language-review-receipt/v1',
        'scope': 'constructed_candidate_first_reading_preparation',
        'confirmatory_eligible': False, 'distributed': False,
        'participants': 0, 'human_labels': 0, 'forms': 6, 'items_per_form': 4,
        'unique_prompts': 10, 'files': {name: _sha(raw) for name, raw in files.items()},
    })
    return files


def export_review(output: Path, seed: int = 20260914) -> dict:
    files = prepare_review(language_controls.cases(), seed)
    output = Path(output)
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name, raw in files.items():
        target = output / name
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
        target.chmod(0o600)
    return {'status': 'drafts_prepared', 'file_count': len(files),
            'confirmatory_eligible': False, 'distributed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path,
                        help='new directory under an existing private parent')
    parser.add_argument('--seed', type=int, default=20260914)
    args = parser.parse_args()
    print(json.dumps(export_review(args.output, args.seed), sort_keys=True))


if __name__ == '__main__':
    main()
