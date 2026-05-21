# Manual de Usuario

## Portada

| Campo | Valor |
| --- | --- |
| Proyecto | RadarScript |
| Tipo de sistema | Compilador academico con interfaz grafica y modo CLI |
| Curso | [Completar] |
| Universidad | [Completar] |
| Integrantes | [Completar] |
| Fecha | 2026-05-20 |
| Version | 1.0 |

## Introduccion

RadarScript es un compilador academico para un lenguaje imperativo pequeno con soporte para declaraciones tipadas, asignaciones, condicionales, ciclos, generacion de codigo intermedio, generacion de codigo objeto y ejecucion mediante una maquina virtual.

La aplicacion permite:

- Cargar archivos fuente `.rdr`.
- Compilar el programa y generar archivos `.lex`, `.sym`, `.int` y `.obj`.
- Revisar los resultados de cada fase desde la interfaz grafica.
- Ejecutar el codigo objeto generado y ver la salida producida por la maquina virtual.

## Que es RadarScript

RadarScript es un proyecto academico orientado a mostrar el flujo completo de un compilador:

1. Analisis lexico.
2. Analisis sintactico.
3. Analisis semantico.
4. Generacion de codigo intermedio.
5. Generacion de codigo objeto.
6. Ejecucion en maquina virtual.

## Requisitos

### Requisitos detectados en el proyecto real

| Elemento | Estado |
| --- | --- |
| Version de Python validada | `Python 3.10.6` |
| Dependencias externas obligatorias para CLI | Ninguna |
| Dependencia externa para UI | `customtkinter` |
| Librerias estandar usadas | `argparse`, `pathlib`, `dataclasses`, `enum`, `typing`, `ast`, `tkinter` |

### Observaciones

- El modo linea de comandos funciona con Python estandar.
- La interfaz grafica requiere `customtkinter`.
- `tkinter` se usa para dialogos y mensajes de la UI.

## Instalacion y ejecucion

### Ejecutar la interfaz grafica

El proyecto arranca la UI cuando se ejecuta `main.py` sin archivo de entrada o cuando se usa `--ui`.

```bash
python main.py
```

o:

```bash
python main.py --ui
```

Si `customtkinter` no esta instalado, la aplicacion muestra este error:

```text
customtkinter no esta instalado. Instala la dependencia con 'pip install customtkinter' para usar la UI.
```

### Ejecutar en modo linea de comandos

```bash
python main.py entrada.rdr
```

Para compilar y ejecutar el programa generado:

```bash
python main.py entrada.rdr --run
```

Salida real observada con `entrada.rdr`:

```text
LEX: entrada.lex
SYM: entrada.sym
INT: entrada.int
OBJ: entrada.obj
ALERTA: Tormenta detectada en NORTE
REPORTE: Proceso finalizado
```

## Interfaz grafica

La interfaz esta implementada en `ui.py` con `customtkinter`. La ventana principal se titula `RadarScript Compiler` y contiene cuatro botones de accion, un panel de resumen, pestanas de salida y una barra de progreso.

[Insertar imagen aqui: pantalla principal]

### Botones disponibles

| Boton | Funcion |
| --- | --- |
| `Cargar archivo` | Abre un selector de archivos para elegir un `.rdr`. |
| `Compilar` | Ejecuta el pipeline completo hasta codigo objeto. |
| `Ejecutar` | Compila si hace falta y luego ejecuta la maquina virtual. |
| `Limpiar` | Borra el archivo actual, reinicia el estado y limpia las salidas. |

### Panel de resumen

La UI muestra tarjetas con:

- Archivo cargado.
- Total de tokens.
- Variables detectadas.
- Numero de errores.
- Estado actual.

### Pestanas de salida

| Pestana | Contenido |
| --- | --- |
| `.lex` | Tokens exportados por el analizador lexico. |
| `.sym` | Tabla de simbolos generada en analisis semantico. |
| `.int` | Codigo intermedio. |
| `.obj` | Codigo objeto. |
| `salida` | Salida producida por la maquina virtual. |
| `errores` | Reporte de errores por fase. |

## Flujo de uso

