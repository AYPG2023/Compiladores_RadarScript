# Manual Tecnico

## Portada

| Campo | Valor |
| --- | --- |
| Proyecto | RadarScript |
| Tipo | Compilador academico con maquina virtual |
| Curso | [Completar] |
| Universidad | [Completar] |
| Integrantes | [Completar] |
| Fecha | 2026-05-20 |
| Version | 1.0 |

## Introduccion tecnica

RadarScript implementa un pipeline de compilacion lineal para un lenguaje pequeno orientado a fines didacticos. El sistema cubre desde la lectura de un archivo fuente `.rdr` hasta la ejecucion del codigo objeto mediante una maquina virtual propia.

Objetivos tecnicos observados en el codigo:

- Tokenizar el lenguaje fuente con seguimiento de linea y columna.
- Construir un AST sencillo para sentencias y expresiones.
- Validar declaraciones, tipos y condiciones.
- Generar un codigo intermedio tipo cuadruplo.
- Traducir ese IR a pseudoensamblador.
- Ejecutar el programa resultante usando memoria, pila y saltos por etiqueta.

## Arquitectura general real

Flujo real detectado en `compiler.py`:

```text
.rdr
  -> lexer.tokenize_file
  -> parser.parse_tokens
  -> semantic.analyze_semantics
  -> intermediate_code.generate_intermediate_code
  -> object_code.generate_object_code
  -> virtual_machine.execute_object_program
```

La clase `CompilerPipeline` coordina la compilacion y acumula resultados en `CompilationResult`, incluyendo tokens, AST, tabla de simbolos, programa intermedio, programa objeto, resultado de ejecucion, errores y rutas de artefactos.

## Estructura real del proyecto

```text
Compiladores_RadarScript/
|-- __init__.py
|-- compiler.py
|-- errors.py
|-- intermediate_code.py
|-- lexer.py
|-- main.py
|-- object_code.py
|-- parser.py
|-- semantic.py
|-- symbol_table.py
|-- tokens.py
|-- ui.py
|-- virtual_machine.py
|-- entrada.rdr
|-- entrada.lex
|-- entrada.sym
|-- entrada.int
|-- entrada.obj
|-- tarea.md
|-- README.md
```

## Responsabilidad por modulo

| Modulo | Responsabilidad principal |
| --- | --- |
| `main.py` | Punto de entrada CLI/UI. |
| `compiler.py` | Orquestacion del pipeline y manejo de resultados. |
| `tokens.py` | Definicion de tokens, palabras reservadas y formato de exportacion lexico. |
| `lexer.py` | Analisis lexico y exportacion de `.lex`. |
| `parser.py` | Analisis sintactico y construccion del AST. |
| `semantic.py` | Validacion semantica y exportacion de `.sym`. |
| `symbol_table.py` | Estructura de simbolos y persistencia de tabla. |
| `intermediate_code.py` | Generacion de IR basado en cuadruplos. |
| `object_code.py` | Traduccion IR -> pseudoensamblador `.obj`. |
| `virtual_machine.py` | Ejecucion del codigo objeto. |
| `errors.py` | Jerarquia de errores del compilador. |
| `ui.py` | Interfaz grafica, eventos y visualizacion de artefactos. |

## Lenguaje RadarScript detectado

### Palabras reservadas

| Categoria | Elementos |
| --- | --- |
| Inicio de programa | `programa` |
| Tipos | `entero`, `decimal`, `cadena`, `booleano` |
| Control | `si`, `entonces`, `fin`, `mientras`, `hacer` |
| Booleanos | `verdadero`, `falso` |
| Salida | `alerta`, `reporte` |

### Operadores y simbolos

| Tipo | Elementos |
| --- | --- |
| Aritmeticos | `+`, `-`, `*`, `/` |
| Relacionales | `>`, `>=`, `<`, `<=`, `==`, `!=` |
| Asignacion | `=` |
| Agrupacion | `(`, `)` |
| Terminacion | `;` |

### Literales soportados

- Enteros.
- Decimales.
- Cadenas delimitadas por comillas dobles.
- Booleanos `verdadero` y `falso`.

