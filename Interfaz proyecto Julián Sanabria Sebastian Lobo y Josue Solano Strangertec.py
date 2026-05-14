import pygame                                           # Biblioteca para la interfaz gráfica y manejo de eventos
import random                                           # Para seleccionar frases aleatorias de la lista
import time                                             # Para manejo de tiempos
from difflib import SequenceMatcher                     # Para calcular similitud entre strings y asignar puntaje
import socket                                           # Para la conexión TCP con la Raspberry Pi Pico W


# CONEXIÓN A LA PICO


SERVER_IP = "172.20.10.8"                              # Dirección IP de la Pico W en la red WiFi
PORT      = 1717                                        # Puerto TCP donde escucha el servidor de la Pico

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Crea socket TCP IPv4
    client_socket.connect((SERVER_IP, PORT))            # Intenta conectarse al servidor de la Pico
    print("Conectado a Pico W")
    PICO_CONECTADA = True                               # Bandera: indica que la Pico está conectada
except Exception as e:
    print("ERROR: No se pudo conectar a la Pico W:", e)
    print("Iniciando en modo simulado...")
    client_socket  = None                               # Sin socket si no hay conexión
    PICO_CONECTADA = False                              # Bandera: indica modo simulado


# MORSE


morse_inverso = {v: k for k, v in {                    # Construye el diccionario inverso automáticamente
    "A": ".-",    "B": "-...",  "C": "-.-.",            # Código Morse letras A, B, C
    "D": "-..",   "E": ".",     "F": "..-.",            # Código Morse letras D, E, F
    "G": "--.",   "H": "....",  "I": "..",              # Código Morse letras G, H, I
    "J": ".---",  "K": "-.-",   "L": ".-..",            # Código Morse letras J, K, L
    "M": "--",    "N": "-.",    "O": "---",             # Código Morse letras M, N, O
    "P": ".--.",  "Q": "--.-",  "R": ".-.",             # Código Morse letras P, Q, R
    "S": "...",   "T": "-",     "U": "..-",             # Código Morse letras S, T, U
    "V": "...-",  "W": ".--",   "X": "-..-",            # Código Morse letras V, W, X
    "Y": "-.--",  "Z": "--..",                          # Código Morse letras Y, Z
    "0": "-----", "1": ".----", "2": "..---",           # Código Morse números 0, 1, 2
    "3": "...--", "4": "....-", "5": ".....",           # Código Morse números 3, 4, 5
    "6": "-....", "7": "--...", "8": "---..",            # Código Morse números 6, 7, 8
    "9": "----.",                                        # Código Morse número 9
    "-": "-....-", "+": ".-.-.", ".": ".-.-.-"          # Código Morse símbolos -, +, .
}.items()}                                              # .items() da pares (letra, código) que se invierten

UMBRAL_RAYA   = 400                                     # Presión mayor a 400ms = raya, menor = punto
PAUSA_LETRA   = 600                                     # 600ms de silencio = fin de letra
PAUSA_PALABRA = 1400                                    # 1400ms de silencio = espacio entre palabras
FIN_MENSAJE   = 4200                                    # 4200ms de silencio = fin del mensaje completo


# COMUNICACIÓN CON PICO


def enviar_pico(mensaje):                               # Envía un mensaje a la Pico y espera respuesta
    if not PICO_CONECTADA or client_socket is None:     # Si no hay conexión devuelve texto simulado
        return "Simulado"
    try:
        client_socket.send(mensaje.encode())            # Envía el mensaje como bytes
        return client_socket.recv(1024).decode()        # Recibe y decodifica la respuesta
    except Exception as e:
        print("Error comunicando con Pico:", e)
        return ""


# PYGAME


pygame.init()                                           # Inicializa todos los módulos de Pygame

BLANCO   = (255, 255, 255)                             # Color blanco RGB
NEGRO    = (0,   0,   0)                               # Color negro RGB
ROJO     = (255, 60,  60)                              # Color rojo RGB para errores y modo simulado
AMARILLO = (255, 220, 0)                               # Color amarillo RGB para Jugador A
AZUL     = (80,  140, 255)                             # Color azul RGB para Jugador B
GRIS     = (170, 170, 170)                             # Color gris RGB para bordes y textos secundarios
VERDE    = (80,  200, 80)                              # Color verde RGB para puntaje perfecto y conexión OK
GRIS_OSC = (50,  50,  50)                              # Color gris oscuro RGB para fondos de barras