1. Abrir la aplicacion con `python main.py` o `python main.py --ui`.
2. Presionar `Cargar archivo`.
3. Seleccionar un archivo fuente con extension `.rdr`.
4. Presionar `Compilar`.
5. Revisar las pestanas `.lex`, `.sym`, `.int` y `.obj`.
6. Presionar `Ejecutar` para correr el programa compilado.
7. Revisar la pestana `salida`.
8. Revisar la pestana `errores` si ocurre alguna falla.

## Archivos generados

El pipeline crea los artefactos usando el mismo nombre base del archivo fuente.

| Extension | Generado por | Contenido |
| --- | --- | --- |
| `.lex` | `lexer.py` | Lista de tokens con tipo, lexema, linea y columna. |
| `.sym` | `semantic.py` y `symbol_table.py` | Simbolos declarados y su tipo. |
| `.int` | `intermediate_code.py` | Instrucciones intermedias tipo cuadruplo. |
| `.obj` | `object_code.py` | Pseudoensamblador ejecutable por la VM. |

### Ejemplo real de `.lex`

```text
PALABRA_RESERVADA      programa                 linea=1    columna=1
IDENTIFICADOR          monitoreo_clima          linea=1    columna=10
TIPO                   entero                   linea=2    columna=1
IDENTIFICADOR          distancia                linea=2    columna=8
```

### Ejemplo real de `.sym`

```text
distancia : entero
viento : decimal
zona : cadena
alerta_activa : booleano
```

### Ejemplo real de `.int`

```text
(=, 120, -, distancia)
(>, viento, 70, t1)
(JF, t1, -, L1)
(CONCAT, 'Tormenta detectada en ', zona, t2)
(ALERTA, t2, -, -)
```

### Ejemplo real de `.obj`

```text
MOV distancia, 120
LOAD viento
PUSH 70
GT
JMPF L1
```

## Programa de ejemplo real

El archivo `entrada.rdr` incluido en el proyecto contiene:

```rdr
programa monitoreo_clima;
entero distancia;
decimal viento;
cadena zona;
booleano alerta_activa;
distancia = 120;
viento = 85.5;
zona = "NORTE";
alerta_activa = verdadero;
si viento > 70 entonces
alerta("Tormenta detectada en " + zona);
fin
mientras distancia > 0 hacer
distancia = distancia - 30;
fin
reporte("Proceso finalizado");
```

### Que hace este programa

- Declara variables enteras, decimales, de cadena y booleanas.
- Asigna valores iniciales.
- Evalua si la velocidad del viento supera `70`.
- Emite una alerta si la condicion se cumple.
- Ejecuta un ciclo mientras la distancia sea mayor que `0`.
- Emite un reporte final.

## Manejo de errores

El sistema define errores especializados en `errors.py`. Todos heredan de `CompilerError` y reportan:

- tipo de error,
- linea,
- columna,
- mensaje descriptivo.

Formato real:

```text
<TipoError> at line <n>, column <m>: <mensaje>
```

### Tipos de errores detectados

| Tipo | Origen |
| --- | --- |
| `LexicalError` | Caracteres no soportados, cadenas no cerradas, comentarios de bloque no cerrados, decimal mal formado. |
| `ParseError` | Tokens inesperados o estructuras incompletas segun la gramatica. |
| `SemanticError` | Variables redeclaradas, uso antes de declaracion, incompatibilidad de tipos, condicion no booleana. |
| `IntermediateCodeError` | Problemas en generacion intermedia. |
| `ObjectCodeError` | OpCodes intermedios no soportados en traduccion a objeto. |
| `VirtualMachineError` | Etiquetas inexistentes, pila insuficiente u opcodes invalidos en ejecucion. |

## Buenas practicas de uso

- Declarar las variables antes de utilizarlas.
- Respetar el `;` en declaraciones, asignaciones y llamadas.
- Usar `fin` para cerrar bloques `si` y `mientras`.
- Mantener tipos compatibles en expresiones y asignaciones.
- Ejecutar primero la compilacion y revisar la pestana `errores` si algo falla.

## Conclusion

RadarScript cumple una finalidad academica clara: mostrar de forma integrada como un lenguaje fuente pasa por las fases principales de compilacion hasta llegar a una ejecucion controlada por una maquina virtual. La UI facilita la inspeccion de cada salida y el modo CLI permite validar el flujo completo desde terminal.