### Estructuras sintacticas soportadas

- Declaracion de variable con o sin inicializacion.
- Asignacion.
- Condicional `si ... entonces ... fin`.
- Ciclo `mientras ... hacer ... fin`.
- Llamadas `alerta(...)` y `reporte(...)` con cero o un argumento.
- Expresiones unarias con `-`.
- Expresiones binarias aritmeticas y relacionales.

## `tokens.py`

`TokenType` define el vocabulario lexico completo. `RESERVED_WORDS` mapea lexemas del lenguaje a sus tipos de token. La clase `Token` conserva:

- `token_type`
- `lexeme`
- `line`
- `column`

La exportacion lexico usa `to_lex_row()`, que transforma cada token al formato persistido en `.lex`.

## `lexer.py`

### Funcionamiento real

El lexer recorre el codigo fuente caracter por caracter y mantiene:

- indice actual,
- linea,
- columna,
- longitud total,
- bandera `emit_comments`.

### Reglas implementadas

- Ignora espacios, tabulaciones y saltos de linea.
- Reconoce identificadores y palabras reservadas.
- Reconoce enteros y decimales.
- Reconoce cadenas entre comillas dobles.
- Reconoce comentarios de linea `//`.
- Reconoce comentarios de bloque `/* ... */`.
- Emite tokens para operadores, parentesis y `;`.
- Agrega siempre un token `EOF`.

### Casos de error lexico

- Decimal mal formado, por ejemplo un punto sin parte fraccionaria.
- Cadena no cerrada.
- Comentario de bloque no cerrado.
- Caracter inesperado.
- Uso de `!` sin `=`.

## `parser.py`

### Modelo de AST

El parser construye nodos tipados con `dataclass`:

- `ProgramNode`
- `VariableDeclarationNode`
- `AssignmentNode`
- `IfNode`
- `WhileNode`
- `CallNode`
- `BinaryExpressionNode`
- `UnaryExpressionNode`
- `LiteralNode`
- `IdentifierNode`

Todos conservan `line` y `column` mediante la jerarquia base `Node`.

### Gramatica efectiva observada

```text
programa <identificador> ;
<sentencia>*
EOF
```

Sentencias soportadas:

- Declaraciones de tipo.
- Asignaciones.
- Bloques `si`.
- Bloques `mientras`.
- Llamadas a `alerta` y `reporte`.

El parser descarta tokens `COMMENT` antes de analizar la gramatica.

### Precedencia de expresiones

La precedencia efectiva es:

1. Primarias.
2. Unarias.
3. Multiplicacion y division.
4. Suma y resta.
5. Relacionales e igualdad.

## `semantic.py`

### Validaciones reales

El analizador semantico mantiene una instancia de `SymbolTable` y valida:

- redeclaracion de identificadores,
- uso de variables antes de declararlas,
- compatibilidad de tipos en inicializacion y asignacion,
- que las condiciones de `si` y `mientras` sean booleanas,
- que `alerta` y `reporte` reciban como maximo un argumento,
- uso correcto de `-` unario sobre `entero` o `decimal`,
- compatibilidad de operandos en operadores binarios.

### Reglas de tipos detectadas

- `entero` y `decimal` son compatibles entre si.
- `+` entre dos `cadena` produce concatenacion.
- `/` siempre produce `decimal`.
- Comparaciones `>`, `>=`, `<`, `<=` requieren operandos numericos.
- `==` y `!=` exigen compatibilidad de tipos.

### Exportacion de simbolos

`analyze_semantics()` escribe el archivo `.sym` mediante `export_symbol_table()`.

## `symbol_table.py`

La estructura de simbolos es un diccionario en memoria indexado por nombre. Cada `Symbol` contiene:

- `name`
- `symbol_type`
- `declaration_line`
- `initial_value`

El archivo `.sym` exporta solo `nombre : tipo`.

Ejemplo real:

```text
distancia : entero
viento : decimal
zona : cadena
alerta_activa : booleano
```

## `intermediate_code.py`

