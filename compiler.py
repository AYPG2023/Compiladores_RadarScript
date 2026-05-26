from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from errors import (
    CompilerError,
    IntermediateCodeError,
    LexicalError,
    ObjectCodeError,
    ParseError,
    SemanticError,
    VirtualMachineError,
)
from intermediate_code import IntermediateProgram, export_intermediate_code, generate_intermediate_code
from lexer import export_tokens, tokenize_file
from object_code import ObjectProgram, export_object_code, generate_object_code, generate_output_html
from parser import ProgramNode, parse_tokens
from semantic import SemanticResult, analyze_semantics
from tokens import Token
from virtual_machine import ExecutionResult, execute_object_program


@dataclass(frozen=True, slots=True)
class ArtifactPaths:
    lex_path: Path
    sym_path: Path
    int_path: Path
    obj_path: Path
    obj_viewer_path: Path


@dataclass(slots=True)
class CompilationResult:
    source_path: Path
    tokens: list[Token] = field(default_factory=list)
    ast: ProgramNode | None = None
    semantic_result: SemanticResult | None = None
    intermediate_program: IntermediateProgram | None = None
    object_program: ObjectProgram | None = None
    execution_result: ExecutionResult | None = None
    errors: dict[str, str] = field(default_factory=dict)
    artifacts: ArtifactPaths | None = None

    @property
    def successful(self) -> bool:
        return not self.errors

    def error_report(self) -> str:
        if not self.errors:
            return "Sin errores."
        return "\n\n".join(f"[{phase}]\n{message}" for phase, message in self.errors.items())


class CompilerPipeline:
    def compile_file(self, source_path: str | Path) -> CompilationResult:
        source = Path(source_path)
        result = CompilationResult(source_path=source)
        result.artifacts = self._build_artifact_paths(source)

        try:
            result.tokens = tokenize_file(source)
            export_tokens(result.tokens, result.artifacts.lex_path)
        except (FileNotFoundError, LexicalError) as error:
            result.errors["lexico"] = str(error)
            return result

        try:
            result.ast = parse_tokens(result.tokens)
        except ParseError as error:
            result.errors["sintactico"] = str(error)
            return result

        try:
            result.semantic_result = analyze_semantics(result.ast, result.artifacts.sym_path)
        except SemanticError as error:
            result.errors["semantico"] = str(error)
            return result

        try:
            result.intermediate_program = generate_intermediate_code(result.ast, result.semantic_result)
            export_intermediate_code(result.intermediate_program, result.artifacts.int_path)
        except (IntermediateCodeError, TypeError) as error:
            result.errors["intermedio"] = str(error)
            return result

        try:
            result.object_program = generate_object_code(result.intermediate_program)
            export_object_code(result.object_program, result.artifacts.obj_path)
            generate_output_html(
                result.artifacts.obj_path,
                "La salida final aun no esta disponible. Ejecuta el programa para actualizar este visor.",
            )
        except ObjectCodeError as error:
            result.errors["objeto"] = str(error)
            return result
        except OSError as error:
            result.errors["objeto"] = f"No se pudo generar el visor HTML de salida: {error}"
            return result

        return result

    def execute(self, result: CompilationResult) -> CompilationResult:
        if result.object_program is None:
            result.errors.setdefault("ejecucion", "No hay codigo objeto disponible para ejecutar.")
            return result

        try:
            result.execution_result = execute_object_program(result.object_program)
            if result.artifacts is not None:
                generate_output_html(result.artifacts.obj_path, result.execution_result.output)
        except VirtualMachineError as error:
            result.errors["ejecucion"] = str(error)
        except OSError as error:
            result.errors["ejecucion"] = f"No se pudo actualizar el visor HTML de salida: {error}"

        return result

    def _build_artifact_paths(self, source_path: Path) -> ArtifactPaths:
        base_path = source_path.with_suffix("")
        return ArtifactPaths(
            lex_path=base_path.with_suffix(".lex"),
            sym_path=base_path.with_suffix(".sym"),
            int_path=base_path.with_suffix(".int"),
            obj_path=base_path.with_suffix(".obj"),
            obj_viewer_path=base_path.with_name(f"{base_path.name}_obj.html"),
        )