info     = pygame.display.Info()                        # Obtiene información de la pantalla del sistema
ANCHO    = info.current_w                               # Ancho real de la pantalla en píxeles
ALTO     = info.current_h                               # Alto real de la pantalla en píxeles

pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.FULLSCREEN) # Crea ventana en pantalla completa
CENTRO_X = ANCHO // 2                                  # Coordenada X del centro de la pantalla
CENTRO_Y = ALTO  // 2                                  # Coordenada Y del centro de la pantalla

def cx(x): return int(x * ANCHO / 1000)                # Escala coordenada X de base 1000 a pantalla real
def cy(y): return int(y * ALTO  / 650)                 # Escala coordenada Y de base 650 a pantalla real

pygame.display.set_caption("StrangerTEC Morse Translator") # Título de la ventana

fuente_titulo  = pygame.font.SysFont("Arial", cy(36), bold=True) # Fuente grande para títulos
fuente_grande  = pygame.font.SysFont("Arial", cy(30))            # Fuente para texto importante
fuente_mediana = pygame.font.SysFont("Arial", cy(22))            # Fuente para opciones de menú
fuente_pequena = pygame.font.SysFont("Arial", cy(16))            # Fuente para instrucciones y detalles
fuente_mono    = pygame.font.SysFont("Courier", cy(28), bold=True) # Fuente monoespaciada para símbolos Morse


# FRASES


frases = [                                              # Lista de frases disponibles para el juego
    "SOS", "SI", "NO", "SANABRIA", "JOSUDA",
    "LOBO", "MCPOLLO", "TILIN", "POTAXIO", "CE1104"
]

TOTAL_RONDAS = 3                                        # Cantidad de rondas por partida en Modo 1
velocidades  = [1.0, 0.7, 0.4]                         # Velocidades por ronda: normal, rápido, muy rápido

ranking = []                                            # Lista que guarda los mejores puntajes de la sesión


# FUNCIONES GRÁFICAS


def dibujar_texto(texto, fuente, color, x, y):         # Dibuja texto en una posición específica
    sup = fuente.render(str(texto), True, color)        # Renderiza el texto con antialiasing
    pantalla.blit(sup, (cx(x), cy(y)))                 # Lo dibuja en las coordenadas escaladas

def dibujar_texto_centrado(texto, fuente, color, y):   # Dibuja texto centrado horizontalmente
    sup  = fuente.render(str(texto), True, color)       # Renderiza el texto
    rect = sup.get_rect(center=(CENTRO_X, cy(y)))      # Calcula rectángulo centrado en X
    pantalla.blit(sup, rect)                            # Lo dibuja centrado

def dibujar_caja(x, y, ancho, alto, color):            # Dibuja un rectángulo con bordes redondeados
    pygame.draw.rect(
        pantalla, GRIS,                                 # Color gris para el borde
        (cx(x), cy(y), cx(ancho), cy(alto)),           # Posición y tamaño escalados
        4, border_radius=10                             # Grosor 4px y esquinas redondeadas
    )

def dibujar_boton_visual(presionado, x, y, radio=40):  # Dibuja el botón animado en pantalla
    color_ext = AMARILLO if presionado else GRIS        # Amarillo si presionado, gris si no
    color_int = AMARILLO if presionado else GRIS_OSC    # Interior amarillo si presionado
    pygame.draw.circle(pantalla, color_ext, (cx(x), cy(y)), radio + 6) # Círculo exterior
    pygame.draw.circle(pantalla, color_int, (cx(x), cy(y)), radio)     # Círculo interior
    label = fuente_pequena.render("BOTÓN", True, NEGRO if presionado else BLANCO) # Etiqueta
    rect  = label.get_rect(center=(cx(x), cy(y)))      # Centra la etiqueta en el círculo
    pantalla.blit(label, rect)                          # Dibuja la etiqueta


# PUNTAJE


def calcular_puntaje(original, respuesta):             # Calcula puntaje comparando frase original con respuesta
    original  = original.strip().upper()               # Normaliza la frase original
    respuesta = respuesta.strip().upper()              # Normaliza la respuesta del jugador
    if not respuesta:                                   # Si no hay respuesta el puntaje es 0
        return 0
    return int(SequenceMatcher(None, original, respuesta).ratio() * 100) # Similitud 0-100

