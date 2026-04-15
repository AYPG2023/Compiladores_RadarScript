from __future__ import annotations

from pathlib import Path
from typing import Iterable

from errors import LexicalError
from tokens import RESERVED_WORDS, Token, TokenType


class Lexer:
    def __init__(self, source: str, emit_comments: bool = False) -> None:
        self.source = source
        self.emit_comments = emit_comments
        self.length = len(source)
        self.current = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []

        while not self._is_at_end():
            char = self._peek()

            if char in {" ", "\r", "\t"}:
                self._advance()
                continue

            if char == "\n":
                self._advance()
                continue

            if char.isalpha():
                tokens.append(self._consume_identifier_or_keyword())
                continue

            if char.isdigit():
                tokens.append(self._consume_number())
                continue

            if char == '"':
                tokens.append(self._consume_string())
                continue

            if char == "/" and self._peek_next() == "/":
                comment = self._consume_line_comment()
                if self.emit_comments:
                    tokens.append(comment)
                continue

            if char == "/" and self._peek_next() == "*":
                comment = self._consume_block_comment()
                if self.emit_comments:
                    tokens.append(comment)
                continue

            tokens.append(self._consume_symbol())

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

    def _consume_identifier_or_keyword(self) -> Token:
        line, column = self.line, self.column
        start = self.current

        self._advance()
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        lexeme = self.source[start:self.current]
        token_type = RESERVED_WORDS.get(lexeme, TokenType.IDENTIFIER)
        return Token(token_type, lexeme, line, column)

    def _consume_number(self) -> Token:
        line, column = self.line, self.column
        start = self.current

        while self._peek().isdigit():
            self._advance()

        if self._peek() == ".":
            if not self._peek_next().isdigit():
                raise LexicalError("Malformed decimal literal.", self.line, self.column)

            self._advance()
            while self._peek().isdigit():
                self._advance()

            lexeme = self.source[start:self.current]
            return Token(TokenType.DECIMAL_LITERAL, lexeme, line, column)

        lexeme = self.source[start:self.current]
        return Token(TokenType.INTEGER, lexeme, line, column)

    def _consume_string(self) -> Token:
        line, column = self.line, self.column
        self._advance()
        start = self.current

        while not self._is_at_end() and self._peek() != '"':
            if self._peek() == "\n":
                raise LexicalError("Unterminated string literal.", self.line, self.column)
            self._advance()

        if self._is_at_end():
            raise LexicalError("Unterminated string literal.", line, column)

        lexeme = self.source[start:self.current]
        self._advance()
        return Token(TokenType.STRING, lexeme, line, column)

    def _consume_line_comment(self) -> Token:
        line, column = self.line, self.column
        self._advance()
        self._advance()
        start = self.current

        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

        lexeme = self.source[start:self.current]
        return Token(TokenType.COMMENT, lexeme, line, column)

    def _consume_block_comment(self) -> Token:
        line, column = self.line, self.column
        self._advance()
        self._advance()
        start = self.current

        while not self._is_at_end():
            if self._peek() == "*" and self._peek_next() == "/":
                lexeme = self.source[start:self.current]
                self._advance()
                self._advance()
                return Token(TokenType.COMMENT, lexeme, line, column)
            self._advance()

        raise LexicalError("Unterminated block comment.", line, column)

    def _consume_symbol(self) -> Token:
        line, column = self.line, self.column
        char = self._advance()

        match char:
            case "+":
                return Token(TokenType.PLUS, char, line, column)
            case "-":
                return Token(TokenType.MINUS, char, line, column)
            case "*":
                return Token(TokenType.STAR, char, line, column)
            case "/":
                return Token(TokenType.SLASH, char, line, column)
            case "(":
                return Token(TokenType.LEFT_PAREN, char, line, column)
            case ")":
                return Token(TokenType.RIGHT_PAREN, char, line, column)
            case ";":
                return Token(TokenType.SEMICOLON, char, line, column)
            case ">":
                if self._match("="):
                    return Token(TokenType.GREATER_EQUAL, ">=", line, column)
                return Token(TokenType.GREATER, char, line, column)
            case "<":
                if self._match("="):
                    return Token(TokenType.LESS_EQUAL, "<=", line, column)
                return Token(TokenType.LESS, char, line, column)
            case "=":
                if self._match("="):
                    return Token(TokenType.EQUAL_EQUAL, "==", line, column)
                return Token(TokenType.ASSIGN, char, line, column)
            case "!":
                if self._match("="):
                    return Token(TokenType.NOT_EQUAL, "!=", line, column)
                raise LexicalError("Unexpected character '!'. Did you mean '!='?", line, column)
            case _:
                raise LexicalError(f"Unexpected character {char!r}.", line, column)

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.current] != expected:
            return False

        self._advance()
        return True

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        next_index = self.current + 1
        if next_index >= self.length:
            return "\0"
        return self.source[next_index]

    def _advance(self) -> str:
        char = self.source[self.current]
        self.current += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def _is_at_end(self) -> bool:
        return self.current >= self.length


def tokenize_file(file_path: str | Path, emit_comments: bool = False) -> list[Token]:
    path = Path(file_path)
    source = path.read_text(encoding="utf-8")
    lexer = Lexer(source=source, emit_comments=emit_comments)
    return lexer.tokenize()


def export_tokens(tokens: Iterable[Token], output_path: str | Path) -> Path:
    path = Path(output_path)
    content = "\n".join(token.to_lex_row() for token in tokens)
    path.write_text(content + "\n", encoding="utf-8")
    return path


def analyze_file(file_path: str | Path, output_path: str | Path = "salida.lex", emit_comments: bool = False) -> list[Token]:
    tokens = tokenize_file(file_path=file_path, emit_comments=emit_comments)
    export_tokens(tokens=tokens, output_path=output_path)
    return tokens
