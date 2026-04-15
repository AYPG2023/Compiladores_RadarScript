from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from errors import SemanticError
from parser import (
    AssignmentNode,
    BinaryExpressionNode,
    CallNode,
    IdentifierNode,
    IfNode,
    LiteralNode,
    ProgramNode,
    UnaryExpressionNode,
    VariableDeclarationNode,
    WhileNode,
)
from symbol_table import Symbol, SymbolTable, export_symbol_table
from tokens import TokenType


@dataclass(frozen=True, slots=True)
class SemanticResult:
    symbol_table: SymbolTable


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.symbol_table = SymbolTable()

    def analyze(self, program: ProgramNode) -> SemanticResult:
        for statement in program.statements:
            self._analyze_statement(statement)
        return SemanticResult(symbol_table=self.symbol_table)

    def _analyze_statement(self, statement: object) -> None:
        if isinstance(statement, VariableDeclarationNode):
            self._analyze_variable_declaration(statement)
            return
        if isinstance(statement, AssignmentNode):
            self._analyze_assignment(statement)
            return
        if isinstance(statement, IfNode):
            self._analyze_conditional(statement.condition)
            for nested_statement in statement.body:
                self._analyze_statement(nested_statement)
            return
        if isinstance(statement, WhileNode):
            self._analyze_conditional(statement.condition)
            for nested_statement in statement.body:
                self._analyze_statement(nested_statement)
            return
        if isinstance(statement, CallNode):
            self._analyze_call(statement)
            return

    def _analyze_variable_declaration(self, statement: VariableDeclarationNode) -> None:
        if self.symbol_table.contains(statement.name):
            raise SemanticError(
                f"Identifier '{statement.name}' is already declared.",
                statement.line,
                statement.column,
            )

        initial_value: str | None = None
        if statement.initializer is not None:
            expression_type = self._resolve_expression_type(statement.initializer)
            self._ensure_type_compatibility(
                expected_type=statement.variable_type,
                actual_type=expression_type,
                line=statement.initializer.line,
                column=statement.initializer.column,
            )
            initial_value = self._render_expression(statement.initializer)

        self.symbol_table.declare(
            Symbol(
                name=statement.name,
                symbol_type=statement.variable_type,
                declaration_line=statement.line,
                initial_value=initial_value,
            )
        )

    def _analyze_assignment(self, statement: AssignmentNode) -> None:
        symbol = self.symbol_table.get(statement.name)
        if symbol is None:
            raise SemanticError(
                f"Identifier '{statement.name}' must be declared before assignment.",
                statement.line,
                statement.column,
            )

        expression_type = self._resolve_expression_type(statement.expression)
        self._ensure_type_compatibility(
            expected_type=symbol.symbol_type,
            actual_type=expression_type,
            line=statement.expression.line,
            column=statement.expression.column,
        )

    def _analyze_conditional(self, expression: object) -> None:
        expression_type = self._resolve_expression_type(expression)
        if expression_type != "booleano":
            raise SemanticError(
                "Condition expressions must evaluate to 'booleano'.",
                expression.line,
                expression.column,
            )

    def _analyze_call(self, statement: CallNode) -> None:
        if len(statement.arguments) > 1:
            raise SemanticError(
                f"Call '{statement.callee}' accepts at most one argument.",
                statement.line,
                statement.column,
            )

        for argument in statement.arguments:
            self._resolve_expression_type(argument)

    def _resolve_expression_type(self, expression: object) -> str:
        if isinstance(expression, LiteralNode):
            return expression.value_type

        if isinstance(expression, IdentifierNode):
            symbol = self.symbol_table.get(expression.name)
            if symbol is None:
                raise SemanticError(
                    f"Identifier '{expression.name}' must be declared before use.",
                    expression.line,
                    expression.column,
                )
            return symbol.symbol_type

        if isinstance(expression, UnaryExpressionNode):
            operand_type = self._resolve_expression_type(expression.operand)
            if expression.operator.token_type != TokenType.MINUS or operand_type not in {"entero", "decimal"}:
                raise SemanticError(
                    "Unary '-' requires an 'entero' or 'decimal' operand.",
                    expression.line,
                    expression.column,
                )
            return operand_type

        if isinstance(expression, BinaryExpressionNode):
            return self._resolve_binary_type(expression)

        raise SemanticError("Unsupported expression node.", expression.line, expression.column)

    def _resolve_binary_type(self, expression: BinaryExpressionNode) -> str:
        left_type = self._resolve_expression_type(expression.left)
        right_type = self._resolve_expression_type(expression.right)
        operator_type = expression.operator.token_type

        if operator_type in {TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH}:
            if operator_type == TokenType.PLUS and left_type == right_type == "cadena":
                return "cadena"
            if left_type not in {"entero", "decimal"} or right_type not in {"entero", "decimal"}:
                raise SemanticError(
                    f"Operator '{expression.operator.lexeme}' requires numeric operands or string concatenation with '+'.",
                    expression.line,
                    expression.column,
                )
            if operator_type == TokenType.SLASH or "decimal" in {left_type, right_type}:
                return "decimal"
            return "entero"

        if operator_type in {
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        }:
            if left_type not in {"entero", "decimal"} or right_type not in {"entero", "decimal"}:
                raise SemanticError(
                    f"Operator '{expression.operator.lexeme}' requires numeric operands.",
                    expression.line,
                    expression.column,
                )
            return "booleano"

        if operator_type in {TokenType.EQUAL_EQUAL, TokenType.NOT_EQUAL}:
            if not self._types_are_compatible(left_type, right_type):
                raise SemanticError(
                    f"Cannot compare values of types '{left_type}' and '{right_type}'.",
                    expression.line,
                    expression.column,
                )
            return "booleano"

        raise SemanticError(
            f"Unsupported operator '{expression.operator.lexeme}'.",
            expression.line,
            expression.column,
        )

    def _ensure_type_compatibility(self, expected_type: str, actual_type: str, line: int, column: int) -> None:
        if not self._types_are_compatible(expected_type, actual_type):
            raise SemanticError(
                f"Type mismatch: expected '{expected_type}', found '{actual_type}'.",
                line,
                column,
            )

    def _types_are_compatible(self, left_type: str, right_type: str) -> bool:
        if left_type == right_type:
            return True
        return {left_type, right_type} == {"entero", "decimal"}

    def _render_expression(self, expression: object) -> str:
        if isinstance(expression, LiteralNode):
            return str(expression.value)
        if isinstance(expression, IdentifierNode):
            return expression.name
        if isinstance(expression, UnaryExpressionNode):
            return f"{expression.operator.lexeme}{self._render_expression(expression.operand)}"
        if isinstance(expression, BinaryExpressionNode):
            left = self._render_expression(expression.left)
            right = self._render_expression(expression.right)
            return f"({left} {expression.operator.lexeme} {right})"
        return "<expr>"


def analyze_semantics(program: ProgramNode, output_path: str | Path = "salida.sym") -> SemanticResult:
    analyzer = SemanticAnalyzer()
    result = analyzer.analyze(program)
    export_symbol_table(result.symbol_table.values(), output_path)
    return result
