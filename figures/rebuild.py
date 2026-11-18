"""Rebuild the figures from their drawing sources and fixed aggregate inputs."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent


def run(command):
    subprocess.run(command, cwd=HERE, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lang', choices=['en', 'zh', 'both'], default='both')
    parser.add_argument('--figures', default='all', help='all or comma-separated numbers 1-7')
    parser.add_argument('--output-dir', type=Path, default=HERE / 'output')
    parser.add_argument('--node', default=os.environ.get('NODE', 'node'))
    parser.add_argument('--artifact-module', default=os.environ.get('ARTIFACT_TOOL_MODULE'))
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--check-reference', action='store_true', help='Require pixel equality with png/ reference files')
    args = parser.parse_args()
    numbers = list(range(1, 8)) if args.figures == 'all' else sorted(set(map(int, args.figures.split(','))))
    if not numbers or any(n not in range(1, 8) for n in numbers):
        parser.error('--figures must contain numbers 1-7')
    languages = ['en', 'zh'] if args.lang == 'both' else [args.lang]
    output = args.output_dir.resolve()
    for folder in ['png', 'source', 'native', 'data']:
        if output.is_relative_to(HERE / folder):
            parser.error('Use a generated-output directory, not a reference or source directory')
    for lang in languages:
        for number in numbers:
            target = output / lang / f'Figure_{number:02d}.png'
            if target.exists() and not args.overwrite:
                parser.error(f'Output exists: {target}; use a new output directory or --overwrite')
    native = [n for n in numbers if n != 1]
    if native and not (Path(args.node).is_file() or shutil.which(args.node)):
        parser.error('Node.js is required for Figures 2-7; provide --node or use --figures 1')
    output.mkdir(parents=True, exist_ok=True)
    if 1 in numbers:
        folder = output / 'full' / 'figure1'
        run([sys.executable, '-B', '-X', 'utf8', str(HERE / 'source' / 'figure_01.py'), '--lang', args.lang, '--output-dir', str(folder)])
        for lang in languages:
            target = output / lang
            target.mkdir(parents=True, exist_ok=True)
            for ext in ['png', 'svg']:
                shutil.copyfile(folder / f'Figure_01_{lang}.{ext}', target / f'Figure_01.{ext}')
    if native:
        command = [args.node, str(HERE / 'render_native.mjs'), '--lang', args.lang,
                   '--figures', ','.join(map(str, native)), '--output-dir', str(output / 'full' / 'native')]
        if args.artifact_module:
            command += ['--artifact-module', args.artifact_module]
        if args.overwrite:
            command += ['--overwrite']
        run(command)
        for lang in languages:
            (output / lang).mkdir(parents=True, exist_ok=True)
            for number in native:
                source = output / 'full' / 'native' / lang / f'Figure_{number:02d}_full.png'
                image = Image.open(source).convert('RGB')
                bbox = ImageChops.difference(image, Image.new('RGB', image.size, 'white')).getbbox()
                if bbox is None:
                    raise ValueError(f'Empty figure: {source.name}')
                # Preserve full width; remove only blank vertical margins, with40px padding.
                image = image.crop((0, max(0, bbox[1] - 40), image.width, min(image.height, bbox[3] + 40)))
                image.save(output / lang / f'Figure_{number:02d}.png', dpi=(500, 500))
    report = []
    for lang in languages:
        for number in numbers:
            generated = output / lang / f'Figure_{number:02d}.png'
            reference = HERE / 'png' / lang / f'Figure_{number:02d}.png'
            a = Image.open(generated).convert('RGB')
            b = Image.open(reference).convert('RGB')
            equal = a.size == b.size and ImageChops.difference(a, b).getbbox() is None
            report.append({'language': lang, 'figure': number, 'file': f'{lang}/{generated.name}',
                           'pixels': list(a.size), 'sha256': hashlib.sha256(generated.read_bytes()).hexdigest(),
                           'reference_pixels_equal': equal})
    (output / 'render_check.json').write_text(json.dumps({'figures': report}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Generated {len(report)} figures; {sum(r["reference_pixels_equal"] for r in report)} match the reference pixels.')
    if args.check_reference and not all(r['reference_pixels_equal'] for r in report):
        raise SystemExit('Pixel comparison failed; check fonts, source edits, aggregate inputs and renderer version.')


if __name__ == '__main__':
    main()
