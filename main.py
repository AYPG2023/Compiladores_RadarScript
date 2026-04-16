from __future__ import annotations

import argparse
from pathlib import Path

from compiler import CompilerPipeline
from ui import launch_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RadarScript compiler")
    parser.add_argument("input", nargs="?", help="Archivo .rdr a compilar en modo CLI")
    parser.add_argument("--run", action="store_true", help="Ejecuta el codigo objeto despues de compilar")
    parser.add_argument("--ui", action="store_true", help="Fuerza el arranque de la interfaz grafica")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.ui or not args.input:
        try:
            launch_app()
        except RuntimeError as error:
            print(error)
            return 1
        return 0

    pipeline = CompilerPipeline()
    result = pipeline.compile_file(Path(args.input))

    if not result.successful:
        print(result.error_report())
        return 1

    if result.artifacts is not None:
        print(f"LEX: {result.artifacts.lex_path}")
        print(f"SYM: {result.artifacts.sym_path}")
        print(f"INT: {result.artifacts.int_path}")
        print(f"OBJ: {result.artifacts.obj_path}")

    if args.run:
        pipeline.execute(result)
        if result.execution_result is not None:
            print(result.execution_result.output or "Sin salida.")
        if "ejecucion" in result.errors:
            print(result.errors["ejecucion"])
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
