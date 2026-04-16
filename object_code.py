from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from errors import ObjectCodeError
from intermediate_code import IRInstruction, IntermediateProgram


@dataclass(frozen=True, slots=True)
class ObjectInstruction:
    opcode: str
    operands: tuple[str, ...] = ()

    def to_text(self) -> str:
        if self.opcode == "LABEL":
            return f"{self.operands[0]}:"
        if not self.operands:
            return self.opcode
        rendered_operands = ", ".join(self._render_operand(operand) for operand in self.operands)
        return f"{self.opcode} {rendered_operands}"

    def _render_operand(self, operand: str) -> str:
        if operand == "True":
            return "verdadero"
        if operand == "False":
            return "falso"
        if len(operand) >= 2 and operand[0] == operand[-1] and operand[0] in {"'", '"'}:
            return f'"{operand[1:-1]}"'
        return operand


@dataclass(frozen=True, slots=True)
class ObjectProgram:
    program_name: str
    instructions: list[ObjectInstruction]

    def to_text(self) -> str:
        return "\n".join(instruction.to_text() for instruction in self.instructions)


class ObjectCodeGenerator:
    _binary_opcodes = {
        "+": "ADD",
        "-": "SUB",
        "*": "MUL",
        "/": "DIV",
        ">": "GT",
        ">=": "GE",
        "<": "LT",
        "<=": "LE",
        "==": "EQ",
        "!=": "NE",
        "CONCAT": "CONCAT",
    }

    def generate(self, program: IntermediateProgram) -> ObjectProgram:
        instructions: list[ObjectInstruction] = []
        ir_instructions = program.instructions
        index = 0

        while index < len(ir_instructions):
            current = ir_instructions[index]
            next_instruction = ir_instructions[index + 1] if index + 1 < len(ir_instructions) else None

            consumed = self._translate_instruction(current, next_instruction, instructions)
            index += consumed

        return ObjectProgram(program_name=program.program_name, instructions=instructions)

    def _translate_instruction(
        self,
        instruction: IRInstruction,
        next_instruction: IRInstruction | None,
        output: list[ObjectInstruction],
    ) -> int:
        opcode = instruction.opcode

        if opcode == "=":
            if self._is_temp(instruction.arg1):
                output.append(ObjectInstruction("STORE", (instruction.result,)))
            else:
                output.append(ObjectInstruction("MOV", (instruction.result, instruction.arg1)))
            return 1

        if opcode in self._binary_opcodes:
            output.extend(self._emit_binary_operation(instruction))
            return 1

        if opcode == "NEG":
            output.append(ObjectInstruction("LOAD", (instruction.arg1,)))
            output.append(ObjectInstruction("NEG"))
            return 1

        if opcode == "JF":
            output.append(ObjectInstruction("JMPF", (instruction.result,)))
            return 1

        if opcode == "JMP":
            output.append(ObjectInstruction("JMP", (instruction.result,)))
            return 1

        if opcode == "LABEL":
            output.append(ObjectInstruction("LABEL", (instruction.result,)))
            return 1

        if opcode == "ALERTA":
            if instruction.arg1 != "-" and not self._is_temp(instruction.arg1):
                output.append(ObjectInstruction("LOAD", (instruction.arg1,)))
            output.append(ObjectInstruction("ALERTA"))
            return 1

        if opcode == "REPORTE":
            if instruction.arg1 != "-" and not self._is_temp(instruction.arg1):
                output.append(ObjectInstruction("LOAD", (instruction.arg1,)))
            output.append(ObjectInstruction("REPORTE"))
            return 1

        raise ObjectCodeError(f"Unsupported IR opcode '{opcode}'.")

    def _emit_binary_operation(self, instruction: IRInstruction) -> list[ObjectInstruction]:
        opcode = self._binary_opcodes[instruction.opcode]
        emitted: list[ObjectInstruction] = [ObjectInstruction("LOAD", (instruction.arg1,))]

        if instruction.opcode == "CONCAT":
            emitted.append(ObjectInstruction("LOAD", (instruction.arg2,)))
        else:
            emitted.append(self._emit_second_operand(instruction.arg2))

        emitted.append(ObjectInstruction(opcode))
        return emitted

    def _emit_second_operand(self, operand: str) -> ObjectInstruction:
        if self._is_literal(operand):
            return ObjectInstruction("PUSH", (operand,))
        return ObjectInstruction("LOAD", (operand,))

    def _is_temp(self, value: str) -> bool:
        return value.startswith("t")

    def _is_literal(self, value: str) -> bool:
        if value in {"True", "False", "verdadero", "falso"}:
            return True
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            return True
        try:
            float(value)
        except ValueError:
            return False
        return True


def generate_object_code(program: IntermediateProgram) -> ObjectProgram:
    generator = ObjectCodeGenerator()
    return generator.generate(program)


def export_object_code(program: ObjectProgram, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.write_text(program.to_text() + "\n", encoding="utf-8")
    return path
