from machine import Pin, SoftI2C
from ssd1306 import SSD1306_I2C
import time

# 1. Inicialização do Display OLED SSD1306 via SoftI2C (Validado na BitDogLab V7)[cite: 2]
i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=400000) #[cite: 2]
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C) #[cite: 2]

# 2. Configuração dos Botões (Com Pull-Up interno)[cite: 2]
btn_a = Pin(5, Pin.IN, Pin.PULL_UP)   # Botão A: Incrementa Horas[cite: 2]
btn_b = Pin(6, Pin.IN, Pin.PULL_UP)   # Botão B: Incrementa Minutos[cite: 2]
btn_c = Pin(10, Pin.IN, Pin.PULL_UP)  # Botão C: Alterna modo de edição[cite: 2]

# 3. Estrutura de Horários de Alimentação
horarios = {
    "Cafe": [7, 0],
    "Almoco": [12, 0],
    "Jantar": [19, 0]
}

# 0 = Modo Normal / Monitoramento
# 1 = Editando Café | 2 = Editando Almoço | 3 = Editando Jantar
modo_edicao = 0  
chaves = ["Cafe", "Almoco", "Jantar"]

def ler_botao(pino):
    """Lê o estado do botão com filtro de debouncing."""
    if pino.value() == 0:
        time.sleep_ms(150)
        return True
    return False

def atualizar_display():
    """Desenha a interface gráfica no display OLED SSD1306 (128x64)."""
    oled.fill(0)
    
    # Cabeçalho
    if modo_edicao == 0:
        oled.text("MODO MONITOR", 16, 0)
    else:
        oled.text("EDITANDO HORARIO", 0, 0)
    
    oled.hline(0, 10, 128, 1)
    
    # Exibição dos 3 horários no display 128x64[cite: 1]
    y = 16
    for idx, chave in enumerate(chaves):
        h, m = horarios[chave]
        # Adiciona uma seta '>' para indicar o item selecionado
        indicador = ">" if modo_edicao == (idx + 1) else " "
        oled.text(f"{indicador}{chave}: {h:02d}:{m:02d}", 0, y)
        y += 14

    oled.hline(0, 54, 128, 1)
    
    # Dica do botão C
    if modo_edicao == 0:
        oled.text("BtnC: Editar", 16, 56)
    else:
        oled.text("A:+H | B:+M | C:Prox", 0, 56)
        
    oled.show()

# Teste inicial do display
atualizar_display()

# Para verificar o funcionamento do código, rode o loop principal abaixo
while True:
    # Botão C: Troca de modo (Monitor -> Café -> Almoço -> Jantar -> Monitor)[cite: 1]
    if ler_botao(btn_c):
        modo_edicao = (modo_edicao + 1) % 4
        atualizar_display()

    # Modos de edição (1, 2 ou 3)
    if modo_edicao > 0:
        chave_atual = chaves[modo_edicao - 1]
        
        # Botão A: Incrementa a hora (00-23)[cite: 1]
        if ler_botao(btn_a):
            horarios[chave_atual][0] = (horarios[chave_atual][0] + 1) % 24
            atualizar_display()
            
        # Botão B: Incrementa os minutos (00-59)[cite: 1]
        if ler_botao(btn_b):
            horarios[chave_atual][1] = (horarios[chave_atual][1] + 1) % 60
            atualizar_display()

    time.sleep_ms(20)