"""Copia o compilado validado para a pasta do GitHub Pages."""
from pathlib import Path
import json
import shutil
from verificar_dados import main as verificar

ROOT = Path(__file__).resolve().parents[1]
verificar()
source = ROOT / 'dashboard/app/dist'
target = ROOT / 'docs'
assert (source/'index.html').is_file(), 'Compile o dashboard primeiro'
snapshots = list(source.glob('snapshot.*.json'))
assert len(snapshots) == 1, 'Esperado um snapshot compilado'
authored = json.loads((ROOT/'dashboard/app/src/data.json').read_text(encoding='utf-8'))
compiled = json.loads(snapshots[0].read_text(encoding='utf-8'))
assert compiled == authored, 'Build desatualizado: recompile'
target.mkdir(exist_ok=True)
for file in source.iterdir():
    if file.is_file():
        shutil.copy2(file, target/file.name)
(target/'.nojekyll').touch()
print('Site preparado em docs. Selecione main /docs no GitHub Pages.')
