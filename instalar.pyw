"""
    Ventana: Instalador e Gerenciador de Integração
    Desenvolvido por Luis Augusto Malaquias Ghidini
    GitHub: https://github.com/lghidini12

    Este instalador configura as dependências de Python para o Ventana
    e cria de forma visual a integração com o menu de contexto do Windows Explorer.
"""

import sys
import os
import subprocess
import threading
import ctypes
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

# Se não estiver rodando no Windows, exibir mensagem amigável orientando sobre macOS/Linux
if sys.platform != "win32":
    root = tk.Tk()
    root.withdraw()
    opcao = messagebox.askyesno(
        "Instalação Multiplataforma",
        "O instalador gráfico de menu de contexto foi projetado especificamente para o Windows.\n\n"
        "No macOS e Linux, a integração com o Finder ou com o gerenciador de arquivos é feita de forma manual e muito simples.\n\n"
        "Gostaria de abrir o guia de instalação no GitHub para ver como fazer?",
        icon="info"
    )
    if opcao:
        webbrowser.open_new("https://github.com/lghidini12/Ventana#%EF%B8%8F-instala%C3%A7%C3%A3o-e-requisitos")
    sys.exit(0)

# Verificar se o script está rodando com privilégios de Administrador no Windows
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

# Tentar reiniciar o script como Administrador de forma silenciosa e nativa
if not is_admin():
    try:
        # Abre o prompt UAC do Windows
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{__file__}"', None, 1)
        sys.exit(0)
    except Exception:
        # Caso o usuário recuse a elevação UAC
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Permissão Necessária", 
            "Este instalador precisa de privilégios de Administrador para configurar o menu de contexto do Windows Explorer.\n\nPor favor, execute novamente e autorize as permissões."
        )
        sys.exit(1)

# Importações condicionais do Pillow para tolerância a falhas
try:
    from PIL import Image, ImageTk
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# Funções de compatibilidade para compilação com PyInstaller (executável congelado)
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

LOGO_PATH = get_resource_path(os.path.join("app", "logo.png"))
ICON_PATH = os.path.join(SCRIPT_DIR, "app", "ventana.ico")
EXE_PATH = os.path.join(SCRIPT_DIR, "app", "ventana.pyw")

APP_NAME = "Ventana"
APP_VERSION = "v1.0"

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
    "error":         "#EF4444",
    "font_main":     ("Segoe UI", 10),
    "font_title":    ("Segoe UI", 12, "bold"),
    "font_sub":      ("Segoe UI", 9),
}

_DEPENDENCIES = [
    ("Pillow", "PIL", "Suporte a imagens e ícones (Pillow)"),
    ("tiktoken", "tiktoken", "Tokenizador OpenAI (tiktoken)"),
    ("transformers", "transformers", "Tokenizadores HuggingFace (transformers)"),
    ("anthropic", "anthropic", "Integração Claude (anthropic)"),
]

