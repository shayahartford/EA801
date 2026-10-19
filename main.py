import network
import ntptime
import time
from machine import Pin, PWM
import menu
from menu import menu_principal, horarios


# =========================================================
# OLED
# =========================================================

oled = menu.oled


# =========================================================
# PERIFÉRICOS
# =========================================================

led = Pin(11, Pin.OUT)
led.value(0)

buzzer = PWM(Pin(21))
buzzer.duty_u16(0)


# =========================================================
# WI-FI
# =========================================================

WIFI_SSID = "iPhone de Luana"
WIFI_PASS = "floripou"

MAX_TENTATIVAS_WIFI = 5


# =========================================================
# MOTOR CC + PONTE H
# =========================================================

STBY = Pin(20, Pin.OUT)
MOTOR_FWD = Pin(4, Pin.OUT)
MOTOR_BWD = Pin(9, Pin.OUT)
MOTOR_PWM = PWM(Pin(8))

MOTOR_PWM.freq(1000)
VELOCIDADE_MOTOR = 40000  # Faixa: 0 a 65535

# Habilita a ponte H
STBY.value(1)


def parar_motor():
    MOTOR_PWM.duty_u16(0)
    MOTOR_FWD.value(0)
    MOTOR_BWD.value(0)


def motor_horario():
    MOTOR_FWD.value(1)
    MOTOR_BWD.value(0)
    MOTOR_PWM.duty_u16(VELOCIDADE_MOTOR)


def motor_antihorario():
    MOTOR_FWD.value(0)
    MOTOR_BWD.value(1)
    MOTOR_PWM.duty_u16(VELOCIDADE_MOTOR)


# Inicia com o motor parado
parar_motor()



# =========================================================
# BUZZER
# =========================================================

def emitir_bip():

    buzzer.freq(2000)

    buzzer.duty_u16(32768)

    time.sleep_ms(200)

    buzzer.duty_u16(0)


# =========================================================
# BOTÃO A
# =========================================================

def botao_a_pressionado():

    if menu.btn_a.value() == 0:

        time.sleep_ms(150)

        return True

    return False


# =========================================================
# TELA DE ERRO WI-FI
# =========================================================

def tela_erro_wifi():

    oled.fill(0)

    oled.text(
        "SEM INTERNET",
        15,
        5
    )

    oled.text(
        "Falha ao",
        30,
        22
    )

    oled.text(
        "conectar",
        30,
        34
    )

    oled.hline(
        0,
        48,
        128,
        1
    )

    oled.text(
        "A: Tentar",
        20,
        54
    )

    oled.show()


# =========================================================
# CONEXÃO WI-FI
# =========================================================

def conectar_wifi():

    wlan = network.WLAN(
        network.STA_IF
    )

    wlan.active(True)


    while True:

        # =================================================
        # 5 TENTATIVAS
        # =================================================

        for tentativa in range(
            1,
            MAX_TENTATIVAS_WIFI + 1
        ):

            # ---------------------------------------------
            # Já conectado?
            # ---------------------------------------------

            if wlan.isconnected():

                print(
                    "Wi-Fi conectado!"
                )

                print(
                    "IP:",
                    wlan.ifconfig()[0]
                )


                oled.fill(0)

                oled.text(
                    "WI-FI OK!",
                    30,
                    15
                )

                oled.text(
                    "Conectado",
                    28,
                    32
                )

                oled.show()

                time.sleep_ms(1000)

                return wlan


            # ---------------------------------------------
            # Mostra tentativa
            # ---------------------------------------------

            oled.fill(0)

            oled.text(
                "CONECTANDO",
                20,
                5
            )

            oled.text(
                "AO WI-FI...",
                20,
                20
            )

            oled.text(
                "Tentativa "
                + str(tentativa)
                + "/5",
                30,
                42
            )

            oled.show()


            print(
                "Tentativa Wi-Fi "
                + str(tentativa)
                + "/5"
            )


            # ---------------------------------------------
            # Reinicia conexão
            # ---------------------------------------------

            try:

                wlan.disconnect()

            except:

                pass


            time.sleep_ms(500)


            # ---------------------------------------------
            # Conecta
            # ---------------------------------------------

            wlan.connect(
                WIFI_SSID,
                WIFI_PASS
            )


            inicio = time.time()


            # ---------------------------------------------
            # Aguarda até 10 segundos
            # ---------------------------------------------

            while not wlan.isconnected():

                if (
                    time.time() - inicio
                    >= 10
                ):

                    break

                time.sleep_ms(500)


            # ---------------------------------------------
            # Verifica resultado
            # ---------------------------------------------

            if wlan.isconnected():

                print(
                    "Wi-Fi conectado!"
                )

                print(
                    "IP:",
                    wlan.ifconfig()[0]
                )


                oled.fill(0)

                oled.text(
                    "WI-FI OK!",
                    30,
                    15
                )

                oled.text(
                    "Conectado",
                    28,
                    32
                )

                oled.show()

                time.sleep_ms(1000)

                return wlan


            print(
                "Falha na tentativa "
                + str(tentativa)
            )


            time.sleep_ms(500)


        # =================================================
        # 5 TENTATIVAS FALHARAM
        # =================================================

        print(
            "As 5 tentativas de conexão "
            "falharam."
        )


        tela_erro_wifi()


        # =================================================
        # AGUARDA AÇÃO DO USUÁRIO
        # =================================================

        while True:

            if botao_a_pressionado():

                print(
                    "Usuário solicitou "
                    "nova tentativa."
                )

                break

            time.sleep_ms(100)


