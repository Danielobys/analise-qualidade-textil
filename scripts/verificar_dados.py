"""Verifica equivalência entre CSV tratado e snapshot, sem dependências externas."""
from pathlib import Path
import csv
import json
import math

ROOT = Path(__file__).resolve().parents[1]
ALIASES = dict(zip(
    ['Data', 'Fornecedor', 'Lote', 'Tipo de Malha', 'Cor', 'Gramatura', 'Torção', 'Defeito', 'Status'],
    ['date', 'supplier', 'lot', 'fabric', 'color', 'weight', 'twist', 'defect', 'status']))

def main():
    with (ROOT / 'data/inspecoes_malha_tratada.csv').open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        assert set(reader.fieldnames) == set(ALIASES), 'Colunas inesperadas'
        expected = []
        for row in reader:
            r = {alias: row[key] for key, alias in ALIASES.items()}
            for field in ('weight', 'twist'):
                r[field] = float(r[field]) if r[field] else None
                assert r[field] is None or math.isfinite(r[field]), 'Medição não finita'
            assert r['status'] in ('Aprovado', 'Reprovado'), 'Status inválido'
            r['rejected'] = int(r['status'] == 'Reprovado')
            expected.append(r)
    assert expected, 'Base vazia'
    assert len({r['lot'] for r in expected}) == len(expected), 'Lotes duplicados'
    snapshot = json.loads((ROOT / 'dashboard/app/src/data.json').read_text(encoding='utf-8'))
    actual = snapshot['queries']['inspections']['rows']
    assert sorted(expected, key=lambda r:r['lot']) == sorted(actual, key=lambda r:r['lot']), 'Snapshot diverge do CSV: atualize e recompile'
    rejected = sum(r['rejected'] for r in expected)
    print(f'CSV e snapshot equivalentes: {len(expected)} lotes, {rejected} reprovados, {rejected/len(expected):.4%}.')

if __name__ == '__main__':
    main()
