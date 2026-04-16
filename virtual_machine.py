from __future__ import annotations

import ast
from dataclasses import dataclass

from errors import VirtualMachineError
from object_code import ObjectInstruction, ObjectProgram


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    output: str
    memory: dict[str, object]


class VirtualMachine:
    def __init__(self) -> None:
        self.memory: dict[str, object] = {}
        self.stack: list[object] = []
        self.output_lines: list[str] = []
        self.labels: dict[str, int] = {}

    def execute(self, program: ObjectProgram) -> ExecutionResult:
        self.memory.clear()
        self.stack.clear()
        self.output_lines.clear()
        self.labels = self._index_labels(program.instructions)

        pointer = 0
        instructions = program.instructions

        while pointer < len(instructions):
            instruction = instructions[pointer]
            opcode = instruction.opcode

            if opcode == "MOV":
                target, source = instruction.operands
                self.memory[target] = self._resolve_operand(source)
            elif opcode == "LOAD":
                self.stack.append(self._resolve_operand(instruction.operands[0]))
            elif opcode == "PUSH":
                self.stack.append(self._resolve_operand(instruction.operands[0]))
            elif opcode == "STORE":
                self._ensure_stack_size(1, opcode)
                self.memory[instruction.operands[0]] = self.stack.pop()
            elif opcode == "NEG":
                self._ensure_stack_size(1, opcode)
                self.stack.append(-self.stack.pop())
            elif opcode in {"ADD", "SUB", "MUL", "DIV", "GT", "GE", "LT", "LE", "EQ", "NE", "CONCAT"}:
                self._execute_binary(opcode)
            elif opcode == "ALERTA":
                self._ensure_stack_size(1, opcode)
                self.output_lines.append(f"ALERTA: {self.stack.pop()}")
            elif opcode == "REPORTE":
                self._ensure_stack_size(1, opcode)
                self.output_lines.append(f"REPORTE: {self.stack.pop()}")
            elif opcode == "JMPF":
                self._ensure_stack_size(1, opcode)
                if not self.stack.pop():
                    pointer = self._jump_to(instruction.operands[0])
                    continue
            elif opcode == "JMP":
                pointer = self._jump_to(instruction.operands[0])
                continue
            elif opcode == "LABEL":
                pass
            else:
                raise VirtualMachineError(f"Unsupported object opcode '{opcode}'.")

            pointer += 1

        filtered_memory = {key: value for key, value in self.memory.items() if not key.startswith("t")}
        return ExecutionResult(output="\n".join(self.output_lines), memory=filtered_memory)

    def _execute_binary(self, opcode: str) -> None:
        self._ensure_stack_size(2, opcode)
        right = self.stack.pop()
        left = self.stack.pop()

        try:
            if opcode == "ADD":
                result = left + right
            elif opcode == "SUB":
                result = left - right
            elif opcode == "MUL":
                result = left * right
            elif opcode == "DIV":
                result = left / right
            elif opcode == "GT":
                result = left > right
            elif opcode == "GE":
                result = left >= right
            elif opcode == "LT":
                result = left < right
            elif opcode == "LE":
                result = left <= right
            elif opcode == "EQ":
                result = left == right
            elif opcode == "NE":
                result = left != right
            elif opcode == "CONCAT":
                result = f"{left}{right}"
            else:
                raise VirtualMachineError(f"Unsupported binary opcode '{opcode}'.")
        except TypeError as error:
            raise VirtualMachineError(f"Invalid operands for '{opcode}': {left!r}, {right!r}.") from error

        self.stack.append(result)

    def _resolve_operand(self, operand: str) -> object:
        if operand in self.memory:
            return self.memory[operand]
        if operand == "verdadero":
            return True
        if operand == "falso":
            return False
        try:
            return ast.literal_eval(operand)
        except (ValueError, SyntaxError):
            pass
        return operand

    def _index_labels(self, instructions: list[ObjectInstruction]) -> dict[str, int]:
        labels: dict[str, int] = {}
        for index, instruction in enumerate(instructions):
            if instruction.opcode == "LABEL":
                labels[instruction.operands[0]] = index
        return labels

    def _jump_to(self, label: str) -> int:
        if label not in self.labels:
            raise VirtualMachineError(f"Label '{label}' does not exist.")
        return self.labels[label]

    def _ensure_stack_size(self, expected: int, opcode: str) -> None:
        if len(self.stack) < expected:
            raise VirtualMachineError(f"Stack underflow while executing '{opcode}'.")


def execute_object_program(program: ObjectProgram) -> ExecutionResult:
    machine = VirtualMachine()
    return machine.execute(program)