def color_puntaje(p):                                  # Devuelve el color según el puntaje
    if p == 100:  return VERDE                         # Verde para puntaje perfecto
    elif p >= 60: return AMARILLO                      # Amarillo para puntaje aceptable
    else:         return ROJO                          # Rojo para puntaje bajo


# MENÚ PRINCIPAL


def menu_principal():                                  # Muestra el menú de selección de modo de juego
    reloj = pygame.time.Clock()                        # Reloj para controlar FPS
    while True:
        pantalla.fill(NEGRO)                           # Fondo negro
        dibujar_texto_centrado("STRANGERTEC MORSE TRANSLATOR", fuente_titulo, BLANCO, 110) # Título

        estado = "CONECTADO A PICO W" if PICO_CONECTADA else "MODO SIMULADO — Sin Raspberry Pi"
        color_estado = VERDE if PICO_CONECTADA else ROJO  # Verde si conectado, rojo si simulado
        dibujar_texto_centrado(f"[ {estado} ]", fuente_pequena, color_estado, 160) # Estado de conexión

        dibujar_caja(220, 240, 560, 90, AMARILLO)      # Caja del botón Modo 1
        dibujar_texto_centrado("1 - TRANSMISION SIMPLE",    fuente_mediana, AMARILLO, 265) # Texto Modo 1

        dibujar_caja(220, 370, 560, 90, AZUL)          # Caja del botón Modo 2
        dibujar_texto_centrado("2 - ESCUCHA Y TRANSMISION", fuente_mediana, AZUL,     395) # Texto Modo 2

        dibujar_texto_centrado("ESC → SALIR", fuente_pequena, GRIS, 560) # Instrucción salir
        pygame.display.flip()                          # Actualiza la pantalla

        for evento in pygame.event.get():              # Revisa eventos del teclado y ventana
            if evento.type == pygame.QUIT:        return None  # Cierre de ventana
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_1:      return 1     # Tecla 1 → Modo 1
                if evento.key == pygame.K_2:      return 2     # Tecla 2 → Modo 2
                if evento.key == pygame.K_ESCAPE: return None  # ESC → salir
        reloj.tick(60)                                 # Limita a 60 FPS

# TURNO TECLADO (Jugador A)

def turno_texto(frase_objetivo, nombre, color):        # Pantalla donde el jugador escribe su respuesta
    reloj = pygame.time.Clock()
    texto_usuario = ""                                 # Acumula las letras que escribe el jugador

    while True:
        pantalla.fill(NEGRO)
        dibujar_caja(0, 0, ANCHO, 70, color)          # Barra superior con color del jugador
        dibujar_texto_centrado(f"TURNO DEL {nombre}", fuente_titulo, color, 32) # Nombre del jugador
        dibujar_texto(
            "Escucha/observa el mensaje Morse y escribí la frase:",
            fuente_pequena, BLANCO, 60, 120            # Instrucción principal
        )
        dibujar_caja(80, 175, 840, 100, color)        # Caja donde se muestra el texto escrito
        dibujar_texto(texto_usuario, fuente_grande, BLANCO, 100, 200) # Texto del jugador
        dibujar_texto("ENTER → Confirmar",  fuente_pequena, GRIS, 60, 340) # Instrucción confirmar
        dibujar_texto("BACKSPACE → Borrar", fuente_pequena, GRIS, 60, 375) # Instrucción borrar
        pygame.display.flip()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: return None
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:      # ENTER confirma la respuesta
                    return texto_usuario
                elif evento.key == pygame.K_BACKSPACE: # BACKSPACE borra el último carácter
                    texto_usuario = texto_usuario[:-1]
                else:
                    if len(texto_usuario) < 25:        # Límite de 25 caracteres
                        texto_usuario += evento.unicode.upper() # Agrega letra en mayúscula
        reloj.tick(60)


# TURNO BOTÓN


