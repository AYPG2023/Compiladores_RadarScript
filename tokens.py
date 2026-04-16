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
        token_label = TOKEN_EXPORT_LABELS.get(self.token_type, self.token_type.value)
        rendered_lexeme = self._render_lexeme()
        return f"{token_label:<22} {rendered_lexeme:<24} linea={self.line:<4} columna={self.column}"

    def _render_lexeme(self) -> str:
        if self.token_type == TokenType.EOF:
            return "EOF"
        return self.lexeme


TOKEN_EXPORT_LABELS: dict[TokenType, str] = {
    TokenType.PROGRAMA: "PALABRA_RESERVADA",
    TokenType.SI: "PALABRA_RESERVADA",
    TokenType.ENTONCES: "PALABRA_RESERVADA",
    TokenType.FIN: "PALABRA_RESERVADA",
    TokenType.MIENTRAS: "PALABRA_RESERVADA",
    TokenType.HACER: "PALABRA_RESERVADA",
    TokenType.VERDADERO: "BOOLEANO_LITERAL",
    TokenType.FALSO: "BOOLEANO_LITERAL",
    TokenType.ALERTA: "PALABRA_RESERVADA",
    TokenType.REPORTE: "PALABRA_RESERVADA",
    TokenType.ENTERO: "TIPO",
    TokenType.DECIMAL: "TIPO",
    TokenType.CADENA: "TIPO",
    TokenType.BOOLEANO: "TIPO",
    TokenType.IDENTIFIER: "IDENTIFICADOR",
    TokenType.INTEGER: "NUMERO_ENTERO",
    TokenType.DECIMAL_LITERAL: "NUMERO_DECIMAL",
    TokenType.STRING: "CADENA_LITERAL",
    TokenType.PLUS: "OPERADOR_ARITMETICO",
    TokenType.MINUS: "OPERADOR_ARITMETICO",
    TokenType.STAR: "OPERADOR_ARITMETICO",
    TokenType.SLASH: "OPERADOR_ARITMETICO",
    TokenType.GREATER: "OPERADOR_RELACIONAL",
    TokenType.LESS: "OPERADOR_RELACIONAL",
    TokenType.EQUAL_EQUAL: "OPERADOR_RELACIONAL",
    TokenType.GREATER_EQUAL: "OPERADOR_RELACIONAL",
    TokenType.LESS_EQUAL: "OPERADOR_RELACIONAL",
    TokenType.NOT_EQUAL: "OPERADOR_RELACIONAL",
    TokenType.ASSIGN: "OPERADOR_ASIGNACION",
    TokenType.LEFT_PAREN: "PARENTESIS_IZQUIERDO",
    TokenType.RIGHT_PAREN: "PARENTESIS_DERECHO",
    TokenType.SEMICOLON: "PUNTO_Y_COMA",
    TokenType.COMMENT: "COMENTARIO",
    TokenType.EOF: "FIN_DE_ARCHIVO",
}
