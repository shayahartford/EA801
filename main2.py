from machine import Pin, SoftI2C, ADC
from ssd1306 import SSD1306_I2C
import time

# 1. Configuração do Display OLED (SSD1306 via SoftI2C)[cite: 2]
i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=400000)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# 2. Configuração dos Botões A, B e C[cite: 2]
btn_a = Pin(5, Pin.IN, Pin.PULL_UP)   # Incrementa Horas[cite: 2]
btn_b = Pin(6, Pin.IN, Pin.PULL_UP)   # Incrementa Minutos[cite: 2]
btn_c = Pin(10, Pin.IN, Pin.PULL_UP)  # Reservado / Auxiliar[cite: 2]

# 3. Configuração do Joystick KY023 (Orientação validada da BitDogLab V7)[cite: 2]
adc_y = ADC(Pin(26))                  # Eixo Y (VRy) no GPIO 26[cite: 2]
btn_sw = Pin(22, Pin.IN, Pin.PULL_UP) # Botão do Joystick no GPIO 22[cite: 2]
JOY_INVERT_Y = False                  # Ajuste de sentido vertical do Joystick[cite: 2]

def ler_joystick_y():
    """Retorna -1 para cima, 1 para baixo e 0 para neutro."""
    valor = adc_y.read_u16()
    if JOY_INVERT_Y:
        valor = 65535 - valor
    if valor < 20000:
        return -1
    if valor > 45000:
        return 1
    return 0

def ler_botao(pino):
    """Leitura de botão digital com debouncing."""
    if pino.value() == 0:
        time.sleep_ms(150)
        return True
    return False

# ---------- Variáveis Globais de Estado ----------
horarios = {"Cafe": [7, 0], "Almoco": [12, 0], "Jantar": [19, 0]}
chaves_refeicao = ["Cafe", "Almoco", "Jantar"]
quantidade_atual = "Medio"  # Valor padrão inicial ("Pouco", "Medio", "Muito")[cite: 1]

# ---------- Tela: Refeição ----------
def atualizar_display_refeicao(selecionado):
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

def tela_refeicao():
    selecionado = 0
    ultimo_movimento = time.ticks_ms()
    atualizar_display_refeicao(selecionado)

    while True:
        # Navegação pelos horários com o Joystick
        direcao = ler_joystick_y()
        agora = time.ticks_ms()
        if direcao != 0 and time.ticks_diff(agora, ultimo_movimento) > 250:
            selecionado = (selecionado + direcao) % len(chaves_refeicao)
            ultimo_movimento = agora
            atualizar_display_refeicao(selecionado)

        chave_atual = chaves_refeicao[selecionado]

        # Botão A: Incrementa Horas[cite: 1, 2]
        if ler_botao(btn_a):
            horarios[chave_atual][0] = (horarios[chave_atual][0] + 1) % 24
            atualizar_display_refeicao(selecionado)

        # Botão B: Incrementa Minutos[cite: 1, 2]
        if ler_botao(btn_b):
            horarios[chave_atual][1] = (horarios[chave_atual][1] + 1) % 60
            atualizar_display_refeicao(selecionado)

        # Botão SW do Joystick: Retorna ao Menu Principal[cite: 2]
        if ler_botao(btn_sw):
            return

        time.sleep_ms(20)

# ---------- Tela: Quantidade ----------
def atualizar_display_quantidade(selecionado):
    oled.fill(0)
    oled.text("QUANTIDADE RACAO", 0, 0)
    oled.hline(0, 10, 128, 1)

    opcoes_qtd = ["Pouco", "Medio", "Muito"]
    y = 16
    for idx, opcao in enumerate(opcoes_qtd):
        indicador = ">" if idx == selecionado else " "
        marcador = "[*]" if opcao == quantidade_atual else "[ ]"
        oled.text(f"{indicador}{opcao:<7} {marcador}", 10, y)
        y += 13

    oled.hline(0, 54, 128, 1)
    oled.text("SW: Salvar/Sair", 4, 56)
    oled.show()

def tela_quantidade():
    global quantidade_atual
    opcoes_qtd = ["Pouco", "Medio", "Muito"]
    
    # Inicia o cursor na opção salva atualmente
    try:
        selecionado = opcoes_qtd.index(quantidade_atual)
    except ValueError:
        selecionado = 1

    ultimo_movimento = time.ticks_ms()
    atualizar_display_quantidade(selecionado)

    while True:
        # Navegação com o Joystick (Eixo Y)[cite: 1, 2]
        direcao = ler_joystick_y()
        agora = time.ticks_ms()
        if direcao != 0 and time.ticks_diff(agora, ultimo_movimento) > 250:
            selecionado = (selecionado + direcao) % len(opcoes_qtd)
            ultimo_movimento = agora
            atualizar_display_quantidade(selecionado)

        # Pressionar o Joystick (SW) confirma a opção e volta ao Menu[cite: 1, 2]
        if ler_botao(btn_sw):
            quantidade_atual = opcoes_qtd[selecionado]
            return

        time.sleep_ms(20)

# ---------- Menu Principal ----------
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

# Executa o programa principal
menu_principal()