def turno_boton(frase_objetivo, nombre, color):        # Turno del Jugador B: ESPACIO o botón físico
    reloj    = pygame.time.Clock()
    clock_ms = pygame.time.get_ticks                   # Función para obtener tiempo en ms

    codigo_actual = ""                                 # Puntos y rayas de la letra en curso
    frase_result  = ""                                 # Frase decodificada acumulada
    historial     = []                                 # Lista de letras y espacios ingresados

    presionado     = False                             # True cuando ESPACIO está siendo presionado
    inicio_presion = 0                                 # Momento en que se empezó a presionar
    ultimo_evento  = clock_ms()                        # Tiempo del último pulso detectado
    letra_cerrada  = False                             # True cuando ya se procesó la letra actual
    confirmado     = False                             # True cuando el mensaje está completo
    frase_final    = None                              # Almacena la frase final para retornar

    if PICO_CONECTADA:                                 # Si la Pico está conectada
        try:
            client_socket.send("BOTON".encode())       # Envía comando BOTON a la Pico
            client_socket.recv(1024).decode()          # Espera confirmación de la Pico
        except:
            pass

    while not confirmado:
        ahora    = clock_ms()                          # Tiempo actual
        silencio = ahora - ultimo_evento               # Tiempo desde el último evento

        if (                                           # Si hay código acumulado y pasó tiempo suficiente
            not presionado
            and not letra_cerrada
            and len(codigo_actual) > 0
            and silencio >= PAUSA_LETRA                # 600ms de silencio = fin de letra
        ):
            letra = morse_inverso.get(codigo_actual, "?") # Decodifica el código a letra
            frase_result += letra                      # Agrega la letra a la frase
            historial.append(("LETRA", letra, codigo_actual)) # Guarda en historial
            print(f"LETRA: {letra} ({codigo_actual})")
            codigo_actual = ""                         # Limpia el código para la siguiente letra
            letra_cerrada = True                       # Marca la letra como procesada

        if (                                           # Si pasó tiempo suficiente para espacio
            not presionado
            and letra_cerrada
            and silencio >= PAUSA_PALABRA              # 1400ms de silencio = espacio entre palabras
            and not frase_result.endswith(" ")
        ):
            frase_result += " "                        # Agrega espacio a la frase
            historial.append(("ESPACIO", " ", ""))
            print("ESPACIO")
            ultimo_evento = ahora                      # Reinicia el contador

        if (                                           # Si pasó tiempo suficiente para fin de mensaje
            not presionado
            and silencio >= FIN_MENSAJE                # 4200ms de silencio = fin del mensaje
            and len(frase_result.strip()) > 0
        ):
            frase_final = frase_result.strip()         # Guarda la frase final
            confirmado  = True                         # Sale del bucle principal

        if PICO_CONECTADA and frase_final is None:     # Si la Pico está conectada, revisar si mandó algo
            try:
                client_socket.settimeout(0.01)         # Timeout de 10ms para no bloquear el dibujo
                datos = client_socket.recv(1024)       # Intenta recibir datos de la Pico
                if datos:
                    frase_final = datos.decode().strip() # Decodifica la frase recibida
                    confirmado  = True
                    print("Frase recibida de Pico:", frase_final)
            except:
                pass                                   # Si no llegó nada en 10ms continúa normalmente
            finally:
                client_socket.settimeout(None)         # Restaura el socket a modo normal

        pantalla.fill(NEGRO)                           # Limpia la pantalla

        dibujar_caja(0, 0, ANCHO, 70, color)          # Barra superior con color del jugador
        dibujar_texto_centrado(
            f"{nombre} — BOTÓN FÍSICO / ESPACIO",
            fuente_titulo, color, 32                   # Título del turno
        )

        dibujar_texto("ESPACIO o botón físico = ingresar Morse", fuente_pequena, GRIS,    60,  90) # Instrucción
        dibujar_texto("Corto (<0.4s) = punto  ·",               fuente_pequena, BLANCO,  60, 113) # Punto
        dibujar_texto("Largo (≥0.4s) = raya   —",               fuente_pequena, BLANCO,  60, 136) # Raya
        dibujar_texto("Silencio 0.6s = fin de letra",           fuente_pequena, AMARILLO, 60, 159) # Fin letra
        dibujar_texto("Silencio 1.4s = espacio entre palabras", fuente_pequena, AMARILLO, 60, 182) # Espacio
        dibujar_texto("Silencio 4.2s = confirma automáticamente",fuente_pequena, VERDE,   60, 205) # Fin mensaje
        dibujar_texto("ENTER = confirmar ya  |  ESC = cancelar", fuente_pequena, GRIS,    60, 228) # Controles

        dibujar_boton_visual(presionado, 870, 160, radio=50)    # Dibuja el botón visual animado

        dibujar_texto("Letra actual:", fuente_pequena, GRIS, 60, 268) # Etiqueta de letra actual
        simbolos_vis = "  ".join("·" if c == "." else "—" for c in codigo_actual) # Convierte a símbolos
        dibujar_texto(
            simbolos_vis if simbolos_vis else "—",
            fuente_mono, AMARILLO, 200, 263            # Muestra puntos y rayas de la letra actual
        )

        dibujar_caja(60, 308, 880, 80, color)          # Caja de la frase decodificada
        dibujar_texto_centrado(
            frase_result if frase_result else "...",
            fuente_grande, BLANCO, 348                 # Muestra la frase decodificada en tiempo real
        )

        if not presionado and len(codigo_actual) > 0 and not letra_cerrada: # Barra de fin de letra
            progreso = min(silencio / PAUSA_LETRA, 1.0) # Progreso de 0 a 1
            pygame.draw.rect(pantalla, GRIS_OSC,
                (cx(60), cy(413), cx(880), cy(18)), border_radius=5) # Fondo de la barra
            pygame.draw.rect(pantalla, AMARILLO,
                (cx(60), cy(413), int(cx(880) * progreso), cy(18)), border_radius=5) # Barra de progreso
            dibujar_texto("← fin de letra", fuente_pequena, AMARILLO, 60, 433)

        if letra_cerrada and not presionado:            # Barra de fin de mensaje
            progreso2 = min(silencio / FIN_MENSAJE, 1.0) # Progreso de 0 a 1
            pygame.draw.rect(pantalla, GRIS_OSC,
                (cx(60), cy(413), cx(880), cy(18)), border_radius=5) # Fondo de la barra
            pygame.draw.rect(pantalla, VERDE,
                (cx(60), cy(413), int(cx(880) * progreso2), cy(18)), border_radius=5) # Barra verde
            dibujar_texto("← fin de mensaje", fuente_pequena, VERDE, 60, 433)

        dibujar_texto("Historial:", fuente_pequena, GRIS, 60, 463) # Etiqueta del historial
        hist_txt = "  ".join(                          # Construye el texto del historial
            f"{h[1]}({h[2]})" if h[0] == "LETRA" else "[SPC]"
            for h in historial[-12:]                   # Muestra las últimas 12 entradas
        )
        dibujar_texto(hist_txt, fuente_pequena, GRIS, 60, 486) # Dibuja el historial

        if PICO_CONECTADA:                             # Si la Pico está conectada muestra confirmación
            dibujar_texto(
                "✓ Pico conectada — botón físico también activo",
                fuente_pequena, VERDE, 60, 515
            )

        pygame.display.flip()                          # Actualiza la pantalla

        for evento in pygame.event.get():              # Revisa eventos del teclado
            if evento.type == pygame.QUIT:
                return ""

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE and not presionado: # ESPACIO presionado
                    presionado     = True              # Marca que el botón está siendo presionado
                    inicio_presion = clock_ms()        # Registra cuándo empezó la presión
                    letra_cerrada  = False             # Resetea la bandera de letra cerrada

                if evento.key == pygame.K_RETURN:      # ENTER confirma inmediatamente
                    if len(codigo_actual) > 0:         # Si hay código pendiente lo procesa
                        letra = morse_inverso.get(codigo_actual, "?")
                        frase_result += letra
                    frase_final = frase_result.strip() # Guarda la frase final
                    confirmado  = True

                if evento.key == pygame.K_ESCAPE:      # ESC cancela el turno
                    return ""

            if evento.type == pygame.KEYUP:
                if evento.key == pygame.K_SPACE and presionado: # ESPACIO soltado
                    duracion   = clock_ms() - inicio_presion    # Calcula duración de la presión
                    presionado = False                           # Marca que ya no está presionado

                    if duracion >= UMBRAL_RAYA:        # Si duró más de 400ms → raya
                        codigo_actual += "-"
                        print("RAYA")
                    else:                              # Si duró menos de 400ms → punto
                        codigo_actual += "."
                        print("PUNTO")

                    ultimo_evento = clock_ms()         # Actualiza el tiempo del último evento
                    letra_cerrada = False              # Resetea para seguir acumulando símbolos

        reloj.tick(60)                                 # Limita a 60 FPS

    pantalla.fill(NEGRO)                               # Pantalla de confirmación breve
    dibujar_texto_centrado("✓ MENSAJE REGISTRADO", fuente_titulo, VERDE, 300) # Confirmación
    dibujar_texto_centrado(frase_final if frase_final else "", fuente_grande, BLANCO, 380) # Frase final
    pygame.display.flip()
    pygame.time.wait(1500)                             # Espera 1.5 segundos antes de continuar

    return frase_final if frase_final else ""          # Retorna la frase decodificada


