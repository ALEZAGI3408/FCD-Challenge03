#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Ejecuta el notebook del Challenge 03 de extremo a extremo.

Regenera figures/, outputs/*.html y outputs/results.json a partir de los datos crudos.
El notebook es la única fuente de verdad del análisis; este script sólo lo orquesta.

Uso:  python scripts/run_analysis.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "notebooks" / "Challenge_03_Geo_Temporal_Redes.ipynb"


def main() -> int:
    if not NOTEBOOK.exists():
        print(f"ERROR: no se encuentra {NOTEBOOK}", file=sys.stderr)
        return 1

    print(f"Ejecutando {NOTEBOOK.name} ...")
    resultado = subprocess.run(
        [sys.executable, "-m", "jupyter", "nbconvert",
         "--to", "notebook", "--execute", "--inplace",
         "--ExecutePreprocessor.timeout=900", str(NOTEBOOK)],
        cwd=ROOT,
    )
    if resultado.returncode != 0:
        print("ERROR: la ejecución del notebook falló.", file=sys.stderr)
        return resultado.returncode

    figuras = sorted((ROOT / "figures").glob("*.png"))
    interactivos = sorted((ROOT / "outputs").glob("*.html"))
    print(f"\n✔ {len(figuras)} figuras en figures/")
    print(f"✔ {len(interactivos)} visualizaciones interactivas en outputs/")
    print(f"✔ resultados en outputs/results.json")
    print("\nSiguiente paso:  python scripts/build_report.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
