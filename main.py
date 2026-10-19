import network
import ntptime
import time
from machine import Pin, PWM
import menu
from menu import menu_principal, horarios


# =========================================================
# CONFIGURACAO
# =========================================================
# Preencha com as credenciais da rede Wi-Fi usada no projeto.
WIFI_SSID = "iPhone de Luana"
WIFI_PASS = "floripou"
MAX_TENTATIVAS_WIFI = 5
FUSO_UTC_SEGUNDOS = -3 * 3600

# Pinos da ponte H TB6612FNG - manter conforme a montagem atual.
STBY = Pin(20, Pin.OUT)
MOTOR_FWD = Pin(4, Pin.OUT)
MOTOR_BWD = Pin(9, Pin.OUT)
MOTOR_PWM = PWM(Pin(8))
MOTOR_PWM.freq(1000)
VELOCIDADE_MOTOR = 40000  # 0 a 65535

led = Pin(11, Pin.OUT)
led.value(0)
buzzer = PWM(Pin(21))
buzzer.duty_u16(0)
oled = menu.oled

# Tempos independentes de ida e volta; ajuste conforme a mecanica.
TEMPOS_IDA = {"Pouco": 5, "Medio": 10, "Muito": 15}
TEMPOS_VOLTA = {"Pouco": 5, "Medio": 10, "Muito": 15}
PAUSA_REVERSAO_MS = 300


# =========================================================
# CONTROLE DO MOTOR CC
# =========================================================
STBY.value(1)


def parar_motor():
    MOTOR_PWM.duty_u16(0)
    MOTOR_FWD.value(0)
    MOTOR_BWD.value(0)


def motor_horario():
    STBY.value(1)
    MOTOR_FWD.value(1)
    MOTOR_BWD.value(0)
    MOTOR_PWM.duty_u16(VELOCIDADE_MOTOR)


def motor_antihorario():
    STBY.value(1)
    MOTOR_FWD.value(0)
    MOTOR_BWD.value(1)
    MOTOR_PWM.duty_u16(VELOCIDADE_MOTOR)


parar_motor()


def emitir_bip(duracao_ms=200):
    buzzer.freq(2000)
    buzzer.duty_u16(32768)
    time.sleep_ms(duracao_ms)
    buzzer.duty_u16(0)


def botao_a_pressionado():
    if menu.btn_a.value() == 0:
        time.sleep_ms(150)
        return True
    return False


# =========================================================
# WI-FI E SINCRONIZACAO DE HORARIO
# =========================================================
def tela_erro_wifi():
    oled.fill(0)
    oled.text("SEM INTERNET", 15, 5)
    oled.text("Falha ao", 30, 22)
    oled.text("conectar", 30, 34)
    oled.hline(0, 48, 128, 1)
    oled.text("A: Tentar", 20, 54)
    oled.show()


def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    while True:
        for tentativa in range(1, MAX_TENTATIVAS_WIFI + 1):
            if wlan.isconnected():
                print("Wi-Fi conectado:", wlan.ifconfig()[0])
                oled.fill(0)
                oled.text("WI-FI OK!", 30, 15)
                oled.text("Conectado", 28, 32)
                oled.show()
                time.sleep_ms(800)
                return wlan

            oled.fill(0)
            oled.text("CONECTANDO", 20, 5)
            oled.text("AO WI-FI...", 20, 20)
            oled.text("Tentativa {}/{}".format(
                tentativa, MAX_TENTATIVAS_WIFI), 10, 42)
            oled.show()

            try:
                wlan.disconnect()
            except Exception:
                pass

            time.sleep_ms(300)
            try:
                wlan.connect(WIFI_SSID, WIFI_PASS)
            except Exception as erro:
                print("Falha ao iniciar Wi-Fi:", erro)

            inicio = time.ticks_ms()
            while (not wlan.isconnected() and
                   time.ticks_diff(time.ticks_ms(), inicio) < 10000):
                time.sleep_ms(250)

            if wlan.isconnected():
                break

        if wlan.isconnected():
            continue

        print("Falharam as tentativas de Wi-Fi.")
        tela_erro_wifi()
        while not botao_a_pressionado():
            time.sleep_ms(100)


