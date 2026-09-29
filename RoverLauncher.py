import os
import re
import base64
import random
import ctypes
import threading
import queue
import time
import subprocess
import tkinter as tk
from ctypes import wintypes
from PIL import Image, ImageTk


# =====================================================================
# MCI — reproductor nativo de Windows
# =====================================================================
mci = ctypes.windll.winmm.mciSendStringW
mci.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
mci.restype = ctypes.c_long


# =====================================================================
# WIN32 API
# =====================================================================
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

WS_OVERLAPPED = 0x00000000
WS_CAPTION = 0x00C00000
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_TABSTOP = 0x00010000
WS_VSCROLL = 0x00200000

WS_EX_CLIENTEDGE = 0x00000200
WS_EX_DLGMODALFRAME = 0x00000001

CBS_DROPDOWNLIST = 0x0003
CBS_HASSTRINGS = 0x0200
BS_PUSHBUTTON = 0x00000000
BS_DEFPUSHBUTTON = 0x00000001
SS_LEFT = 0x00000000

WM_CREATE = 0x0001
WM_DESTROY = 0x0002
WM_COMMAND = 0x0111
WM_CLOSE = 0x0010
WM_SETFONT = 0x0030

CB_ADDSTRING = 0x0143
CB_SETCURSEL = 0x014E
CB_GETCURSEL = 0x0147

BN_CLICKED = 0
CBN_SELCHANGE = 1

SW_SHOW = 5
SW_RESTORE = 9
IDC_ARROW = 32512
COLOR_BTNFACE = 15


# =====================================================================
# ESTRUCTURAS WIN32
# =====================================================================
class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]


# =====================================================================
# ARGTYPES/RESTYPE
# =====================================================================
user32.DefWindowProcW.argtypes = [
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
]
user32.DefWindowProcW.restype = ctypes.c_longlong

user32.SendMessageW.argtypes = [
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPVOID
]
user32.SendMessageW.restype = ctypes.c_longlong

user32.CreateWindowExW.restype = wintypes.HWND
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
]

user32.SetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
user32.SetWindowTextW.restype = wintypes.BOOL

user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
user32.GetWindowRect.restype = wintypes.BOOL

user32.MoveWindow.argtypes = [
    wintypes.HWND, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wintypes.BOOL
]
user32.MoveWindow.restype = wintypes.BOOL

user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL

user32.UpdateWindow.argtypes = [wintypes.HWND]
user32.UpdateWindow.restype = wintypes.BOOL

user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL

user32.PostQuitMessage.argtypes = [ctypes.c_int]

user32.PostMessageW.argtypes = [
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
]
user32.PostMessageW.restype = wintypes.BOOL

user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wintypes.ATOM

user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
user32.UnregisterClassW.restype = wintypes.BOOL

user32.GetMessageW.argtypes = [
    ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT
]
user32.GetMessageW.restype = ctypes.c_int

user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.TranslateMessage.restype = wintypes.BOOL

user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype = ctypes.c_longlong

user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL

user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL

user32.GetForegroundWindow.restype = wintypes.HWND

user32.LoadIconW.argtypes = [wintypes.HINSTANCE, wintypes.LPVOID]
user32.LoadIconW.restype = wintypes.HICON

user32.LoadCursorW.argtypes = [wintypes.HINSTANCE, wintypes.LPVOID]
user32.LoadCursorW.restype = wintypes.HANDLE

user32.LoadImageW.argtypes = [
    wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
    ctypes.c_int, ctypes.c_int, wintypes.UINT
]
user32.LoadImageW.restype = wintypes.HANDLE

user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int

kernel32.LoadLibraryExW.argtypes = [
    wintypes.LPCWSTR, wintypes.HANDLE, wintypes.DWORD
]
kernel32.LoadLibraryExW.restype = wintypes.HMODULE

kernel32.FreeLibrary.argtypes = [wintypes.HMODULE]
kernel32.FreeLibrary.restype = wintypes.BOOL

gdi32.CreateFontW.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
    wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
    wintypes.LPCWSTR,
]
gdi32.CreateFontW.restype = wintypes.HANDLE

gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
gdi32.DeleteObject.restype = wintypes.BOOL


IMAGE_ICON = 1
LR_DEFAULTSIZE = 0x00000040
LR_SHARED = 0x00008000
LOAD_LIBRARY_AS_DATAFILE = 0x00000002


