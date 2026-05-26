from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

from compiler import CompilationResult, CompilerPipeline

try:
    import customtkinter as ctk
except ImportError:  # pragma: no cover - depende del entorno local
    ctk = None


@dataclass(frozen=True, slots=True)
class UITheme:
    background: str = "#050816"
    background_alt: str = "#07111f"
    panel: str = "#0b1020"
    panel_alt: str = "#10182b"
    panel_soft: str = "#0f172a"
    border: str = "#1b2b45"
    border_active: str = "#2b476f"
    text_primary: str = "#f3f7ff"
    text_secondary: str = "#8fa7c4"
    text_muted: str = "#5f7695"
    accent_cyan: str = "#38f4ff"
    accent_cyan_hover: str = "#19d8e4"
    accent_lime: str = "#95ff4a"
    accent_lime_hover: str = "#79eb33"
    accent_orange: str = "#ff9d2e"
    accent_orange_hover: str = "#ff8814"
    accent_purple: str = "#9d7bff"
    accent_purple_hover: str = "#825dff"
    success: str = "#00c853"
    warning: str = "#ffb020"
    danger: str = "#ff4d4f"
    idle: str = "#6b7b94"
    code_bg: str = "#08101d"
    hud_line: str = "#123052"


class SummaryCard(ctk.CTkFrame if ctk else object):
    def __init__(self, master: "ctk.CTkFrame", title: str, module_id: str, theme: UITheme) -> None:
        super().__init__(
            master=master,
            fg_color=theme.panel_alt,
            corner_radius=20,
            border_width=1,
            border_color=theme.border,
        )
        self._theme = theme

        self.grid_columnconfigure(0, weight=1)

        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        top_row.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            top_row,
            text=title.upper(),
            text_color=theme.text_secondary,
            font=ctk.CTkFont(family="Orbitron", size=12, weight="bold"),
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.module_label = ctk.CTkLabel(
            top_row,
            text=module_id,
            text_color=theme.accent_cyan,
            fg_color=theme.background_alt,
            corner_radius=999,
            padx=10,
            pady=4,
            font=ctk.CTkFont(family="JetBrains Mono", size=10, weight="bold"),
        )
        self.module_label.grid(row=0, column=1, sticky="e")

        self.value_label = ctk.CTkLabel(
            self,
            text="--",
            text_color=theme.text_primary,
            font=ctk.CTkFont(family="Orbitron", size=24, weight="bold"),
            anchor="w",
        )
        self.value_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))

        self.caption_label = ctk.CTkLabel(
            self,
            text="Sin datos",
            text_color=theme.text_muted,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            justify="left",
            anchor="w",
        )
        self.caption_label.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))

    def update_content(self, value: str, caption: str) -> None:
        self.value_label.configure(text=value)
        self.caption_label.configure(text=caption)


