import network                                          # Biblioteca para manejar la conexión WiFi de la Pico W
import socket                                           # Biblioteca para crear el servidor TCP y comunicarse con la PC
import time                                             # Biblioteca para manejar delays y medir tiempos
from machine import Pin, PWM                            # Pin para controlar GPIOs, PWM para el buzzer


# WIFI


SSID = "aifondetupadre"                                 # Nombre de la red WiFi a la que se conecta la Pico
PASSWORD = "papoi6767"                                  # Contraseña de la red WiFi


# REGISTROS


DATA  = Pin(27, Pin.OUT)                                # GPIO27 → pin de datos del registro de corrimiento U1
CLOCK = Pin(26, Pin.OUT)                                # GPIO26 → pin de reloj de ambos registros U1 y U2


# BOTON


boton = Pin(                                            # Define el botón físico S1 de la maqueta
    16,                                                 # Conectado al GPIO16 de la Pico W
    Pin.IN,                                             # Configurado como entrada digital
    Pin.PULL_DOWN                                       # Pull-down interno: lee 0 cuando no se presiona
)


# SWITCH


modoSwitch = Pin(                                       # Define el switch de modo S2
    17,                                                 # Conectado al GPIO17 de la Pico W
    Pin.IN,                                             # Configurado como entrada digital
    Pin.PULL_DOWN                                       # OFF=0 (modo LEDs), ON=1 (modo buzzer)
)


# BUZZER


buzzer = PWM(Pin(5))                                    # Crea señal PWM en GPIO5 para controlar el buzzer pasivo
buzzer.freq(200)                                        # Frecuencia de 200Hz para el tono del buzzer


# LEDS DE FILA (14, 15, 16)


led14 = Pin(15, Pin.OUT)                                # GPIO15 → controla LED14 (indicador fila 1: letras A-Y)
led15 = Pin(14, Pin.OUT)                                # GPIO14 → controla LED15 (indicador fila 2: letras B-Z)
led16 = Pin(13, Pin.OUT)                                # GPIO13 → controla LED16 (indicador fila 3: números y símbolos)


# MORSE


morse = {
    "A": ".-",    "B": "-...",  "C": "-.-.",            # Código Morse de las letras A, B, C
    "D": "-..",   "E": ".",     "F": "..-.",            # Código Morse de las letras D, E, F
    "G": "--.",   "H": "....",  "I": "..",              # Código Morse de las letras G, H, I
    "J": ".---",  "K": "-.-",   "L": ".-..",            # Código Morse de las letras J, K, L
    "M": "--",    "N": "-.",    "O": "---",             # Código Morse de las letras M, N, O
    "P": ".--.",  "Q": "--.-",  "R": ".-.",             # Código Morse de las letras P, Q, R
    "S": "...",   "T": "-",     "U": "..-",             # Código Morse de las letras S, T, U
    "V": "...-",  "W": ".--",   "X": "-..-",            # Código Morse de las letras V, W, X
    "Y": "-.--",  "Z": "--..",                          # Código Morse de las letras Y, Z
    "0": "-----", "1": ".----", "2": "..---",           # Código Morse de los números 0, 1, 2
    "3": "...--", "4": "....-", "5": ".....",           # Código Morse de los números 3, 4, 5
    "6": "-....", "7": "--...", "8": "---..",            # Código Morse de los números 6, 7, 8
    "9": "----.",                                        # Código Morse del número 9
    "-": "-....-", "+": ".-.-.", ".": ".-.-.-"          # Código Morse de los símbolos -, +, .
}

morse_inverso = {v: k for k, v in morse.items()}        # Diccionario invertido: dado un código Morse devuelve la letra


# LEDS — secuencias de 13 bits (LED1-LED13)


