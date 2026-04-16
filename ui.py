from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox

from compiler import CompilationResult, CompilerPipeline

try:
    import customtkinter as ctk
except ImportError:  # pragma: no cover - depende del entorno local
    ctk = None


@dataclass(frozen=True, slots=True)
class UITheme:
    background: str = "#0a1220"
    panel: str = "#111c2f"
    panel_alt: str = "#0f1728"
    border: str = "#213250"
    text_primary: str = "#f3f7ff"
    text_secondary: str = "#92a4c3"
    accent_blue: str = "#1f6feb"
    accent_blue_hover: str = "#388bfd"
    accent_yellow: str = "#d29922"
    accent_yellow_hover: str = "#e3b341"
    accent_green: str = "#238636"
    accent_green_hover: str = "#2ea043"
    accent_red: str = "#da3633"
    accent_red_hover: str = "#f85149"
    accent_cyan: str = "#39c5cf"
    success: str = "#3fb950"
    warning: str = "#d29922"
    danger: str = "#f85149"
    idle: str = "#6e7681"


class SummaryCard(ctk.CTkFrame if ctk else object):
    def __init__(self, master: "ctk.CTkFrame", title: str, theme: UITheme) -> None:
        super().__init__(master=master, fg_color=theme.panel_alt, corner_radius=18, border_width=1, border_color=theme.border)
        self._theme = theme

        self.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            text_color=theme.text_secondary,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))

        self.value_label = ctk.CTkLabel(
            self,
            text="--",
            text_color=theme.text_primary,
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w",
        )
        self.value_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))

        self.caption_label = ctk.CTkLabel(
            self,
            text="Sin datos",
            text_color=theme.text_secondary,
            font=ctk.CTkFont(size=12),
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
        "Archivo cargado": UITheme().accent_blue,
        "Compilado": UITheme().success,
        "Ejecutado": UITheme().accent_cyan,
        "Error": UITheme().danger,
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
        self._set_status("Sin archivo", "Listo")

    def run(self) -> None:
        self.root.mainloop()

    def _configure_window(self) -> None:
        self.root.title("RadarScript Compiler")
        self.root.geometry("1280x760")
        self.root.minsize(1200, 700)
        self.root.configure(fg_color=self.theme.background)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

    def _build_layout(self) -> None:
        shell = ctk.CTkFrame(self.root, fg_color=self.theme.background)
        shell.grid(row=0, column=0, sticky="nsew", padx=22, pady=22)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(2, weight=1)

        self._build_header(shell)
        self._build_actions(shell)
        self._build_main_content(shell)
        self._build_footer(shell)

    def _build_header(self, master: "ctk.CTkFrame") -> None:
        header = ctk.CTkFrame(master, fg_color=self.theme.panel, corner_radius=24, border_width=1, border_color=self.theme.border)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.grid(row=0, column=0, sticky="w", padx=24, pady=22)

        ctk.CTkLabel(
            title_block,
            text="RadarScript Compiler",
            text_color=self.theme.text_primary,
            font=ctk.CTkFont(size=30, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_block,
            text="Compilador academico",
            text_color=self.theme.text_secondary,
            font=ctk.CTkFont(size=14),
        ).pack(anchor="w", pady=(4, 0))

        status_block = ctk.CTkFrame(header, fg_color="transparent")
        status_block.grid(row=0, column=1, sticky="e", padx=24, pady=22)

        self.status_badge = ctk.CTkLabel(
            status_block,
            text="Sin archivo",
            text_color=self.theme.text_primary,
            fg_color=self.theme.idle,
            corner_radius=999,
            padx=16,
            pady=8,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.status_badge.pack(anchor="e")

        self.file_name_label = ctk.CTkLabel(
            status_block,
            text="Archivo: Ninguno",
            text_color=self.theme.text_secondary,
            font=ctk.CTkFont(size=13),
        )
        self.file_name_label.pack(anchor="e", pady=(10, 0))

    def _build_actions(self, master: "ctk.CTkFrame") -> None:
        actions = ctk.CTkFrame(master, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", pady=(18, 18))
        actions.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._create_action_button(
            actions,
            text="Cargar archivo",
            command=self._load_file,
            fg_color=self.theme.accent_blue,
            hover_color=self.theme.accent_blue_hover,
            column=0,
        )
        self._create_action_button(
            actions,
            text="Compilar",
            command=self._compile_current_file,
            fg_color=self.theme.accent_yellow,
            hover_color=self.theme.accent_yellow_hover,
            text_color="#10151f",
            column=1,
        )
        self._create_action_button(
            actions,
            text="Ejecutar",
            command=self._execute_program,
            fg_color=self.theme.accent_green,
            hover_color=self.theme.accent_green_hover,
            column=2,
        )
        self._create_action_button(
            actions,
            text="Limpiar",
            command=self._clear_session,
            fg_color=self.theme.accent_red,
            hover_color=self.theme.accent_red_hover,
            column=3,
        )

    def _create_action_button(
        self,
        master: "ctk.CTkFrame",
        text: str,
        command: object,
        fg_color: str,
        hover_color: str,
        column: int,
        text_color: str | None = None,
    ) -> None:
        button = ctk.CTkButton(
            master,
            text=text,
            command=command,
            height=48,
            corner_radius=16,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color or self.theme.text_primary,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        button.grid(row=0, column=column, sticky="ew", padx=6)

    def _build_main_content(self, master: "ctk.CTkFrame") -> None:
        content = ctk.CTkFrame(master, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=0)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self._build_summary_panel(content)
        self._build_tabs_panel(content)

    def _build_summary_panel(self, master: "ctk.CTkFrame") -> None:
        summary = ctk.CTkFrame(
            master,
            fg_color=self.theme.panel,
            corner_radius=24,
            border_width=1,
            border_color=self.theme.border,
            width=320,
        )
        summary.grid(row=0, column=0, sticky="nsw", padx=(0, 18))
        summary.grid_propagate(False)
        summary.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            summary,
            text="Resumen",
            text_color=self.theme.text_primary,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 6))

        ctk.CTkLabel(
            summary,
            text="Estado actual del flujo de compilacion",
            text_color=self.theme.text_secondary,
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 18))

        cards = (
            ("archivo", "Archivo cargado"),
            ("tokens", "Total de tokens"),
            ("variables", "Variables detectadas"),
            ("errores", "Numero de errores"),
            ("estado", "Estado actual"),
        )

        for row_index, (key, title) in enumerate(cards, start=2):
            card = SummaryCard(summary, title=title, theme=self.theme)
            card.grid(row=row_index, column=0, sticky="ew", padx=16, pady=8)
            self.summary_cards[key] = card

        self._refresh_summary()

    def _build_tabs_panel(self, master: "ctk.CTkFrame") -> None:
        panel = ctk.CTkFrame(master, fg_color=self.theme.panel, corner_radius=24, border_width=1, border_color=self.theme.border)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)

        tabview = ctk.CTkTabview(
            panel,
            fg_color=self.theme.panel,
            segmented_button_fg_color=self.theme.panel_alt,
            segmented_button_selected_color=self.theme.accent_blue,
            segmented_button_selected_hover_color=self.theme.accent_blue_hover,
            segmented_button_unselected_color=self.theme.panel_alt,
            segmented_button_unselected_hover_color="#16243b",
            text_color=self.theme.text_primary,
            corner_radius=20,
        )
        tabview.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)

        for tab_name in self.TAB_NAMES:
            tab = tabview.add(tab_name)
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

            textbox = ctk.CTkTextbox(
                tab,
                corner_radius=16,
                fg_color=self.theme.panel_alt,
                border_width=1,
                border_color=self.theme.border,
                text_color=self.theme.text_primary,
                wrap="none",
                font=ctk.CTkFont(family="Consolas", size=13),
            )
            textbox.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
            self.tab_views[tab_name] = textbox

    def _build_footer(self, master: "ctk.CTkFrame") -> None:
        footer = ctk.CTkFrame(master, fg_color=self.theme.panel, corner_radius=20, border_width=1, border_color=self.theme.border)
        footer.grid(row=3, column=0, sticky="ew", pady=(18, 0))
        footer.grid_columnconfigure(0, weight=1)

        self.footer_label = ctk.CTkLabel(
            footer,
            text="Listo",
            text_color=self.theme.text_secondary,
            font=ctk.CTkFont(size=13),
        )
        self.footer_label.grid(row=0, column=0, sticky="w", padx=18, pady=14)

        self.progress = ctk.CTkProgressBar(footer, progress_color=self.theme.accent_cyan, fg_color=self.theme.panel_alt)
        self.progress.grid(row=0, column=1, sticky="e", padx=18, pady=14)
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
        self.file_name_label.configure(text=f"Archivo: {self.current_file.name}")
        self._set_status("Archivo cargado", f"Archivo cargado: {self.current_file}")
        self._clear_outputs()
        self._refresh_summary()

    def _compile_current_file(self) -> None:
        if self.current_file is None:
            messagebox.showwarning("Archivo requerido", "Selecciona un archivo .rdr antes de compilar.")
            return

        self._set_status("Archivo cargado", "Compilando...")
        self.progress.set(0.35)
        self.root.update_idletasks()

        self.current_result = self.pipeline.compile_file(self.current_file)
        self.progress.set(0.75 if self.current_result.successful else 1)
        self._render_result(self.current_result)

        if self.current_result.successful:
            self._set_status("Compilado", "Compilacion completada")
        else:
            self._set_status("Error", "Errores encontrados durante la compilacion")

    def _execute_program(self) -> None:
        if self.current_file is None:
            messagebox.showwarning("Archivo requerido", "Selecciona un archivo .rdr antes de ejecutar.")
            return

        if self.current_result is None or not self.current_result.successful:
            self._compile_current_file()

        if self.current_result is None or not self.current_result.successful:
            return

        self._set_status("Compilado", "Ejecutando maquina virtual...")
        self.progress.set(0.9)
        self.root.update_idletasks()

        self.current_result = self.pipeline.execute(self.current_result)
        self._render_result(self.current_result)

        if "ejecucion" in self.current_result.errors:
            self._set_status("Error", "Error durante la ejecucion")
        else:
            self._set_status("Ejecutado", "Ejecucion completada")

    def _clear_session(self) -> None:
        self.current_file = None
        self.current_result = None
        self.file_name_label.configure(text="Archivo: Ninguno")
        self._clear_outputs()
        self._refresh_summary()
        self._set_status("Sin archivo", "Listo")

    def _render_result(self, result: CompilationResult) -> None:
        self._set_tab_content(".lex", self._read_artifact(result, "lex_path"))
        self._set_tab_content(".sym", self._read_artifact(result, "sym_path"))
        self._set_tab_content(".int", self._read_artifact(result, "int_path"))
        self._set_tab_content(".obj", self._read_artifact(result, "obj_path"))
        self._set_tab_content("salida", self._build_output_text(result))
        self._set_tab_content("errores", result.error_report())
        self._refresh_summary()

    def _build_output_text(self, result: CompilationResult) -> str:
        if result.execution_result is None:
            return ""

        return result.execution_result.output

    def _read_artifact(self, result: CompilationResult, attribute: str) -> str:
        if result.artifacts is None:
            return ""
        path = getattr(result.artifacts, attribute)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _set_tab_content(self, tab_name: str, content: str) -> None:
        textbox = self.tab_views[tab_name]
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", content)
        textbox.configure(state="disabled")

    def _clear_outputs(self) -> None:
        for tab_name in self.TAB_NAMES:
            self._set_tab_content(tab_name, "")
        self.progress.set(0)

    def _refresh_summary(self) -> None:
        file_value = self.current_file.name if self.current_file else "Ninguno"
        file_caption = str(self.current_file) if self.current_file else "No hay archivo cargado"

        token_count = len(self.current_result.tokens) if self.current_result else 0
        symbol_count = 0
        if self.current_result and self.current_result.semantic_result is not None:
            symbol_count = len(self.current_result.semantic_result.symbol_table.values())
        error_count = len(self.current_result.errors) if self.current_result else 0
        state_value = self.status_badge.cget("text") if hasattr(self, "status_badge") else "Sin archivo"
        state_caption = self.footer_label.cget("text") if hasattr(self, "footer_label") else "Listo"

        self.summary_cards["archivo"].update_content(file_value, file_caption)
        self.summary_cards["tokens"].update_content(str(token_count), "Tokens generados por el lexer")
        self.summary_cards["variables"].update_content(str(symbol_count), "Simbolos registrados en la tabla")
        self.summary_cards["errores"].update_content(str(error_count), "Errores detectados por fase")
        self.summary_cards["estado"].update_content(state_value, state_caption)

    def _set_status(self, status: str, footer_message: str) -> None:
        color = self.STATUS_COLORS.get(status, self.theme.idle)
        self.status_badge.configure(text=status, fg_color=color)
        self.footer_label.configure(text=footer_message)
        self._refresh_summary()


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
