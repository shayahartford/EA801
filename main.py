
import network
import ntptime
import time
from machine import Pin, PWM, I2C, time_pulse_us
from math import atan2, degrees
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

# Quantidade de camaras a avancar em cada alimentacao automatica.
# Ajuste caso o significado de Pouco/Medio/Muito no menu seja diferente.
PORCOES_POR_QUANTIDADE = {"Pouco": 1, "Medio": 2, "Muito": 3}
ANGULO_POR_CAMARA = 120.0

# Configuracao do HMC5883L. O sensor fica fixo na estrutura e um ima
# permanente acompanha o disco. A geometria precisa ser calibrada.
I2C_MAG =  menu.i2c
ENDERECO_HMC = 0x1E
I2C_MAG.writeto_mem(ENDERECO_HMC, 0x00, b'\x70')
I2C_MAG.writeto_mem(ENDERECO_HMC, 0x01, b'\x20')
I2C_MAG.writeto_mem(ENDERECO_HMC, 0x02, b'\x00')
time.sleep_ms(100)

# Se o angulo medido diminuir quando o disco gira no sentido escolhido,
# altere para -1. A leitura deve ser validada na montagem real.
SINAL_ROTACAO_SENSOR = 1
# Descarta saltos impossiveis entre duas amostras consecutivas.
MAX_VARIACAO_LEITURA_GRAUS = 45.0
INTERVALO_LEITURA_MAG_MS = 20
TEMPO_MAXIMO_ROTACAO_AUTO_MS = 60000  # protecao contra ausencia de progresso angular

# Sensor ultrassonico HC-SR04: TRIG no GPIO 1 e ECHO no GPIO 0.
TRIG = Pin(1, Pin.OUT)
ECHO = Pin(0, Pin.IN)
TRIG.value(0)

# Distancia medida do sensor ate a superficie da racao.
# Quanto MAIOR a distancia, MENOR o nivel de racao.
# CALIBRE este valor conforme a altura e o formato do reservatorio.
DISTANCIA_RACAO_BAIXA_CM = 15.0   # Aviso: nivel baixo, mas ainda pode alimentar
DISTANCIA_RACAO_VAZIA_CM = 20.0   # Bloqueio: calibrar para o fundo do reservatorio
HISTERese_CM = 0.5               # Evita alternancia perto dos limites
LEITURAS_CONSECUTIVAS_CONFIRMACAO = 2
INTERVALO_LEITURA_SENSOR_MS = 1000
DISTANCIA_MIN_CM = 2.0
DISTANCIA_MAX_CM = 400.0


# =========================================================
# CONTROLE DO MOTOR CC
# =========================================================
STBY.value(1)


def parar_motor():
    MOTOR_PWM.duty_u16(0)
    MOTOR_FWD.value(0)
    MOTOR_BWD.value(0)


def motor_horario():
    """Aciona o motor somente no sentido definido como horario."""
    STBY.value(1)
    MOTOR_FWD.value(1)
    MOTOR_BWD.value(0)
    MOTOR_PWM.duty_u16(VELOCIDADE_MOTOR)


def signed16(valor):
    if valor >= 32768:
        return valor - 65536
    return valor


def ler_angulo_magnetometro():
    """Le o angulo XY do campo magnetico, em graus [0, 360)."""
    dados = I2C_MAG.readfrom_mem(ENDERECO_HMC, 0x03, 6)
    x = signed16(int.from_bytes(dados[0:2], 'big'))
    # A leitura de Z e mantida para respeitar a ordem de registradores.
    y = signed16(int.from_bytes(dados[4:6], 'big'))

    if x == 0 and y == 0:
        raise OSError("Campo magnetico XY sem leitura valida")

    angulo = degrees(atan2(y, x))
    if angulo < 0:
        angulo += 360
    return angulo


def diferenca_angular(atual, anterior):
    """Diferenca assinada mais curta entre dois angulos."""
    diferenca = atual - anterior
    if diferenca < -180:
        diferenca += 360
    elif diferenca > 180:
        diferenca -= 360
    return diferenca


def capturar_referencia_angular():
    """Inicia uma nova medicao incremental do movimento do disco."""
    angulo = ler_angulo_magnetometro()
    return angulo, 0.0, time.ticks_ms()


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
    oled.text("ERRO DE WI-FI", 16, 5)
    oled.text("Sem conexao", 20, 22)
    oled.text("Verifique a rede", 4, 36)
    oled.hline(0, 49, 128, 1)
    oled.text("A: Tentar", 28, 54)
    oled.show()


