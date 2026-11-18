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
    assert sum(r['full_n'] for r in tasks) == 392871
    assert sum(r['training_n'] for r in tasks) == 15923
    figs = {r['number']: r for r in data['figures']}
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
    snapshots = json.loads((ROOT / 'data' / 'published_pngs.json').read_text(encoding='utf-8-sig'))['figures']
    assert len(snapshots) == 14
    for r in snapshots:
        assert hashlib.sha256((ROOT / r['file']).read_bytes()).hexdigest() == r['sha256']
    print(f'PASS: {len(manifest["files"])} package files, 14 reference PNGs and all aggregate checks.')


if __name__ == '__main__':
    main()
