#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATASET_DIR = ROOT / 'docs' / 'tutorial' / 'datasets'
DATASET_JSON_PATH = DATASET_DIR / 'training_real_world_dataset.json'
FASTA_PATH = DATASET_DIR / 'training_real_world_sequences.fasta'


def load_dataset() -> dict:
    return json.loads(DATASET_JSON_PATH.read_text(encoding='utf-8'))


def load_fasta() -> dict[str, str]:
    records: dict[str, str] = {}
    name: str | None = None
    chunks: list[str] = []
    for line in FASTA_PATH.read_text(encoding='utf-8').splitlines():
        if line.startswith('>'):
            if name is not None:
                records[name] = ''.join(chunks)
            name = line[1:].strip()
            chunks = []
        else:
            chunks.append(line.strip())
    if name is not None:
        records[name] = ''.join(chunks)
    return records


def apply_edits(seq: str, edits: list[dict]) -> str:
    new_seq = seq
    offset = 0
    for edit in edits:
        start = int(edit['start_1based']) - 1 + offset
        end = int(edit['end_1based']) + offset
        replacement = str(edit['replacement'])
        new_seq = new_seq[:start] + replacement + new_seq[end:]
        offset += len(replacement) - (end - start)
    return new_seq


def resolve_record(record_name: str, record_map: dict[str, dict], fasta_records: dict[str, str]) -> tuple[dict, str]:
    rec = record_map[record_name]
    if 'sequence_ref' in rec:
        base_name = str(rec['sequence_ref']).split(':', 1)[1]
        return rec, fasta_records[base_name]
    if 'derived_from' in rec:
        _, parent_seq = resolve_record(rec['derived_from'], record_map, fasta_records)
        return rec, apply_edits(parent_seq, list(rec.get('edits', [])))
    raise KeyError(record_name)


def write_bundle(case_id: str, out_dir: Path) -> None:
    dataset = load_dataset()
    fasta_records = load_fasta()
    record_map = {record['name']: record for record in dataset['records']}
    case_map = {case['case_id']: case for case in dataset['case_inputs']}
    if case_id not in case_map:
        raise SystemExit(f'Unknown case id: {case_id}')
    case_info = case_map[case_id]
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_records = []
    fasta_lines = []
    for record_name in case_info['records']:
        rec, seq = resolve_record(record_name, record_map, fasta_records)
        fasta_lines.append(f'>{record_name}')
        fasta_lines.append(seq)
        manifest_records.append({
            'name': record_name,
            'topology': rec.get('topology', 'linear'),
            'type': rec.get('type', 'unknown'),
            'origin': rec.get('origin', ''),
            'why_it_matters': rec.get('why_it_matters', ''),
        })
        (out_dir / f'{record_name}.fasta').write_text(f'>{record_name}\n{seq}\n', encoding='utf-8')
    (out_dir / 'records.fasta').write_text('\n'.join(fasta_lines) + '\n', encoding='utf-8')
    manifest = {
        'case': case_info,
        'records': manifest_records,
    }
    (out_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Wrote {out_dir / "records.fasta"}')
    print(f'Wrote {out_dir / "manifest.json"}')


def main() -> None:
    parser = argparse.ArgumentParser(description='Extract a ready-to-run Genome Forge tutorial case bundle.')
    parser.add_argument('--case', help='Case identifier such as A, K, or AJ')
    parser.add_argument('--out', help='Output directory for the bundle')
    parser.add_argument('--list-cases', action='store_true', help='List available cases and exit')
    args = parser.parse_args()

    dataset = load_dataset()
    if args.list_cases:
        for case in dataset['case_inputs']:
            print(f"{case['case_id']}: {case['title']} [{', '.join(case['records'])}]")
        return

    if not args.case or not args.out:
        parser.error('--case and --out are required unless --list-cases is used')
    write_bundle(args.case.upper(), Path(args.out))


if __name__ == '__main__':
    main()
