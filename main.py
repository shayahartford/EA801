import network
import ntptime
import time
from machine import Pin
from menu import menu_principal
from menu import horarios

# LED Verde no GPIO 11 da BitDogLab V7[cite: 2]
led = Pin(11, Pin.OUT)
led.value(0)

WIFI_SSID = "iPhone de Luana"
WIFI_PASS = "floripou"

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

ultimo_minuto_disparado = -1

def verificar_alimentacao():
    global ultimo_minuto_disparado
    hora, minuto, segundo = obter_horario_local()

    if segundo == 0 and minuto != ultimo_minuto_disparado:
        for refeicao, horaf in horarios.items():
            if hora == horaf[0] and minuto == horaf[1]:
                print(f"!!! ALIMENTANDO: {refeicao} !!!")
                # Pisca o LED Verde para simular acionamento[cite: 1]
                for _ in range(10):
                    led.value(1)
                    time.sleep_ms(100)
                    led.value(0)
                    time.sleep_ms(100)
                ultimo_minuto_disparado = minuto
                break

# Conecta à rede e sincroniza horário
if conectar_wifi():
    sincronizar_ntp()

# Inicia a interface gráfica passando a função de verificação
menu_principal(callback_verificacao=verificar_alimentacao)