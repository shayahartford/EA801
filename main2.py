from machine import Pin, SoftI2C, ADC
from ssd1306 import SSD1306_I2C
import time

# Display
i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=400000)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Botões
btn_a = Pin(5, Pin.IN, Pin.PULL_UP)
btn_b = Pin(6, Pin.IN, Pin.PULL_UP)
btn_c = Pin(10, Pin.IN, Pin.PULL_UP)

# Joystick KY023 (orientação validada na BitDogLab V7: invertido no eixo Y)
adc_y = ADC(Pin(26))   # VRy
btn_sw = Pin(22, Pin.IN, Pin.PULL_UP)
JOY_INVERT_Y = True

def ler_joystick_y():
    """-1 = cima, 1 = baixo, 0 = neutro."""
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

# ---------- Tela: Refeicao ----------
horarios = {"Cafe": [7, 0], "Almoco": [12, 0], "Jantar": [19, 0]}
chaves = ["Cafe", "Almoco", "Jantar"]

def atualizar_display_refeicao(modo_edicao):
    oled.fill(0)
    oled.text("MODO MONITOR" if modo_edicao == 0 else "EDITANDO HORARIO", 0, 0)
    oled.hline(0, 10, 128, 1)
    y = 16
    for idx, chave in enumerate(chaves):
        h, m = horarios[chave]
        indicador = ">" if modo_edicao == (idx + 1) else " "
        oled.text(f"{indicador}{chave}: {h:02d}:{m:02d}", 0, y)
        y += 14
    oled.hline(0, 54, 128, 1)
    oled.text("BtnC:Edit SW:Sair" if modo_edicao == 0 else "A:+H | B:+M | C:Prox", 0, 56)
    oled.show()

def tela_refeicao():
    modo_edicao = 0
    atualizar_display_refeicao(modo_edicao)
    while True:
        if ler_botao(btn_c):
            modo_edicao = (modo_edicao + 1) % 4
            atualizar_display_refeicao(modo_edicao)

        if modo_edicao > 0:
            chave_atual = chaves[modo_edicao - 1]
            if ler_botao(btn_a):
                horarios[chave_atual][0] = (horarios[chave_atual][0] + 1) % 24
                atualizar_display_refeicao(modo_edicao)
            if ler_botao(btn_b):
                horarios[chave_atual][1] = (horarios[chave_atual][1] + 1) % 60
                atualizar_display_refeicao(modo_edicao)

        if modo_edicao == 0 and ler_botao(btn_sw):
            return  # volta ao menu principal

        time.sleep_ms(20)

# ---------- Tela: Quantidade ----------
def tela_quantidade():
    oled.fill(0)
    oled.text("QUANTIDADE", 20, 0)
    oled.hline(0, 10, 128, 1)
    oled.text("Em construcao...", 4, 28)
    oled.text("SW: voltar", 20, 56)
    oled.show()
    while True:
        if ler_botao(btn_sw):
            return
        time.sleep_ms(20)

# ---------- Menu principal ----------
def menu_principal():
    opcoes = ["Refeicao", "Quantidade"]
    selecionado = 0
    ultimo_movimento = time.ticks_ms()

    while True:
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
                tela_refeicao()
            else:
                tela_quantidade()

        time.sleep_ms(20)

menu_principal()
