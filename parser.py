from __future__ import annotations

from dataclasses import dataclass

from errors import ParseError
from tokens import Token, TokenType


LANGUAGE_TYPE_NAMES: dict[TokenType, str] = {
    TokenType.ENTERO: "entero",
    TokenType.DECIMAL: "decimal",
    TokenType.CADENA: "cadena",
    TokenType.BOOLEANO: "booleano",
}

DECLARATION_TOKENS = tuple(LANGUAGE_TYPE_NAMES.keys())


@dataclass(frozen=True, slots=True)
class Node:
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class ProgramNode(Node):
    name: str
    statements: list["StatementNode"]


@dataclass(frozen=True, slots=True)
class StatementNode(Node):
    pass


@dataclass(frozen=True, slots=True)
class ExpressionNode(Node):
    pass


@dataclass(frozen=True, slots=True)
class VariableDeclarationNode(StatementNode):
    variable_type: str
    name: str
    initializer: ExpressionNode | None


@dataclass(frozen=True, slots=True)
class AssignmentNode(StatementNode):
    name: str
    expression: ExpressionNode


@dataclass(frozen=True, slots=True)
class IfNode(StatementNode):
    condition: ExpressionNode
    body: list[StatementNode]


@dataclass(frozen=True, slots=True)
class WhileNode(StatementNode):
    condition: ExpressionNode
    body: list[StatementNode]


@dataclass(frozen=True, slots=True)
class CallNode(StatementNode):
    callee: str
    arguments: list[ExpressionNode]


@dataclass(frozen=True, slots=True)
class BinaryExpressionNode(ExpressionNode):
    left: ExpressionNode
    operator: Token
    right: ExpressionNode


@dataclass(frozen=True, slots=True)
class UnaryExpressionNode(ExpressionNode):
    operator: Token
    operand: ExpressionNode


@dataclass(frozen=True, slots=True)
class LiteralNode(ExpressionNode):
    value: object
    value_type: str