leds = {
    # FILA 1 → led14 se enciende por pin directo
    "A":[1,0,0,0,0,0,0,0,0,0,0,0,0],                  # LED1 encendido → letra A en fila 1
    "C":[0,0,1,0,0,0,0,0,0,0,0,0,0],                  # LED3 encendido → letra C en fila 1
    "E":[0,1,0,0,0,0,0,0,0,0,0,0,0],                  # LED2 encendido → letra E en fila 1
    "G":[0,0,0,1,0,0,0,0,0,0,0,0,0],                  # LED4 encendido → letra G en fila 1
    "I":[0,0,0,0,1,0,0,0,0,0,0,0,0],                  # LED5 encendido → letra I en fila 1
    "K":[0,0,0,0,0,1,0,0,0,0,0,0,0],                  # LED6 encendido → letra K en fila 1
    "M":[0,0,0,0,0,0,1,0,0,0,0,0,0],                  # LED7 encendido → letra M en fila 1
    "O":[0,0,0,0,0,0,0,1,0,0,0,0,0],                  # LED8 encendido → letra O en fila 1
    "Q":[0,0,0,0,0,0,0,0,1,0,0,0,0],                  # LED9 encendido → letra Q en fila 1
    "S":[0,0,0,0,0,0,0,0,0,1,0,0,0],                  # LED10 encendido → letra S en fila 1
    "U":[0,0,0,0,0,0,0,0,0,0,1,0,0],                  # LED11 encendido → letra U en fila 1
    "W":[0,0,0,0,0,0,0,0,0,0,0,1,0],                  # LED12 encendido → letra W en fila 1
    "Y":[0,0,0,0,0,0,0,0,0,0,0,0,1],                  # LED13 encendido → letra Y en fila 1

    # FILA 2 → led15 se enciende por pin directo
    "B":[1,0,0,0,0,0,0,0,0,0,0,0,0],                  # LED1 encendido → letra B en fila 2
    "D":[0,0,1,0,0,0,0,0,0,0,0,0,0],                  # LED3 encendido → letra D en fila 2
    "F":[0,1,0,0,0,0,0,0,0,0,0,0,0],                  # LED2 encendido → letra F en fila 2
    "H":[0,0,0,1,0,0,0,0,0,0,0,0,0],                  # LED4 encendido → letra H en fila 2
    "J":[0,0,0,0,1,0,0,0,0,0,0,0,0],                  # LED5 encendido → letra J en fila 2
    "L":[0,0,0,0,0,1,0,0,0,0,0,0,0],                  # LED6 encendido → letra L en fila 2
    "N":[0,0,0,0,0,0,1,0,0,0,0,0,0],                  # LED7 encendido → letra N en fila 2
    "P":[0,0,0,0,0,0,0,1,0,0,0,0,0],                  # LED8 encendido → letra P en fila 2
    "R":[0,0,0,0,0,0,0,0,1,0,0,0,0],                  # LED9 encendido → letra R en fila 2
    "T":[0,0,0,0,0,0,0,0,0,1,0,0,0],                  # LED10 encendido → letra T en fila 2
    "V":[0,0,0,0,0,0,0,0,0,0,1,0,0],                  # LED11 encendido → letra V en fila 2
    "X":[0,0,0,0,0,0,0,0,0,0,0,1,0],                  # LED12 encendido → letra X en fila 2
    "Z":[0,0,0,0,0,0,0,0,0,0,0,0,1],                  # LED13 encendido → letra Z en fila 2

    # FILA 3 → led16 se enciende por pin directo
    "0":[1,0,0,0,0,0,0,0,0,0,0,0,0],                  # LED1 encendido → número 0 en fila 3
    "1":[0,0,1,0,0,0,0,0,0,0,0,0,0],                  # LED3 encendido → número 1 en fila 3
    "2":[0,1,0,0,0,0,0,0,0,0,0,0,0],                  # LED2 encendido → número 2 en fila 3
    "3":[0,0,0,1,0,0,0,0,0,0,0,0,0],                  # LED4 encendido → número 3 en fila 3
    "4":[0,0,0,0,1,0,0,0,0,0,0,0,0],                  # LED5 encendido → número 4 en fila 3
    "5":[0,0,0,0,0,1,0,0,0,0,0,0,0],                  # LED6 encendido → número 5 en fila 3
    "6":[0,0,0,0,0,0,1,0,0,0,0,0,0],                  # LED7 encendido → número 6 en fila 3
    "7":[0,0,0,0,0,0,0,1,0,0,0,0,0],                  # LED8 encendido → número 7 en fila 3
    "8":[0,0,0,0,0,0,0,0,1,0,0,0,0],                  # LED9 encendido → número 8 en fila 3
    "9":[0,0,0,0,0,0,0,0,0,1,0,0,0],                  # LED10 encendido → número 9 en fila 3
    "-":[0,0,0,0,0,0,0,0,0,0,1,0,0],                  # LED11 encendido → símbolo - en fila 3
    "+":[0,0,0,0,0,0,0,0,0,0,0,1,0],                  # LED12 encendido → símbolo + en fila 3
    ".":[0,0,0,0,0,0,0,0,0,0,0,0,1]                   # LED13 encendido → símbolo . en fila 3
}

