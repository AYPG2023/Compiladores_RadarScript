from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class Symbol:
    name: str
    symbol_type: str
    declaration_line: int
    initial_value: str | None = None

    def to_sym_row(self) -> str:
        rendered_value = self.initial_value if self.initial_value is not None else "-"
        return (
            f"{self.name:<18} type={self.symbol_type:<10} "
            f"declared_at={self.declaration_line:<4} initial_value={rendered_value}"
        )


class SymbolTable:
    def __init__(self) -> None:
        self._symbols: dict[str, Symbol] = {}

    def declare(self, symbol: Symbol) -> None:
        self._symbols[symbol.name] = symbol

    def contains(self, name: str) -> bool:
        return name in self._symbols

    def get(self, name: str) -> Symbol | None:
        return self._symbols.get(name)

    def values(self) -> list[Symbol]:
        return list(self._symbols.values())


def export_symbol_table(symbols: Iterable[Symbol], output_path: str | Path) -> Path:
    path = Path(output_path)
    content = "\n".join(symbol.to_sym_row() for symbol in symbols)
    path.write_text(content + "\n", encoding="utf-8")
    return path
