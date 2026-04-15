from __future__ import annotations

import sys
from pathlib import Path

from errors import LexicalError, ParseError, SemanticError
from lexer import export_tokens, tokenize_file
from parser import parse_tokens
from semantic import analyze_semantics


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python main.py <input.rdr> [output.lex] [output.sym]")
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("salida.lex")
    symbols_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("salida.sym")

    try:
        tokens = tokenize_file(file_path=input_path)
        export_tokens(tokens=tokens, output_path=output_path)
        program = parse_tokens(tokens)
        semantic_result = analyze_semantics(program=program, output_path=symbols_path)
    except FileNotFoundError:
        print(f"Input file not found: {input_path}")
        return 1
    except (LexicalError, ParseError, SemanticError) as error:
        print(error)
        return 1

    print(
        f"Generated {len(tokens)} tokens in {output_path} and "
        f"{len(semantic_result.symbol_table.values())} symbols in {symbols_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