def conectar_wifi():
    oled.fill(0)
    oled.show()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    while True:
        for tentativa in range(1, MAX_TENTATIVAS_WIFI + 1):
            if wlan.isconnected():
                print("Wi-Fi conectado:", wlan.ifconfig()[0])
                oled.fill(0)
                oled.text("WI-FI OK!", 32, 15)
                oled.text("Conectado", 24, 32)
                oled.show()
                time.sleep_ms(800)
                return wlan

            oled.fill(0)
            oled.text("CONECTANDO", 20, 5)
            oled.text("AO WI-FI...", 20, 19)

            texto = "Tent. {}/{}".format(
                tentativa, MAX_TENTATIVAS_WIFI
            )
            oled.text(texto, (128 - len(texto) * 8) // 2, 39)
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
                continue

            inicio = time.ticks_ms()

            while (
                not wlan.isconnected()
                and time.ticks_diff(time.ticks_ms(), inicio) < 10000
            ):
                time.sleep_ms(250)

        if wlan.isconnected():
            continue

        print("Falharam as tentativas de Wi-Fi.")
        tela_erro_wifi()

        # Espera o botao A sem bloquear a leitura de Ctrl+C.
        while True:
            if botao_a_pressionado():
                break
            time.sleep_ms(100)


def sincronizar_ntp():
    while True:
        for tentativa in range(1, 6):
            oled.fill(0)
            oled.text("AJUSTANDO HORA", 8, 5)
            oled.text("VIA INTERNET", 16, 19)

            texto = "Tent. {}/5".format(tentativa)
            oled.text(texto, (128 - len(texto) * 8) // 2, 39)
            oled.show()

            try:
                ntptime.settime()

                oled.fill(0)
                oled.text("HORARIO OK!", 24, 15)
                oled.text("Sincronizado", 12, 32)
                oled.show()
                time.sleep_ms(800)

                print("Horario sincronizado via NTP.")
                return True

            except KeyboardInterrupt:
                raise

            except Exception as erro:
                print("Erro NTP:", erro)
                time.sleep(1)

        oled.fill(0)
        oled.text("ERRO NO", 36, 5)
        oled.text("HORARIO NTP", 20, 20)
        oled.hline(0, 48, 128, 1)
        oled.text("A: Tentar", 28, 54)
        oled.show()

        while True:
            if botao_a_pressionado():
                break
            time.sleep_ms(100)


def obter_horario_local():
    tm = time.localtime(time.time() + FUSO_UTC_SEGUNDOS)
    return tm[3], tm[4], tm[5]


# =========================================================
# SENSOR ULTRASSONICO E NIVEL DE RACAO
# =========================================================
ultima_leitura_sensor_ms = 0
ultima_distancia_cm = None
estado_nivel_racao = "inicializando"  # ok, baixo, vazio ou erro
ultimo_aviso_sensor = None
estado_candidato_sensor = None
contagem_candidato_sensor = 0
contagem_leituras_invalidas = 0
MAX_LEITURAS_INVALIDAS_ERRO = 5
ultimo_estado_alerta_saida = "inicializando"


def medir_distancia():
    """Retorna a distancia em cm ou None quando nao ha eco valido."""
    # Mesmo pulso do teste original do sensor: 20 microssegundos.
    TRIG.value(0)
    time.sleep_us(2)
    TRIG.value(1)
    time.sleep_us(20)
    TRIG.value(0)

    tempo = time_pulse_us(ECHO, 1, 30000)
    if tempo < 0:
        return None

    distancia_cm = tempo / 58.0
    if distancia_cm < DISTANCIA_MIN_CM or distancia_cm > DISTANCIA_MAX_CM:
        return None

    return distancia_cm


def avisar_estado_racao(estado, distancia=None):
    """Avisa quando muda o estado confirmado do reservatorio."""
    global ultimo_aviso_sensor

    if estado == ultimo_aviso_sensor:
        return
    ultimo_aviso_sensor = estado

    if estado == "baixo":
        print("AVISO: racao acabando. Alimentacao continua liberada.")
        oled.fill(0)
        oled.text("RACAO ACABANDO", 4, 5)
        oled.text("Alimentacao OK", 8, 24)
        if distancia is not None:
            oled.text("Dist: {:.1f} cm".format(distancia), 12, 44)
        oled.show()

    elif estado == "vazio":
        print("BLOQUEIO: reservatorio aparentemente vazio; motor bloqueado.")
        oled.fill(0)
        oled.text("RACAO MUITO", 16, 5)
        oled.text("BAIXA / VAZIO", 16, 19)
        oled.text("Reabasteca", 24, 39)
        if distancia is not None:
            oled.text("Dist: {:.1f} cm".format(distancia), 12, 52)
        oled.show()

    elif estado == "erro":
        print("AVISO: sensor sem leitura valida. Automatico bloqueado; manual liberado com cautela.")
        emitir_bip(400)
        oled.fill(0)
        oled.text("ERRO SENSOR", 20, 8)
        oled.text("Confira ligacao", 4, 26)
        oled.text("Manual c/ cuidado", 0, 44)
        oled.show()

    elif estado == "ok":
        print("Nivel de racao suficiente.")


def atualizar_alertas_nivel():
    """Mantem LED continuo no nivel baixo e buzzer continuo no nivel vazio."""
    global ultimo_estado_alerta_saida

    if estado_nivel_racao == "vazio":
        led.value(1)
        buzzer.freq(2000)
        buzzer.duty_u16(32768)
    elif estado_nivel_racao == "baixo":
        # Nivel baixo: LED aceso continuamente; alimentacao continua liberada.
        led.value(1)
        buzzer.duty_u16(0)
    else:
        # Ao sair de baixo/vazio, remove o alerta. Em funcionamento normal,
        # o controle de alimentacao volta a comandar LED e buzzer.
        if ultimo_estado_alerta_saida in ("baixo", "vazio"):
            led.value(0)
            buzzer.duty_u16(0)

    ultimo_estado_alerta_saida = estado_nivel_racao


def classificar_distancia(distancia, estado_atual):
    """Classifica nivel com histerese sem saltar de vazio direto para ok.

    Distancia maior significa menos racao. Ao sair do estado vazio, a leitura
    e reclassificada tambem pelo limite de nivel baixo: uma distancia como
    17,7 cm deve virar "baixo", nao "ok", quando o limite de vazio e 20 cm.
    """
    if distancia is None:
        return estado_atual

    limite_vazio_saida = DISTANCIA_RACAO_VAZIA_CM - HISTERese_CM
    limite_baixo_saida = DISTANCIA_RACAO_BAIXA_CM - HISTERese_CM

    # Mantem o estado vazio ate cruzar o limite inferior de histerese.
    if estado_atual == "vazio" and distancia >= limite_vazio_saida:
        return "vazio"

    # Entrada em vazio exige cruzar o limite superior.
    if estado_atual != "vazio" and distancia >= DISTANCIA_RACAO_VAZIA_CM:
        return "vazio"

    # Ao sair de vazio, ou estando em baixo, usa a faixa de histerese
    # de baixo. Assim, 17,7 cm nao pode ser classificado como "ok".
    if estado_atual == "baixo":
        if distancia >= limite_baixo_saida:
            return "baixo"
    elif distancia >= DISTANCIA_RACAO_BAIXA_CM:
        return "baixo"

    return "ok"


def atualizar_nivel_racao(forcar=False):
    """Confirma mudancas somente apos 3 leituras consecutivas do mesmo estado."""
    global ultima_leitura_sensor_ms, ultima_distancia_cm, estado_nivel_racao
    global estado_candidato_sensor, contagem_candidato_sensor
    global contagem_leituras_invalidas

    agora_ms = time.ticks_ms()
    if (not forcar and
            time.ticks_diff(agora_ms, ultima_leitura_sensor_ms) < INTERVALO_LEITURA_SENSOR_MS):
        return estado_nivel_racao

    ultima_leitura_sensor_ms = agora_ms
    distancia = medir_distancia()
    ultima_distancia_cm = distancia

    if distancia is None:
        contagem_leituras_invalidas += 1
        print("Leitura invalida ({}/{} consecutivas). Estado mantido: {}".format(
            contagem_leituras_invalidas, MAX_LEITURAS_INVALIDAS_ERRO, estado_nivel_racao))
        # Nao muda um nivel ja conhecido por causa de falha pontual de eco.
        # So sinaliza erro apos varias falhas consecutivas.
        if contagem_leituras_invalidas >= MAX_LEITURAS_INVALIDAS_ERRO and estado_nivel_racao != "erro":
            estado_nivel_racao = "erro"
            estado_candidato_sensor = None
            contagem_candidato_sensor = 0
            avisar_estado_racao("erro", None)
        return estado_nivel_racao

    # Qualquer distancia valida zera a sequencia de falhas do sensor.
    contagem_leituras_invalidas = 0
    candidato = classificar_distancia(distancia, estado_nivel_racao)

    if candidato == estado_candidato_sensor:
        # A contagem nao deve crescer indefinidamente depois de confirmar
        # tres leituras consecutivas. Mantem o indicador limitado a 3/3.
        contagem_candidato_sensor = min(
            contagem_candidato_sensor + 1,
            LEITURAS_CONSECUTIVAS_CONFIRMACAO
        )
    else:
        estado_candidato_sensor = candidato
        contagem_candidato_sensor = 1

    if (contagem_candidato_sensor >= LEITURAS_CONSECUTIVAS_CONFIRMACAO
            and candidato != estado_nivel_racao):
        estado_nivel_racao = candidato
        avisar_estado_racao(candidato, distancia)

    print("Distancia da racao: {:.1f} cm | Estado confirmado: {} | candidato: {} ({}/{})".format(
        distancia, estado_nivel_racao, candidato, contagem_candidato_sensor,
        LEITURAS_CONSECUTIVAS_CONFIRMACAO))

    return estado_nivel_racao


def nivel_racao_permite_alimentacao():
    """Automatico pode operar com nivel ok ou baixo; bloqueia vazio/erro."""
    return estado_nivel_racao in ("ok", "baixo")


# =========================================================
# ALIMENTACAO COM CONTROLE ANGULAR
# =========================================================
# Automatico: avanca 1, 2 ou 3 camaras (120 graus cada).
# Manual: gira continuamente enquanto o botao estiver pressionado;
# ao soltar, para imediatamente, sem retorno.

estado_auto = "inativo"
inicio_estado_auto = 0
porcoes_alvo_auto = 0
angulo_acumulado_auto = 0.0
ultimo_angulo_auto = None
ultima_leitura_mag_auto = 0
falhas_leitura_mag_auto = 0
inicio_movimento_auto = 0

alimentacao_manual_ativa = False
ultimo_angulo_manual = None
angulo_acumulado_manual = 0.0
ultima_leitura_mag_manual = 0
falhas_leitura_mag_manual = 0

fila_alimentacoes = []
ultima_execucao_por_refeicao = {}


def atualizar_medicao_angular(modo):
    """Atualiza deslocamento angular acumulado durante a rotacao.

    O angulo do HMC5883L e uma direcao de campo magnetico, nao uma medida
    mecanica garantida. A conversao so e valida apos calibrar a montagem.
    """
    global ultimo_angulo_auto, angulo_acumulado_auto, ultima_leitura_mag_auto
    global ultimo_angulo_manual, angulo_acumulado_manual, ultima_leitura_mag_manual
    global falhas_leitura_mag_auto, falhas_leitura_mag_manual

    agora = time.ticks_ms()
    if modo == "auto":
        if time.ticks_diff(agora, ultima_leitura_mag_auto) < INTERVALO_LEITURA_MAG_MS:
            return angulo_acumulado_auto
        ultima_leitura_mag_auto = agora
        anterior = ultimo_angulo_auto
    else:
        if time.ticks_diff(agora, ultima_leitura_mag_manual) < INTERVALO_LEITURA_MAG_MS:
            return angulo_acumulado_manual
        ultima_leitura_mag_manual = agora
        anterior = ultimo_angulo_manual

    try:
        atual = ler_angulo_magnetometro()
    except Exception as erro:
        if modo == "auto":
            falhas_leitura_mag_auto += 1
            print("Falha HMC5883L no automatico:", erro)
        else:
            falhas_leitura_mag_manual += 1
            print("Falha HMC5883L no manual:", erro)
        return angulo_acumulado_auto if modo == "auto" else angulo_acumulado_manual

    if anterior is None:
        if modo == "auto":
            ultimo_angulo_auto = atual
        else:
            ultimo_angulo_manual = atual
        return 0.0

    delta = diferenca_angular(atual, anterior) * SINAL_ROTACAO_SENSOR

    # Atualiza a referencia mesmo quando o delta e descartado, evitando
    # que um pico isolado contamine as leituras seguintes.
    if modo == "auto":
        ultimo_angulo_auto = atual
        falhas_leitura_mag_auto = 0
    else:
        ultimo_angulo_manual = atual
        falhas_leitura_mag_manual = 0

    if abs(delta) > MAX_VARIACAO_LEITURA_GRAUS:
        print("Salto magnetico descartado: {:.1f} graus".format(delta))
        return angulo_acumulado_auto if modo == "auto" else angulo_acumulado_manual

    # O disco deve girar em um unico sentido. Pequenas variacoes negativas
    # podem ocorrer por ruido; nao sao somadas ao deslocamento.
    if delta > 0:
        if modo == "auto":
            angulo_acumulado_auto += delta
            return angulo_acumulado_auto
        angulo_acumulado_manual += delta
        return angulo_acumulado_manual

    return angulo_acumulado_auto if modo == "auto" else angulo_acumulado_manual


def iniciar_mecanismo_alimentacao(numero_porcoes):
    global estado_auto, inicio_estado_auto, porcoes_alvo_auto
    global angulo_acumulado_auto, ultimo_angulo_auto
    global ultima_leitura_mag_auto, falhas_leitura_mag_auto
    global inicio_movimento_auto

    if estado_auto != "inativo" or alimentacao_manual_ativa:
        return False

    if numero_porcoes not in (1, 2, 3):
        print("Quantidade de porcoes invalida:", numero_porcoes)
        return False

    try:
        ultimo_angulo_auto = ler_angulo_magnetometro()
    except Exception as erro:
        print("Alimentacao automatica bloqueada: falha no HMC5883L:", erro)
        emitir_bip(500)
        return False

    angulo_acumulado_auto = 0.0
    ultima_leitura_mag_auto = time.ticks_ms()
    inicio_movimento_auto = 0
    falhas_leitura_mag_auto = 0
    porcoes_alvo_auto = numero_porcoes

    buzzer.freq(2000)
    buzzer.duty_u16(32768)
    inicio_estado_auto = time.ticks_ms()
    estado_auto = "bipe1"
    print("Alimentacao automatica iniciada:", numero_porcoes,
          "camara(s); alvo:", numero_porcoes * ANGULO_POR_CAMARA, "graus")
    return True


def finalizar_alimentacao_automatica():
    global estado_auto, inicio_estado_auto
    parar_motor()
    led.value(0)
    buzzer.freq(2000)
    buzzer.duty_u16(32768)
    inicio_estado_auto = time.ticks_ms()
    estado_auto = "bipe_final"
    print("Deslocamento automatico concluido:",
          round(angulo_acumulado_auto, 1), "graus")


def atualizar_mecanismo_alimentacao():
    global estado_auto, inicio_estado_auto
    global alimentacao_manual_ativa
    global ultimo_angulo_auto, ultima_leitura_mag_auto, angulo_acumulado_auto
    global inicio_movimento_auto

    agora = time.ticks_ms()

    if estado_auto == "inativo":
        if alimentacao_manual_ativa:
            atualizar_medicao_angular("manual")
            led.value(1)
        else:
            parar_motor()
        return

    decorrido_estado = time.ticks_diff(agora, inicio_estado_auto)

    if estado_auto == "bipe1":
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
            try:
                # Atualiza a referencia imediatamente antes de ligar o motor.
                ultimo_angulo_auto = ler_angulo_magnetometro()
                angulo_acumulado_auto = 0.0
                ultima_leitura_mag_auto = agora
                motor_horario()
                inicio_movimento_auto = agora
                estado_auto = "girando"
                led.value(1)
            except Exception as erro:
                print("Nao foi possivel iniciar movimento: ", erro)
                parar_motor()
                buzzer.duty_u16(0)
                estado_auto = "inativo"

    elif estado_auto == "girando":
        deslocamento = atualizar_medicao_angular("auto")
        alvo = porcoes_alvo_auto * ANGULO_POR_CAMARA
        led.value(1 if (time.ticks_ms() // 200) % 2 == 0 else 0)

        if deslocamento >= alvo:
            finalizar_alimentacao_automatica()
        elif falhas_leitura_mag_auto >= 10:
            print("ERRO: leituras magneticas insuficientes; motor parado por seguranca.")
            parar_motor()
            led.value(0)
            buzzer.duty_u16(0)
            estado_auto = "inativo"
        elif time.ticks_diff(agora, inicio_movimento_auto) >= TEMPO_MAXIMO_ROTACAO_AUTO_MS:
            print("ERRO: tempo maximo de rotacao excedido; motor parado por seguranca.")
            parar_motor()
            led.value(0)
            buzzer.duty_u16(0)
            estado_auto = "inativo"

    elif estado_auto == "bipe_final":
        if decorrido_estado >= 200:
            buzzer.duty_u16(0)
            parar_motor()
            led.value(0)
            estado_auto = "inativo"
            print("Alimentacao automatica concluida.")


def acionar_manual(ligado):
    global alimentacao_manual_ativa
    global ultimo_angulo_manual, angulo_acumulado_manual
    global ultima_leitura_mag_manual, falhas_leitura_mag_manual

    if ligado:
        if alimentacao_manual_ativa:
            return False
        if estado_auto != "inativo":
            print("Modo manual bloqueado: alimentacao automatica em andamento.")
            return False

        estado_sensor = atualizar_nivel_racao(forcar=True)
        if estado_sensor == "vazio":
            print("Alimentacao manual bloqueada: reservatorio confirmado como vazio.")
            emitir_bip(500)
            return False
        if estado_sensor == "erro":
            print("ATENCAO: sensor sem leitura valida; liberando modo manual com cautela.")
        elif estado_sensor == "baixo":
            print("ATENCAO: racao acabando; modo manual permitido.")

        try:
            ultimo_angulo_manual = ler_angulo_magnetometro()
        except Exception as erro:
            print("Acionamento manual bloqueado: falha no HMC5883L:", erro)
            emitir_bip(500)
            return False

        angulo_acumulado_manual = 0.0
        ultima_leitura_mag_manual = time.ticks_ms()
        falhas_leitura_mag_manual = 0
        alimentacao_manual_ativa = True
        emitir_bip()
        motor_horario()
        led.value(1)
        print("Alimentacao manual iniciada. Gira enquanto o botao estiver pressionado.")
        return True

    # Soltar o botao interrompe imediatamente o motor. Nao ha retorno.
    if not alimentacao_manual_ativa:
        return False

    parar_motor()
    led.value(0)
    alimentacao_manual_ativa = False
    emitir_bip()
    print("Alimentacao manual encerrada. Deslocamento medido:",
          round(angulo_acumulado_manual, 1), "graus. Sem retorno.")
    return True


def verificar_alimentacao():
    # Atualiza motor, posicao angular e nivel do reservatorio sem esperas longas.
    atualizar_mecanismo_alimentacao()
    atualizar_nivel_racao()
    atualizar_alertas_nivel()

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

        if not nivel_racao_permite_alimentacao():
            print("Refeicao {} ignorada: reservatorio vazio ou sensor sem leitura valida.".format(refeicao))
            ultima_execucao_por_refeicao[refeicao] = identificador
            continue

        qtd = getattr(menu, "quantidade_atual", "Medio")
        numero_porcoes = PORCOES_POR_QUANTIDADE.get(qtd, 2)

        fila_alimentacoes.append((
            refeicao, numero_porcoes, data_atual,
            hora_prog, minuto_prog, versao
        ))
        ultima_execucao_por_refeicao[refeicao] = identificador
        print("Refeicao agendada:", refeicao, "{:02d}:{:02d}".format(
            hora_prog, minuto_prog), "| porcoes:", numero_porcoes)

    # Comeca a proxima tarefa valida quando o motor estiver livre.
    while estado_auto == "inativo" and not alimentacao_manual_ativa and fila_alimentacoes:
        (refeicao, numero_porcoes, data_ref, hora_fila,
         minuto_fila, versao_fila) = fila_alimentacoes.pop(0)

        if data_ref != data_atual:
            continue
        if getattr(menu, "versoes_horario", {}).get(refeicao, 0) != versao_fila:
            continue
        if tuple(horarios[refeicao]) != (hora_fila, minuto_fila):
            continue
        if not nivel_racao_permite_alimentacao():
            print("Refeicao {} cancelada: reservatorio vazio ou sensor sem leitura valida.".format(refeicao))
            continue

        print("Motor CC:", refeicao, "| camaras:", numero_porcoes,
              "| angulo alvo:", numero_porcoes * ANGULO_POR_CAMARA)
        iniciar_mecanismo_alimentacao(numero_porcoes)
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

except KeyboardInterrupt:
    print("Programa interrompido pelo usuario.")
    oled.fill(0)
    oled.show()

finally:
    parar_motor()
    led.value(0)
    buzzer.duty_u16(0)
    print("Motor e buzzer desligados.")
