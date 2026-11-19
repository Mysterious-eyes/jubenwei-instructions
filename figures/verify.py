"""Verify reference figures, package hashes and fixed aggregate statistics."""
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8-sig'))
    for item in manifest['files']:
        path = (ROOT / item['path']).resolve()
        assert path.is_relative_to(ROOT), item['path']
        assert path.is_file(), item['path']
        assert path.stat().st_size == item['bytes'], item['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], item['path']
    data = json.loads((ROOT / 'data' / 'figure_data.json').read_text(encoding='utf-8-sig'))
    tasks = data['tasks']
    assert len(tasks) == 15
    assert [r['id'] for r in tasks] == [f'A{i}' for i in range(1, 15)] + ['M0']
    counts = data['counts']
    assert counts['test_records'] == 1200
    assert counts['test_unique_whitespace_normalized_texts'] == 1100
    assert counts['source_records'] - counts['excluded_matching_source_records'] == counts['training_sources'] == 3635
    assert counts['training_sources'] + 12000 + 107 == counts['training_examples'] == 15742
    assert counts['shared_clause_only_records_retained'] == 88
    assert sum(r['full_n'] for r in tasks) == 392871
    assert sum(r['training_n'] for r in tasks) == 15742
    figs = {r['number']: r for r in data['figures']}
    assert [r['stem'] for r in figs[5]['panels'][0]['rows']] == [r['stem'] for r in tasks]
    for row in figs[5]['panels'][0]['rows']:
        values = [row[k] for k in ['p10', 'p25', 'median', 'p75', 'p90']]
        assert values[0] > 0 and values == sorted(values), row['stem']
    assert sum(r['count'] for r in figs[5]['panels'][1]['rows']) == 392871
    assert [sum(r['count'] for r in panel['rows']) for panel in figs[6]['panels']] == [17240, 5325, 5177]
    assert next(r for r in figs[6]['panels'][0]['rows'] if r['code'] == 'VOCC')['count'] == 1
    conditions = figs[7]['conditions']
    assert len(conditions) == 6
    for r in conditions:
        assert r['total'] == r['valid'] + r['invalid'] == 1200
        assert r['valid'] == r['text_consistent'] + r['text_mismatch']
        assert len(r['metrics']['f1_percent']) == 4
        assert math.isclose(r['metrics']['all_input_structure_percent'], r['structure_correct'] / 1200 * 100)
    expected_pngs = {f'png/{lang}/Figure_{number:02d}.png'
                     for lang in ['en', 'zh'] for number in range(1, 8)}
    indexed_paths = [item['path'] for item in manifest['files']]
    assert len(indexed_paths) == len(set(indexed_paths)), 'Duplicate manifest entries'
    actual_pngs = {str(path.relative_to(ROOT)).replace('\\', '/')
                   for path in (ROOT / 'png').rglob('*.png')}
    assert actual_pngs == expected_pngs, 'Expected seven PNGs in each language'
    assert expected_pngs <= set(indexed_paths), 'A reference PNG is missing from the manifest'
    print(f'PASS: {len(manifest["files"])} package files, 14 reference PNGs and all aggregate checks.')


if __name__ == '__main__':
    main()
