"""
    Ventana v1.0
    Desenvolvido por Luis Augusto Malaquias Ghidini
    GitHub: https://github.com/lghidini12

    Uma ferramenta de contagem de tokens versátil e refinada para arquivos e diretórios locais.
    Suporta arquivos e diretórios inteiros por meio do menu de contexto do Windows Explorer.

    Baseado no projeto de código aberto token-counter de autoria de NickNau (GNU AGPL v3).
"""

import sys
import subprocess
import importlib
import tkinter as tk
from tkinter import ttk
import webbrowser
import os
import json
import threading
from pathlib import Path

# Funções de compatibilidade para compilação com PyInstaller (executável congelado)
def get_resource_path(relative_path):
    try:
        # PyInstaller extrai arquivos para a pasta temporária _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(SCRIPT_DIR, "ventana_config.json")
ICON_PATH   = get_resource_path("ventana.ico")
LOGO_PATH   = get_resource_path("logo.png")
APP_NAME    = "Ventana"
APP_VERSION = "v1.0"

_REQUIRED = [
    ("tiktoken",      "tiktoken",      "Tokenizador OpenAI"),
    ("Pillow",        "PIL",           "Suporte a imagens (logo)"),
    ("transformers",  "transformers",  "Tokenizadores HuggingFace"),
    ("anthropic",     "anthropic",     "SDK Anthropic"),
]

def _missing_packages():
    missing = []
    for pkg, imp, desc in _REQUIRED:
        try:
            importlib.import_module(imp)
        except ImportError:
            missing.append((pkg, desc))
    return missing

def _install_with_ui(missing: list):
    root = tk.Tk()
    root.title("Ventana: Instalando dependências")
    root.resizable(False, False)
    root.configure(bg="#F7F8FA")

    # Definir ícone da janela se for Windows
    if sys.platform.startswith("win"):
        if os.path.exists(ICON_PATH):
            try:
                root.iconbitmap(ICON_PATH)
            except Exception:
                pass

    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"420x160+{(sw-420)//2}+{(sh-160)//2}")

    tk.Label(root, text="🪟  Instalando dependências...",
             font=("Segoe UI", 11, "bold"), bg="#F7F8FA", fg="#1A1D23").pack(pady=(18, 4))

    status_var = tk.StringVar(value="Aguarde...")
    tk.Label(root, textvariable=status_var,
             font=("Segoe UI", 9), bg="#F7F8FA", fg="#6B7280").pack()

    bar = ttk.Progressbar(root, length=360, mode="determinate", maximum=len(missing))
    bar.pack(pady=14)

    root.update()

    for i, (pkg, desc) in enumerate(missing):
        status_var.set(f"Instalando {desc} ({pkg})...")
        root.update()
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            status_var.set(f"Erro ao instalar {pkg}. Continuando mesmo assim...")
            root.update()
            root.after(1500)
        bar["value"] = i + 1
        root.update()

    status_var.set("Concluído! Iniciando o aplicativo...")
    root.update()
    root.after(800, root.destroy)
    root.mainloop()

# Se não estiver rodando como executável compilado, verifica/instala dependências
if not getattr(sys, 'frozen', False):
    _missing = _missing_packages()
    if _missing:
        _install_with_ui(_missing)

THEME = {
    "bg":            "#F7F8FA",
    "surface":       "#FFFFFF",
    "border":        "#DDE1E7",
    "accent":        "#5B7CF6",
    "accent_hover":  "#4466E8",
    "accent_light":  "#EEF1FE",
    "text":          "#1A1D23",
    "text_secondary":"#6B7280",
    "success":       "#22C55E",
    "warning":       "#F59E0B",
    "error":         "#EF4444",
    "row_alt":       "#F3F4F6",
    "header_bg":     "#EAECF0",
    "font_main":     ("Segoe UI", 10),
    "font_title":    ("Segoe UI", 11, "bold"),
    "font_count":    ("Segoe UI", 26, "bold"),
    "font_mono":     ("Consolas", 9),
}

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    default = {"default_tokenizer": "gpt-4o", "window_geometry": "620x510"}
    save_config(default)
    return default

def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

TOKENIZER_GROUPS = {
    "OpenAI": [
        "gpt-4o", "gpt-4o-mini",
        "o1", "o1-mini",
        "o3", "o3-mini", "o4-mini",
        "gpt-4", "gpt-3.5-turbo",
    ],
    "Anthropic": ["claude (aprox.)"],
    "Meta":      ["llama", "llama3"],
    "Google":    ["gemma"],
    "Alibaba":   ["qwen"],
}