### Modelo intermedio

El IR se representa con `IRInstruction(opcode, arg1, arg2, result)`. El generador mantiene contadores de:

- temporales `t1`, `t2`, ...
- etiquetas `L1`, `L2`, ...

### Estrategia de generacion

- Declaraciones con inicializacion producen asignaciones `=`.
- Asignaciones producen `=`.
- Llamadas producen `ALERTA` o `REPORTE`.
- `si` genera `JF` y una etiqueta de salida.
- `mientras` genera una etiqueta de inicio, una de salida y un salto `JMP`.
- Expresiones binarias generan temporales.
- Concatenacion de cadenas cambia `+` por `CONCAT`.

### Ejemplo real de IR

```text
(=, 120, -, distancia)
(>, viento, 70, t1)
(JF, t1, -, L1)
(CONCAT, 'Tormenta detectada en ', zona, t2)
(ALERTA, t2, -, -)
```

## `object_code.py`

### Traduccion real

El generador convierte IR a instrucciones de una maquina de pila y memoria.

Mapeo de operaciones binarias:

| IR | Objeto |
| --- | --- |
| `+` | `ADD` |
| `-` | `SUB` |
| `*` | `MUL` |
| `/` | `DIV` |
| `>` | `GT` |
| `>=` | `GE` |
| `<` | `LT` |
| `<=` | `LE` |
| `==` | `EQ` |
| `!=` | `NE` |
| `CONCAT` | `CONCAT` |

### Reglas de traduccion destacadas

- `=` puede emitir `MOV` o `STORE` segun el origen.
- `NEG` se traduce a `LOAD` seguido de `NEG`.
- `JF` se traduce a `JMPF`.
- `LABEL` se exporta como `Lx:`.
- `ALERTA` y `REPORTE` cargan argumento si no esta en un temporal.

### Ejemplo real de `.obj`

```text
MOV distancia, 120
LOAD viento
PUSH 70
GT
JMPF L1
LOAD "Tormenta detectada en "
LOAD zona
CONCAT
ALERTA
```

## `virtual_machine.py`

### Modelo de ejecucion

La VM mantiene:

- `memory: dict[str, object]`
- `stack: list[object]`
- `output_lines: list[str]`
- `labels: dict[str, int]`

### Instrucciones soportadas

| Instruccion | Efecto |
| --- | --- |
| `MOV` | Asigna un valor resuelto a una variable. |
| `LOAD` | Apila el valor de un literal o variable. |
| `PUSH` | Apila un literal. |
| `STORE` | Desapila y guarda en memoria. |
| `NEG` | Niega numericamante el tope de la pila. |
| `ADD`, `SUB`, `MUL`, `DIV` | Operaciones aritmeticas. |
| `GT`, `GE`, `LT`, `LE`, `EQ`, `NE` | Comparaciones. |
| `CONCAT` | Concatena dos valores y deja el resultado en pila. |
| `ALERTA` | Desapila y agrega `ALERTA: <valor>` a la salida. |
| `REPORTE` | Desapila y agrega `REPORTE: <valor>` a la salida. |
| `JMPF` | Salta si el valor desapilado es falso. |
| `JMP` | Salto incondicional. |
| `LABEL` | Marca una posicion de salto. |

### Resolucion de operandos

La VM reconoce:

- variables existentes en memoria,
- booleanos `verdadero` y `falso`,
- literales evaluables mediante `ast.literal_eval`,
- cadenas sin resolver como texto plano.

### Errores de ejecucion

- Etiqueta inexistente.
- `stack underflow`.
- Operandos invalidos para una operacion.
- Opcode objeto no soportado.

## `errors.py`

La jerarquia de errores real es:

- `CompilerError`
- `LexicalError`
- `ParseError`
- `SemanticError`
- `IntermediateCodeError`
- `ObjectCodeError`
- `VirtualMachineError`

Todos los errores formatean su salida como:

```text
<error_type> at line <line>, column <column>: <message>
```

## `compiler.py`

### Modelo de datos