def sincronizar_ntp():
    while True:
        for tentativa in range(1, 6):
            try:
                oled.fill(0)
                oled.text("SINCRONIZANDO", 8, 5)
                oled.text("HORARIO...", 20, 22)
                oled.text("Tentativa {}/5".format(tentativa), 25, 42)
                oled.show()
                ntptime.settime()
                oled.fill(0)
                oled.text("HORARIO OK!", 20, 18)
                oled.text("Sincronizado", 15, 36)
                oled.show()
                time.sleep_ms(800)
                print("Horario sincronizado via NTP.")
                return True
            except Exception as erro:
                print("Erro NTP:", erro)
                time.sleep(1)

        oled.fill(0)
        oled.text("ERRO DE", 30, 5)
        oled.text("HORARIO NTP", 20, 20)
        oled.text("A: Tentar", 20, 54)
        oled.show()
        while not botao_a_pressionado():
            time.sleep_ms(100)


def obter_horario_local():
    tm = time.localtime(time.time() + FUSO_UTC_SEGUNDOS)
    return tm[3], tm[4], tm[5]


# =========================================================
# ALIMENTACAO NAO BLOQUEANTE COM MOTOR CC
# =========================================================
# Estados: inativo -> bipes -> ida -> pausa -> volta -> bipe final.
# O callback e chamado repetidamente pelo menu, portanto o display e
# os botoes continuam sendo processados durante a alimentacao.

estado_auto = "inativo"
inicio_estado_auto = 0
inicio_movimento = 0
duracao_ida_ms = 0
duracao_volta_ms = 0
alimentacao_manual_ativa = False
fila_alimentacoes = []
ultima_execucao_por_refeicao = {}


def iniciar_mecanismo_alimentacao(tempo_ida_s, tempo_volta_s):
    global estado_auto, inicio_estado_auto
    global duracao_ida_ms, duracao_volta_ms

    if estado_auto != "inativo" or alimentacao_manual_ativa:
        return False

    duracao_ida_ms = int(tempo_ida_s * 1000)
    duracao_volta_ms = int(tempo_volta_s * 1000)
    buzzer.freq(2000)
    buzzer.duty_u16(32768)
    inicio_estado_auto = time.ticks_ms()
    estado_auto = "bipe1"
    print("Alimentacao automatica iniciada.")
    return True


