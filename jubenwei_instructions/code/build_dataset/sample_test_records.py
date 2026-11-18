"""Draw a new grouped test sample; use rebuild_test_reference.py for the paper's fixed sample."""
import argparse
import hashlib
import json
import platform
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from build_common import new_output, resolve, sha256
from preprocess import normalize_pairs


def collect_groups(source_dir):
    """Group top-level XML files by the name before a final '-<digits>'."""
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        raise ValueError(f"Source directory does not exist: {source_dir}")
    files = sorted(
        (p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() == '.xml'),
        key=lambda p: p.name,
    )
    if not files:
        raise ValueError(f"No XML files found: {source_dir}")
    groups, source_files = {}, []
    source_row = 0
    for path in files:
        match = re.fullmatch(r'(.+?)-\d+', path.stem)
        group = match.group(1) if match else path.stem
        records = groups.setdefault(group, [])
        nodes = list(ET.parse(path).getroot().iter('ju'))
        source_files.append({'file': path.name, 'sha256': sha256(path), 'sentences': len(nodes)})
        for ju_index, node in enumerate(nodes, 1):
            source_row += 1
            records.append({
                'pair': [''.join(part.strip() for part in node.itertext()),
                         ET.tostring(node, encoding='unicode').strip()],
                'source_file': path.name,
                'ju_index_1based': ju_index,
                'source_row_1based': source_row,
                'group_row_1based': len(records) + 1,
            })
    if not source_row:
        raise ValueError('No ju sentence records found in the XML files')
    return groups, source_files


def sample_records(groups, per_group=200, seed=None):
    """Sample occurrences without replacement; retain every record in small groups."""
    if per_group < 1:
        raise ValueError('--per-group must be a positive integer')
    rng = random.Random(seed)
    pairs, index, summary = [], [], []
    for group in sorted(groups):
        records = groups[group]
        indices = (list(range(len(records))) if len(records) <= per_group
                   else rng.sample(range(len(records)), per_group))
        summary.append({'group': group, 'available': len(records), 'selected': len(indices)})
        for position in indices:
            record = records[position]
            pairs.append(record['pair'])
            index.append({
                'reference_row_1based': len(pairs), 'group': group,
                **{key: value for key, value in record.items() if key != 'pair'},
            })
    return pairs, index, summary


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', default='source_annotations')
    parser.add_argument('--per-group', type=int, default=200)
    parser.add_argument('--seed', type=int, default=None,
                        help='Optional seed for a repeatable new sample; not the historical test seed')
    parser.add_argument('--output-dir', default='reproduced/new_test_sample')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.per_group < 1:
        parser.error('--per-group must be a positive integer')
    source, destination = resolve(args.source_dir), resolve(args.output_dir)
    if destination.is_relative_to(source):
        parser.error('Output must be outside the source XML directory')
    if args.dry_run:
        print(json.dumps({'source_directory': str(source), 'output_directory': str(destination),
                          'per_group': args.per_group, 'seed': args.seed,
                          'new_random_sample': True, 'writes': False}))
        return
    if destination.exists():
        parser.error(f'Output already exists; choose a new directory: {destination}')
    groups, source_files = collect_groups(source)
    pairs, index, summary = sample_records(groups, args.per_group, args.seed)
    # Select raw ju occurrences first; only then apply the standard attribute normalization.
    reference = normalize_pairs(pairs)
    payloads = {
        'sampled_pairs.json': json_bytes(pairs),
        'reference.json': json_bytes(reference),
        'sentences.txt': ''.join(pair[0] + '\n' for pair in pairs).encode('utf-8'),
    }
    report = {
        'sampling': 'New sample; not the fixed paper test set',
        'per_group': args.per_group, 'seed': args.seed,
        'python_version': platform.python_version(),
        'grouping': "Filename prefix before a final '-<digits>'; otherwise the full stem",
        'ordering': 'Sorted groups and filenames; ju document order; sampled indices kept in draw order',
        'small_groups': 'Keep every record in source order when the group size is at most per_group',
        'source_records': sum(item['available'] for item in summary),
        'reference_records': len(reference), 'groups': summary, 'source_files': source_files,
        'retained_attributes': ['scp', 'fun', 'mod'],
        'serialization': 'UTF-8 JSON, two-space indentation and LF newlines',
        'output_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()},
        'records': index,
    }
    output = new_output(destination)
    for name, data in payloads.items():
        (output / name).write_bytes(data)
    (output / 'sampling_index.json').write_bytes(json_bytes(report))
    print(json.dumps({'groups': summary, 'records': len(reference), 'seed': args.seed,
                      'new_random_sample': True, 'output': str(output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