- `ArtifactPaths`: rutas a `.lex`, `.sym`, `.int` y `.obj`.
- `CompilationResult`: contenedor mutable del estado completo de compilacion.

### Fases del pipeline

1. `tokenize_file()`
2. `export_tokens()`
3. `parse_tokens()`
4. `analyze_semantics()`
5. `generate_intermediate_code()`
6. `export_intermediate_code()`
7. `generate_object_code()`
8. `export_object_code()`

La ejecucion de la VM es una fase separada a traves de `execute()`.

### Manejo de errores por fase

`CompilationResult.errors` usa claves por etapa:

- `lexico`
- `sintactico`
- `semantico`
- `intermedio`
- `objeto`
- `ejecucion`

## `ui.py`

### Tecnologia real

- `customtkinter` para widgets principales.
- `tkinter.filedialog` para seleccionar archivos.
- `tkinter.messagebox` para advertencias.

### Componentes visibles

- Encabezado con estado y nombre de archivo.
- Botones `Cargar archivo`, `Compilar`, `Ejecutar`, `Limpiar`.
- Tarjetas de resumen.
- Pestanas `.lex`, `.sym`, `.int`, `.obj`, `salida`, `errores`.
- Barra de progreso.

### Flujo de eventos

- `_load_file()` selecciona el `.rdr` y limpia resultados previos.
- `_compile_current_file()` ejecuta el pipeline y renderiza artefactos.
- `_execute_program()` compila si es necesario y luego ejecuta la VM.
- `_clear_session()` reinicia la sesion.
- `_render_result()` actualiza todas las vistas.

[Insertar imagen aqui]

## `main.py`

`main.py` expone dos modos reales:

- UI por defecto si no se pasa archivo.
- CLI si se pasa un archivo de entrada.

Argumentos disponibles:

| Argumento | Funcion |
| --- | --- |
| `input` | Archivo `.rdr` a compilar. |
| `--run` | Ejecuta el codigo objeto despues de compilar. |
| `--ui` | Fuerza el inicio de la interfaz grafica. |

## Archivos generados

La salida se produce con el mismo nombre base del archivo fuente:

- `.lex`
- `.sym`
- `.int`
- `.obj`

No existe un generador dedicado para `.rdr`; ese archivo es la entrada del sistema.

## Caso real: `entrada.rdr`

El programa incluido modela un escenario de monitoreo de clima:

- declara variables `distancia`, `viento`, `zona` y `alerta_activa`,
- genera una alerta si `viento > 70`,
- reduce `distancia` en un ciclo,
- emite un reporte final.

Salida real al ejecutar:

```text
ALERTA: Tormenta detectada en NORTE
REPORTE: Proceso finalizado
```

## Dependencias detectadas

### Librerias estandar

- `argparse`
- `ast`
- `dataclasses`
- `enum`
- `pathlib`
- `tkinter`
- `typing`

### Dependencia externa

- `customtkinter`

No existe `requirements.txt` en el proyecto actual.

## Instalacion real

### Modo CLI

```bash
python main.py entrada.rdr
python main.py entrada.rdr --run
```

### Modo UI

```bash
pip install customtkinter
python main.py --ui
```

## Posibles mejoras tecnicas

Estas mejoras no existen hoy en el codigo, pero son extensiones razonables sobre la arquitectura actual:

- agregar pruebas automatizadas por fase,
- separar mejor AST, IR y backend en paquetes,
- ampliar la gramatica con bloques mas ricos y llamadas con varios argumentos,
- persistir mas metadatos en `.sym`,
- agregar optimizaciones sobre el IR,
- introducir validaciones de alcance por bloque,
- mejorar la VM con trazas e inspeccion de estado paso a paso,
- agregar empaquetado formal de dependencias.

## Conclusiones tecnicas

RadarScript presenta una arquitectura clara para fines academicos: lexer manual, parser descendente recursivo, chequeo semantico basado en tabla de simbolos, IR de cuadruplos, backend a pseudoensamblador y ejecucion en VM. La implementacion es pequena, legible y suficiente para documentar el ciclo esencial de construccion de un compilador.
