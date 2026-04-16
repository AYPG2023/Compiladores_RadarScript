from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

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
from semantic import SemanticResult


@dataclass(frozen=True, slots=True)
class IRInstruction:
    opcode: str
    arg1: str = "-"
    arg2: str = "-"
    result: str = "-"

    def to_text(self) -> str:
        return f"({self.opcode}, {self.arg1}, {self.arg2}, {self.result})"


@dataclass(frozen=True, slots=True)
class IntermediateProgram:
    program_name: str
    instructions: list[IRInstruction]
    temp_count: int
    label_count: int

    def to_text(self) -> str:
        return "\n".join(instruction.to_text() for instruction in self.instructions)


@dataclass(slots=True)
class IRGenerator:
    semantic_result: SemanticResult | None = None
    instructions: list[IRInstruction] = field(default_factory=list)
    _temp_counter: int = 0
    _label_counter: int = 0

    def generate(self, program: ProgramNode) -> IntermediateProgram:
        self.instructions.clear()
        self._temp_counter = 0
        self._label_counter = 0

        for statement in program.statements:
            self._emit_statement(statement)

        return IntermediateProgram(
            program_name=program.name,
            instructions=list(self.instructions),
            temp_count=self._temp_counter,
            label_count=self._label_counter,
        )

    def _emit_statement(self, statement: object) -> None:
        if isinstance(statement, VariableDeclarationNode):
            if statement.initializer is not None:
                value = self._emit_expression(statement.initializer)
                self.instructions.append(IRInstruction("=", value, "-", statement.name))
            return

        if isinstance(statement, AssignmentNode):
            value = self._emit_expression(statement.expression)
            self.instructions.append(IRInstruction("=", value, "-", statement.name))
            return

        if isinstance(statement, CallNode):
            argument = self._emit_expression(statement.arguments[0]) if statement.arguments else "-"
            self.instructions.append(IRInstruction(statement.callee.upper(), argument, "-", "-"))
            return

        if isinstance(statement, IfNode):
            end_label = self._next_label()
            condition = self._emit_expression(statement.condition)
            self.instructions.append(IRInstruction("JF", condition, "-", end_label))
            for nested_statement in statement.body:
                self._emit_statement(nested_statement)
            self.instructions.append(IRInstruction("LABEL", "-", "-", end_label))
            return

        if isinstance(statement, WhileNode):
            start_label = self._next_label()
            end_label = self._next_label()
            self.instructions.append(IRInstruction("LABEL", "-", "-", start_label))
            condition = self._emit_expression(statement.condition)
            self.instructions.append(IRInstruction("JF", condition, "-", end_label))
            for nested_statement in statement.body:
                self._emit_statement(nested_statement)
            self.instructions.append(IRInstruction("JMP", "-", "-", start_label))
            self.instructions.append(IRInstruction("LABEL", "-", "-", end_label))
            return

    def _emit_expression(self, expression: object) -> str:
        if isinstance(expression, LiteralNode):
            return repr(expression.value)

        if isinstance(expression, IdentifierNode):
            return expression.name

        if isinstance(expression, UnaryExpressionNode):
            operand = self._emit_expression(expression.operand)
            temp = self._next_temp()
            self.instructions.append(IRInstruction("NEG", operand, "-", temp))
            return temp

        if isinstance(expression, BinaryExpressionNode):
            left = self._emit_expression(expression.left)
            right = self._emit_expression(expression.right)
            temp = self._next_temp()
            opcode = self._map_binary_opcode(expression.operator.lexeme, expression.left, expression.right)
            self.instructions.append(IRInstruction(opcode, left, right, temp))
            return temp

        raise TypeError(f"Unsupported expression node: {type(expression)!r}")

    def _map_binary_opcode(self, operator: str, left: object, right: object) -> str:
        if operator == "+" and self._expression_type(left) == self._expression_type(right) == "cadena":
            return "CONCAT"
        return operator

    def _expression_type(self, expression: object) -> str | None:
        if isinstance(expression, LiteralNode):
            return expression.value_type
        if isinstance(expression, IdentifierNode) and self.semantic_result is not None:
            symbol = self.semantic_result.symbol_table.get(expression.name)
            return symbol.symbol_type if symbol is not None else None
        if isinstance(expression, UnaryExpressionNode):
            return self._expression_type(expression.operand)
        if isinstance(expression, BinaryExpressionNode):
            if expression.operator.lexeme == "+":
                left_type = self._expression_type(expression.left)
                right_type = self._expression_type(expression.right)
                if left_type == right_type == "cadena":
                    return "cadena"
            return None
        return None

    def _next_temp(self) -> str:
        self._temp_counter += 1
        return f"t{self._temp_counter}"

    def _next_label(self) -> str:
        self._label_counter += 1
        return f"L{self._label_counter}"


def generate_intermediate_code(program: ProgramNode, semantic_result: SemanticResult | None = None) -> IntermediateProgram:
    generator = IRGenerator(semantic_result=semantic_result)
    return generator.generate(program)


def export_intermediate_code(program: IntermediateProgram, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.write_text(program.to_text() + "\n", encoding="utf-8")
    return path