FLAT_TOKENIZERS = [t for group in TOKENIZER_GROUPS.values() for t in group]

APPROXIMATE_TOKENIZERS = {"claude (aprox.)"}

class ApproximateClaudeTokenizer:
    def encode(self, text: str) -> list:
        if not text:
            return []

        import re
        tokens = []

        pattern = r'[A-Za-z]+|[0-9]+|[^\x00-\x7F]+|[^\w\s]|\s+'
        for chunk in re.findall(pattern, text):
            first = chunk[0]

            if first.isspace():
                tokens.append(chunk)

            elif first.isdigit():
                tokens.extend([chunk[i:i+3] for i in range(0, len(chunk), 3)])

            elif first.isascii():
                if len(chunk) <= 4:
                    tokens.append(chunk)
                else:
                    tokens.extend([chunk[i:i+4] for i in range(0, len(chunk), 4)])

            else:
                tokens.extend([chunk[i:i+2] for i in range(0, len(chunk), 2)])

        return tokens

def get_tokenizer(name: str):
    if name == "claude (aprox.)":
        return ApproximateClaudeTokenizer()
    elif name.startswith("gpt") or name in ("o1","o1-mini","o3","o3-mini","o4-mini"):
        import tiktoken
        return tiktoken.encoding_for_model(name)
    elif name == "llama":
        from transformers import LlamaTokenizerFast
        return LlamaTokenizerFast.from_pretrained("hf-internal-testing/llama-tokenizer")
    elif name == "llama3":
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained("Xenova/llama-3-tokenizer")
    elif name == "gemma":
        from transformers import GemmaTokenizerFast
        return GemmaTokenizerFast.from_pretrained("Xenova/gemma-tokenizer")
    elif name == "qwen":
        from transformers import Qwen2TokenizerFast
        return Qwen2TokenizerFast.from_pretrained("Qwen/Qwen-tokenizer")
    raise ValueError(f"Tokenizador não suportado: {name}")