fila_led = {                                            # Diccionario que mapea cada letra al pin de fila que debe encender
    "A": led14, "C": led14, "E": led14, "G": led14,   # Letras de fila 1 usan led14
    "I": led14, "K": led14, "M": led14, "O": led14,   # Letras de fila 1 usan led14
    "Q": led14, "S": led14, "U": led14, "W": led14,   # Letras de fila 1 usan led14
    "Y": led14,                                         # Última letra de fila 1
    "B": led15, "D": led15, "F": led15, "H": led15,   # Letras de fila 2 usan led15
    "J": led15, "L": led15, "N": led15, "P": led15,   # Letras de fila 2 usan led15
    "R": led15, "T": led15, "V": led15, "X": led15,   # Letras de fila 2 usan led15
    "Z": led15,                                         # Última letra de fila 2
    "0": led16, "1": led16, "2": led16, "3": led16,   # Números usan led16
    "4": led16, "5": led16, "6": led16, "7": led16,   # Números usan led16
    "8": led16, "9": led16, "-": led16, "+": led16,   # Números y símbolos usan led16
    ".": led16                                          # Último símbolo de fila 3
}


# TIEMPOS MORSE


UNIDAD        = 200                                     # Unidad base de tiempo en ms (duración de un punto)
UMBRAL_RAYA   = UNIDAD * 2                              # Presión mayor a 400ms se interpreta como raya
PAUSA_LETRA   = UNIDAD * 3                              # 600ms de silencio indica fin de una letra
PAUSA_PALABRA = UNIDAD * 7                              # 1400ms de silencio indica espacio entre palabras


# FUNCIONES DE HARDWARE


def ejecutarSecuencia(secuencia):                       # Envía 13 bits al registro de corrimiento para LED1-LED13
    for i in range(12, -1, -1):                         # Recorre los 13 bits de mayor a menor (MSB primero)
        DATA.value(secuencia[i])                        # Pone el bit actual en el pin de datos
        CLOCK.value(1)                                  # Flanco de subida: el registro captura el bit
        time.sleep_ms(1)                                # Espera 1ms para estabilidad
        CLOCK.value(0)                                  # Flanco de bajada: listo para el siguiente bit
        time.sleep_ms(1)                                # Espera 1ms antes del siguiente ciclo

def apagarLeds():                                       # Apaga todos los LEDs del sistema
    for i in range(13):                                 # Envía 13 bits en cero para apagar LED1-LED13
        DATA.value(0)                                   # Bit en cero = LED apagado
        CLOCK.value(1)                                  # Flanco de subida del reloj
        time.sleep_ms(1)                                # Espera de estabilidad
        CLOCK.value(0)                                  # Flanco de bajada del reloj
        time.sleep_ms(1)                                # Espera antes del siguiente ciclo
    led14.value(0)                                      # Apaga el LED indicador de fila 1
    led15.value(0)                                      # Apaga el LED indicador de fila 2
    led16.value(0)                                      # Apaga el LED indicador de fila 3

def sonidoON():                                         # Activa el buzzer con ciclo de trabajo bajo
    buzzer.duty_u16(2000)                               # 2000/65535 ≈ 3% de duty cycle, suficiente para sonar

def sonidoOFF():                                        # Apaga el buzzer completamente
    buzzer.duty_u16(0)                                  # 0 = sin señal = silencio total

def punto():                                            # Reproduce un punto Morse: señal corta de 1 unidad
    sonidoON()                                          # Enciende el buzzer
    time.sleep_ms(UNIDAD)                               # Suena durante 200ms
    sonidoOFF()                                         # Apaga el buzzer
    time.sleep_ms(UNIDAD)                               # Silencio de 1 unidad entre símbolos

def raya():                                             # Reproduce una raya Morse: señal larga de 3 unidades
    sonidoON()                                          # Enciende el buzzer
    time.sleep_ms(UNIDAD * 3)                           # Suena durante 600ms
    sonidoOFF()                                         # Apaga el buzzer
    time.sleep_ms(UNIDAD)                               # Silencio de 1 unidad entre símbolos

