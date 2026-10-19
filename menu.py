from machine import Pin, SoftI2C, ADC
from ssd1306 import SSD1306_I2C
import time

# =========================================================
# DISPLAY OLED
# =========================================================

i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=400000)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# =========================================================
# BOTOES
# =========================================================

btn_a = Pin(5, Pin.IN, Pin.PULL_UP)
btn_b = Pin(6, Pin.IN, Pin.PULL_UP)
btn_c = Pin(10, Pin.IN, Pin.PULL_UP)

# =========================================================
# JOYSTICK
# =========================================================

adc_y = ADC(Pin(26))
btn_sw = Pin(22, Pin.IN, Pin.PULL_UP)
JOY_INVERT_Y = False

# =========================================================
# HORARIOS SALVOS E VERSOES
# =========================================================

horarios = {
    "Cafe": [7, 0],
    "Almoco": [12, 0],
    "Jantar": [19, 0],
}

versoes_horario = {
    "Cafe": 0,
    "Almoco": 0,
    "Jantar": 0,
}

horarios_edicao = {
    "Cafe": [7, 0],
    "Almoco": [12, 0],
    "Jantar": [19, 0],
}

chaves_refeicao = ["Cafe", "Almoco", "Jantar"]
quantidade_atual = "Medio"


def ler_joystick_y():
    valor = adc_y.read_u16()
    if JOY_INVERT_Y:
        valor = 65535 - valor
    if valor < 20000:
        return -1
    if valor > 45000:
        return 1
    return 0


def ler_botao(pino):
    if pino.value() == 0:
        time.sleep_ms(150)
        return True
    return False


# =========================================================
# EDICAO DOS HORARIOS
# A aumenta hora, B aumenta minuto, C salva, SW sai.
# =========================================================

def tela_refeicao(callback_verificacao=None):
    global horarios_edicao

    horarios_edicao = {
        chave: [horarios[chave][0], horarios[chave][1]]
        for chave in chaves_refeicao
    }

    selecionado = 0
    ultimo_movimento = time.ticks_ms()

    while True:
        if callback_verificacao:
            callback_verificacao()

        oled.fill(0)
        oled.text("EDITAR HORARIOS", 4, 0)
        oled.hline(0, 10, 128, 1)

        y = 16
        for idx, chave in enumerate(chaves_refeicao):
            h, m = horarios_edicao[chave]
            indicador = ">" if idx == selecionado else " "
            oled.text("{}{}: {:02d}:{:02d}".format(indicador, chave, h, m), 0, y)
            y += 12

        oled.hline(0, 54, 128, 1)
        oled.text("A:+H B:+M C:Salvar", 0, 56)
        oled.show()

        direcao = ler_joystick_y()
        agora = time.ticks_ms()
        if direcao != 0 and time.ticks_diff(agora, ultimo_movimento) > 250:
            selecionado = (selecionado + direcao) % len(chaves_refeicao)
            ultimo_movimento = agora

        chave_atual = chaves_refeicao[selecionado]

        if ler_botao(btn_a):
            horarios_edicao[chave_atual][0] = (horarios_edicao[chave_atual][0] + 1) % 24

        if ler_botao(btn_b):
            horarios_edicao[chave_atual][1] = (horarios_edicao[chave_atual][1] + 1) % 60

        if ler_botao(btn_c):
            for chave in chaves_refeicao:
                antigo = tuple(horarios[chave])
                novo = tuple(horarios_edicao[chave])
                if antigo != novo:
                    versoes_horario[chave] += 1
                horarios[chave][0] = novo[0]
                horarios[chave][1] = novo[1]
            print("Horarios salvos:", horarios)
            print("Versoes:", versoes_horario)

        if ler_botao(btn_sw):
            return

        time.sleep_ms(20)


# =========================================================
# CONFIGURACAO DA QUANTIDADE
# =========================================================