def atualizar_mecanismo_alimentacao():
    global estado_auto, inicio_estado_auto, inicio_movimento

    agora = time.ticks_ms()
    decorrido_estado = time.ticks_diff(agora, inicio_estado_auto)

    if estado_auto == "inativo":
        parar_motor()
        led.value(0)

    elif estado_auto == "bipe1":
        if decorrido_estado >= 200:
            buzzer.duty_u16(0)
            inicio_estado_auto = agora
            estado_auto = "intervalo"

    elif estado_auto == "intervalo":
        if decorrido_estado >= 100:
            buzzer.duty_u16(32768)
            inicio_estado_auto = agora
            estado_auto = "bipe2"

    elif estado_auto == "bipe2":
        if decorrido_estado >= 200:
            buzzer.duty_u16(0)
            motor_horario()
            inicio_movimento = agora
            estado_auto = "ida"
            led.value(1)

    elif estado_auto == "ida":
        decorrido_movimento = time.ticks_diff(agora, inicio_movimento)
        led.value(1 if (decorrido_movimento // 200) % 2 == 0 else 0)
        if decorrido_movimento >= duracao_ida_ms:
            parar_motor()
            led.value(0)
            inicio_estado_auto = agora
            estado_auto = "pausa"

    elif estado_auto == "pausa":
        if decorrido_estado >= PAUSA_REVERSAO_MS:
            motor_antihorario()
            inicio_movimento = agora
            estado_auto = "volta"
            led.value(1)

    elif estado_auto == "volta":
        decorrido_movimento = time.ticks_diff(agora, inicio_movimento)
        led.value(1 if (decorrido_movimento // 200) % 2 == 0 else 0)
        if decorrido_movimento >= duracao_volta_ms:
            parar_motor()
            led.value(0)
            buzzer.freq(2000)
            buzzer.duty_u16(32768)
            inicio_estado_auto = agora
            estado_auto = "bipe_final"

    elif estado_auto == "bipe_final":
        if decorrido_estado >= 200:
            buzzer.duty_u16(0)
            parar_motor()
            led.value(0)
            estado_auto = "inativo"
            print("Alimentacao automatica concluida.")


def acionar_manual(ligado):
    global alimentacao_manual_ativa

    if ligado:
        if estado_auto != "inativo":
            print("Modo manual bloqueado: alimentacao automatica em andamento.")
            return False
        if alimentacao_manual_ativa:
            return False

        alimentacao_manual_ativa = True
        print("Alimentacao manual iniciada.")
        emitir_bip()
        motor_horario()
        led.value(1)
        return True

    if not alimentacao_manual_ativa:
        return False

    parar_motor()
    led.value(0)
    alimentacao_manual_ativa = False
    emitir_bip()
    print("Alimentacao manual encerrada.")
    return True


def verificar_alimentacao():
    # Atualiza a maquina de estados sem esperas bloqueantes.
    atualizar_mecanismo_alimentacao()

    if alimentacao_manual_ativa:
        return

    agora = time.time()
    tm = time.localtime(agora + FUSO_UTC_SEGUNDOS)
    data_atual = (tm[0], tm[1], tm[2])
    hora, minuto = tm[3], tm[4]

    # Enfileira cada refeicao uma unica vez por data e versao do horario.
    for refeicao, horario in horarios.items():
        hora_prog, minuto_prog = horario
        if (hora, minuto) != (hora_prog, minuto_prog):
            continue

        versao = getattr(menu, "versoes_horario", {}).get(refeicao, 0)
        identificador = (data_atual, versao)
        if ultima_execucao_por_refeicao.get(refeicao) == identificador:
            continue

        qtd = getattr(menu, "quantidade_atual", "Medio")
        if qtd not in TEMPOS_IDA:
            qtd = "Medio"

        fila_alimentacoes.append((
            refeicao, TEMPOS_IDA[qtd], TEMPOS_VOLTA[qtd],
            data_atual, hora_prog, minuto_prog, versao
        ))
        ultima_execucao_por_refeicao[refeicao] = identificador
        print("Refeicao agendada:", refeicao, "{:02d}:{:02d}".format(
            hora_prog, minuto_prog))

    # Comeca a proxima tarefa valida quando o motor estiver livre.
    while estado_auto == "inativo" and not alimentacao_manual_ativa and fila_alimentacoes:
        (refeicao, tempo_ida, tempo_volta, data_ref, hora_fila,
         minuto_fila, versao_fila) = fila_alimentacoes.pop(0)

        if data_ref != data_atual:
            continue
        if getattr(menu, "versoes_horario", {}).get(refeicao, 0) != versao_fila:
            continue
        if tuple(horarios[refeicao]) != (hora_fila, minuto_fila):
            continue

        print("Motor CC:", refeicao, "| ida:", tempo_ida,
              "s | volta:", tempo_volta, "s")
        iniciar_mecanismo_alimentacao(tempo_ida, tempo_volta)
        break


# =========================================================
# INICIALIZACAO
# =========================================================
print("================================")
print("INICIANDO ALIMENTADOR AUTOMATICO")
print("================================")

try:
    conectar_wifi()
    sincronizar_ntp()
    print("Sistema pronto.")
    menu_principal(
        callback_verificacao=verificar_alimentacao,
        callback_acionar_manual=acionar_manual
    )
finally:
    # Em qualquer saida/erro, tenta deixar a ponte H em estado seguro.
    parar_motor()
    led.value(0)
    buzzer.duty_u16(0)