def reproducirMorse(letra):                             # Reproduce el Morse de una letra según el modo del switch
    letra = letra.upper()                               # Convierte a mayúscula por seguridad

    if letra == " ":                                    # Si es espacio entre palabras
        time.sleep_ms(UNIDAD * 7)                       # Pausa de 7 unidades = 1400ms
        return                                          # Sale sin hacer nada más

    if letra not in morse:                              # Si la letra no tiene Morse definido
        return                                          # La ignora y sale

    codigo     = morse[letra]                           # Obtiene el código Morse (ej: "A" → ".-")
    soloSonido = modoSwitch.value()                     # Lee el switch: 0=LEDs, 1=buzzer

    print("Morse:", letra, "→", codigo, "| Modo:",     # Imprime en consola para debug
          "sonido" if soloSonido else "LEDs")

    if not soloSonido and letra in leds:                # Si modo LEDs y la letra tiene secuencia
        ejecutarSecuencia(leds[letra])                  # Enciende LED1-LED13 según la letra
        fila_led[letra].value(1)                        # Enciende el LED de fila correspondiente

    for simbolo in codigo:                              # Recorre cada símbolo del código Morse
        if soloSonido:                                  # Si está en modo buzzer
            if simbolo == ".":                          # Si el símbolo es punto
                punto()                                 # Reproduce pitido corto
            elif simbolo == "-":                        # Si el símbolo es raya
                raya()                                  # Reproduce pitido largo
        else:                                           # Si está en modo LEDs
            if letra in leds:
                ejecutarSecuencia(leds[letra])          # Enciende LED de la letra
                fila_led[letra].value(1)                # Enciende LED de fila

                if simbolo == ".":
                    time.sleep_ms(UNIDAD)               # Punto: LED encendido 200ms
                elif simbolo == "-":
                    time.sleep_ms(UNIDAD * 3)           # Raya: LED encendido 600ms

                apagarLeds()                            # Apaga todos los LEDs
                time.sleep_ms(UNIDAD)                   # Pausa de 1 unidad entre símbolos

    time.sleep_ms(UNIDAD * 2)                           # Pausa adicional para completar 3 unidades entre letras
    apagarLeds()                                        # Apaga todos los LEDs al terminar la letra

def mostrarLetra(letra):                                # Mantiene el LED de una letra encendido durante 2 segundos
    if letra not in leds:                               # Si la letra no tiene LED asignado la ignora
        return
    print("MOSTRANDO:", letra)                          # Imprime en consola para debug
    inicio = time.ticks_ms()                            # Guarda el tiempo de inicio
    while time.ticks_diff(time.ticks_ms(), inicio) < 2000: # Repite durante 2000ms
        ejecutarSecuencia(leds[letra])                  # Refresca la secuencia del LED
        fila_led[letra].value(1)                        # Mantiene el LED de fila encendido
        time.sleep_ms(20)                               # Pausa pequeña para no saturar el procesador
    apagarLeds()                                        # Apaga todo al terminar

def leerMorseDesdeBoton():                              # Lee Morse del botón físico y lo decodifica a texto
    frase_resultado = ""                                # Acumula las letras decodificadas
    codigo_actual   = ""                                # Acumula puntos y rayas de la letra en curso
    ultimo_evento   = time.ticks_ms()                  # Tiempo del último evento detectado
    letra_enviada   = False                             # Indica si la letra actual ya fue procesada
    fin_timeout     = PAUSA_PALABRA * 3                 # 4200ms sin pulso = fin del mensaje

    print("Esperando entrada Morse del botón...")       # Avisa que está listo para recibir
    sonidoOFF()                                         # Asegura que el buzzer esté apagado

    while True:                                         # Bucle hasta detectar fin de mensaje
        ahora    = time.ticks_ms()                      # Tiempo actual en ms
        silencio = time.ticks_diff(ahora, ultimo_evento) # Tiempo desde el último evento

        if boton.value() == 1:                          # Si el botón está presionado
            inicio_presion = time.ticks_ms()            # Registra cuándo se presionó
            sonidoON()                                  # Activa buzzer como retroalimentación auditiva

            while boton.value() == 1:                   # Espera hasta que se suelte el botón
                time.sleep_ms(10)                       # Revisa cada 10ms

            duracion = time.ticks_diff(                 # Calcula cuánto tiempo estuvo presionado
                time.ticks_ms(), inicio_presion)
            sonidoOFF()                                 # Apaga el buzzer al soltar

            if duracion >= UMBRAL_RAYA:                 # Si estuvo más de 400ms → raya
                codigo_actual += "-"
                print("RAYA")
            else:                                       # Si estuvo menos de 400ms → punto
                codigo_actual += "."
                print("PUNTO")

            ultimo_evento = time.ticks_ms()             # Actualiza el tiempo del último evento
            letra_enviada = False                       # Resetea la bandera de letra procesada

        else:                                           # Si el botón no está presionado (silencio)
            if (not letra_enviada                       # Si la letra no fue procesada aún
                and len(codigo_actual) > 0              # y hay símbolos acumulados
                and silencio >= PAUSA_LETRA):           # y pasaron 600ms de silencio
                letra = morse_inverso.get(              # Decodifica el código Morse a letra
                    codigo_actual, "?")
                print("LETRA:", letra, "(", codigo_actual, ")")
                frase_resultado += letra                # Agrega la letra a la frase
                codigo_actual   = ""                    # Limpia el código para la siguiente letra
                letra_enviada   = True                  # Marca la letra como procesada

            if (letra_enviada                           # Si la letra fue procesada
                and silencio >= PAUSA_PALABRA):         # y pasaron 1400ms de silencio
                frase_resultado += " "                  # Agrega espacio entre palabras
                letra_enviada = False                   # Resetea para la siguiente letra
                print("ESPACIO")
                ultimo_evento = time.ticks_ms()         # Reinicia el contador de silencio

            if silencio >= fin_timeout:                 # Si pasaron 4200ms sin ningún pulso
                print("FIN DE MENSAJE:", frase_resultado.strip())
                return frase_resultado.strip()          # Retorna la frase completa decodificada

        time.sleep_ms(10)                               # Pausa pequeña para no saturar el procesador