def tela_quantidade(callback_verificacao=None):
    global quantidade_atual

    opcoes = ["Pouco", "Medio", "Muito"]
    selecionado = opcoes.index(quantidade_atual) if quantidade_atual in opcoes else 1
    ultimo_movimento = time.ticks_ms()

    while True:
        if callback_verificacao:
            callback_verificacao()

        oled.fill(0)
        oled.text("QUANTIDADE RACAO", 0, 0)
        oled.hline(0, 10, 128, 1)

        for idx, opcao in enumerate(opcoes):
            indicador = ">" if idx == selecionado else " "
            marcador = "[*]" if opcao == quantidade_atual else "[ ]"
            oled.text("{}{:<7} {}".format(indicador, opcao, marcador), 8, 18 + idx * 12)

        oled.hline(0, 54, 128, 1)
        oled.text("SW: Salvar/Sair", 4, 56)
        oled.show()

        direcao = ler_joystick_y()
        agora = time.ticks_ms()
        if direcao != 0 and time.ticks_diff(agora, ultimo_movimento) > 250:
            selecionado = (selecionado + direcao) % len(opcoes)
            ultimo_movimento = agora

        if ler_botao(btn_sw):
            quantidade_atual = opcoes[selecionado]
            return

        time.sleep_ms(20)


# =========================================================
# MODO MANUAL
# A inicia, B para, SW volta.
# A verificacao automatica continua sendo chamada no loop.
# =========================================================

def tela_alimentacao_manual(callback_acionar_manual=None, callback_verificacao=None):
    alimentando = False

    while True:
        if callback_verificacao:
            callback_verificacao()

        if ler_botao(btn_a):
            if not alimentando and callback_acionar_manual:
                iniciou = callback_acionar_manual(True)
                if iniciou:
                    alimentando = True

        if ler_botao(btn_b):
            if alimentando and callback_acionar_manual:
                callback_acionar_manual(False)
                alimentando = False

        if ler_botao(btn_sw):
            if alimentando and callback_acionar_manual:
                callback_acionar_manual(False)
            return

        oled.fill(0)
        oled.text("MODO MANUAL", 25, 5)
        oled.hline(0, 18, 128, 1)

        if alimentando:
            oled.text("ALIMENTANDO", 18, 27)
            oled.text("B: PARAR", 30, 42)
        else:
            oled.text("A: INICIAR", 20, 27)
            oled.text("B: PARAR", 20, 40)

        oled.text("SW: VOLTAR", 15, 54)
        oled.show()
        time.sleep_ms(20)


# =========================================================
# MENU PRINCIPAL
# =========================================================

def menu_principal(callback_verificacao=None, callback_acionar_manual=None):
    opcoes = ["Refeicao", "Quantidade", "Manual"]
    selecionado = 0
    ultimo_movimento = time.ticks_ms()

    while True:
        if callback_verificacao:
            callback_verificacao()

        oled.fill(0)
        oled.text("MENU PRINCIPAL", 8, 0)
        oled.hline(0, 10, 128, 1)

        for idx, opcao in enumerate(opcoes):
            indicador = ">" if idx == selecionado else " "
            oled.text("{}{}".format(indicador, opcao), 5, 20 + idx * 13)

        oled.show()

        direcao = ler_joystick_y()
        agora = time.ticks_ms()
        if direcao != 0 and time.ticks_diff(agora, ultimo_movimento) > 250:
            selecionado = (selecionado + direcao) % len(opcoes)
            ultimo_movimento = agora

        if ler_botao(btn_sw):
            opcao_atual = opcoes[selecionado]

            if opcao_atual == "Refeicao":
                tela_refeicao(callback_verificacao)
            elif opcao_atual == "Quantidade":
                tela_quantidade(callback_verificacao)
            elif opcao_atual == "Manual":
                tela_alimentacao_manual(
                    callback_acionar_manual,
                    callback_verificacao
                )

        time.sleep_ms(20)
