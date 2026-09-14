from machine import Pin, SoftI2C, ADC
from ssd1306 import SSD1306_I2C
import time

# Display OLED SSD1306 (SoftI2C no GPIO 2 e 3)[cite: 2]
i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=400000)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Botões A, B e C[cite: 2]
btn_a = Pin(5, Pin.IN, Pin.PULL_UP)
btn_b = Pin(6, Pin.IN, Pin.PULL_UP)
btn_c = Pin(10, Pin.IN, Pin.PULL_UP)

# Joystick KY023[cite: 2]
adc_y = ADC(Pin(26)) #[cite: 2]
btn_sw = Pin(22, Pin.IN, Pin.PULL_UP)
JOY_INVERT_Y = False #[cite: 2]

# Dados compartilhados de horários e quantidade[cite: 1]
horarios = {"Cafe": [7, 0], "Almoco": [12, 0], "Jantar": [19, 0]}
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

def tela_refeicao(callback_verificacao=None):
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
            h, m = horarios[chave]
            indicador = ">" if idx == selecionado else " "
            oled.text(f"{indicador}{chave}: {h:02d}:{m:02d}", 0, y)
            y += 14
        oled.hline(0, 54, 128, 1)
        oled.text("A:+H B:+M SW:Sair", 0, 56)
        oled.show()

        direcao = ler_joystick_y()
        agora = time.ticks_ms()
        if direcao != 0 and time.ticks_diff(agora, ultimo_movimento) > 250:
            selecionado = (selecionado + direcao) % len(chaves_refeicao)
            ultimo_movimento = agora

        chave_atual = chaves_refeicao[selecionado]
        if ler_botao(btn_a):
            horarios[chave_atual][0] = (horarios[chave_atual][0] + 1) % 24
        if ler_botao(btn_b):
            horarios[chave_atual][1] = (horarios[chave_atual][1] + 1) % 60
        if ler_botao(btn_sw):
            return

        time.sleep_ms(20)

def tela_quantidade(callback_verificacao=None):
    global quantidade_atual
    opcoes_qtd = ["Pouco", "Medio", "Muito"]
    selecionado = opcoes_qtd.index(quantidade_atual) if quantidade_atual in opcoes_qtd else 1
    ultimo_movimento = time.ticks_ms()

    while True:
        if callback_verificacao:
            callback_verificacao()

        oled.fill(0)
        oled.text("QUANTIDADE RACAO", 0, 0)
        oled.hline(0, 10, 128, 1)
        y = 16
        for idx, opcao in enumerate(opcoes_qtd):
            indicador = ">" if idx == selecionado else " "
            marcador = "[*]" if opcao == quantidade_atual else "[ ]"
            oled.text(f"{indicador}{opcao:<7} {marcador}", 10, y)
            y += 13
        oled.hline(0, 54, 128, 1)
        oled.text("SW: Salvar/Sair", 4, 56)
        oled.show()

        direcao = ler_joystick_y()
        agora = time.ticks_ms()
        if direcao != 0 and time.ticks_diff(agora, ultimo_movimento) > 250:
            selecionado = (selecionado + direcao) % len(opcoes_qtd)
            ultimo_movimento = agora

        if ler_botao(btn_sw):
            quantidade_atual = opcoes_qtd[selecionado]
            return

        time.sleep_ms(20)

def menu_principal(callback_verificacao=None):
    opcoes = ["Refeicao", "Quantidade"]
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
            oled.text(f"{indicador}{opcao}", 10, 24 + idx * 14)
        oled.show()

        direcao = ler_joystick_y()
        agora = time.ticks_ms()
        if direcao != 0 and time.ticks_diff(agora, ultimo_movimento) > 250:
            selecionado = (selecionado + direcao) % len(opcoes)
            ultimo_movimento = agora

        if ler_botao(btn_sw):
            if opcoes[selecionado] == "Refeicao":
                tela_refeicao(callback_verificacao)
            else:
                tela_quantidade(callback_verificacao)

        time.sleep_ms(20)