from __future__ import annotations

from dataclasses import dataclass
import html
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


def generate_output_html(obj_path: str | Path, output_text: str) -> Path:
    path = Path(obj_path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontro el archivo objeto: {path}")

    rendered_output = output_text.strip() or "La salida final aun no esta disponible. Ejecuta el programa para actualizar este visor."
    escaped_output = html.escape(rendered_output)
    html_path = path.with_name(f"{path.stem}_obj.html")

    document = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Salida del Programa - RadarScript</title>
    <style>
        :root {{
            color-scheme: dark;
            --bg: #0f172a;
            --panel: #111827;
            --panel-soft: #020617;
            --text: #e5e7eb;
            --muted: #cbd5e1;
            --accent: #38bdf8;
            --accent-strong: #0ea5e9;
            --code: #f8fafc;
            --border: rgba(148, 163, 184, 0.2);
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            font-family: Arial, sans-serif;
            background:
                radial-gradient(circle at top, rgba(56, 189, 248, 0.15), transparent 28%),
                linear-gradient(180deg, #020617 0%, var(--bg) 100%);
            color: var(--text);
            padding: 30px 18px;
        }}

        .container {{
            max-width: 1000px;
            margin: auto;
            background: var(--panel);
            padding: 25px;
            border-radius: 16px;
            border: 1px solid var(--border);
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.35);
        }}

        h1 {{
            margin: 0 0 8px;
            color: var(--accent);
        }}

        .info {{
            color: var(--muted);
            margin-bottom: 18px;
        }}

        .actions {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 18px;
        }}

        .button {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 10px 16px;
            border-radius: 10px;
            border: 1px solid transparent;
            background: var(--accent);
            color: #082f49;
            font-weight: 700;
            text-decoration: none;
            cursor: pointer;
        }}

        .button.secondary {{
            background: transparent;
            border-color: var(--border);
            color: var(--text);
        }}

        .button:hover {{
            background: var(--accent-strong);
            color: #e0f2fe;
        }}

        .button.secondary:hover {{
            background: rgba(148, 163, 184, 0.12);
        }}

        pre {{
            margin: 0;
            background: var(--panel-soft);
            color: var(--code);
            padding: 20px;
            border-radius: 12px;
            overflow-x: auto;
            font-size: 15px;
            line-height: 1.6;
            border: 1px solid rgba(34, 197, 94, 0.15);
            white-space: pre-wrap;
            word-break: break-word;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>RadarScript - Salida Final</h1>
        <p class="info">Archivo objeto asociado: {html.escape(path.name)}</p>
        <div class="actions">
            <button class="button" type="button" onclick="window.location.reload()">Recargar visor</button>
            <a class="button secondary" href="javascript:history.back()">Volver</a>
        </div>
        <pre>{escaped_output}</pre>
    </div>
</body>
</html>
"""

    html_path.write_text(document, encoding="utf-8")

    return html_path