class RadarScriptApp:
    TAB_NAMES = (".lex", ".sym", ".int", ".obj", "salida", "errores")
    STATUS_COLORS = {
        "Sin archivo": UITheme().idle,
        "Archivo cargado": UITheme().accent_cyan,
        "Compilado": UITheme().success,
        "Ejecutado": UITheme().accent_lime,
        "Ejecutando": UITheme().accent_orange,
        "Error": UITheme().danger,
    }
    STATUS_LABELS = {
        "Sin archivo": "EN ESPERA",
        "Archivo cargado": "LISTO",
        "Compilado": "COMPILADO",
        "Ejecutado": "EJECUTADO",
        "Ejecutando": "EJECUTANDO",
        "Error": "ERROR",
    }

    def __init__(self, root: "ctk.CTk") -> None:
        self.root = root
        self.pipeline = CompilerPipeline()
        self.theme = UITheme()
        self.current_file: Path | None = None
        self.current_result: CompilationResult | None = None
        self.tab_views: dict[str, ctk.CTkTextbox] = {}
        self.summary_cards: dict[str, SummaryCard] = {}

        self._configure_window()
        self._build_layout()
        self._set_status("Sin archivo", "SISTEMA LISTO")
        self._start_clock()

    def run(self) -> None:
        self.root.mainloop()

    def _configure_window(self) -> None:
        self.root.title("RadarScript Compiler")
        self.root.geometry("1380x840")
        self.root.minsize(1120, 700)
        self.root.configure(fg_color=self.theme.background)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

    def _build_layout(self) -> None:
        shell = ctk.CTkFrame(self.root, fg_color=self.theme.background)
        shell.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        self._build_header(shell)
        self._build_workspace(shell)
        self._build_footer(shell)

    def _build_header(self, master: "ctk.CTkFrame") -> None:
        header = ctk.CTkFrame(
            master,
            fg_color=self.theme.panel,
            corner_radius=26,
            border_width=1,
            border_color=self.theme.border_active,
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=0)

        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="nsew", padx=(22, 12), pady=18)
        brand.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            brand,
            text="RADARSCRIPT COMPILER",
            text_color=self.theme.text_primary,
            font=ctk.CTkFont(family="Orbitron", size=30, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            brand,
            text="CONSOLA TACTICA DE COMPILACION // FLUJO DE OBJETOS RADARSCRIPT",
            text_color=self.theme.text_secondary,
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        telemetry = ctk.CTkFrame(header, fg_color=self.theme.panel_alt, corner_radius=22, border_width=1, border_color=self.theme.border)
        telemetry.grid(row=0, column=1, sticky="ew", padx=12, pady=18)
        telemetry.grid_columnconfigure((0, 1), weight=1)

        self._build_header_metric(telemetry, "SISTEMA", "EN LINEA", self.theme.success, 0, 0)
        self.system_mode_label = self._build_header_metric(telemetry, "ESTADO DEL COMPILADOR", "EN ESPERA", self.theme.idle, 0, 1)
        self.file_name_label = self._build_header_metric(telemetry, "ARCHIVO ACTIVO", "NINGUN ARCHIVO CARGADO", self.theme.accent_cyan, 1, 0)
        self.signal_label = self._build_header_metric(telemetry, "BARRIDO RADAR", "CUADRICULA ACTIVA", self.theme.accent_purple, 1, 1)

        right_panel = ctk.CTkFrame(header, fg_color="transparent")
        right_panel.grid(row=0, column=2, sticky="e", padx=(12, 22), pady=18)
        right_panel.grid_columnconfigure(0, weight=1)

        self.status_badge = ctk.CTkLabel(
            right_panel,
            text="EN ESPERA",
            text_color=self.theme.text_primary,
            fg_color=self.theme.idle,
            corner_radius=999,
            padx=16,
            pady=8,
            font=ctk.CTkFont(family="JetBrains Mono", size=13, weight="bold"),
        )
        self.status_badge.grid(row=0, column=0, sticky="e")

        self.clock_label = ctk.CTkLabel(
            right_panel,
            text="--:--:--",
            text_color=self.theme.accent_lime,
            font=ctk.CTkFont(family="Orbitron", size=24, weight="bold"),
        )
        self.clock_label.grid(row=1, column=0, sticky="e", pady=(12, 4))

        self.status_detail_label = ctk.CTkLabel(
            right_panel,
            text="ESTADO // SISTEMA LISTO",
            text_color=self.theme.text_secondary,
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
        )
        self.status_detail_label.grid(row=2, column=0, sticky="e")

    def _build_header_metric(
        self,
        master: "ctk.CTkFrame",
        title: str,
        value: str,
        accent: str,
        row: int,
        column: int,
    ) -> "ctk.CTkLabel":
        module = ctk.CTkFrame(master, fg_color="transparent")
        module.grid(row=row, column=column, sticky="ew", padx=14, pady=12)
        module.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            module,
            text=title,
            text_color=self.theme.text_muted,
            font=ctk.CTkFont(family="JetBrains Mono", size=10, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        label = ctk.CTkLabel(
            module,
            text=value,
            text_color=accent,
            font=ctk.CTkFont(family="Orbitron", size=15, weight="bold"),
            anchor="w",
        )
        label.grid(row=1, column=0, sticky="w", pady=(4, 0))
        return label

    def _build_workspace(self, master: "ctk.CTkFrame") -> None:
        workspace = ctk.CTkFrame(master, fg_color="transparent")
        workspace.grid(row=1, column=0, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=0)
        workspace.grid_columnconfigure(1, weight=1)
        workspace.grid_rowconfigure(0, weight=1)

        self._build_control_panel(workspace)
        self._build_main_panel(workspace)

    def _build_control_panel(self, master: "ctk.CTkFrame") -> None:
        self.left_panel = ctk.CTkScrollableFrame(
            master,
            fg_color=self.theme.panel,
            corner_radius=26,
            border_width=1,
            border_color=self.theme.border,
            width=330,
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(0, weight=0)

        hero = ctk.CTkFrame(self.left_panel, fg_color=self.theme.panel_alt, corner_radius=22, border_width=1, border_color=self.theme.border)
        hero.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 14))
        hero.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hero,
            text="TORRE DE CONTROL",
            text_color=self.theme.accent_cyan,
            font=ctk.CTkFont(family="Orbitron", size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))
        ctk.CTkLabel(
            hero,
            text="Orquestacion del compilador, ejecucion del programa y seguimiento de archivos generados.",
            text_color=self.theme.text_secondary,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            justify="left",
            wraplength=270,
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

        actions = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", padx=18)
        actions.grid_columnconfigure((0, 1), weight=1)

        self._create_action_button(actions, "CARGAR", "ARCHIVO", self._load_file, self.theme.accent_cyan, self.theme.accent_cyan_hover, 0, 0)
        self._create_action_button(actions, "COMPILAR", "", self._compile_current_file, self.theme.accent_orange, self.theme.accent_orange_hover, 0, 1, text_color="#170d02")
        self._create_action_button(actions, "EJECUTAR", "", self._execute_program, self.theme.accent_lime, self.theme.accent_lime_hover, 1, 0, text_color="#081204")
        self._create_action_button(actions, "LIMPIAR", "", self._clear_session, self.theme.accent_purple, self.theme.accent_purple_hover, 1, 1)

        module_header = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        module_header.grid(row=2, column=0, sticky="ew", padx=18, pady=(18, 8))
        module_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            module_header,
            text="TELEMETRIA DEL SISTEMA",
            text_color=self.theme.text_primary,
            font=ctk.CTkFont(family="Orbitron", size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            module_header,
            text="Metricas actualizadas despues de cada compilacion.",
            text_color=self.theme.text_muted,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        cards = (
            ("archivo", "Archivo activo", "MOD-01"),
            ("tokens", "Flujo de tokens", "MOD-02"),
            ("variables", "Mapa de simbolos", "MOD-03"),
            ("errores", "Conteo de errores", "MOD-04"),
            ("estado", "Estado del sistema", "MOD-05"),
        )

        for row_index, (key, title, module_id) in enumerate(cards, start=3):
            card = SummaryCard(self.left_panel, title=title, module_id=module_id, theme=self.theme)
            card.grid(row=row_index, column=0, sticky="ew", padx=18, pady=8)
            self.summary_cards[key] = card

        strip = ctk.CTkFrame(self.left_panel, fg_color=self.theme.background_alt, corner_radius=18, border_width=1, border_color=self.theme.border)
        strip.grid(row=8, column=0, sticky="ew", padx=18, pady=(14, 18))
        strip.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            strip,
            text="NOTAS DE MISION",
            text_color=self.theme.accent_orange,
            font=ctk.CTkFont(family="JetBrains Mono", size=11, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))
        ctk.CTkLabel(
            strip,
            text="1. Carga un archivo .rdr.\n2. Compila para generar artefactos.\n3. Ejecuta para revisar la salida final.",
            text_color=self.theme.text_secondary,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))

        self._refresh_summary()

    def _create_action_button(
        self,
        master: "ctk.CTkFrame",
        code: str,
        label: str,
        command: object,
        fg_color: str,
        hover_color: str,
        row: int,
        column: int,
        text_color: str | None = None,
    ) -> None:
        button_text = code if not label else f"{code}\n{label}"
        button = ctk.CTkButton(
            master,
            text=button_text,
            command=command,
            height=76,
            corner_radius=18,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color or self.theme.text_primary,
            border_width=1,
            border_color=self.theme.border_active,
            font=ctk.CTkFont(family="Orbitron", size=15, weight="bold"),
        )
        button.grid(row=row, column=column, sticky="ew", padx=6, pady=6)

    def _build_main_panel(self, master: "ctk.CTkFrame") -> None:
        panel = ctk.CTkFrame(
            master,
            fg_color=self.theme.panel,
            corner_radius=26,
            border_width=1,
            border_color=self.theme.border,
        )
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        monitor = ctk.CTkFrame(panel, fg_color=self.theme.panel_alt, corner_radius=22, border_width=1, border_color=self.theme.border)
        monitor.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
        monitor.grid_columnconfigure(0, weight=1)
        monitor.grid_columnconfigure(1, weight=0)

        title_wrap = ctk.CTkFrame(monitor, fg_color="transparent")
        title_wrap.grid(row=0, column=0, sticky="w", padx=16, pady=14)

        ctk.CTkLabel(
            title_wrap,
            text="MATRIZ DE SALIDA TACTICA",
            text_color=self.theme.text_primary,
            font=ctk.CTkFont(family="Orbitron", size=20, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_wrap,
            text="LEX // SYM // INT // OBJ // SALIDA // ERRORES",
            text_color=self.theme.text_secondary,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
        ).pack(anchor="w", pady=(4, 0))

        indicators = ctk.CTkFrame(monitor, fg_color="transparent")
        indicators.grid(row=0, column=1, sticky="e", padx=16, pady=14)

        self.radar_indicator = ctk.CTkLabel(
            indicators,
            text="CUADRICULA RADAR ACTIVA",
            text_color=self.theme.accent_purple,
            fg_color=self.theme.background_alt,
            corner_radius=999,
            padx=14,
            pady=8,
            font=ctk.CTkFont(family="JetBrains Mono", size=11, weight="bold"),
        )
        self.radar_indicator.pack(anchor="e")

        self.tabview = ctk.CTkTabview(
            panel,
            fg_color=self.theme.panel,
            segmented_button_fg_color=self.theme.background_alt,
            segmented_button_selected_color=self.theme.accent_cyan,
            segmented_button_selected_hover_color=self.theme.accent_cyan_hover,
            segmented_button_unselected_color=self.theme.panel_alt,
            segmented_button_unselected_hover_color=self.theme.border_active,
            text_color="#07111f",
            corner_radius=22,
            border_width=1,
            border_color=self.theme.border,
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))

        for tab_name in self.TAB_NAMES:
            tab = self.tabview.add(tab_name)
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

            textbox = ctk.CTkTextbox(
                tab,
                corner_radius=18,
                fg_color=self.theme.code_bg,
                border_width=1,
                border_color=self.theme.border_active,
                text_color=self.theme.text_primary,
                wrap="none",
                font=ctk.CTkFont(family="JetBrains Mono", size=13),
                scrollbar_button_color=self.theme.border_active,
                scrollbar_button_hover_color=self.theme.accent_cyan,
            )
            textbox.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
            self.tab_views[tab_name] = textbox

    def _build_footer(self, master: "ctk.CTkFrame") -> None:
        footer = ctk.CTkFrame(
            master,
            fg_color=self.theme.panel,
            corner_radius=22,
            border_width=1,
            border_color=self.theme.border,
        )
        footer.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=0)

        footer_left = ctk.CTkFrame(footer, fg_color="transparent")
        footer_left.grid(row=0, column=0, sticky="w", padx=18, pady=14)

        self.footer_label = ctk.CTkLabel(
            footer_left,
            text="SISTEMA LISTO",
            text_color=self.theme.text_primary,
            font=ctk.CTkFont(family="JetBrains Mono", size=12, weight="bold"),
        )
        self.footer_label.pack(anchor="w")

        self.footer_hint_label = ctk.CTkLabel(
            footer_left,
            text="Esperando un archivo fuente para iniciar la compilacion.",
            text_color=self.theme.text_muted,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
        )
        self.footer_hint_label.pack(anchor="w", pady=(4, 0))

        footer_right = ctk.CTkFrame(footer, fg_color="transparent")
        footer_right.grid(row=0, column=1, sticky="e", padx=18, pady=14)

        self.progress = ctk.CTkProgressBar(
            footer_right,
            width=260,
            progress_color=self.theme.accent_cyan,
            fg_color=self.theme.background_alt,
            border_width=1,
            border_color=self.theme.border,
        )
        self.progress.pack(anchor="e")
        self.progress.set(0)

    def _load_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Seleccionar archivo RadarScript",
            filetypes=[("RadarScript", "*.rdr"), ("Todos los archivos", "*.*")],
        )
        if not selected:
            return

        self.current_file = Path(selected)
        self.current_result = None
        self.file_name_label.configure(text=self.current_file.name.upper())
        self._set_status("Archivo cargado", f"ARCHIVO CARGADO // {self.current_file}")
        self._clear_outputs()
        self._refresh_summary()

    def _compile_current_file(self) -> None:
        if self.current_file is None:
            messagebox.showwarning("Archivo requerido", "Selecciona un archivo .rdr antes de compilar.")
            return

        self._set_status("Archivo cargado", "FASE DE COMPILACION // DE LEXICO A OBJETO")
        self.progress.set(0.35)
        self.root.update_idletasks()

        self.current_result = self.pipeline.compile_file(self.current_file)
        self.progress.set(0.78 if self.current_result.successful else 1)
        self._render_result(self.current_result)

        if self.current_result.successful:
            self._set_status("Compilado", "COMPILACION COMPLETADA // ARTEFACTOS SINCRONIZADOS")
        else:
            self._set_status("Error", "FALLO DE COMPILACION // REVISA EL CANAL DE ERRORES")

    def _execute_program(self) -> None:
        if self.current_file is None:
            messagebox.showwarning("Archivo requerido", "Selecciona un archivo .rdr antes de ejecutar.")
            return

        if self.current_result is None or not self.current_result.successful:
            self._compile_current_file()

        if self.current_result is None or not self.current_result.successful:
            return

        self._set_status("Ejecutando", "EJECUCION ACTIVA // DESPACHANDO MAQUINA VIRTUAL")
        self.progress.set(0.9)
        self.root.update_idletasks()

        self.current_result = self.pipeline.execute(self.current_result)
        self._render_result(self.current_result)

        if "ejecucion" in self.current_result.errors:
            self._set_status("Error", "FALLO DE EJECUCION // PROCESO INTERRUMPIDO")
        else:
            self._set_status("Ejecutado", "EJECUCION COMPLETADA // SALIDA CAPTURADA")

    def _clear_session(self) -> None:
        self.current_file = None
        self.current_result = None
        self.file_name_label.configure(text="NINGUN ARCHIVO CARGADO")
        self._clear_outputs()
        self._refresh_summary()
        self._set_status("Sin archivo", "SISTEMA LISTO")

    def _render_result(self, result: CompilationResult) -> None:
        self._set_tab_content(".lex", self._read_artifact(result, "lex_path"), numbered=True)
        self._set_tab_content(".sym", self._read_artifact(result, "sym_path"), numbered=True)
        self._set_tab_content(".int", self._read_artifact(result, "int_path"), numbered=True)
        self._set_tab_content(".obj", self._read_artifact(result, "obj_path"), numbered=True)
        self._set_tab_content("salida", self._build_output_text(result))
        self._set_tab_content("errores", result.error_report())
        self._refresh_summary()

    def _build_output_text(self, result: CompilationResult) -> str:
        if result.execution_result is None:
            return ">> La salida aun no esta disponible.\n>> Ejecuta el programa para llenar esta consola."
        if not result.execution_result.output:
            return ">> Programa ejecutado correctamente.\n>> No se genero ninguna salida."
        return result.execution_result.output

    def _read_artifact(self, result: CompilationResult, attribute: str) -> str:
        if result.artifacts is None:
            return ""
        path = getattr(result.artifacts, attribute)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _set_tab_content(self, tab_name: str, content: str, numbered: bool = False) -> None:
        textbox = self.tab_views[tab_name]
        rendered = self._format_tab_content(tab_name, content, numbered=numbered)
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", rendered)
        textbox.configure(state="disabled")

    def _format_tab_content(self, tab_name: str, content: str, numbered: bool = False) -> str:
        stripped = content.strip()
        if tab_name == "errores":
            return self._format_error_report(content)
        if not stripped:
            if tab_name == "salida":
                return ">> Esperando la ejecucion del programa."
            return f">> No hay datos cargados para {tab_name}."
        if numbered:
            return self._with_line_numbers(content)
        if tab_name == "salida":
            return f">> CANAL DE SALIDA ACTIVO\n\n{content}"
        return content

    def _format_error_report(self, report: str) -> str:
        if not report.strip() or report.strip() == "Sin errores.":
            return "====================\nVERIFICACION DEL SISTEMA: CORRECTA\n====================\nNo se detectaron errores en el flujo actual."

        phase_titles = {
            "lexico": "ERROR LEXICO",
            "sintactico": "ERROR SINTACTICO",
            "semantico": "ERROR SEMANTICO",
            "intermedio": "ERROR DE CODIGO INTERMEDIO",
            "objeto": "ERROR DE CODIGO OBJETO",
            "ejecucion": "ERROR DE EJECUCION",
        }

        blocks: list[str] = []
        for section in report.strip().split("\n\n"):
            lines = [line for line in section.splitlines() if line.strip()]
            if not lines:
                continue

            phase_key = ""
            message_lines = lines
            if lines[0].startswith("[") and lines[0].endswith("]"):
                phase_key = lines[0][1:-1].strip().lower()
                message_lines = lines[1:]

            title = phase_titles.get(phase_key, "ERROR DEL COMPILADOR")
            header = f"====================\n!! {title} !!\n===================="
            blocks.append(f"{header}\n" + "\n".join(message_lines))

        return "\n\n".join(blocks)

    def _with_line_numbers(self, content: str) -> str:
        lines = content.splitlines()
        if not lines:
            return content
        width = max(2, len(str(len(lines))))
        return "\n".join(f"{index:>{width}} | {line}" for index, line in enumerate(lines, start=1))

    def _clear_outputs(self) -> None:
        for tab_name in self.TAB_NAMES:
            self._set_tab_content(tab_name, "")
        self.progress.set(0)

    def _refresh_summary(self) -> None:
        file_value = self.current_file.name if self.current_file else "NINGUNO"
        file_caption = str(self.current_file) if self.current_file else "No hay archivo fuente cargado"

        token_count = len(self.current_result.tokens) if self.current_result else 0
        symbol_count = 0
        if self.current_result and self.current_result.semantic_result is not None:
            symbol_count = len(self.current_result.semantic_result.symbol_table.values())
        error_count = len(self.current_result.errors) if self.current_result else 0
        state_value = self.status_badge.cget("text") if hasattr(self, "status_badge") else "EN ESPERA"
        state_caption = self.status_detail_label.cget("text") if hasattr(self, "status_detail_label") else "ESTADO // SISTEMA LISTO"

        self.summary_cards["archivo"].update_content(file_value, file_caption)
        self.summary_cards["tokens"].update_content(str(token_count), "Tokens generados por el lexer")
        self.summary_cards["variables"].update_content(str(symbol_count), "Entradas registradas en la tabla de simbolos")
        self.summary_cards["errores"].update_content(str(error_count), "Incidentes acumulados del compilador")
        self.summary_cards["estado"].update_content(state_value, state_caption)

    def _set_status(self, status: str, footer_message: str) -> None:
        color = self.STATUS_COLORS.get(status, self.theme.idle)
        label = self.STATUS_LABELS.get(status, status.upper())
        self.status_badge.configure(text=label, fg_color=color)
        self.system_mode_label.configure(text=label)
        self.status_detail_label.configure(text=f"ESTADO // {footer_message}")
        self.footer_label.configure(text=footer_message)
        hint = "Esperando un archivo fuente para iniciar la compilacion."
        if self.current_file is not None:
            hint = f"Artefactos generados para {self.current_file.name}"
        self.footer_hint_label.configure(text=hint)
        self._refresh_summary()

    def _start_clock(self) -> None:
        now = datetime.now()
        self.clock_label.configure(text=now.strftime("%H:%M:%S"))
        self.root.after(1000, self._start_clock)


def launch_app() -> None:
    if ctk is None:
        raise RuntimeError(
            "customtkinter no esta instalado. Instala la dependencia con 'pip install customtkinter' para usar la UI."
        )

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    app = RadarScriptApp(root)
    app.run()