def is_binary(file_path: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            return b"\0" in f.read(8192)
    except IOError:
        return True

def process_file(file_path: str, tokenizer, base_path: str | None = None):
    label = os.path.relpath(file_path, base_path) if base_path else os.path.basename(file_path)
    if is_binary(file_path):
        return 0, [(label, "Binário")]
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        tokens = len(tokenizer.encode(content))
        return tokens, [(label, tokens)]
    except Exception:
        return 0, [(label, "Erro")]

def count_tokens(path: str, tokenizer_name: str, progress_cb=None):
    tokenizer = get_tokenizer(tokenizer_name)
    total_tokens = 0
    file_results: list = []

    if os.path.isfile(path):
        tokens, results = process_file(path, tokenizer)
        return tokens, results

    all_files = []
    for root, _, files in os.walk(path):
        for fname in files:
            all_files.append(os.path.join(root, fname))

    total_files = len(all_files)
    for idx, fp in enumerate(all_files, 1):
        tok, res = process_file(fp, tokenizer, path)
        total_tokens += tok
        file_results.extend(res)
        if progress_cb:
            progress_cb(idx, total_files)

    return total_tokens, file_results

class VentanaApp:
    def __init__(self, master: tk.Tk, path: str):
        self.master = master
        self.path   = path
        self.config = load_config()

        self._sort_col     = None
        self._sort_reverse = False
        self._file_results: list = []
        self._counting     = False

        self._setup_window()
        self._apply_theme()
        self._build_ui()
        self._start_count()
        self._check_for_updates()

    def _setup_window(self):
        self.master.title(f"{APP_NAME} {APP_VERSION}")
        geo = self.config.get("window_geometry", "620x510")
        self.master.geometry(geo)
        self.master.update_idletasks()
        w = self.master.winfo_width()
        h = self.master.winfo_height()
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        self.master.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
        self.master.minsize(520, 420)
        self.master.configure(bg=THEME["bg"])
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

        # Definir ícone da janela
        if sys.platform.startswith("win"):
            if os.path.exists(ICON_PATH):
                try:
                    self.master.iconbitmap(ICON_PATH)
                except Exception:
                    pass
        else:
            if os.path.exists(LOGO_PATH):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(LOGO_PATH)
                    self._window_icon = ImageTk.PhotoImage(img)
                    self.master.iconphoto(True, self._window_icon)
                except Exception:
                    pass

    def _apply_theme(self):
        style = ttk.Style(self.master)
        style.theme_use("clam")

        bg      = THEME["bg"]
        surface = THEME["surface"]
        border  = THEME["border"]
        accent  = THEME["accent"]
        text    = THEME["text"]
        alt     = THEME["row_alt"]
        hdr     = THEME["header_bg"]
        sec     = THEME["text_secondary"]

        style.configure("TFrame",       background=bg)
        style.configure("Surface.TFrame", background=surface, relief="flat")
        style.configure("TLabel",       background=bg, foreground=text, font=THEME["font_main"])
        style.configure("Secondary.TLabel", foreground=sec, font=("Segoe UI", 9))

        style.configure("Accent.TButton",
                        background=accent, foreground="#FFFFFF",
                        font=THEME["font_main"], relief="flat",
                        padding=(12, 6))
        style.map("Accent.TButton",
                  background=[("active", THEME["accent_hover"]), ("disabled", border)],
                  foreground=[("disabled", sec)])

        style.configure("TButton",
                        background=surface, foreground=text,
                        font=THEME["font_main"], relief="flat",
                        padding=(10, 6), borderwidth=1)
        style.map("TButton",
                  background=[("active", THEME["accent_light"])],
                  relief=[("pressed", "flat")])

        style.configure("TCombobox",
                        fieldbackground=surface, background=surface,
                        foreground=text, font=THEME["font_main"],
                        selectbackground=accent, selectforeground="#FFF",
                        arrowcolor=accent, bordercolor=border)
        style.map("TCombobox",
                  fieldbackground=[("readonly", surface)],
                  background=[("active", surface)])

        style.configure("Ventana.Treeview",
                        background=surface, foreground=text,
                        rowheight=26, font=THEME["font_mono"],
                        fieldbackground=surface, borderwidth=0)
        style.configure("Ventana.Treeview.Heading",
                        background=hdr, foreground=text,
                        font=THEME["font_main"], relief="flat", padding=(8, 6))
        style.map("Ventana.Treeview.Heading",
                  background=[("active", border)])
        style.map("Ventana.Treeview",
                  background=[("selected", THEME["accent_light"])],
                  foreground=[("selected", accent)])

        style.configure("Accent.Horizontal.TProgressbar",
                        troughcolor=border, background=accent,
                        borderwidth=0, thickness=4)

        style.configure("TScrollbar",
                        background=bg, troughcolor=bg,
                        arrowcolor=sec, borderwidth=0)

        style.configure("TSeparator", background=border)

    def _build_ui(self):
        root = self.master

        header = ttk.Frame(root, style="TFrame")
        header.pack(fill=tk.X, padx=0, pady=0)
        header.configure(style="TFrame")

        brand_frame = ttk.Frame(header)
        brand_frame.pack(side=tk.LEFT, padx=16, pady=10)

        # Carregar logotipo de forma compatível com PyInstaller
        logo_path = get_resource_path("logo.png")
        self._logo_image = None  # manter referência para evitar Garbage Collection
        
        logo_loaded = False
        if os.path.exists(logo_path):
            # Tentar carregar com Pillow
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path)
                img = img.resize((40, 40), Image.LANCZOS)
                self._logo_image = ImageTk.PhotoImage(img)
                tk.Label(brand_frame, image=self._logo_image,
                         bg=THEME["bg"]).pack(side=tk.LEFT, padx=(0, 8))
                logo_loaded = True
            except Exception:
                pass

            # Fallback nativo usando PhotoImage do Tkinter (sem Pillow)
            if not logo_loaded:
                try:
                    self._logo_image = tk.PhotoImage(file=logo_path).subsample(25, 25)
                    tk.Label(brand_frame, image=self._logo_image,
                             bg=THEME["bg"]).pack(side=tk.LEFT, padx=(0, 8))
                    logo_loaded = True
                except Exception:
                    pass

        if not logo_loaded:
            tk.Label(brand_frame, text="🪟", font=("Segoe UI Emoji", 18),
                     bg=THEME["bg"]).pack(side=tk.LEFT, padx=(0, 6))

        title_stack = ttk.Frame(brand_frame)
        title_stack.pack(side=tk.LEFT)
        ttk.Label(title_stack, text=APP_NAME, font=THEME["font_title"]).pack(anchor="w")
        ttk.Label(title_stack, text=APP_VERSION, style="Secondary.TLabel").pack(anchor="w")

        short_path = self.path if len(self.path) < 55 else "…" + self.path[-52:]
        path_var = tk.StringVar(value=short_path)
        path_lbl = ttk.Label(header, textvariable=path_var, style="Secondary.TLabel")
        path_lbl.pack(side=tk.RIGHT, padx=16)

        sep = ttk.Separator(root, orient="horizontal")
        sep.pack(fill=tk.X)

        card = tk.Frame(root, bg=THEME["surface"], bd=0, relief="flat")
        card.pack(fill=tk.X, padx=16, pady=(14, 0))

        self.token_count_var = tk.StringVar(value="...")
        count_lbl = tk.Label(card, textvariable=self.token_count_var,
                             font=THEME["font_count"], bg=THEME["surface"],
                             fg=THEME["accent"], anchor="center")
        count_lbl.pack(fill=tk.X, pady=(12, 2))

        tk.Label(card, text="tokens", font=("Segoe UI", 10),
                 bg=THEME["surface"], fg=THEME["text_secondary"]).pack()

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(card, variable=self.progress_var,
                                             maximum=100,
                                             style="Accent.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, padx=20, pady=(8, 4))
        self.progress_bar.pack_forget()   # oculto inicialmente

        self.status_var = tk.StringVar(value="")
        self.status_lbl = ttk.Label(card, textvariable=self.status_var,
                                    style="Secondary.TLabel")
        self.status_lbl.pack(pady=(0, 10))

        ctrl = ttk.Frame(root)
        ctrl.pack(fill=tk.X, padx=16, pady=8)

        self.copy_btn = ttk.Button(ctrl, text="⎘  Copiar Contagem",
                                   style="Accent.TButton",
                                   command=self.copy_to_clipboard)
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.recount_btn = ttk.Button(ctrl, text="↺  Recontar",
                                      command=self._start_count)
        self.recount_btn.pack(side=tk.LEFT, padx=(0, 8))

        tok_frame = ttk.Frame(ctrl)
        tok_frame.pack(side=tk.RIGHT)
        ttk.Label(tok_frame, text="Modelo:").pack(side=tk.LEFT, padx=(0, 6))
        self.tokenizer_var = tk.StringVar(value=self.config.get("default_tokenizer", "gpt-4o"))
        self.tokenizer_cb  = ttk.Combobox(tok_frame,
                                          textvariable=self.tokenizer_var,
                                          values=FLAT_TOKENIZERS,
                                          state="readonly", width=16)
        self.tokenizer_cb.pack(side=tk.LEFT)
        self.tokenizer_cb.bind("<<ComboboxSelected>>", self._on_tokenizer_change)

        # Rodapé com autoria e link do GitHub (empacotado primeiro no fundo)
        self.footer_ref = ttk.Frame(root, style="TFrame")
        self.footer_ref.pack(fill=tk.X, side=tk.BOTTOM, padx=16, pady=(0, 8))

        # Tenta carregar o avatar redondo do desenvolvedor
        self._avatar_img = None
        autor_path = get_resource_path("autor.png")
        if not os.path.exists(autor_path):
            autor_path = os.path.join(SCRIPT_DIR, "autor.png")
            
        if os.path.exists(autor_path):
            try:
                from PIL import Image, ImageTk, ImageOps, ImageDraw
                img = Image.open(autor_path).convert("RGBA")
                size = (20, 20)
                mask = Image.new("L", size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + size, fill=255)
                output = ImageOps.fit(img, size, centering=(0.5, 0.5))
                output.putalpha(mask)
                self._avatar_img = ImageTk.PhotoImage(output)
                
                avatar_lbl = tk.Label(self.footer_ref, image=self._avatar_img, bg=THEME["bg"])
                avatar_lbl.pack(side=tk.LEFT, padx=(0, 6))
            except Exception:
                pass

        dev_lbl = ttk.Label(self.footer_ref, text="Desenvolvido por Luis Augusto Malaquias Ghidini  ·  ", style="Secondary.TLabel")
        dev_lbl.pack(side=tk.LEFT)

        def open_github(_event):
            webbrowser.open_new("https://github.com/lghidini12")

        link_lbl = tk.Label(self.footer_ref, text="GitHub", fg=THEME["accent"], cursor="hand2", font=("Segoe UI", 9, "underline"), bg=THEME["bg"])
        link_lbl.pack(side=tk.LEFT)
        link_lbl.bind("<Button-1>", open_github)

        # List frame ocupando o espaço central restante
        list_frame = ttk.Frame(root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        sb_y = ttk.Scrollbar(list_frame, orient="vertical")
        sb_x = ttk.Scrollbar(list_frame, orient="horizontal")
        sb_y.pack(side=tk.RIGHT,  fill=tk.Y)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.file_list = ttk.Treeview(list_frame,
                                      yscrollcommand=sb_y.set,
                                      xscrollcommand=sb_x.set,
                                      columns=("File", "Tokens"),
                                      show="headings",
                                      style="Ventana.Treeview",
                                      selectmode="browse")
        self.file_list.heading("File",   text="Arquivo",   command=lambda: self._sort_by("File"))
        self.file_list.heading("Tokens", text="Tokens", command=lambda: self._sort_by("Tokens"))
        self.file_list.column("File",   width=430, stretch=True,  minwidth=150)
        self.file_list.column("Tokens", width=90,  stretch=False, minwidth=70, anchor="e")
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb_y.config(command=self.file_list.yview)
        sb_x.config(command=self.file_list.xview)

        self.file_list.tag_configure("odd",  background=THEME["surface"])
        self.file_list.tag_configure("even", background=THEME["row_alt"])
        self.file_list.tag_configure("binary",  foreground=THEME["text_secondary"])
        self.file_list.tag_configure("error",   foreground=THEME["error"])

        self._build_context_menu()

    def _build_context_menu(self):
        self.ctx = tk.Menu(self.master, tearoff=0,
                           bg=THEME["surface"], fg=THEME["text"],
                           activebackground=THEME["accent_light"],
                           activeforeground=THEME["accent"],
                           font=THEME["font_main"],
                           relief="solid", bd=1)
        self.ctx.add_command(label="📋  Copiar caminho",   command=self._ctx_copy_path)
        self.ctx.add_command(label="📂  Abrir pasta", command=self._ctx_open_folder)
        self.ctx.add_separator()
        self.ctx.add_command(label="🗑  Excluir arquivo",  command=self._ctx_delete_file)
        self.file_list.bind("<Button-3>", self._show_ctx_menu)
        self.file_list.bind("<Double-1>", lambda e: self._ctx_open_folder())

    def _show_ctx_menu(self, event):
        row = self.file_list.identify_row(event.y)
        if row:
            self.file_list.selection_set(row)
            self.ctx.tk_popup(event.x_root, event.y_root)

    def _selected_full_path(self):
        sel = self.file_list.selection()
        if not sel:
            return None
        relative = self.file_list.item(sel[0], "values")[0]
        if os.path.isdir(self.path):
            return os.path.join(self.path, relative)
        return self.path

    def _ctx_copy_path(self):
        p = self._selected_full_path()
        if p:
            self.master.clipboard_clear()
            self.master.clipboard_append(p)

    def _ctx_open_folder(self):
        p = self._selected_full_path()
        if not p:
            return
        folder = p if os.path.isdir(p) else os.path.dirname(p)
        try:
            os.startfile(folder)
        except AttributeError:
            import subprocess
            import sys
            if sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])

    def _ctx_delete_file(self):
        p = self._selected_full_path()
        if not p:
            return
        if not os.path.isfile(p):
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{p}", parent=self.master)
            return
        if not messagebox.askyesno("Excluir arquivo",
                                   f"Excluir este arquivo permanentemente?\n\n{p}",
                                   icon="warning", parent=self.master):
            return
        try:
            os.remove(p)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self.master)
            return
        sel = self.file_list.selection()
        if sel:
            rel = self.file_list.item(sel[0], "values")[0]
            self._file_results = [(fp, t) for fp, t in self._file_results if fp != rel]
        total = sum(t for _, t in self._file_results if isinstance(t, int))
        self.token_count_var.set(f"{total:,}")
        self._refresh_list()

    def _start_count(self):
        if self._counting:
            return
        self._counting = True
        self.token_count_var.set("…")
        self.status_var.set("Contando tokens...")
        self.recount_btn.configure(state="disabled")
        self.tokenizer_cb.configure(state="disabled")
        self.copy_btn.configure(state="disabled")

        if os.path.isdir(self.path):
            self.progress_bar.pack(fill=tk.X, padx=20, pady=(8, 4))
            self.progress_var.set(0)

        tokenizer_name = self.tokenizer_var.get()

        def progress_cb(done, total):
            pct = (done / total * 100) if total else 100
            self.master.after(0, lambda: self.progress_var.set(pct))
            self.master.after(0, lambda: self.status_var.set(
                f"Processando {done}/{total} arquivos..."))

        def worker():
            try:
                total, results = count_tokens(self.path, tokenizer_name, progress_cb)
                self.master.after(0, lambda: self._on_count_done(total, results))
            except Exception as e:
                self.master.after(0, lambda: self._on_count_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_count_done(self, total: int, results: list):
        self._counting = False
        self._file_results = results
        tok_name  = self.tokenizer_var.get()
        is_approx = tok_name in APPROXIMATE_TOKENIZERS
        self.token_count_var.set(f"~{total:,}" if is_approx else f"{total:,}")
        approx_note = "  ⚠ estimativa aproximada (±10% a 15%)" if is_approx else ""
        self.status_var.set(f"{len(results)} arquivo(s) · {tok_name}{approx_note}")
        self.progress_bar.pack_forget()
        self.recount_btn.configure(state="normal")
        self.tokenizer_cb.configure(state="readonly")
        self.copy_btn.configure(state="normal")

        self.config["default_tokenizer"] = self.tokenizer_var.get()
        save_config(self.config)

        self._sort_col     = None
        self._sort_reverse = False
        for c in ("File", "Tokens"):
            header_text = "Arquivo" if c == "File" else "Tokens"
            self.file_list.heading(c, text=header_text)

        self._refresh_list()

    def _on_count_error(self, msg: str):
        self._counting = False
        self.token_count_var.set("Erro")
        self.status_var.set(msg)
        self.progress_bar.pack_forget()
        self.recount_btn.configure(state="normal")
        self.tokenizer_cb.configure(state="readonly")

    def _on_tokenizer_change(self, _event=None):
        self._start_count()

    def _token_sort_key(self, value):
        try:
            return (0, int(value))
        except (ValueError, TypeError):
            return (1, str(value))

    def _sort_by(self, col: str):
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col     = col
            self._sort_reverse = False
        self._refresh_list()
        for c in ("File", "Tokens"):
            arrow = ""
            if c == self._sort_col:
                arrow = "  ▼" if self._sort_reverse else "  ▲"
            header_text = "Arquivo" if c == "File" else "Tokens"
            self.file_list.heading(c, text=header_text + arrow)

    def _sorted_results(self):
        if self._sort_col is None:
            return list(self._file_results)
        if self._sort_col == "Tokens":
            return sorted(self._file_results,
                          key=lambda r: self._token_sort_key(r[1]),
                          reverse=self._sort_reverse)
        return sorted(self._file_results,
                      key=lambda r: str(r[0]).lower(),
                      reverse=self._sort_reverse)

    def _refresh_list(self):
        self.file_list.delete(*self.file_list.get_children())
        for idx, (fp, tokens) in enumerate(self._sorted_results()):
            tag = "even" if idx % 2 == 0 else "odd"
            if tokens == "Binário":
                tag = "binary"
                display = "Binário"
            elif tokens == "Erro":
                tag = "error"
                display = "Erro"
            else:
                display = f"{tokens:,}" if isinstance(tokens, int) else str(tokens)
            self.file_list.insert("", "end", values=(fp, display), tags=(tag,))

    def copy_to_clipboard(self):
        self.master.clipboard_clear()
        raw = self.token_count_var.get().replace(",", "").replace("~", "")
        self.master.clipboard_append(raw)

    def _check_for_updates(self):
        def check():
            import urllib.request
            import json
            try:
                req = urllib.request.Request(
                    "https://api.github.com/repos/lghidini12/Ventana/releases/latest",
                    headers={"User-Agent": "Ventana-App"}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    tag = data.get("tag_name", "")
                    if tag and tag != APP_VERSION:
                        self.master.after(0, lambda: self._display_update_message(tag))
            except Exception:
                pass

        threading.Thread(target=check, daemon=True).start()

    def _display_update_message(self, tag):
        self.update_lbl = tk.Label(
            self.footer_ref, 
            text=f"✨ Nova versão disponível ({tag})", 
            fg=THEME["success"], 
            cursor="hand2", 
            font=("Segoe UI", 9, "bold", "underline"), 
            bg=THEME["bg"]
        )
        self.update_lbl.pack(side=tk.RIGHT)
        self.update_lbl.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/lghidini12/Ventana/releases"))

    def _on_close(self):
        geo = self.master.geometry()
        self.config["window_geometry"] = geo
        save_config(self.config)
        self.master.destroy()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Uso: python ventana.pyw <caminho_do_arquivo_ou_pasta>")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"Erro: Caminho não encontrado: '{path}'")
        sys.exit(1)

    root = tk.Tk()
    app  = VentanaApp(root, path)
    root.mainloop()
