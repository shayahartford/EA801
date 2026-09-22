import network
import ntptime
import time
from machine import Pin, PWM
import menu
from menu import menu_principal, horarios

# 1. Configuração dos Periféricos (LED, Buzzer e Servo)[cite: 2]
led = Pin(11, Pin.OUT)                   # LED Verde no GPIO 11[cite: 2]
led.value(0)

buzzer = PWM(Pin(21))                     # Buzzer A no GPIO 21[cite: 2]
buzzer.duty_u16(0)

servo = PWM(Pin(8))                       # Sinal do Servomotor no GPIO 8[cite: 2]
servo.freq(50)                            # Frequência padrão de 50 Hz para servos

WIFI_SSID = "iPhone de Luana"
WIFI_PASS = "floripou"

def definir_angulo_servo(angulo):
    """Define a posição do servomotor entre 0 e 180 graus."""
    # Pulso varia tipicamente de 500.000 ns (0°) a 2.500.000 ns (180°)
    duty_ns = int(500000 + (angulo / 180) * 2000000)
    servo.duty_ns(duty_ns)

# Garante que o servo inicie fechado (0°)
definir_angulo_servo(0)

def emitir_bip():
    """Emite um bip sonoro curto no buzzer.[cite: 1]"""
    buzzer.freq(2000)
    buzzer.duty_u16(32768)
    time.sleep_ms(200)
    buzzer.duty_u16(0)

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando ao Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        inicio = time.time()
        while not wlan.isconnected():
            if time.time() - inicio > 10:
                print("Falha na conexão Wi-Fi!")
                return False
            time.sleep_ms(500)
    print("Wi-Fi Conectado! IP:", wlan.ifconfig()[0])
    return True

def sincronizar_ntp():
    try:
        ntptime.settime()
        print("Horário NTP sincronizado com sucesso!")
        return True
    except Exception as e:
        print("Erro ao sincronizar NTP:", e)
        return False

def obter_horario_local():
    fuso_utc_3 = -3 * 3600
    tm = time.localtime(time.time() + fuso_utc_3)
    return tm[3], tm[4], tm[5]

def acionar_mecanismo_alimentacao(duracao_segundos):
    """Executa a sequência de aviso sonoro, abertura do servo e pisca do LED.[cite: 1]"""
    # 1. Sinal Sonoro de início[cite: 1]
    emitir_bip()
    time.sleep_ms(100)
    emitir_bip()

    # 2. Abre o servomotor (90 graus)[cite: 1]
    definir_angulo_servo(90)

    # 3. Mantém o mecanismo aberto pelo tempo configurado piscando o LED[cite: 1]
    tempo_inicio = time.time()
    while (time.time() - tempo_inicio) < duracao_segundos:
        led.value(1)
        time.sleep_ms(100)
        led.value(0)
        time.sleep_ms(100)

    # 4. Retorna o servomotor para a posição inicial/fechado (0 graus)[cite: 1]
    definir_angulo_servo(0)
    
    # Sinal sonoro de término
    emitir_bip()

ultimo_minuto_disparado = -1

def verificar_alimentacao():
    global ultimo_minuto_disparado
    hora, minuto, segundo = obter_horario_local()

    if segundo == 0 and minuto != ultimo_minuto_disparado:
        for refeicao, horaf in horarios.items():
            if hora == horaf[0] and minuto == horaf[1]:
                # Lê a quantidade configurada ("Pouco", "Medio", "Muito")[cite: 1]
                qtd = getattr(menu, 'quantidade_atual', 'Medio')
                
                if qtd == "Pouco":
                    tempo_execucao = 5
                elif qtd == "Muito":
                    tempo_execucao = 15
                else:  # "Medio"
                    tempo_execucao = 10

                print(f"!!! SERVO ACIONADO: {refeicao} | Qtd: {qtd} | Tempo: {tempo_execucao}s !!!")
                
                # Aciona o ciclo completo de liberação da ração[cite: 1]
                acionar_mecanismo_alimentacao(tempo_execucao)

                ultimo_minuto_disparado = minuto
                break

# Inicialização do sistema
if conectar_wifi():
    sincronizar_ntp()

# Execução do menu interativo
menu_principal(callback_verificacao=verificar_alimentacao)