# TRANSICIÓN

def pantalla_transicion(nombre, color):                # Pantalla de cambio de turno entre jugadores
    reloj = pygame.time.Clock()
    while True:
        pantalla.fill(NEGRO)
        dibujar_texto_centrado("CAMBIO DE TURNO",   fuente_titulo,  BLANCO, 180) # Título
        dibujar_texto_centrado(nombre,              fuente_grande,  color,  290) # Nombre del siguiente jugador
        dibujar_texto_centrado("ENTER → CONTINUAR", fuente_mediana, BLANCO, 420) # Instrucción
        pygame.display.flip()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:    return False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN: return True # ENTER continúa
        reloj.tick(60)


# RESULTADOS


def pantalla_resultados(                               # Muestra resultados de la ronda o puntaje final
    frase_objetivo,
    respuesta_a, respuesta_b,
    puntaje_a,   puntaje_b,
    posicion_a,  posicion_b
):
    reloj = pygame.time.Clock()
    pantalla_final = (frase_objetivo == "PUNTAJE FINAL") # True si es la pantalla de puntaje acumulado

    if   puntaje_a > puntaje_b: ganador, color_ganador = "GANA JUGADOR A", AMARILLO # A gana
    elif puntaje_b > puntaje_a: ganador, color_ganador = "GANA JUGADOR B", AZUL     # B gana
    else:                        ganador, color_ganador = "EMPATE",          BLANCO  # Empate

    while True:
        pantalla.fill(NEGRO)
        dibujar_texto_centrado("RESULTADOS DE LA RONDA", fuente_titulo, BLANCO, 35) # Título

        if not pantalla_final:                         # Solo muestra frase original si no es pantalla final
            dibujar_texto("Frase original:", fuente_pequena, GRIS, 70, 90)

        dibujar_caja(60, 120, 880, 70, BLANCO)        # Caja de la frase original
        dibujar_texto_centrado(frase_objetivo, fuente_grande, BLANCO, 155) # Frase de la ronda

        dibujar_caja(50, 220, 420, 210, AMARILLO)     # Caja del Jugador A
        dibujar_texto("JUGADOR A",                 fuente_titulo,  AMARILLO,                 70, 240) # Nombre A
        dibujar_texto(f"Respuesta: {respuesta_a}", fuente_pequena, BLANCO,                   70, 320) # Respuesta A
        dibujar_texto(f"Puntaje: {puntaje_a} pts", fuente_mediana, color_puntaje(puntaje_a), 70, 370) # Puntaje A
        if posicion_a:                                 # Si está en el Top 10 muestra la posición
            dibujar_texto(f"TOP 10 → Puesto #{posicion_a}", fuente_pequena, BLANCO, 70, 415)

        dibujar_caja(530, 220, 420, 210, AZUL)        # Caja del Jugador B
        dibujar_texto("JUGADOR B",                 fuente_titulo,  AZUL,                    550, 240) # Nombre B
        dibujar_texto(f"Respuesta: {respuesta_b}", fuente_pequena, BLANCO,                  550, 320) # Respuesta B
        dibujar_texto(f"Puntaje: {puntaje_b} pts", fuente_mediana, color_puntaje(puntaje_b),550, 370) # Puntaje B
        if posicion_b:                                 # Si está en el Top 10 muestra la posición
            dibujar_texto(f"TOP 10 → Puesto #{posicion_b}", fuente_pequena, BLANCO, 550, 415)

        dibujar_caja(120, 500, 760, 70, color_ganador) # Caja del ganador
        dibujar_texto_centrado(ganador, fuente_titulo, color_ganador, 540) # Nombre del ganador
        dibujar_texto_centrado("ENTER → CONTINUAR    ESC → SALIR", fuente_pequena, GRIS, 620) # Controles

        pygame.display.flip()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:    return False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN: return True  # ENTER continúa
                if evento.key == pygame.K_ESCAPE: return False # ESC vuelve al menú
        reloj.tick(60)


