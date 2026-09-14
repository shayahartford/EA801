from machine import Pin, ADC, SoftI2C
from ssd1306 import SSD1306_I2C
import time

# 1. Configuração do Display OLED (SSD1306) via SoftI2C[cite: 2]
i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=400000)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# 2. Configuração dos Botões A e B (Horas e Minutos)[cite: 1, 2]
btn_a = Pin(5, Pin.IN, Pin.PULL_UP)  # Incrementa Horas[cite: 2]
btn_b = Pin(6, Pin.IN, Pin.PULL_UP)  # Incrementa Minutos[cite: 2]

# 3. Configuração do Thumbstick / Joystick (Navegação)[cite: 2]
joy_y = ADC(26)                       # Eixo Y no pino analógico GPIO 26[cite: 2]
joy_sw = Pin(22, Pin.IN, Pin.PULL_UP) # Botão integrado do Joystick no GPIO 22[cite: 2]

# 4. Estrutura dos Horários de Alimentação
horarios = {
    "Cafe": [7, 0],
    "Almoco": [12, 0],
    "Jantar": [19, 0]
}

# 0 = Modo Monitor | 1 = Editando Café | 2 = Editando Almoço | 3 = Editando Jantar
modo_edicao = 0  
chaves = ["Cafe", "Almoco", "Jantar"]

def ler_botao(pino):
    """Lê o estado de um botão digital com filtro de debounce."""
    if pino.value() == 0:
        time.sleep_ms(150)
        return True
    return False

def ler_joystick_y():
    """Lê a posição vertical do thumbstick para navegação."""
    valor = joy_y.read_u16()
    # Pressionar para CIMA ou para BAIXO altera o índice selecionado
    if valor < 15000:
        time.sleep_ms(200)
        return "CIMA"
    elif valor > 50000:
        time.sleep_ms(200)
        return "BAIXO"
    return None

def atualizar_display():
    """Renderiza a interface visual no display OLED."""
    oled.fill(0)
    
    if modo_edicao == 0:
        oled.text("MODO MONITOR", 16, 0)
    else:
        oled.text("EDITANDO HORARIO", 0, 0)
    
    oled.hline(0, 10, 128, 1)
    
    y = 16
    for idx, chave in enumerate(chaves):
        h, m = horarios[chave]
        indicador = ">" if modo_edicao == (idx + 1) else " "
        oled.text(f"{indicador}{chave}: {h:02d}:{m:02d}", 0, y)
        y += 14

    oled.hline(0, 54, 128, 1)
    
    if modo_edicao == 0:
        oled.text("Joy: Mover Selecao", 0, 56)
    else:
        oled.text("A:+H | B:+M | Joy:Mover", 0, 56)
        
    oled.show()

atualizar_display()

while True:
    # Navegação entre os horários utilizando o Thumbstick (Eixo Y ou Botão do Joystick)[cite: 1, 2]
    direcao = ler_joystick_y()
    if direcao == "BAIXO":
        modo_edicao = (modo_edicao + 1) % 4
        atualizar_display()
    elif direcao == "CIMA":
        modo_edicao = (modo_edicao - 1) % 4
        atualizar_display()
    elif ler_botao(joy_sw):
        modo_edicao = (modo_edicao + 1) % 4
        atualizar_display()

    # Ajuste dos valores de Horas e Minutos usando os botões A e B[cite: 1]
    if modo_edicao > 0:
        chave_atual = chaves[modo_edicao - 1]
        
        if ler_botao(btn_a):
            horarios[chave_atual][0] = (horarios[chave_atual][0] + 1) % 24
            atualizar_display()
            
        if ler_botao(btn_b):
            horarios[chave_atual][1] = (horarios[chave_atual][1] + 1) % 60
            atualizar_display()

    time.sleep_ms(20)