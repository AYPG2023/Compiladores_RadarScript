from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompilerError(Exception):
    message: str
    line: int
    column: int
    error_type: str

    def __str__(self) -> str:
        return f"{self.error_type} at line {self.line}, column {self.column}: {self.message}"


@dataclass(frozen=True, slots=True)
class LexicalError(CompilerError):
    def __init__(self, message: str, line: int, column: int) -> None:
        CompilerError.__init__(self, message=message, line=line, column=column, error_type="LexicalError")


@dataclass(frozen=True, slots=True)
class ParseError(CompilerError):
    def __init__(self, message: str, line: int, column: int) -> None:
        CompilerError.__init__(self, message=message, line=line, column=column, error_type="ParseError")


@dataclass(frozen=True, slots=True)
class SemanticError(CompilerError):
    def __init__(self, message: str, line: int, column: int) -> None:
        CompilerError.__init__(self, message=message, line=line, column=column, error_type="SemanticError")


@dataclass(frozen=True, slots=True)
class IntermediateCodeError(CompilerError):
    def __init__(self, message: str, line: int = 0, column: int = 0) -> None:
        CompilerError.__init__(self, message=message, line=line, column=column, error_type="IntermediateCodeError")


@dataclass(frozen=True, slots=True)
class ObjectCodeError(CompilerError):
    def __init__(self, message: str, line: int = 0, column: int = 0) -> None:
        CompilerError.__init__(self, message=message, line=line, column=column, error_type="ObjectCodeError")


@dataclass(frozen=True, slots=True)
class VirtualMachineError(CompilerError):
    def __init__(self, message: str, line: int = 0, column: int = 0) -> None:
        CompilerError.__init__(self, message=message, line=line, column=column, error_type="VirtualMachineError")
