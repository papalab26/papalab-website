"""Build an offline, single-file playtest copy; does not publish the website."""
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('output', help='Destination HTML file outside the source folder')
args = parser.parse_args()
root = Path(__file__).resolve().parent
html = (root / 'index.html').read_text(encoding='utf-8')
styles = (root / 'style.css').read_text(encoding='utf-8')
parts = []
for name in ['rules', 'questions', 'battle', 'art', 'audio', 'game']:
    source = (root / f'js/{name}.mjs').read_text(encoding='utf-8')
    source = '\n'.join(line for line in source.splitlines() if not line.startswith('import '))
    for declaration in ['class', 'function', 'const']:
        source = source.replace(f'export {declaration} ', f'{declaration} ')
    parts.append(source)
html = html.replace('<link rel="stylesheet" href="style.css">', '<style>' + styles + '</style>')
html = html.replace('<script type="module" src="js/game.mjs"></script>', '<script>' + '\n'.join(parts) + '</script>')
html = html.replace('href="../../../"', 'href="https://papalab26.com/"')
output = Path(args.output).resolve()
if output == root / 'index.html':
    raise SystemExit('Do not overwrite the source index.html')
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(html, encoding='utf-8')
print(output)