# JUEGO


def jugar(modo):                                       # Función principal del juego según el modo elegido

    if modo == 1:                                      # MODO 1 — TRANSMISIÓN SIMPLE

        puntaje_total_a = 0                            # Acumulador de puntaje total del Jugador A
        puntaje_total_b = 0                            # Acumulador de puntaje total del Jugador B

        for ronda in range(TOTAL_RONDAS):              # Repite por la cantidad de rondas (3)

            frase_objetivo   = random.choice(frases)   # Selecciona frase aleatoria de la lista
            velocidad_actual = velocidades[ronda]      # Velocidad de esta ronda (aumenta cada ronda)
            print(f"Ronda {ronda+1} | Frase: {frase_objetivo} | Vel: {velocidad_actual}")

            enviar_pico(f"MATRIZ:{frase_objetivo}")    # Envía frase a la Pico para mostrar en LEDs

            traduccion_a = turno_texto(frase_objetivo, "JUGADOR A", AMARILLO) # Turno Jugador A
            if traduccion_a is None: return            # Si cierra la ventana termina el juego

            continuar = pantalla_transicion("JUGADOR B", AZUL) # Pantalla de cambio de turno
            if not continuar: return

            traduccion_b = turno_texto(frase_objetivo, "JUGADOR B", AZUL) # Turno Jugador B
            if traduccion_b is None: return

            puntaje_a = calcular_puntaje(frase_objetivo, traduccion_a) # Puntaje Jugador A
            puntaje_b = calcular_puntaje(frase_objetivo, traduccion_b) # Puntaje Jugador B
            puntaje_total_a += puntaje_a               # Suma al acumulado de A
            puntaje_total_b += puntaje_b               # Suma al acumulado de B

            continuar = pantalla_resultados(           # Muestra resultados de la ronda
                frase_objetivo,
                traduccion_a, traduccion_b,
                puntaje_a,    puntaje_b,
                None, None
            )
            if not continuar: return

        ranking.append(("A", puntaje_total_a))         # Agrega puntaje final de A al ranking
        ranking.append(("B", puntaje_total_b))         # Agrega puntaje final de B al ranking
        ranking.sort(key=lambda x: x[1], reverse=True) # Ordena de mayor a menor
        if len(ranking) > 10:
            del ranking[10:]                           # Mantiene solo los 10 mejores

        scores     = [r[1] for r in ranking]           # Lista solo de valores numéricos
        posicion_a = (scores.index(puntaje_total_a) + 1) if puntaje_total_a in scores else None
        posicion_b = (scores.index(puntaje_total_b) + 1) if puntaje_total_b in scores else None
        if posicion_a and posicion_a > 10: posicion_a = None # Fuera del top 10
        if posicion_b and posicion_b > 10: posicion_b = None

        pantalla_resultados(                           # Muestra pantalla de puntaje final acumulado
            "PUNTAJE FINAL",
            str(puntaje_total_a), str(puntaje_total_b),
            puntaje_total_a,      puntaje_total_b,
            posicion_a,           posicion_b
        )

    elif modo == 2:                                    # MODO 2 — ESCUCHA Y TRANSMISIÓN

        while True:                                    # Bucle infinito: nueva frase en cada ronda

            frase_objetivo = random.choice(frases)     # Selecciona frase aleatoria

            enviar_pico(frase_objetivo)                # Envía frase a la Pico para reproducir en Morse

            traduccion_a = turno_texto(frase_objetivo, "JUGADOR A", AMARILLO) # Jugador A escucha y escribe
            if traduccion_a is None: return

            continuar = pantalla_transicion("JUGADOR B — BOTÓN FÍSICO / ESPACIO", AZUL) # Cambio de turno
            if not continuar: return

            traduccion_b = turno_boton(frase_objetivo, "JUGADOR B", AZUL) # Jugador B ingresa con botón/ESPACIO
            if traduccion_b is None: return

            puntaje_a = calcular_puntaje(frase_objetivo, traduccion_a) # Puntaje Jugador A
            puntaje_b = calcular_puntaje(frase_objetivo, traduccion_b) # Puntaje Jugador B

            continuar = pantalla_resultados(           # Muestra resultados de la ronda
                frase_objetivo,
                traduccion_a, traduccion_b,
                puntaje_a,    puntaje_b,
                None, None
            )
            if not continuar: return                   # ESC vuelve al menú principal


# MAIN


if __name__ == "__main__":                             # Punto de entrada del programa
    while True:
        modo = menu_principal()                        # Muestra el menú y espera selección
        if modo is None:                               # Si elige salir o cierra la ventana
            break                                      # Sale del bucle principal
        jugar(modo)                                    # Ejecuta el juego con el modo seleccionado

pygame.quit()                                          # Cierra Pygame limpiamente al terminar