# =========================================================
# SINCRONIZAÇÃO NTP
# =========================================================

def sincronizar_ntp():

    MAX_TENTATIVAS_NTP = 5


    for tentativa in range(
        1,
        MAX_TENTATIVAS_NTP + 1
    ):

        try:

            print(
                "Sincronizando NTP - "
                "tentativa "
                + str(tentativa)
                + "/5"
            )


            oled.fill(0)

            oled.text(
                "SINCRONIZANDO",
                8,
                5
            )

            oled.text(
                "HORARIO...",
                20,
                22
            )

            oled.text(
                "Tentativa "
                + str(tentativa)
                + "/5",
                30,
                42
            )

            oled.show()


            ntptime.settime()


            print(
                "Horário NTP sincronizado!"
            )


            oled.fill(0)

            oled.text(
                "HORARIO OK!",
                20,
                18
            )

            oled.text(
                "Sincronizado",
                15,
                36
            )

            oled.show()

            time.sleep_ms(1000)

            return True


        except Exception as e:

            print(
                "Erro ao sincronizar NTP:",
                e
            )

            time.sleep(1)


    # =====================================================
    # NTP FALHOU
    # =====================================================

    while True:

        oled.fill(0)

        oled.text(
            "ERRO DE",
            30,
            5
        )

        oled.text(
            "HORARIO",
            25,
            20
        )

        oled.text(
            "NTP",
            50,
            35
        )

        oled.hline(
            0,
            48,
            128,
            1
        )

        oled.text(
            "A: Tentar",
            20,
            54
        )

        oled.show()


        if botao_a_pressionado():

            if sincronizar_ntp():

                return True


        time.sleep_ms(100)


# =========================================================
# HORÁRIO LOCAL
# =========================================================

def obter_horario_local():

    fuso_utc_3 = -3 * 3600

    tm = time.localtime(
        time.time()
        +
        fuso_utc_3
    )

    return (
        tm[3],
        tm[4],
        tm[5]
    )


# =========================================================
# ALIMENTAÇÃO AUTOMÁTICA COM MOTOR CC
# =========================================================

alimentacao_automatica_ativa = False


def acionar_mecanismo_alimentacao(duracao_segundos):
    global alimentacao_automatica_ativa

    # Não permite conflito com a alimentação manual
    if alimentacao_manual_ativa:
        return False

    if alimentacao_automatica_ativa:
        return False

    alimentacao_automatica_ativa = True

    try:
        # Bipes de início
        emitir_bip()
        time.sleep_ms(100)
        emitir_bip()

        # Inicia a rotação
        motor_horario()

        inicio = time.ticks_ms()
        duracao_ms = int(duracao_segundos * 1000)
        proxima_troca_led = inicio
        led_ligado = False

        while time.ticks_diff(
            time.ticks_ms(), inicio
        ) < duracao_ms:

            agora = time.ticks_ms()

            # Pisca o LED durante a alimentação
            if time.ticks_diff(
                agora, proxima_troca_led
            ) >= 0:
                led_ligado = not led_ligado
                led.value(1 if led_ligado else 0)
                proxima_troca_led = time.ticks_add(
                    agora, 200
                )

            time.sleep_ms(20)

    finally:
        # Garante a parada ao terminar ou ocorrer erro
        parar_motor()
        led.value(0)
        alimentacao_automatica_ativa = False

    emitir_bip()
    return True