# =====================================================================
# AGENTE — ROVER
# =====================================================================
class RoverAgente:
    def __init__(self, root):
        self.root = root
        self.nombre_personaje = "Rover"
        self.ruta_base = os.path.join("agents", self.nombre_personaje)

        print(f"Iniciando {self.nombre_personaje}...")

        ruta_agent_js = os.path.join(self.ruta_base, "agent.js")
        ruta_sounds_js = os.path.join(self.ruta_base, "sounds-mp3.js")

        if not os.path.exists(ruta_agent_js):
            for alt in ["clippy.ready.js", "agent_clippy.js", "ready.js"]:
                ruta_alt = os.path.join(self.ruta_base, alt)
                if os.path.exists(ruta_alt):
                    ruta_agent_js = ruta_alt
                    break
            else:
                raise FileNotFoundError(f"No encontré agent.js en {self.ruta_base}.")

        with open(ruta_agent_js, "r", encoding="utf-8-sig") as f:
            self.texto_agent = f.read()

        self.sonidos_b64 = self.extraer_diccionario_sonidos(ruta_sounds_js)
        print(f"Sonidos extraídos: {len(self.sonidos_b64)}")

        self.frame_width, self.frame_height = self.extraer_frame_size()
        print(f"Frame size: {self.frame_width} × {self.frame_height}")

        ruta_map = os.path.join(self.ruta_base, "map.png")
        self.spritesheet = Image.open(ruta_map).convert("RGBA")
        print(f"Spritesheet: {self.spritesheet.size}")

        self.frame_size = self.frame_width

        self.datos_animaciones = self.extraer_animaciones()
        self.lista_animaciones = list(self.datos_animaciones.keys())
        print(f"Animaciones encontradas: {len(self.lista_animaciones)}")
        for n in self.lista_animaciones[:10]:
            print(f"  {n}: {len(self.datos_animaciones[n]['frames'])} frames")

        # ===============================================================
        # 🔽 SALUDOS DE ROVER
        # ===============================================================
        self.frases_saludo = [
            "¡Hola! Soy Rover, tu guía personal.",
            "¡Guau! ¡Bienvenido de vuelta!",
            "¡Hola humano! ¿A dónde vamos hoy?",
            "¡Guau guau! ¡Estoy listo para ayudarte!",
            "¡Hola! ¿Qué aventura tenemos hoy?",
            "¡Llegué! ¿Necesitas algo?",
            "¡Hola! Soy Rover. ¿Jugamos?",
            "¡Bienvenido! ¿Qué hacemos hoy?",
        ]

        # ===============================================================
        # 🔽 FRASES GENERALES DE ROVER
        # ===============================================================
        self.frases_nostalgicas = [
            "¡Hola! Bienvenido a tu casa. Soy Rover y seré tu guía.",
            "Para ingresar a una habitación, solo haz clic en una de las puertas.",
            "¿Eres un usuario nuevo? Déjame ayudarte a crear una cuenta.",
            "Por favor, escribe tu contraseña aquí para entrar a la sala.",
            "¡Hiciste un gran trabajo decorando esta habitación!",
            "Si alguna vez te pierdes, solo haz clic sobre mí y te guiaré.",
            "¿Qué desea buscar?",
            "Estoy buscando en todos los archivos y carpetas...",
            "Por favor, espere mientras examino el disco duro...",
            "¿Desea realizar una búsqueda avanzada?",
            "¡He encontrado los archivos que buscaba!",
            "Parece que está escribiendo una carta. ¿Necesita ayuda?",
            "Recuerde guardar su documento frecuentemente para evitar perder cambios.",
            "¡Me encanta jugar a traer la pelota! ¡Lánzame una pregunta!",
            "¿Qué desea hacer hoy en Microsoft Word?",
            "Puedo desenterrar información y traerte cualquier cosa que necesites.",
            "¡Prometo quedarme abajo y no subirme a los muebles!",
        ]

        self._audio_cache = {}

        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg="fuchsia")
        self.root.wm_attributes("-transparentcolor", "fuchsia")

        self.canvas = tk.Canvas(
            root,
            width=self.frame_width,
            height=self.frame_height,
            bg="fuchsia", highlightthickness=0
        )
        self.canvas.pack()

        self.burbuja = tk.Toplevel(self.root)
        self.burbuja.overrideredirect(True)
        self.burbuja.attributes("-topmost", True)
        self.burbuja.config(bg="#FFFFE1", bd=1, relief="solid")
        self.texto_burbuja = tk.Label(
            self.burbuja, text="", bg="#FFFFE1", fg="black",
            font=("MS Sans Serif", 8), wraplength=200, justify="left",
            padx=8, pady=8
        )
        self.texto_burbuja.pack()
        self.burbuja.withdraw()

        self.animacion_actual = "Idle" if "Idle" in self.lista_animaciones else (
            self.lista_animaciones[0] if self.lista_animaciones else ""
        )
        self.indice_cuadro = 0
        self.saliendo = False
        self.saliendo_pendiente = False
        self._after_id = None
        self._after_id_idle = None
        self.arrancando = True
        self._frame_idle_estatico = None
        self._mostrar_saludo_pendiente = False

        self.canvas.bind("<B1-Motion>", self.arrastrar)
        self.canvas.bind("<Button-1>", self.iniciar_arrastre)
        self.canvas.bind("<Button-3>", self.mostrar_menu)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Acerca de...", command=self.abrir_acerca_de)
        self.menu.add_separator()
        self.menu.add_command(
            label="📚 Biblioteca de animaciones",
            command=self.abrir_biblioteca_animaciones
        )
        self.menu.add_command(
            label="🎲 Reproducir animación random",
            command=self.reproducir_animacion_random
        )
        self.menu.add_separator()
        self.menu.add_command(label="Salir", command=self.ejecutar_salir)

        self._cola_comandos = queue.Queue()
        self._procesar_cola()

        self._hwnd_biblioteca = None
        self._hilo_biblioteca = None

        self.pos_x_inicial = 800
        self.pos_y_inicial = 500
        self.root.geometry(f"+{self.pos_x_inicial}+{self.pos_y_inicial}")
        self.actualizar_posicion_burbuja(self.pos_x_inicial, self.pos_y_inicial)

        self.root.attributes("-alpha", 0.0)
        self.root.after(50, self._arrancar_con_show)

    def _procesar_cola(self):
        try:
            while True:
                cmd = self._cola_comandos.get_nowait()
                if cmd[0] == "animacion":
                    self.reproducir_animacion_especifica(cmd[1])
                elif cmd[0] == "random":
                    self.reproducir_animacion_random()
                elif cmd[0] == "cerrar_biblioteca":
                    self._hwnd_biblioteca = None
                    self._hilo_biblioteca = None
        except queue.Empty:
            pass
        self.root.after(100, self._procesar_cola)

    # ===============================================================
    # EXTRACCIÓN
    # ===============================================================
    def extraer_frame_size(self):
        m = re.search(
            r'["\']?framesize["\']?\s*:\s*\[\s*(\d+)\s*(?:,\s*(\d+)\s*)?\]',
            self.texto_agent
        )
        if m:
            ancho = int(m.group(1))
            alto = int(m.group(2)) if m.group(2) else ancho
            print(f"[framesize] Array detectado: ancho={ancho}, alto={alto}")
            return ancho, alto

        m = re.search(r'["\']?framesize["\']?\s*:\s*(\d+)', self.texto_agent)
        if m:
            v = int(m.group(1))
            print(f"[framesize] Escalar detectado: {v}")
            return v, v

        print("[framesize] No detectado, usando fallback (80, 80)")
        return 80, 80

    def extraer_diccionario_sonidos(self, ruta_sounds):
        if not os.path.exists(ruta_sounds):
            return {}
        with open(ruta_sounds, "r", encoding="utf-8-sig") as f:
            contenido = f.read()
        return dict(re.findall(
            r'["\']?([\w\-]+)["\']?\s*:\s*["\'](data:audio/[^"\']+)["\']',
            contenido
        ))

    def extraer_animaciones(self):
        animaciones = {}
        texto = self.texto_agent

        m_anim = re.search(r'["\']animations["\']\s*:\s*\{', texto)
        if not m_anim:
            print("[warn] No encontré bloque 'animations'")
            return animaciones

        inicio_animations = m_anim.end() - 1
        fin_animations = self._encontrar_cierre(texto, inicio_animations, '{', '}')
        if fin_animations is None:
            print("[warn] Bloque 'animations' no cerrado")
            return animaciones

        bloque_animations = texto[inicio_animations + 1:fin_animations]

        patron = re.compile(r'"(\w+)"\s*:\s*\{')
        pos = 0
        while pos < len(bloque_animations):
            m = patron.search(bloque_animations, pos)
            if not m:
                break

            nombre = m.group(1)
            inicio_llave = m.end() - 1

            fin_llave = self._encontrar_cierre(bloque_animations, inicio_llave, '{', '}')
            if fin_llave is None:
                pos = m.end()
                continue

            bloque = bloque_animations[inicio_llave + 1:fin_llave]

            if re.search(r'["\']?frames["\']?\s*:\s*\[', bloque):
                frames = self._extraer_frames(bloque)
                if frames:
                    animaciones[nombre] = {"frames": frames}

            pos = fin_llave + 1

        return animaciones

    def _encontrar_cierre(self, texto, inicio, abre, cierra):
        prof = 0
        i = inicio
        en_str = False
        comilla = None
        while i < len(texto):
            c = texto[i]
            if en_str:
                if c == "\\":
                    i += 2
                    continue
                if c == comilla:
                    en_str = False
            else:
                if c in ('"', "'"):
                    en_str = True
                    comilla = c
                elif c == abre:
                    prof += 1
                elif c == cierra:
                    prof -= 1
                    if prof == 0:
                        return i
            i += 1
        return None

    def _extraer_frames(self, bloque):
        m = re.search(r'["\']?frames["\']?\s*:\s*\[', bloque)
        if not m:
            return []

        inicio = m.end() - 1
        fin = self._encontrar_cierre(bloque, inicio, '[', ']')
        if fin is None:
            return []

        contenido = bloque[inicio + 1:fin]
        frames = []
        pos = 0

        while True:
            mf = re.search(r'\{', contenido[pos:])
            if not mf:
                break
            ini_f = pos + mf.start()
            fin_f = self._encontrar_cierre(contenido, ini_f, '{', '}')
            if fin_f is None:
                break

            props = contenido[ini_f + 1:fin_f]
            d = {}

            f = re.search(r'["\']?frame["\']?\s*:\s*(\d+)', props)
            if f:
                d["frame"] = int(f.group(1))

            f = re.search(r'["\']?duration["\']?\s*:\s*(\d+)', props)
            if f:
                d["duration"] = int(f.group(1))

            f = re.search(r'["\']?sound["\']?\s*:\s*["\']([^"\']+)["\']', props)
            if f:
                d["sound"] = f.group(1)

            f = re.search(r'["\']?images["\']?\s*:\s*\[\s*\[([^\]]+)\]', props)
            if f:
                try:
                    coords = [int(n.strip()) for n in f.group(1).split(",")]
                    if len(coords) >= 2:
                        d["x"] = coords[0]
                        d["y"] = coords[1]
                except ValueError:
                    pass

            if d:
                frames.append(d)

            pos = fin_f + 1

        return frames

    def _recortar_frame(self, x, y):
        x = max(0, min(x, self.spritesheet.width - self.frame_width))
        y = max(0, min(y, self.spritesheet.height - self.frame_height))
        return self.spritesheet.crop(
            (x, y, x + self.frame_width, y + self.frame_height)
        )

    # ===============================================================
    # AUDIO
    # ===============================================================
    def reproducir_sonido(self, nombre_sonido):
        if self.saliendo or self.saliendo_pendiente:
            return
        if nombre_sonido not in self.sonidos_b64:
            return

        if nombre_sonido not in self._audio_cache:
            data_b64 = self.sonidos_b64[nombre_sonido]
            if "," in data_b64:
                data_b64 = data_b64.split(",", 1)[1]
            try:
                audio_bytes = base64.b64decode(data_b64)
            except Exception:
                return
            ext = ".wav" if audio_bytes[:4] == b"RIFF" else ".mp3"
            ruta = os.path.join(
                os.environ.get("TEMP", "."),
                f"agent_{self.nombre_personaje}_{nombre_sonido}{ext}"
            )
            if not os.path.exists(ruta):
                try:
                    with open(ruta, "wb") as f:
                        f.write(audio_bytes)
                except Exception:
                    return
            self._audio_cache[nombre_sonido] = ruta

        ruta = self._audio_cache[nombre_sonido]
        threading.Thread(target=self._play_mci, args=(ruta,), daemon=True).start()

    def _play_mci(self, ruta):
        alias = f"rov{random.randint(0, 9999999)}"
        buf = ctypes.create_unicode_buffer(256)
        status = ctypes.create_unicode_buffer(64)

        try:
            ret = mci(f'open "{ruta}" type mpegvideo alias {alias}', buf, 256, None)
            if ret != 0:
                return
            ret = mci(f'play {alias}', buf, 256, None)
            if ret != 0:
                return
            while True:
                mci(f'status {alias} mode', status, 64, None)
                if status.value != "playing":
                    break
                time.sleep(0.05)
        except Exception:
            pass
        finally:
            mci(f'close {alias}', buf, 256, None)

    def mostrar_mensaje(self, texto, duracion_ms=5000):
        self.texto_burbuja.config(text=texto)
        self.burbuja.deiconify()
        self.actualizar_posicion_burbuja(self.root.winfo_x(), self.root.winfo_y())
        self.root.after(duracion_ms, self.burbuja.withdraw)

    # ===============================================================
    # 🔽 ARRANQUE: Show → saludo aleatorio → Idle
    # ===============================================================
    def _arrancar_con_show(self):
        self.root.attributes("-alpha", 1.0)
        self._mostrar_saludo_pendiente = True

        if "Show" in self.datos_animaciones:
            self.arrancando = True
            self.animacion_actual = "Show"
            self.indice_cuadro = 0
            self.reproducir_animacion()
        else:
            self.arrancando = False
            self._mostrar_saludo_inicial()
            self._mostrar_idle_estatico()

    def _mostrar_saludo_inicial(self):
        if self.saliendo:
            return
        frase = random.choice(self.frases_saludo)
        print(f"[saludo] {frase}")
        self.mostrar_mensaje(frase, 5000)

    def _precachear_idle(self):
        if self._frame_idle_estatico is not None:
            return
        if "Idle" not in self.datos_animaciones:
            return
        frames = self.datos_animaciones["Idle"].get("frames", [])
        if not frames:
            return
        ci = frames[0]
        if "x" in ci and "y" in ci:
            x, y = ci["x"], ci["y"]
        else:
            nc = ci.get("frame", 0)
            cols = self.spritesheet.width // self.frame_width
            x = (nc % cols) * self.frame_width
            y = (nc // cols) * self.frame_height

        celda = self._recortar_frame(x, y)
        self._frame_idle_estatico = ImageTk.PhotoImage(celda)

    def _mostrar_idle_estatico(self):
        if self.saliendo:
            return
        self._precachear_idle()
        if self._frame_idle_estatico is None:
            return
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self._frame_idle_estatico)
        self._after_id = None
        espera = random.randint(20000, 30000)
        self._after_id_idle = self.root.after(espera, self._decidir_siguiente_accion)

    def _decidir_siguiente_accion(self):
        if self.saliendo:
            return
        r = random.random()
        if r < 0.60:
            self._mostrar_idle_estatico()
        else:
            self._reproducir_animacion_al_azar_y_frase()

    # ===============================================================
    # 🔽 RANDOM: elige CUALQUIER animación del agent.js
    # ===============================================================
    def _animaciones_candidatas(self):
        excluidas = {"Hide", "HideQuick", "Ocultar"}
        return [a for a in self.lista_animaciones if a not in excluidas]

    def _reproducir_animacion_al_azar_y_frase(self):
        if self.saliendo:
            return
        candidatas = self._animaciones_candidatas()
        if not candidatas:
            self._mostrar_idle_estatico()
            return

        otras = [a for a in candidatas if a != self.animacion_actual]
        elegida = random.choice(otras if otras else candidatas)

        for attr in ("_after_id", "_after_id_idle"):
            try:
                aid = getattr(self, attr)
                if aid:
                    self.root.after_cancel(aid)
            except Exception:
                pass
            setattr(self, attr, None)

        self.animacion_actual = elegida
        self.indice_cuadro = 0

        if self.frases_nostalgicas:
            self.mostrar_mensaje(random.choice(self.frases_nostalgicas), 4000)

        print(f"[random] {elegida} (de {len(candidatas)} candidatas)")
        self.reproducir_animacion()

    def reproducir_animacion(self):
        if self.animacion_actual not in self.datos_animaciones:
            return
        pasos = self.datos_animaciones[self.animacion_actual].get("frames", [])

        if self.indice_cuadro < len(pasos):
            ci = pasos[self.indice_cuadro]
            if "x" in ci and "y" in ci:
                x, y = ci["x"], ci["y"]
            else:
                nc = ci.get("frame", 0)
                cols = self.spritesheet.width // self.frame_width
                x = (nc % cols) * self.frame_width
                y = (nc // cols) * self.frame_height

            celda = self._recortar_frame(x, y)
            self.img_tk = ImageTk.PhotoImage(celda)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.img_tk)

            if "sound" in ci:
                self.reproducir_sonido(ci["sound"])

            dur = ci.get("duration", 100)
            if dur <= 0:
                dur = 100
            self.indice_cuadro += 1
            self._after_id = self.root.after(dur, self.reproducir_animacion)
        else:
            if self.saliendo and self.animacion_actual == "Hide":
                self._finalizar_salida()
                return

            self.indice_cuadro = 0

            if self.arrancando:
                self.arrancando = False
                self.animacion_actual = "Idle"
                if getattr(self, "_mostrar_saludo_pendiente", False):
                    self._mostrar_saludo_pendiente = False
                    self._mostrar_saludo_inicial()
                self._after_id = self.root.after(500, self._mostrar_idle_estatico)
                return

            self.animacion_actual = "Idle"
            self._after_id = self.root.after(400, self._mostrar_idle_estatico)

    def _finalizar_salida(self):
        try:
            if self._after_id:
                self.root.after_cancel(self._after_id)
        except Exception:
            pass
        try:
            if self._after_id_idle:
                self.root.after_cancel(self._after_id_idle)
        except Exception:
            pass
        try:
            buf = ctypes.create_unicode_buffer(256)
            mci('close all', buf, 256, None)
        except Exception:
            pass
        self._matar_ventanas_fantasma()
        try:
            self.burbuja.destroy()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def _matar_ventanas_fantasma(self):
        for proc in ["lavaudio.exe", "LAVAudio.exe", "lavvideo.exe",
                     "wmplayer.exe", "mplayer2.exe"]:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", proc],
                    capture_output=True, timeout=2,
                    creationflags=0x08000000
                )
            except Exception:
                pass

    def mostrar_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def abrir_acerca_de(self):
        if self.saliendo:
            return
        for attr in ("_after_id", "_after_id_idle"):
            try:
                aid = getattr(self, attr)
                if aid:
                    self.root.after_cancel(aid)
            except Exception:
                pass
            setattr(self, attr, None)

        self.mostrar_mensaje(random.choice(self.frases_nostalgicas), 5000)
        self._reproducir_animacion_al_azar_y_frase()

        try:
            hwnd_str = self.root.frame()
            hwnd = int(hwnd_str, 16) if hwnd_str.startswith("0x") else user32.GetForegroundWindow()
            ctypes.windll.shell32.ShellAboutW(
                hwnd, f"{self.nombre_personaje}",
                "Rover corriendo con parser por conteo + MCI nativo.",
                0
            )
        except Exception as e:
            print(f"[ShellAbout] {e}")

    def reproducir_animacion_random(self):
        self._reproducir_animacion_al_azar_y_frase()

    def ejecutar_salir(self):
        self.burbuja.withdraw()
        if self._hwnd_biblioteca:
            try:
                user32.PostMessageW(self._hwnd_biblioteca, WM_CLOSE, 0, 0)
            except Exception:
                pass
        try:
            buf = ctypes.create_unicode_buffer(256)
            mci('close all', buf, 256, None)
        except Exception:
            pass
        for attr in ("_after_id", "_after_id_idle"):
            try:
                aid = getattr(self, attr)
                if aid:
                    self.root.after_cancel(aid)
            except Exception:
                pass
            setattr(self, attr, None)
        if "Hide" in self.datos_animaciones:
            self.saliendo = True
            self.saliendo_pendiente = True
            self.indice_cuadro = 0
            self.animacion_actual = "Hide"
            print("[salir] Reproduciendo animación Hide...")
            self.reproducir_animacion()
        else:
            print("[salir] No hay Hide, cerrando directo")
            self._finalizar_salida()

    def reproducir_animacion_especifica(self, nombre):
        if self.saliendo or nombre not in self.datos_animaciones:
            return
        for attr in ("_after_id", "_after_id_idle"):
            try:
                aid = getattr(self, attr)
                if aid:
                    self.root.after_cancel(aid)
            except Exception:
                pass
            setattr(self, attr, None)
        self.animacion_actual = nombre
        self.indice_cuadro = 0
        print(f"[biblioteca] {nombre}")
        self.reproducir_animacion()

    def _cargar_icono_panel_control_xp(self):
        sysroot = os.environ.get("SystemRoot", "C:\\Windows")
        ruta_shell32 = os.path.join(sysroot, "System32", "shell32.dll")
        if not os.path.exists(ruta_shell32):
            return None
        hmod = kernel32.LoadLibraryExW(ruta_shell32, None, LOAD_LIBRARY_AS_DATAFILE)
        if not hmod:
            return None
        try:
            hicon = user32.LoadImageW(
                hmod,
                ctypes.c_wchar_p(137),
                IMAGE_ICON,
                0, 0,
                LR_DEFAULTSIZE | LR_SHARED
            )
            return hicon if hicon else None
        except Exception:
            return None

    def abrir_biblioteca_animaciones(self):
        if self._hwnd_biblioteca:
            try:
                if user32.IsWindow(self._hwnd_biblioteca):
                    user32.ShowWindow(self._hwnd_biblioteca, SW_RESTORE)
                    user32.SetForegroundWindow(self._hwnd_biblioteca)
                    return
            except Exception:
                pass
            self._hwnd_biblioteca = None
        hilo = threading.Thread(target=self._hilo_ventana_biblioteca, daemon=True)
        hilo.start()
        self._hilo_biblioteca = hilo

    def _hilo_ventana_biblioteca(self):
        hinst = kernel32.GetModuleHandleW(None)

        prioridades = {"Show", "Hide", "HideQuick", "Greet", "Greeting"}
        normales = sorted([a for a in self.lista_animaciones if a not in prioridades])
        especiales = [a for a in ["Greet", "Greeting", "Show", "Hide", "HideQuick"]
                      if a in self.lista_animaciones]
        orden = normales + especiales

        estado = {
            "hwnd": None,
            "combo": None,
            "lbl_info": None,
            "orden": orden,
            "buffers_combo": [],
        }

        hfuente = gdi32.CreateFontW(
            -11, 0, 0, 0, 400, 0, 0, 0,
            1, 0, 0, 0, 0,
            "Microsoft Sans Serif"
        )

        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_longlong, wintypes.HWND, wintypes.UINT,
            wintypes.WPARAM, wintypes.LPARAM
        )

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == WM_CREATE:
                lbl_sel = user32.CreateWindowExW(
                    0, "STATIC", "Selecciona una animación:",
                    WS_CHILD | WS_VISIBLE | SS_LEFT,
                    16, 12, 360, 18, hwnd, 100, None, None
                )
                user32.SendMessageW(lbl_sel, WM_SETFONT, hfuente, 1)

                combo = user32.CreateWindowExW(
                    WS_EX_CLIENTEDGE, "COMBOBOX", "",
                    WS_CHILD | WS_VISIBLE | WS_TABSTOP | WS_VSCROLL |
                    CBS_DROPDOWNLIST | CBS_HASSTRINGS,
                    16, 34, 360, 260, hwnd, 101, None, None
                )
                user32.SendMessageW(combo, WM_SETFONT, hfuente, 1)

                buffers = []
                for nombre in orden:
                    b = ctypes.c_wchar_p(nombre)
                    buffers.append(b)
                    user32.SendMessageW(combo, CB_ADDSTRING, 0, b)
                estado["buffers_combo"] = buffers

                if self.animacion_actual in orden:
                    user32.SendMessageW(combo, CB_SETCURSEL, orden.index(self.animacion_actual), 0)
                else:
                    user32.SendMessageW(combo, CB_SETCURSEL, 0, 0)
                estado["combo"] = combo

                lbl_info = user32.CreateWindowExW(
                    0, "STATIC", "",
                    WS_CHILD | WS_VISIBLE | SS_LEFT,
                    16, 66, 360, 36, hwnd, 102, None, None
                )
                user32.SendMessageW(lbl_info, WM_SETFONT, hfuente, 1)
                estado["lbl_info"] = lbl_info
                self._actualizar_info_nativa(estado)

                btn1 = user32.CreateWindowExW(
                    0, "BUTTON", "▶ Comenzar",
                    WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_DEFPUSHBUTTON,
                    16, 110, 115, 28, hwnd, 103, None, None
                )
                user32.SendMessageW(btn1, WM_SETFONT, hfuente, 1)

                btn2 = user32.CreateWindowExW(
                    0, "BUTTON", "🎲 Random",
                    WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_PUSHBUTTON,
                    139, 110, 115, 28, hwnd, 104, None, None
                )
                user32.SendMessageW(btn2, WM_SETFONT, hfuente, 1)

                btn3 = user32.CreateWindowExW(
                    0, "BUTTON", "Cerrar",
                    WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_PUSHBUTTON,
                    262, 110, 115, 28, hwnd, 105, None, None
                )
                user32.SendMessageW(btn3, WM_SETFONT, hfuente, 1)
                return 0

            elif msg == WM_COMMAND:
                id_control = wparam & 0xFFFF
                codigo = (wparam >> 16) & 0xFFFF

                if id_control == 101 and codigo == CBN_SELCHANGE:
                    self._actualizar_info_nativa(estado)

                elif id_control == 103 and codigo == BN_CLICKED:
                    idx = user32.SendMessageW(estado["combo"], CB_GETCURSEL, 0, 0)
                    if idx >= 0 and idx < len(estado["orden"]):
                        self._cola_comandos.put(("animacion", estado["orden"][idx]))

                elif id_control == 104 and codigo == BN_CLICKED:
                    self._cola_comandos.put(("random", None))

                elif id_control == 105 and codigo == BN_CLICKED:
                    user32.DestroyWindow(hwnd)
                return 0

            elif msg == WM_CLOSE:
                user32.DestroyWindow(hwnd)
                return 0

            elif msg == WM_DESTROY:
                self._cola_comandos.put(("cerrar_biblioteca", None))
                user32.PostQuitMessage(0)
                return 0

            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        proc_ref = WNDPROC(wnd_proc)
        estado["_proc_ref"] = proc_ref

        nombre_clase = f"RoverBibliotecaCls_{id(self)}_{random.randint(100000, 999999)}"

        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = 0
        wc.lpfnWndProc = ctypes.cast(proc_ref, ctypes.c_void_p)
        wc.hInstance = hinst

        hicon_xp = self._cargar_icono_panel_control_xp()
        wc.hIcon = hicon_xp if hicon_xp else user32.LoadIconW(None, ctypes.c_void_p(32512))
        wc.hCursor = user32.LoadCursorW(None, ctypes.c_void_p(IDC_ARROW))
        wc.hbrBackground = COLOR_BTNFACE + 1
        wc.lpszClassName = nombre_clase
        wc.hIconSm = hicon_xp if hicon_xp else user32.LoadIconW(None, ctypes.c_void_p(32512))

        if not user32.RegisterClassExW(ctypes.byref(wc)):
            print("[biblioteca] RegisterClassExW falló")
            return

        estilo = WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX
        hwnd = user32.CreateWindowExW(
            WS_EX_DLGMODALFRAME, nombre_clase,
            "Biblioteca de animaciones — Rover",
            estilo, 100, 100, 420, 210, None, None, hinst, None
        )
        if not hwnd:
            print("[biblioteca] CreateWindowExW falló")
            try:
                user32.UnregisterClassW(nombre_clase, hinst)
            except Exception:
                pass
            return

        estado["hwnd"] = hwnd
        self._hwnd_biblioteca = hwnd

        try:
            r = RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            w, h = r.right - r.left, r.bottom - r.top
            x = self.root.winfo_x() + self.frame_size + 10
            y = self.root.winfo_y() - 40
            sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            x = max(0, min(x, sw - w))
            y = max(0, min(y, sh - h))
            user32.MoveWindow(hwnd, x, y, w, h, True)
        except Exception:
            pass

        user32.ShowWindow(hwnd, SW_SHOW)
        user32.UpdateWindow(hwnd)

        msg = MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        try:
            gdi32.DeleteObject(hfuente)
        except Exception:
            pass
        try:
            user32.UnregisterClassW(nombre_clase, hinst)
        except Exception:
            pass

    def _actualizar_info_nativa(self, estado):
        try:
            idx = user32.SendMessageW(estado["combo"], CB_GETCURSEL, 0, 0)
            if idx < 0 or idx >= len(estado["orden"]):
                return
            nombre = estado["orden"][idx]
            frames = self.datos_animaciones.get(nombre, {}).get("frames", [])
            total = sum(f.get("duration", 100) for f in frames)
            texto = f"  {len(frames)} frames · duración ≈ {total} ms"
            user32.SetWindowTextW(estado["lbl_info"], ctypes.c_wchar_p(texto))
        except Exception:
            pass

    def iniciar_arrastre(self, event):
        self.x_offset = event.x
        self.y_offset = event.y

    def arrastrar(self, event):
        x = self.root.winfo_x() + event.x - self.x_offset
        y = self.root.winfo_y() + event.y - self.y_offset
        self.root.geometry(f"+{x}+{y}")
        self.actualizar_posicion_burbuja(x, y)

    def actualizar_posicion_burbuja(self, x, y):
        self.burbuja.geometry(f"+{x - 30}+{y - self.frame_height + 20}")


# =====================================================================
# MAIN
# =====================================================================
if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = RoverAgente(root)
    except Exception as e:
        print(f"ERROR al iniciar: {e}")
        import traceback
        traceback.print_exc()
        root.destroy()
        raise SystemExit(1)

    root.mainloop()