@dataclass(frozen=True, slots=True)
class IdentifierNode(ExpressionNode):
    name: str


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = self._discard_non_grammar_tokens(tokens)
        self.current = 0

    def parse(self) -> ProgramNode:
        program_token = self._consume(TokenType.PROGRAMA, "Expected 'programa' at the beginning of the source.")
        name = self._consume(TokenType.IDENTIFIER, "Expected program identifier after 'programa'.")
        self._consume(TokenType.SEMICOLON, "Expected ';' after program declaration.")

        statements = self._parse_block(stop_tokens={TokenType.EOF})
        self._consume(TokenType.EOF, "Unexpected tokens after program body.")
        return ProgramNode(name=name.lexeme, statements=statements, line=program_token.line, column=program_token.column)

    def _parse_block(self, stop_tokens: set[TokenType]) -> list[StatementNode]:
        statements: list[StatementNode] = []
        while not self._check_any(stop_tokens):
            statements.append(self._parse_statement())
        return statements

    def _parse_statement(self) -> StatementNode:
        if self._check_any(set(DECLARATION_TOKENS)):
            return self._parse_variable_declaration()
        if self._check(TokenType.IDENTIFIER):
            return self._parse_assignment()
        if self._match(TokenType.SI):
            return self._parse_if()
        if self._match(TokenType.MIENTRAS):
            return self._parse_while()
        if self._match(TokenType.ALERTA):
            return self._parse_call("alerta", self._previous())
        if self._match(TokenType.REPORTE):
            return self._parse_call("reporte", self._previous())

        token = self._peek()
        raise ParseError(f"Unexpected token '{token.lexeme or token.token_type.value}'.", token.line, token.column)

    def _parse_variable_declaration(self) -> VariableDeclarationNode:
        type_token = self._advance()
        identifier = self._consume(TokenType.IDENTIFIER, "Expected identifier in variable declaration.")
        initializer: ExpressionNode | None = None

        if self._match(TokenType.ASSIGN):
            initializer = self._parse_expression()

        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")
        return VariableDeclarationNode(
            variable_type=LANGUAGE_TYPE_NAMES[type_token.token_type],
            name=identifier.lexeme,
            initializer=initializer,
            line=type_token.line,
            column=type_token.column,
        )

    def _parse_assignment(self) -> AssignmentNode:
        identifier = self._consume(TokenType.IDENTIFIER, "Expected identifier.")
        self._consume(TokenType.ASSIGN, "Expected '=' in assignment.")
        expression = self._parse_expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after assignment.")
        return AssignmentNode(name=identifier.lexeme, expression=expression, line=identifier.line, column=identifier.column)

    def _parse_if(self) -> IfNode:
        keyword = self._previous()
        condition = self._parse_expression()
        self._consume(TokenType.ENTONCES, "Expected 'entonces' after if condition.")
        body = self._parse_block(stop_tokens={TokenType.FIN})
        self._consume(TokenType.FIN, "Expected 'fin' to close 'si' block.")
        return IfNode(condition=condition, body=body, line=keyword.line, column=keyword.column)

    def _parse_while(self) -> WhileNode:
        keyword = self._previous()
        condition = self._parse_expression()
        self._consume(TokenType.HACER, "Expected 'hacer' after while condition.")
        body = self._parse_block(stop_tokens={TokenType.FIN})
        self._consume(TokenType.FIN, "Expected 'fin' to close 'mientras' block.")
        return WhileNode(condition=condition, body=body, line=keyword.line, column=keyword.column)

    def _parse_call(self, callee: str, token: Token) -> CallNode:
        self._consume(TokenType.LEFT_PAREN, f"Expected '(' after '{callee}'.")
        arguments: list[ExpressionNode] = []
        if not self._check(TokenType.RIGHT_PAREN):
            arguments.append(self._parse_expression())
        self._consume(TokenType.RIGHT_PAREN, f"Expected ')' after arguments of '{callee}'.")
        self._consume(TokenType.SEMICOLON, f"Expected ';' after call to '{callee}'.")
        return CallNode(callee=callee, arguments=arguments, line=token.line, column=token.column)

    def _parse_expression(self) -> ExpressionNode:
        return self._parse_relational()

    def _parse_relational(self) -> ExpressionNode:
        expression = self._parse_term()
        relational_tokens = (
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.EQUAL_EQUAL,
            TokenType.NOT_EQUAL,
        )

        while self._match(*relational_tokens):
            operator = self._previous()
            right = self._parse_term()
            expression = BinaryExpressionNode(
                left=expression,
                operator=operator,
                right=right,
                line=operator.line,
                column=operator.column,
            )

        return expression

    def _parse_term(self) -> ExpressionNode:
        expression = self._parse_factor()

        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            right = self._parse_factor()
            expression = BinaryExpressionNode(
                left=expression,
                operator=operator,
                right=right,
                line=operator.line,
                column=operator.column,
            )

        return expression

    def _parse_factor(self) -> ExpressionNode:
        expression = self._parse_unary()

        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self._previous()
            right = self._parse_unary()
            expression = BinaryExpressionNode(
                left=expression,
                operator=operator,
                right=right,
                line=operator.line,
                column=operator.column,
            )

        return expression

    def _parse_unary(self) -> ExpressionNode:
        if self._match(TokenType.MINUS):
            operator = self._previous()
            operand = self._parse_unary()
            return UnaryExpressionNode(operator=operator, operand=operand, line=operator.line, column=operator.column)

        return self._parse_primary()

    def _parse_primary(self) -> ExpressionNode:
        if self._match(TokenType.INTEGER):
            token = self._previous()
            return LiteralNode(value=int(token.lexeme), value_type="entero", line=token.line, column=token.column)

        if self._match(TokenType.DECIMAL_LITERAL):
            token = self._previous()
            return LiteralNode(value=float(token.lexeme), value_type="decimal", line=token.line, column=token.column)

        if self._match(TokenType.STRING):
            token = self._previous()
            return LiteralNode(value=token.lexeme, value_type="cadena", line=token.line, column=token.column)

        if self._match(TokenType.VERDADERO):
            token = self._previous()
            return LiteralNode(value=True, value_type="booleano", line=token.line, column=token.column)

        if self._match(TokenType.FALSO):
            token = self._previous()
            return LiteralNode(value=False, value_type="booleano", line=token.line, column=token.column)

        if self._match(TokenType.IDENTIFIER):
            token = self._previous()
            return IdentifierNode(name=token.lexeme, line=token.line, column=token.column)

        if self._match(TokenType.LEFT_PAREN):
            expression = self._parse_expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after expression.")
            return expression

        token = self._peek()
        raise ParseError(f"Expected expression, found '{token.lexeme or token.token_type.value}'.", token.line, token.column)

    def _discard_non_grammar_tokens(self, tokens: list[Token]) -> list[Token]:
        return [token for token in tokens if token.token_type != TokenType.COMMENT]

    def _match(self, *token_types: TokenType) -> bool:
        for token_type in token_types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()

        token = self._peek()
        raise ParseError(message, token.line, token.column)

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return token_type == TokenType.EOF
        return self._peek().token_type == token_type

    def _check_any(self, token_types: set[TokenType]) -> bool:
        return self._peek().token_type in token_types

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().token_type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]


def parse_tokens(tokens: list[Token]) -> ProgramNode:
    parser = Parser(tokens)
    return parser.parse()
