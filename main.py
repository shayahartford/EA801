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

servo = PWM(Pin(8))
servo.freq(50)


# =========================================================
# WI-FI
# =========================================================

WIFI_SSID = "iPhone de Luana"
WIFI_PASS = "floripou"

MAX_TENTATIVAS_WIFI = 5


# =========================================================
# SERVO
# =========================================================

def definir_angulo_servo(angulo):

    duty_ns = int(
        500000
        +
        (angulo / 180)
        * 2000000
    )

    servo.duty_ns(duty_ns)


# Começa fechado

definir_angulo_servo(0)


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
# ALIMENTAÇÃO AUTOMÁTICA NÃO BLOQUEANTE
# =========================================================

estado_auto = "inativo"
inicio_estado_auto = 0
inicio_alimentacao = 0
duracao_alimentacao_ms = 0

# Fila de refeições aguardando execução
fila_alimentacoes = []

# Última data em que cada refeição foi agendada.
# Protege contra execuções repetidas no mesmo dia
# durante a execução atual do programa.
ultima_execucao_por_refeicao = {}


def iniciar_mecanismo_alimentacao(duracao_segundos):
    global estado_auto, inicio_estado_auto
    global duracao_alimentacao_ms

    if estado_auto != "inativo":
        return False

    duracao_alimentacao_ms = duracao_segundos * 1000

    buzzer.freq(2000)
    buzzer.duty_u16(32768)

    inicio_estado_auto = time.ticks_ms()
    estado_auto = "bipe1"

    print("Iniciando alimentação automática")
    return True


def atualizar_mecanismo_alimentacao():
    global estado_auto, inicio_estado_auto
    global inicio_alimentacao

    agora = time.ticks_ms()

    decorrido = time.ticks_diff(
        agora, inicio_estado_auto
    )

    # Primeiro bipe: 200 ms
    if estado_auto == "bipe1":
        if decorrido >= 200:
            buzzer.duty_u16(0)
            inicio_estado_auto = agora
            estado_auto = "intervalo"

    # Intervalo entre os bipes: 100 ms
    elif estado_auto == "intervalo":
        if decorrido >= 100:
            buzzer.duty_u16(32768)
            inicio_estado_auto = agora
            estado_auto = "bipe2"

    # Segundo bipe: 200 ms
    elif estado_auto == "bipe2":
        if decorrido >= 200:
            buzzer.duty_u16(0)
            definir_angulo_servo(90)

            inicio_alimentacao = agora
            inicio_estado_auto = agora
            led.value(1)
            estado_auto = "alimentando"

    # Servo aberto pelo tempo configurado
    elif estado_auto == "alimentando":
        tempo_aberto = time.ticks_diff(
            agora, inicio_alimentacao
        )

        # Pisca o LED sem bloquear o programa
        if (tempo_aberto // 200) % 2 == 0:
            led.value(1)
        else:
            led.value(0)

        if tempo_aberto >= duracao_alimentacao_ms:
            definir_angulo_servo(0)
            led.value(0)

            buzzer.freq(2000)
            buzzer.duty_u16(32768)

            inicio_estado_auto = agora
            estado_auto = "bipe_final"

    # Bipe final: 200 ms
    elif estado_auto == "bipe_final":
        if decorrido >= 200:
            buzzer.duty_u16(0)
            estado_auto = "inativo"

            print("Alimentação automática concluída")



# =========================================================
# ALIMENTAÇÃO MANUAL
# =========================================================
#
# ligado = True:
#     abre o servo e deixa aberto.
#
# ligado = False:
#     fecha o servo.
#
# Não existe tempo pré-definido.
#
# =========================================================

alimentacao_manual_ativa = False



def acionar_manual(ligado):
    global alimentacao_manual_ativa

    if ligado:
        if estado_auto != "inativo":
            print("Manual bloqueado: alimentação automática em andamento.")
            return False

        if alimentacao_manual_ativa:
            return False

        alimentacao_manual_ativa = True

        # Mantenha aqui os bipes, a abertura do servo e o LED.

        return True

    else:
        # Evita desligar se já estiver desligado
        if not alimentacao_manual_ativa:
            return

        alimentacao_manual_ativa = False

        print("!!! ALIMENTAÇÃO MANUAL ENCERRADA !!!")

        definir_angulo_servo(0)
        led.value(0)
        emitir_bip()



# =========================================================
# CONTROLE DA ÚLTIMA ALIMENTAÇÃO AUTOMÁTICA
# =========================================================

ultima_alimentacao = None



# =========================================================
# VERIFICAR ALIMENTAÇÃO AUTOMÁTICA
# =========================================================

def verificar_alimentacao():
    global ultima_execucao_por_refeicao

    # Primeiro, avança a máquina de estados.
    # Não utiliza esperas bloqueantes.
    atualizar_mecanismo_alimentacao()

    agora = time.time()

    # O RTC sincronizado por NTP está em UTC.
    # Aplicamos UTC-3 para obter o horário local.
    tm = time.localtime(agora - 3 * 3600)

    ano, mes, dia = tm[0], tm[1], tm[2]
    hora, minuto = tm[3], tm[4]

    data_atual = (ano, mes, dia)

    # Verifica cada refeição configurada
    for refeicao, horaf in horarios.items():
        hora_programada, minuto_programado = horaf

        if (hora, minuto) != (
            hora_programada, minuto_programado
        ):
            continue

        # Uma execução por refeição e horário programado por dia
        versao = menu.versoes_horario[refeicao]

        identificador_execucao = (
            data_atual,
            versao
        )

        # Uma execução por versão da programação por dia
        if ultima_execucao_por_refeicao.get(refeicao) == identificador_execucao:
            continue

        qtd = getattr(menu, "quantidade_atual", "Medio")

        if qtd == "Pouco":
            duracao = 5
        elif qtd == "Muito":
            duracao = 15
        else:
            duracao = 10

        # Registra e enfileira a refeição.
        # A fila evita perder uma refeição se outra
        # ainda estiver sendo executada.
        # Registra o horário e a versão que originaram a tarefa
        fila_alimentacoes.append(
            (
                refeicao,
                duracao,
                data_atual,
                hora_programada,
                minuto_programado,
                versao
            )
        )

        ultima_execucao_por_refeicao[refeicao] = (
            identificador_execucao
        )

        print(
            "Refeição agendada:",
            refeicao,
            hora_programada,
            minuto_programado
        )

    # Inicia apenas tarefas que ainda correspondem
    # à programação salva.
    while (
        estado_auto == "inativo"
        and not alimentacao_manual_ativa
        and fila_alimentacoes
    ):
        (
            refeicao,
            duracao,
            data_refeicao,
            hora_fila,
            minuto_fila,
            versao_fila
        ) = fila_alimentacoes.pop(0)

        # Descarta tarefas de outro dia
        if data_refeicao != data_atual:
            continue

        # Descarta tarefas de uma versão antiga
        if menu.versoes_horario[refeicao] != versao_fila:
            continue

        # Descarta tarefas cujo horário não é mais o salvo
        if tuple(horarios[refeicao]) != (
            hora_fila,
            minuto_fila
        ):
            continue

        iniciar_mecanismo_alimentacao(duracao)
        break



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
