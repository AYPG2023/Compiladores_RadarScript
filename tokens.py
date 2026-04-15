from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenType(str, Enum):
    PROGRAMA = "PROGRAMA"
    ENTERO = "ENTERO"
    DECIMAL = "DECIMAL"
    CADENA = "CADENA"
    BOOLEANO = "BOOLEANO"
    SI = "SI"
    ENTONCES = "ENTONCES"
    FIN = "FIN"
    MIENTRAS = "MIENTRAS"
    HACER = "HACER"
    VERDADERO = "VERDADERO"
    FALSO = "FALSO"
    ALERTA = "ALERTA"
    REPORTE = "REPORTE"
    IDENTIFIER = "IDENTIFIER"
    INTEGER = "INTEGER"
    DECIMAL_LITERAL = "DECIMAL_LITERAL"
    STRING = "STRING"
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    GREATER = "GREATER"
    LESS = "LESS"
    EQUAL_EQUAL = "EQUAL_EQUAL"
    GREATER_EQUAL = "GREATER_EQUAL"
    LESS_EQUAL = "LESS_EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    ASSIGN = "ASSIGN"
    LEFT_PAREN = "LEFT_PAREN"
    RIGHT_PAREN = "RIGHT_PAREN"
    SEMICOLON = "SEMICOLON"
    COMMENT = "COMMENT"
    EOF = "EOF"


RESERVED_WORDS: dict[str, TokenType] = {
    "programa": TokenType.PROGRAMA,
    "entero": TokenType.ENTERO,
    "decimal": TokenType.DECIMAL,
    "cadena": TokenType.CADENA,
    "booleano": TokenType.BOOLEANO,
    "si": TokenType.SI,
    "entonces": TokenType.ENTONCES,
    "fin": TokenType.FIN,
    "mientras": TokenType.MIENTRAS,
    "hacer": TokenType.HACER,
    "verdadero": TokenType.VERDADERO,
    "falso": TokenType.FALSO,
    "alerta": TokenType.ALERTA,
    "reporte": TokenType.REPORTE,
}


@dataclass(frozen=True, slots=True)
class Token:
    token_type: TokenType
    lexeme: str
    line: int
    column: int

    def to_lex_row(self) -> str:
        return f"{self.token_type.value:<18} {self.lexeme!r:<24} line={self.line:<4} column={self.column}"