class VentanaInstaller:
    def __init__(self, master: tk.Tk):
        self.master = master
        self._setup_window()
        self._apply_theme()
        self._build_ui()

    def _setup_window(self):
        self.master.title(f"Instalador do {APP_NAME} {APP_VERSION}")
        self.master.resizable(False, False)
        self.master.configure(bg=THEME["bg"])
        
        # Centralizar na tela
        w, h = 480, 340
        self.master.update_idletasks()
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        self.master.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # Definir ícone da janela
        if os.path.exists(ICON_PATH):
            try:
                self.master.iconbitmap(ICON_PATH)
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
        sec     = THEME["text_secondary"]

        style.configure("TFrame",       background=bg)
        style.configure("TLabel",       background=bg, foreground=text, font=THEME["font_main"])
        style.configure("Secondary.TLabel", foreground=sec, font=THEME["font_sub"])
        
        style.configure("Accent.TButton",
                        background=accent, foreground="#FFFFFF",
                        font=THEME["font_main"], relief="flat",
                        padding=(14, 8))
        style.map("Accent.TButton",
                  background=[("active", THEME["accent_hover"]), ("disabled", border)],
                  foreground=[("disabled", sec)])

        style.configure("TButton",
                        background=surface, foreground=text,
                        font=THEME["font_main"], relief="flat",
                        padding=(12, 8), borderwidth=1)
        style.map("TButton",
                  background=[("active", THEME["accent_light"])])

        style.configure("Accent.Horizontal.TProgressbar",
                        troughcolor=border, background=accent,
                        borderwidth=0, thickness=6)

    def _build_ui(self):
        # Topo
        top_frame = ttk.Frame(self.master, style="TFrame")
        top_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        # Logotipo
        self._logo_image = None
        self.logo_label = tk.Label(top_frame, bg=THEME["bg"])
        self.logo_label.pack(side=tk.LEFT, padx=(0, 12))
        self._refresh_logo_display()

        title_stack = ttk.Frame(top_frame)
        title_stack.pack(side=tk.LEFT)
        ttk.Label(title_stack, text=f"Instalador do {APP_NAME}", font=THEME["font_title"]).pack(anchor="w")
        ttk.Label(title_stack, text="Gerencie a integração com o Windows Explorer e dependências", style="Secondary.TLabel").pack(anchor="w")

        # Divisor
        sep = ttk.Separator(self.master, orient="horizontal")
        sep.pack(fill=tk.X, padx=20, pady=5)

        # Rodapé (empacotado primeiro no fundo)
        footer = ttk.Frame(self.master, style="TFrame")
        footer.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(0, 10))

        # Tenta carregar o avatar redondo do desenvolvedor
        self._avatar_img = None
        autor_path = get_resource_path(os.path.join("app", "autor.png"))
        if not os.path.exists(autor_path):
            autor_path = os.path.join(SCRIPT_DIR, "app", "autor.png")
            
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
                
                avatar_lbl = tk.Label(footer, image=self._avatar_img, bg=THEME["bg"])
                avatar_lbl.pack(side=tk.LEFT, padx=(0, 6))
            except Exception:
                pass

        ttk.Label(footer, text="Desenvolvido por Luis Augusto Malaquias Ghidini  ·  ", style="Secondary.TLabel").pack(side=tk.LEFT)

        def open_github(_event):
            webbrowser.open_new("https://github.com/lghidini12")

        link_lbl = tk.Label(footer, text="GitHub", fg=THEME["accent"], cursor="hand2", font=("Segoe UI", 9, "underline"), bg=THEME["bg"])
        link_lbl.pack(side=tk.LEFT)
        link_lbl.bind("<Button-1>", open_github)

        # Conteúdo Central (Ações e Status) - Ocupa o centro
        self.action_frame = ttk.Frame(self.master, style="TFrame")
        self.action_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        self.btn_install = ttk.Button(
            self.action_frame, 
            text="✨  Instalar / Atualizar Integração", 
            style="Accent.TButton",
            command=self._start_install_flow
        )
        self.btn_install.pack(fill=tk.X, pady=(0, 8))

        self.btn_uninstall = ttk.Button(
            self.action_frame, 
            text="🗑  Remover Integração do Explorer", 
            command=self._start_uninstall_flow
        )
        self.btn_uninstall.pack(fill=tk.X, pady=(0, 15))

        # Progresso e Status
        self.status_var = tk.StringVar(value="Pronto para configurar o sistema.")
        self.status_label = ttk.Label(self.action_frame, textvariable=self.status_var, style="Secondary.TLabel", justify="center")
        self.status_label.pack(fill=tk.X)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.action_frame, 
            variable=self.progress_var, 
            maximum=100, 
            style="Accent.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, pady=(6, 0))
        self.progress_bar.pack_forget()

    def _refresh_logo_display(self):
        global HAS_PILLOW
        if not HAS_PILLOW:
            try:
                from PIL import Image, ImageTk
                HAS_PILLOW = True
            except ImportError:
                pass

        if os.path.exists(LOGO_PATH):
            if HAS_PILLOW:
                try:
                    img = Image.open(LOGO_PATH)
                    img = img.resize((48, 48), Image.LANCZOS)
                    self._logo_image = ImageTk.PhotoImage(img)
                    self.logo_label.config(image=self._logo_image, text="")
                    return
                except Exception:
                    pass
            
            # Fallback nativo usando PhotoImage do Tkinter (sem Pillow)
            try:
                self._logo_image = tk.PhotoImage(file=LOGO_PATH).subsample(21, 21)
                self.logo_label.config(image=self._logo_image, text="")
                return
            except Exception:
                pass

        # Fallback de texto se nada funcionar
        self.logo_label.config(text="🪟", font=("Segoe UI Emoji", 24))

    def _lock_ui(self):
        self.btn_install.configure(state="disabled")
        self.btn_uninstall.configure(state="disabled")
        self.progress_bar.pack(fill=tk.X, pady=(6, 0))
        self.progress_var.set(0)

    def _unlock_ui(self):
        self.btn_install.configure(state="normal")
        self.btn_uninstall.configure(state="normal")
        self.progress_bar.pack_forget()

    def _start_install_flow(self):
        self._lock_ui()
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self):
        try:
            # 1. Se NÃO estiver rodando como executável compilado, instala dependências via pip
            if not getattr(sys, 'frozen', False):
                total_deps = len(_DEPENDENCIES)
                for idx, (pkg, imp, desc) in enumerate(_DEPENDENCIES, 1):
                    self.master.after(0, lambda p=pkg: self.status_var.set(f"Instalando dependência: {p}..."))
                    try:
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    except Exception:
                        pass
                    
                    pct = (idx / (total_deps + 2)) * 100
                    self.master.after(0, lambda v=pct: self.progress_var.set(v))
                    
                    if pkg == "Pillow":
                        self.master.after(0, self._refresh_logo_display)

            # 2. Gerar arquivo icon.ico se o Pillow estiver ativo
            self.master.after(0, lambda: self.status_var.set("Gerando arquivo de ícone do sistema..."))
            if os.path.exists(LOGO_PATH):
                try:
                    from PIL import Image
                    img = Image.open(LOGO_PATH)
                    img.save(ICON_PATH, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
                except Exception:
                    pass

            self.master.after(0, lambda v=90: self.progress_var.set(v))

            # 3. Registrar no Windows Explorer
            self.master.after(0, lambda: self.status_var.set("Registrando menu de contexto do Windows Explorer..."))
            
            # Detecta se ventana.exe existe na mesma pasta (distribuição compilada)
            prod_exe_path = os.path.join(SCRIPT_DIR, "app", "ventana.exe")
            if os.path.exists(prod_exe_path):
                self._create_registry_entries(None, prod_exe_path, ICON_PATH)
            else:
                pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                if not os.path.exists(pythonw_path):
                    pythonw_path = sys.executable
                self._create_registry_entries(pythonw_path, EXE_PATH, ICON_PATH)

            self.master.after(0, lambda: self.progress_var.set(100))
            self.master.after(0, lambda: self.status_var.set("Instalação concluída com sucesso!"))
            
            self.master.after(0, lambda: messagebox.showinfo(
                "Instalação Concluída", 
                "O Ventana foi instalado com sucesso!\n\nAgora você pode clicar com o botão direito sobre qualquer arquivo ou pasta no Windows Explorer e selecionar 'Ventana Token Counter' para contar tokens.",
                parent=self.master
            ))
        except Exception as e:
            self.master.after(0, lambda msg=str(e): messagebox.showerror("Erro de Instalação", f"Ocorreu um erro durante a instalação:\n{msg}", parent=self.master))
            self.master.after(0, lambda: self.status_var.set("Instalação falhou."))
        finally:
            self.master.after(0, self._unlock_ui)

    def _create_registry_entries(self, python_path, exe_path, icon_path):
        import winreg

        # Configurar comando de execução (executável direto ou interpretador python)
        if python_path:
            cmd_str = f'"{python_path}" "{exe_path}" "%1"'
        else:
            cmd_str = f'"{exe_path}" "%1"'

        # ── Para arquivos genéricos HKEY_CLASSES_ROOT\*\shell\VentanaTokenCounter ──
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"*\shell\VentanaTokenCounter") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "Ventana")
            if os.path.exists(icon_path):
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)
            
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"*\shell\VentanaTokenCounter\command") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, cmd_str)

        # ── Para pastas HKEY_CLASSES_ROOT\Directory\shell\VentanaTokenCounter ──
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\shell\VentanaTokenCounter") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "Ventana")
            if os.path.exists(icon_path):
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)
            
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\shell\VentanaTokenCounter\command") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, cmd_str)

    def _start_uninstall_flow(self):
        if not messagebox.askyesno(
            "Remover Integração", 
            "Tem certeza que deseja remover o Ventana do menu de contexto do Windows Explorer?\n\nAs dependências instaladas no Python não serão apagadas.",
            icon="warning",
            parent=self.master
        ):
            return

        self._lock_ui()
        threading.Thread(target=self._uninstall_worker, daemon=True).start()

    def _uninstall_worker(self):
        try:
            self.master.after(0, lambda: self.status_var.set("Removendo entradas de registro..."))
            
            self._delete_registry_entries()
            
            # Remover icon.ico se gerado localmente
            if os.path.exists(ICON_PATH):
                try:
                    os.remove(ICON_PATH)
                except Exception:
                    pass

            self.master.after(0, lambda: self.progress_var.set(100))
            self.master.after(0, lambda: self.status_var.set("Desinstalação concluída com sucesso."))
            
            self.master.after(0, lambda: messagebox.showinfo(
                "Integração Removida", 
                "A integração do Ventana com o Windows Explorer foi removida com sucesso.",
                parent=self.master
            ))
        except Exception as e:
            self.master.after(0, lambda msg=str(e): messagebox.showerror("Erro na Remoção", f"Ocorreu um erro ao desinstalar:\n{msg}", parent=self.master))
            self.master.after(0, lambda: self.status_var.set("Remoção falhou."))
        finally:
            self.master.after(0, self._unlock_ui)

    def _delete_registry_entries(self):
        import winreg

        def delete_subkeys(root, path):
            try:
                with winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS) as key:
                    info = winreg.QueryInfoKey(key)
                    # Exclui recursivamente subchaves primeiro
                    for _ in range(info[0]):
                        subkey_name = winreg.EnumKey(key, 0)
                        delete_subkeys(key, subkey_name)
                winreg.DeleteKey(root, path)
            except FileNotFoundError:
                pass
            except Exception:
                pass

        delete_subkeys(winreg.HKEY_CLASSES_ROOT, r"*\shell\VentanaTokenCounter")
        delete_subkeys(winreg.HKEY_CLASSES_ROOT, r"Directory\shell\VentanaTokenCounter")

if __name__ == "__main__":
    root = tk.Tk()
    app = VentanaInstaller(root)
    root.mainloop()