def connect_wifi():                                     # Conecta la Pico W a la red WiFi configurada
    wlan = network.WLAN(network.STA_IF)                 # Crea interfaz WiFi en modo estación (cliente)
    wlan.active(True)                                   # Activa la interfaz WiFi
    wlan.connect(SSID, PASSWORD)                        # Inicia la conexión con las credenciales
    print("Conectando WiFi...")
    while not wlan.isconnected():                       # Espera hasta conectar
        time.sleep(0.5)                                 # Revisa cada 500ms
    print("Conectado:", wlan.ifconfig())                # Imprime la IP asignada
    return wlan.ifconfig()[0]                           # Retorna la IP de la Pico

def start_server(ip):                                   # Inicia el servidor TCP en la IP de la Pico
    s = socket.socket()                                 # Crea un socket TCP
    s.bind((ip, 1717))                                  # Lo enlaza a la IP de la Pico en el puerto 1717
    s.listen(1)                                         # Escucha hasta 1 conexión a la vez
    print("Servidor iniciado en", ip)

    while True:                                         # Bucle infinito esperando conexiones
        print("Esperando cliente...")
        conn, addr = s.accept()                         # Bloquea hasta recibir una conexión
        print("Cliente conectado:", addr)

        try:
            while True:                                 # Bucle de recepción de mensajes
                data = conn.recv(1024)                  # Recibe hasta 1024 bytes del cliente
                if not data:                            # Si no llegan datos el cliente se desconectó
                    break

                mensaje = data.decode().strip()         # Convierte bytes a texto y elimina espacios
                print("Mensaje recibido:", mensaje)

                if mensaje.startswith("MATRIZ:"):       # Comando para mostrar letras en LEDs
                    contenido = mensaje.replace("MATRIZ:", "") # Extrae el texto de la frase
                    for letra in contenido.upper():     # Recorre cada letra
                        print("MOSTRANDO LED:", letra)
                        mostrarLetra(letra)             # Muestra el LED de esa letra 2 segundos
                    conn.send("Mensaje reproducido".encode()) # Confirma al cliente

                elif mensaje == "BOTON":                # Comando para activar entrada por botón físico
                    conn.send("Listo para entrada Morse".encode()) # Confirma que está listo
                    frase = leerMorseDesdeBoton()       # Espera que el jugador ingrese Morse
                    print("Frase ingresada:", frase)
                    conn.send(frase.encode())           # Envía la frase decodificada a la PC

                else:                                   # Comando de texto normal: reproducir Morse
                    for letra in mensaje.upper():       # Recorre cada letra del mensaje
                        reproducirMorse(letra)          # Reproduce el Morse de cada letra
                    conn.send("Mensaje reproducido".encode()) # Confirma al cliente

        except Exception as e:                          # Captura cualquier error de comunicación
            import sys
            sys.print_exception(e)                      # Imprime el error en la consola de Thonny

        finally:                                        # Se ejecuta siempre, haya error o no
            conn.close()                                # Cierra la conexión con el cliente
            print("Cliente desconectado")


# MAIN


ip = connect_wifi()                                     # Conecta al WiFi y obtiene la IP asignada
start_server(ip)                                        # Inicia el servidor TCP con esa IP