# =========================================================
# ALIMENTAÇÃO MANUAL COM MOTOR CC
# =========================================================

alimentacao_manual_ativa = False


def acionar_manual(ligado):
    global alimentacao_manual_ativa

    if ligado:
        # Não permite iniciar durante alimentação automática
        if alimentacao_automatica_ativa:
            print("Manual bloqueado: motor em uso.")
            return False

        if alimentacao_manual_ativa:
            return False

        alimentacao_manual_ativa = True

        print("!!! ALIMENTAÇÃO MANUAL INICIADA !!!")

        emitir_bip()
        time.sleep_ms(100)
        emitir_bip()

        motor_horario()
        led.value(1)

        return True

    else:
        if not alimentacao_manual_ativa:
            return False

        parar_motor()
        led.value(0)
        alimentacao_manual_ativa = False

        print("!!! ALIMENTAÇÃO MANUAL ENCERRADA !!!")
        emitir_bip()

        return True



# =========================================================
# CONTROLE DA ÚLTIMA ALIMENTAÇÃO AUTOMÁTICA
# =========================================================

ultima_alimentacao = None


# =========================================================
# VERIFICAR ALIMENTAÇÃO AUTOMÁTICA
# =========================================================

def verificar_alimentacao():

    global ultima_alimentacao


    # -----------------------------------------------------
    # Não executa alimentação automática enquanto houver
    # uma alimentação manual acontecendo.
    # -----------------------------------------------------

    if alimentacao_manual_ativa:

        return


    agora = time.time()


    tm = time.localtime(
        agora
        +
        (-3 * 3600)
    )


    ano = tm[0]
    mes = tm[1]
    dia = tm[2]

    hora = tm[3]
    minuto = tm[4]
    segundo = tm[5]


    # -----------------------------------------------------
    # Identifica o minuto atual
    # -----------------------------------------------------

    horario_atual = (
        ano,
        mes,
        dia,
        hora,
        minuto
    )


    # =====================================================
    # VERIFICA TODAS AS REFEIÇÕES
    # =====================================================

    for refeicao, horaf in horarios.items():

        hora_programada = horaf[0]

        minuto_programado = horaf[1]


        # -------------------------------------------------
        # O segundo não importa.
        #
        # Exemplo:
        #
        # 19:00:01 -> executa
        # 19:00:20 -> executaria
        # 19:00:50 -> executaria
        #
        # Mas somente uma vez no minuto.
        # -------------------------------------------------

        if (
            hora == hora_programada
            and
            minuto == minuto_programado
        ):


            if (
                ultima_alimentacao
                == horario_atual
            ):

                return


            ultima_alimentacao = (
                horario_atual
            )


            # -------------------------------------------------
            # Quantidade automática
            # -------------------------------------------------

            qtd = getattr(
                menu,
                "quantidade_atual",
                "Medio"
            )


            if qtd == "Pouco":

                tempo_execucao = 5

            elif qtd == "Muito":

                tempo_execucao = 15

            else:

                tempo_execucao = 10


            print(
                "!!! SERVO ACIONADO: "
                + str(refeicao)
                + " | Qtd: "
                + str(qtd)
                + " | Tempo: "
                + str(tempo_execucao)
                + "s | Horário: "
                + "{:02d}:{:02d}:{:02d}"
                .format(
                    hora,
                    minuto,
                    segundo
                )
                + " !!!"
            )


            # -------------------------------------------------
            # Executa alimentação automática
            # -------------------------------------------------

            acionar_mecanismo_alimentacao(
                tempo_execucao
            )


            return


# =========================================================
# INICIALIZAÇÃO
# =========================================================

print(
    "================================"
)

print(
    "INICIANDO SISTEMA"
)

print(
    "================================"
)


# =========================================================
# 1. CONECTA AO WI-FI
# =========================================================

wlan = conectar_wifi()


# =========================================================
# 2. SINCRONIZA HORÁRIO
# =========================================================

sincronizar_ntp()


# =========================================================
# 3. SISTEMA PRONTO
# =========================================================

print(
    "================================"
)

print(
    "SISTEMA PRONTO"
)

print(
    "================================"
)


# =========================================================
# 4. INICIA MENU
# =========================================================

menu_principal(
    callback_verificacao=verificar_alimentacao,
    callback_acionar_manual=acionar_manual
)
