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

kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

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
# AGENTE — LINKS
# =====================================================================
class LinksAgente:
    def __init__(self, root):
        self.root = root
        self.nombre_personaje = "Links"
        self.ruta_base = os.path.join("agents", self.nombre_personaje)

        print(f"Iniciando {self.nombre_personaje}...")

        ruta_agent_js = os.path.join(self.ruta_base, "agent.js")
        ruta_sounds_js = os.path.join(self.ruta_base, "sounds-mp3.js")

        if not os.path.exists(ruta_agent_js):
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
        for n in self.lista_animaciones[:15]:
            print(f"  {n}: {len(self.datos_animaciones[n]['frames'])} frames")

        # Direcciones de las animaciones Move*
        self.direcciones_move = {
            "MoveUp":    (0, -1),
            "MoveDown":  (0,  1),
            "MoveLeft":  (-1, 0),
            "MoveRight": (1,  0),
        }

        # -----------------------------------------------------------------
        # FRASES DE SALUDO
        # -----------------------------------------------------------------
        self.frases_saludo = [
            "¡Miau! Hola, soy Links. ¿En qué te ayudo?",
            "¡Miau! ¿Me llamaste o fue el viento?",
            "¡Hola! Soy Links, tu gato asistente. Ronroneo incluido.",
            "¡Miau! Aparecí justo cuando me necesitabas.",
            "¡Saludos! Links a tu servicio. Y a tus ratones.",
            "¡Hola! Soy Links. ¿Un consejo o una siesta?",
            "¡Miau! ¿Empezamos o dormimos un rato?",
            "¡Hola! Soy Links, el gato más útil de tu escritorio.",
            "¡Miau! ¿Te ayudo con eso o lo persigo?",
            "¡Saludos! Llegó Links. ¿Qué hacemos?",
            "¡Hola! Ronroneo listo. ¿Qué necesitas?",
            "¡Miau! Aparecí de la nada, como todo buen gato.",
            "¡Hola! Soy Links. Puedo ayudarte, pero primero una siesta.",
            "¡Miau! ¿Un atajo de teclado o un ratón?",
            "¡Saludos! Links a la orden. ¡Miau!",
            "¡Hola! Soy Links. ¿Charlo un rato o te ayudo?",
            "¡Miau! ¿Qué se te ofrece hoy?",
            "¡Hola! Soy Links. Cuidado con el teclado, que me gusta dormir ahí.",
            "¡Miau! Estoy listo. Bueno, casi. Dame un segundo.",
            "¡Saludos! Soy Links. ¿Empezamos?",
        ]

        # -----------------------------------------------------------------
        # FRASES NOSTÁLGICAS / ALEATORIAS
        # -----------------------------------------------------------------
        self.frases_nostalgicas = [
            "Parece que estás escribiendo una carta. ¿Quieres que te ayude?",
            "¿Quieres que te muestre cómo hacerlo?",
            "Parece que estás escribiendo un documento. ¿Necesitas ayuda?",
            "¿Sabías que puedes guardar tu trabajo con Ctrl+S?",
            "Veo que estás trabajando duro. ¡Sigue así!",
            "¿Quieres que te muestre algunas plantillas?",
            "Parece que estás creando un currículum. ¿Quieres ayuda?",
            "Para agregar una tabla, ve al menú Insertar.",
            "Para cambiar la fuente, selecciona el texto y usa la barra de formato.",
            "¿Necesitas ayuda con los márgenes?",
            "Puedes usar viñetas para organizar tu lista.",
            "Parece que estás creando una hoja de cálculo.",
            "¿Quieres que te muestre cómo hacer una fórmula?",
            "Para sumar una columna, usa =SUMA().",
            "Puedes ordenar los datos seleccionándolos y usando Datos > Ordenar.",
            "Parece que estás creando una presentación.",
            "¿Quieres que te sugiera un diseño?",
            "Puedes agregar una nueva diapositiva con Ctrl+M.",
            "Recuerda no poner demasiado texto en cada diapositiva.",
            "¿Necesitas ayuda con eso?",
            "Parece que necesitas ayuda.",
            "¿Quieres que te dé un consejo?",
            "Estoy aquí si me necesitas.",
            "¿Puedo ayudarte con algo más?",
            "Presiona F1 si necesitas ayuda.",
            "Recuerda guardar tu trabajo frecuentemente.",
            "¿Has considerado usar un asistente?",
            "Parece que estás perdido. ¿Te ayudo?",
            "¡Hola! ¿Quieres que te enseñe algo nuevo?",

            # — Frases con más sabor a Links —
            "¡Miau! Guarda tu trabajo con Ctrl+S, no lo olvides.",
            "Un gato sabio siempre revisa la vista previa antes de imprimir.",
            "Puedo hacer aparecer una tabla como por arte de gato.",
            "¿Sabías que Ctrl+Z deshace hasta los rasguños más profundos?",
            "¡Miau! Me gusta dormir sobre el teclado. ¿Y a ti?",
            "Puedo cazar ratones... o errores ortográficos. Tú eliges.",
            "Un documento ordenado es como una caja de arena limpia.",
            "¡Miau! Ctrl+C para copiar, Ctrl+V para pegar. Fácil.",
            "Puedo predecir el futuro: te vas a arrepentir si no guardás.",
            "Los gatos también usamos estilos y formatos consistentes.",
            "¡Miau! ¿Quieres que te enseñe el truco de las viñetas?",
            "En mis tiempos, esto se resolvía con una siesta. Ahora con un clic.",
            "Puedo invocar una plantilla si me lo pides.",
            "Un gato siempre tiene un plan B. Tú deberías tener un respaldo.",
            "¡Miau! ¿Sabías que Ctrl+E centra el texto?",
            "Puedo detectar un párrafo largo a simple vista. ¿Lo dividimos?",
            "La magia está en los detalles. Y en los márgenes.",
            "¡Miau! Si te pierdes, silba y vendré... bueno, si no estoy durmiendo.",
            "Puedo ver que estás concentrado. No te interrumpo más... por ahora.",
            "¿Quieres que te enseñe a insertar imágenes?",
            "Los gatos no revisan ortografía. Bueno, este gato sí.",
            "¡Miau! Mi bola de cristal dice que necesitas café. Y guardar.",
            "¿Sabes qué es más poderoso que un gato? Un buen atajo de teclado.",
            "¡Miau! Ctrl+B pone en negrita. De nada.",
            "Puedo hacer aparecer un gráfico como por arte de gato.",
            "Un gato ordenado es un gato eficiente. O algo así.",
            "¡Miau! ¿Un consejo? Usa la función Buscar cuando te pierdas.",
            "Puedo invocar una plantilla de informe si lo deseas.",
            "En mis tiempos, esto se hacía con pluma y papel. Progreso, supongo.",
            "La curiosidad mató al gato. Pero Ctrl+Z lo revive.",
            "¡Miau! ¿Quieres que te enseñe el conjuro de las tablas?",
            "Puedo oler un error de tipeo desde aquí.",
            "Un documento bien ordenado es como un buen plato de comida.",
            "¡Miau! No imprimas sin revisar. Confía en este gato.",
            "Puedo enseñarte el hechizo de las negritas. Ctrl+B.",
            "¿Sabías que Ctrl+M agrega una diapositiva? ¡Miau!",
            "Puedo ver el futuro de tu documento... y necesita más formato.",
            "¡Miau! Deja de teclear un momento y acaricia a este gato.",
            "Puedo invocar una plantilla de currículum si lo deseas.",
            "Un gato siempre tiene siete vidas. Tú deberías tener un respaldo.",
            "¡Miau! ¿Ya guardaste?",
            "Puedo hacer aparecer una fórmula si me lo pides.",
            "La física cuántica es complicada. Ctrl+C y Ctrl+V, no.",
            "¡Miau! ¿Quieres que revise tu ortografía?",
            "Puedo ver que estás pensando. ¿Te ayudo con eso?",
            "Un documento bien ordenado es como una buena siesta: placentero.",
            "¡Miau! Ctrl+P imprime. Pero revisá antes.",
            "Puedo hacer aparecer una tabla como por arte de magia gatuna.",
            "En mis tiempos, esto se hacía con un ratón de verdad. Ahora con uno de plástico.",
            "¡Miau! ¿Un consejo? No pongas demasiado texto en cada diapositiva.",
            "Puedo invocar una plantilla de tesis si lo deseas.",
            "Un gato nunca se pierde. Solo explora nuevos territorios.",
            "¡Miau! ¿Quieres que te enseñe a insertar tablas?",
            "Puedo detectar un párrafo mal alineado a simple vista.",
            "¡Miau! Encontré el botón de centrar: Ctrl+E.",
            "Un documento ordenado es como un gato limpio: siempre listo.",
            "Puedo ver que estás concentrado. No te interrumpo más... ¡Miau!",
            "En mis tiempos, esto se resolvía con una siesta. Ahora con un clic.",
        ]

        self._audio_cache = {}
        self._imgs_tk = []
        self._cerrando = False

        # Cola de audio (reproduce un sonido a la vez, en orden)
        self._cola_audio = queue.Queue()
        self._hilo_audio_activo = False
        self._lock_audio = threading.Lock()

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
            font=("MS Sans Serif", 8), wraplength=220, justify="left",
            padx=8, pady=8
        )
        self.texto_burbuja.pack()
        self.burbuja.withdraw()

        idle_inicial = self._buscar_idle()
        self.animacion_actual = idle_inicial if idle_inicial else (
            self.lista_animaciones[0] if self.lista_animaciones else ""
        )
        self.indice_cuadro = 0
        self.saliendo = False
        self.saliendo_pendiente = False
        self._after_id = None
        self._after_id_idle = None
        self._after_id_movimiento = None
        self._after_id_burbuja = None
        self.arrancando = True
        self._frame_idle_estatico = None
        self._mostrar_saludo_pendiente = False
        self._moviendo = False

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
        self._programar_movimiento_aleatorio()

    # -----------------------------------------------------------------
    # HELPERS
    # -----------------------------------------------------------------
    def _buscar_idle(self):
        for n in ("Idle1_1", "Idle1_2", "Idle1_3", "Idle1_4",
                  "Idle2_1", "Idle2_2", "Idle3_1", "Idle3_2",
                  "RestPose", "Idle"):
            if n in self.datos_animaciones:
                return n
        return None

    def _elegir_branch(self, branches):
        total = sum(b.get("weight", 100) for b in branches)
        if total <= 0:
            return None
        r = random.randint(1, total)
        acum = 0
        for b in branches:
            acum += b.get("weight", 100)
            if r <= acum:
                return b.get("frameIndex")
        return branches[-1].get("frameIndex")

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

        print("[framesize] No detectado, usando fallback (128, 128)")
        return 128, 128

    def extraer_diccionario_sonidos(self, ruta_sounds):
        if not os.path.exists(ruta_sounds):
            print(f"[audio] No existe {ruta_sounds}")
            return {}
        with open(ruta_sounds, "r", encoding="utf-8-sig") as f:
            contenido = f.read()
        return dict(re.findall(
            r'["\']([^"\']+)["\']\s*:\s*["\'](data:audio/[^"\']+)["\']',
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
            tiene_algo = False

            f = re.search(r'["\']?frame["\']?\s*:\s*(\d+)', props)
            if f:
                d["frame"] = int(f.group(1))
                tiene_algo = True

            f = re.search(r'["\']?duration["\']?\s*:\s*(\d+)', props)
            if f:
                d["duration"] = int(f.group(1))
                tiene_algo = True

            f = re.search(r'["\']?sound["\']?\s*:\s*["\']([^"\']+)["\']', props)
            if f:
                d["sound"] = f.group(1)
                tiene_algo = True

            f = re.search(r'["\']?exitBranch["\']?\s*:\s*(\d+)', props)
            if f:
                d["exitBranch"] = int(f.group(1))
                tiene_algo = True

            mb = re.search(r'["\']?branching["\']?\s*:\s*\{', props)
            if mb:
                ini_b = mb.end() - 1
                fin_b = self._encontrar_cierre(props, ini_b, '{', '}')
                if fin_b is not None:
                    bloque_b = props[ini_b + 1:fin_b]
                    mbr = re.search(r'["\']?branches["\']?\s*:\s*\[', bloque_b)
                    if mbr:
                        ini_arr = mbr.end() - 1
                        fin_arr = self._encontrar_cierre(bloque_b, ini_arr, '[', ']')
                        if fin_arr is not None:
                            arr = bloque_b[ini_arr + 1:fin_arr]
                            branches = []
                            p2 = 0
                            while True:
                                mo = re.search(r'\{', arr[p2:])
                                if not mo:
                                    break
                                io = p2 + mo.start()
                                fo = self._encontrar_cierre(arr, io, '{', '}')
                                if fo is None:
                                    break
                                obj = arr[io + 1:fo]
                                fi = re.search(r'["\']?frameIndex["\']?\s*:\s*(\d+)', obj)
                                wi = re.search(r'["\']?weight["\']?\s*:\s*(\d+)', obj)
                                if fi:
                                    branches.append({
                                        "frameIndex": int(fi.group(1)),
                                        "weight": int(wi.group(1)) if wi else 100
                                    })
                                p2 = fo + 1
                            if branches:
                                d["branches"] = branches
                                tiene_algo = True

            mi = re.search(r'["\']?images["\']?\s*:\s*\[', props)
            if mi:
                ini_img = mi.end() - 1
                fin_img = self._encontrar_cierre(props, ini_img, '[', ']')
                if fin_img is not None:
                    arr_img = props[ini_img + 1:fin_img]
                    sprites = []
                    p3 = 0
                    while True:
                        mo = re.search(r'\[', arr_img[p3:])
                        if not mo:
                            break
                        io = p3 + mo.start()
                        fo = self._encontrar_cierre(arr_img, io, '[', ']')
                        if fo is None:
                            break
                        dentro = arr_img[io + 1:fo]
                        try:
                            coords = [int(n.strip()) for n in dentro.split(",")]
                            if len(coords) >= 2:
                                sprites.append(tuple(coords))
                        except ValueError:
                            pass
                        p3 = fo + 1
                    if sprites:
                        d["sprites"] = sprites
                        d["x"], d["y"] = sprites[0][0], sprites[0][1]
                        tiene_algo = True

            if tiene_algo or "duration" in d:
                frames.append(d)

            pos = fin_f + 1

        return frames

    def _recortar_frame(self, x, y, w=None, h=None):
        w = w or self.frame_width
        h = h or self.frame_height
        x = max(0, min(x, self.spritesheet.width - w))
        y = max(0, min(y, self.spritesheet.height - h))
        return self.spritesheet.crop((x, y, x + w, y + h))

    # ===============================================================
    # AUDIO — cola serializada (un sonido a la vez, en orden)
    # ===============================================================
    def reproducir_sonido(self, nombre_sonido):
        if self._cerrando or self.saliendo_pendiente:
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
        self._cola_audio.put(ruta)
        self._asegurar_hilo_audio()

    def _asegurar_hilo_audio(self):
        with self._lock_audio:
            if self._hilo_audio_activo:
                return
            self._hilo_audio_activo = True
        threading.Thread(target=self._loop_audio, daemon=True).start()

    def _loop_audio(self):
        while True:
            try:
                ruta = self._cola_audio.get(timeout=1.0)
            except queue.Empty:
                with self._lock_audio:
                    self._hilo_audio_activo = False
                return
            if ruta is None:
                with self._lock_audio:
                    self._hilo_audio_activo = False
                return
            try:
                self._play_mci(ruta)
            except Exception:
                pass

    def _play_mci(self, ruta):
        alias = f"lnk{random.randint(0, 9999999)}"
        buf = ctypes.create_unicode_buffer(256)
        status = ctypes.create_unicode_buffer(64)

        abierto = False
        try:
            ret = mci(f'open "{ruta}" type mpegvideo alias {alias}', buf, 256, None)
            if ret != 0:
                return
            abierto = True
            ret = mci(f'play {alias}', buf, 256, None)
            if ret != 0:
                return

            time.sleep(0.15)

            inactivo = 0
            while inactivo < 3:
                mci(f'status {alias} mode', status, 64, None)
                if status.value == "playing":
                    inactivo = 0
                else:
                    inactivo += 1
                time.sleep(0.1)
        except Exception:
            pass
        finally:
            if abierto:
                try:
                    mci(f'close {alias}', buf, 256, None)
                except Exception:
                    pass

    def mostrar_mensaje(self, texto, duracion_ms=5000):
        if self._cerrando:
            return
        self.texto_burbuja.config(text=texto)
        self.burbuja.deiconify()
        self.actualizar_posicion_burbuja(self.root.winfo_x(), self.root.winfo_y())

        aid = getattr(self, "_after_id_burbuja", None)
        if aid is not None:
            try:
                self.root.after_cancel(aid)
            except Exception:
                pass
        self._after_id_burbuja = self.root.after(duracion_ms, self._ocultar_burbuja)

    def _ocultar_burbuja(self):
        self._after_id_burbuja = None
        try:
            self.burbuja.withdraw()
        except Exception:
            pass

    # ===============================================================
    # ARRANQUE
    # ===============================================================
    def _arrancar_con_show(self):
        if self._cerrando:
            return
        self.root.attributes("-alpha", 1.0)
        self._mostrar_saludo_pendiente = True

        # Greeting primero, con fallback a Greet y Show
        for entrada in ("Greeting", "Greet", "Show"):
            if entrada in self.datos_animaciones:
                self.arrancando = True
                self.animacion_actual = entrada
                self.indice_cuadro = 0
                self.reproducir_animacion()
                return

        self.arrancando = False
        self._mostrar_saludo_inicial()
        self._mostrar_idle_estatico()

    def _mostrar_saludo_inicial(self):
        if self.saliendo or self._cerrando:
            return
        frase = random.choice(self.frases_saludo)
        print(f"[saludo] {frase}")
        self.mostrar_mensaje(frase, 5000)

    def _precachear_idle(self):
        if self.saliendo or self._cerrando:
            return
        if self._frame_idle_estatico is not None:
            return

        idle = self._buscar_idle()
        if not idle:
            return

        frames = self.datos_animaciones[idle].get("frames", [])
        if not frames:
            return

        ci = None
        for f in frames:
            if "sprites" in f or ("x" in f and "y" in f):
                ci = f
                break
        if ci is None:
            return

        if "sprites" in ci:
            lista = ci["sprites"]
        else:
            lista = [(ci["x"], ci["y"])]

        base = Image.new("RGBA", (self.frame_width, self.frame_height), (0, 0, 0, 0))
        for sp in lista:
            x, y = sp[0], sp[1]
            w = sp[2] if len(sp) >= 4 else None
            h = sp[3] if len(sp) >= 4 else None
            celda = self._recortar_frame(x, y, w, h)
            base.alpha_composite(celda)

        self._frame_idle_estatico = ImageTk.PhotoImage(base)

    def _mostrar_idle_estatico(self):
        if self.saliendo or self._cerrando or self._moviendo:
            return
        self._precachear_idle()
        if self._frame_idle_estatico is None:
            return
        self.canvas.delete("all")
        self._imgs_tk = [self._frame_idle_estatico]
        self.canvas.create_image(0, 0, anchor="nw", image=self._frame_idle_estatico)
        self._after_id = None
        espera = random.randint(20000, 30000)
        self._after_id_idle = self.root.after(espera, self._decidir_siguiente_accion)

    def _decidir_siguiente_accion(self):
        if self.saliendo or self._cerrando or self._moviendo:
            return
        r = random.random()
        if r < 0.60:
            self._mostrar_idle_estatico()
        else:
            self._reproducir_animacion_al_azar_y_frase()

    # ===============================================================
    # RANDOM
    # ===============================================================
    def _animaciones_candidatas(self):
        excluidas = {
            "Hide", "HideQuick", "Ocultar", "GoodBye", "Goodbye",
            "Show", "Greet", "Greeting",
        }
        return [a for a in self.lista_animaciones if a not in excluidas]

    def _reproducir_animacion_al_azar_y_frase(self):
        if self.saliendo or self._cerrando:
            return

        self._detener_movimiento()

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

        if elegida in self.direcciones_move:
            self.reproducir_animacion()
            self._reproducir_move_con_desplazamiento(elegida)
        else:
            self.reproducir_animacion()

    # ===============================================================
    # REPRODUCCIÓN
    # ===============================================================
    def reproducir_animacion(self):
        if self._cerrando:
            return
        if self.animacion_actual not in self.datos_animaciones:
            if self.saliendo:
                self._finalizar_salida()
            return

        pasos = self.datos_animaciones[self.animacion_actual].get("frames", [])
        if not pasos:
            if self.saliendo:
                self._finalizar_salida()
            return

        if self.indice_cuadro < len(pasos):
            ci = pasos[self.indice_cuadro]
            tiene_imagen = ("sprites" in ci) or ("x" in ci and "y" in ci) or ("frame" in ci)

            if not tiene_imagen:
                if "sound" in ci:
                    self.reproducir_sonido(ci["sound"])
                dur = ci.get("duration", 0)
                if dur <= 0:
                    dur = 1

                if "branches" in ci and ci["branches"]:
                    salto = self._elegir_branch(ci["branches"])
                    if salto is not None and 0 <= salto < len(pasos):
                        if salto == self.indice_cuadro:
                            self.indice_cuadro += 1
                        else:
                            self.indice_cuadro = salto
                    else:
                        self.indice_cuadro += 1
                else:
                    self.indice_cuadro += 1

                self._after_id = self.root.after(dur, self.reproducir_animacion)
                return

            self.canvas.delete("all")
            self._imgs_tk = []

            if "sprites" in ci:
                lista = ci["sprites"]
            elif "x" in ci and "y" in ci:
                lista = [(ci["x"], ci["y"])]
            else:
                nc = ci.get("frame", 0)
                cols = self.spritesheet.width // self.frame_width
                lista = [((nc % cols) * self.frame_width,
                          (nc // cols) * self.frame_height)]

            for sp in lista:
                x, y = sp[0], sp[1]
                w = sp[2] if len(sp) >= 4 else None
                h = sp[3] if len(sp) >= 4 else None
                celda = self._recortar_frame(x, y, w, h)
                img_tk = ImageTk.PhotoImage(celda)
                self._imgs_tk.append(img_tk)
                self.canvas.create_image(0, 0, anchor="nw", image=img_tk)

            if "sound" in ci:
                self.reproducir_sonido(ci["sound"])

            dur = ci.get("duration", 100)
            if dur <= 0:
                dur = 100
            if dur > 5000:
                dur = 5000

            if "branches" in ci and ci["branches"]:
                salto = self._elegir_branch(ci["branches"])
                if salto is not None and 0 <= salto < len(pasos):
                    if salto == self.indice_cuadro:
                        self.indice_cuadro += 1
                    else:
                        self.indice_cuadro = salto
                else:
                    self.indice_cuadro += 1
            else:
                self.indice_cuadro += 1

            self._after_id = self.root.after(dur, self.reproducir_animacion)
        else:
            print(f"[anim] FIN de {self.animacion_actual} (saliendo={self.saliendo})")

            if self.saliendo and self.animacion_actual in ("GoodBye", "Goodbye", "Hide"):
                self._finalizar_salida()
                return

            self.indice_cuadro = 0

            if self.arrancando:
                self.arrancando = False
                idle = self._buscar_idle()
                if idle:
                    self.animacion_actual = idle
                if getattr(self, "_mostrar_saludo_pendiente", False):
                    self._mostrar_saludo_pendiente = False
                    self._mostrar_saludo_inicial()
                self._after_id = self.root.after(500, self._mostrar_idle_estatico)
                return

            idle = self._buscar_idle()
            if idle:
                self.animacion_actual = idle
            self._after_id = self.root.after(400, self._mostrar_idle_estatico)

    # ===============================================================
    # MOVIMIENTO
    # ===============================================================
    def _detener_movimiento(self):
        try:
            if self._after_id_movimiento:
                self.root.after_cancel(self._after_id_movimiento)
        except Exception:
            pass
        self._after_id_movimiento = None
        self._moviendo = False

    def _programar_movimiento_aleatorio(self):
        if self.saliendo or self._cerrando:
            return
        self._after_id_movimiento = self.root.after(
            60000, self._mover_a_posicion_aleatoria
        )

    def _mover_a_posicion_aleatoria(self):
        if self.saliendo or self._cerrando or self._moviendo:
            self._programar_movimiento_aleatorio()
            return

        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
        destino_x = random.randint(0, max(0, sw - self.frame_width))
        destino_y = random.randint(0, max(0, sh - self.frame_height))

        origen_x = self.root.winfo_x()
        origen_y = self.root.winfo_y()

        dx = destino_x - origen_x
        dy = destino_y - origen_y

        if abs(dx) >= abs(dy):
            nombre_anim = "MoveRight" if dx > 0 else "MoveLeft"
        else:
            nombre_anim = "MoveDown" if dy > 0 else "MoveUp"

        if nombre_anim not in self.datos_animaciones:
            for alt in ("MoveRight", "MoveLeft", "MoveUp", "MoveDown"):
                if alt in self.datos_animaciones:
                    nombre_anim = alt
                    break
            else:
                self._programar_movimiento_aleatorio()
                return

        print(f"[movimiento] {nombre_anim} → ({destino_x}, {destino_y})")

        for attr in ("_after_id", "_after_id_idle"):
            try:
                aid = getattr(self, attr)
                if aid:
                    self.root.after_cancel(aid)
            except Exception:
                pass
            setattr(self, attr, None)

        self._moviendo = True
        self.animacion_actual = nombre_anim
        self.indice_cuadro = 0

        self.reproducir_animacion()

        self.root.after(0, lambda: self._desplazar_ventana(
            origen_x, origen_y, destino_x, destino_y, pasos=40
        ))

    def _desplazar_ventana(self, x0, y0, x1, y1, pasos=40, paso_actual=0):
        if self.saliendo or self._cerrando:
            self._moviendo = False
            return
        if paso_actual > pasos:
            self._moviendo = False
            idle = self._buscar_idle()
            if idle:
                self.animacion_actual = idle
            self.indice_cuadro = 0
            self._mostrar_idle_estatico()
            self._programar_movimiento_aleatorio()
            return

        t = paso_actual / pasos
        x = int(x0 + (x1 - x0) * t)
        y = int(y0 + (y1 - y0) * t)

        self.root.geometry(f"+{x}+{y}")
        self.actualizar_posicion_burbuja(x, y)

        self.root.after(
            30,
            lambda: self._desplazar_ventana(
                x0, y0, x1, y1, pasos, paso_actual + 1
            )
        )

    def _reproducir_move_con_desplazamiento(self, nombre_anim):
        if nombre_anim not in self.direcciones_move:
            self.reproducir_animacion()
            return

        dx, dy = self.direcciones_move[nombre_anim]

        distancia = 300
        pasos = 30
        intervalo = 30

        x0 = self.root.winfo_x()
        y0 = self.root.winfo_y()

        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)

        x1 = x0 + dx * distancia
        y1 = y0 + dy * distancia

        x1 = max(0, min(x1, sw - self.frame_width))
        y1 = max(0, min(y1, sh - self.frame_height))

        self._moviendo = True

        def paso(i):
            if self.saliendo or self._cerrando:
                self._moviendo = False
                return
            if i > pasos:
                self._moviendo = False
                idle = self._buscar_idle()
                if idle:
                    self.animacion_actual = idle
                self.indice_cuadro = 0
                self._mostrar_idle_estatico()
                if not self.saliendo and self._after_id_movimiento is None:
                    self._programar_movimiento_aleatorio()
                return

            t = i / pasos
            x = int(x0 + (x1 - x0) * t)
            y = int(y0 + (y1 - y0) * t)

            self.root.geometry(f"+{x}+{y}")
            self.actualizar_posicion_burbuja(x, y)

            self.root.after(intervalo, lambda: paso(i + 1))

        self.root.after(0, lambda: paso(0))

    # ===============================================================
    # FINALIZAR SALIDA
    # ===============================================================
    def _finalizar_salida(self):
        if self._cerrando:
            return
        self._cerrando = True
        print("[salir] Cerrando...")

        for attr in ("_after_id", "_after_id_idle", "_after_id_movimiento",
                     "_after_id_burbuja"):
            try:
                aid = getattr(self, attr)
                if aid:
                    self.root.after_cancel(aid)
            except Exception:
                pass
            setattr(self, attr, None)

        # Vaciar cola de audio
        try:
            while True:
                self._cola_audio.get_nowait()
        except queue.Empty:
            pass
        try:
            self._cola_audio.put(None)
        except Exception:
            pass

        try:
            time.sleep(0.3)
        except Exception:
            pass

        try:
            buf = ctypes.create_unicode_buffer(256)
            mci('close all', buf, 256, None)
            print("[salir] MCI cerrado")
        except Exception:
            pass

        self._matar_ventanas_fantasma()

        try:
            self.burbuja.destroy()
        except Exception:
            pass
        try:
            self.root.quit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

        print("[salir] Adiós!")
        import sys
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass
        os._exit(0)

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

    # ===============================================================
    # MENÚ
    # ===============================================================
    def mostrar_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def abrir_acerca_de(self):
        if self.saliendo or self._cerrando:
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
                "Links, el gato curioso de Office. "
                "Cazando ratones y atajos de teclado desde Office 97.",
                0
            )
        except Exception as e:
            print(f"[ShellAbout] {e}")

    def reproducir_animacion_random(self):
        self._reproducir_animacion_al_azar_y_frase()

    def ejecutar_salir(self):
        if self._cerrando:
            return
        self.burbuja.withdraw()
        if self._hwnd_biblioteca:
            try:
                user32.PostMessageW(self._hwnd_biblioteca, WM_CLOSE, 0, 0)
            except Exception:
                pass

        for attr in ("_after_id", "_after_id_idle", "_after_id_movimiento"):
            try:
                aid = getattr(self, attr)
                if aid:
                    self.root.after_cancel(aid)
            except Exception:
                pass
            setattr(self, attr, None)

        if "GoodBye" in self.datos_animaciones:
            self.saliendo = True
            self.saliendo_pendiente = False
            self.indice_cuadro = 0
            self.animacion_actual = "GoodBye"
            print("[salir] Reproduciendo animación GoodBye...")
            self.reproducir_animacion()
        elif "Goodbye" in self.datos_animaciones:
            self.saliendo = True
            self.saliendo_pendiente = False
            self.indice_cuadro = 0
            self.animacion_actual = "Goodbye"
            print("[salir] Reproduciendo animación Goodbye...")
            self.reproducir_animacion()
        elif "Hide" in self.datos_animaciones:
            self.saliendo = True
            self.saliendo_pendiente = False
            self.indice_cuadro = 0
            self.animacion_actual = "Hide"
            print("[salir] Reproduciendo animación Hide...")
            self.reproducir_animacion()
        else:
            print("[salir] No hay GoodBye/Goodbye/Hide, cerrando directo")
            self._finalizar_salida()

    def reproducir_animacion_especifica(self, nombre):
        if self.saliendo or self._cerrando or nombre not in self.datos_animaciones:
            return

        self._detener_movimiento()

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

        if nombre in self.direcciones_move:
            self.reproducir_animacion()
            self._reproducir_move_con_desplazamiento(nombre)
        else:
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

        nombre_clase = f"LinksBibliotecaCls_{id(self)}_{random.randint(100000, 999999)}"

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
            "Biblioteca de animaciones — Links",
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
        if self._moviendo:
            return
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
        app = LinksAgente(root)
    except Exception as e:
        print(f"ERROR al iniciar: {e}")
        import traceback
        traceback.print_exc()
        root.destroy()
        raise SystemExit(1)

    root.mainloop()