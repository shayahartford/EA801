from machine import Pin, SoftI2C, ADC
from ssd1306 import SSD1306_I2C
import time


# =========================================================
# DISPLAY OLED
# =========================================================

i2c = SoftI2C(
    scl=Pin(3),
    sda=Pin(2),
    freq=400000
)

oled = SSD1306_I2C(
    128,
    64,
    i2c,
    addr=0x3C
)


# =========================================================
# BOTÕES
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
# HORÁRIOS SALVOS
# =========================================================

horarios = {
    "Cafe": [7, 0],
    "Almoco": [12, 0],
    "Jantar": [19, 0]
}


# =========================================================
# HORÁRIOS EM EDIÇÃO
# =========================================================
#
# Esses valores são temporários.
#
# A/B alteram somente este dicionário.
# C salva as alterações em "horarios".
#
# =========================================================

horarios_edicao = {
    "Cafe": [7, 0],
    "Almoco": [12, 0],
    "Jantar": [19, 0]
}


chaves_refeicao = [
    "Cafe",
    "Almoco",
    "Jantar"
]


# =========================================================
# QUANTIDADE
# =========================================================

quantidade_atual = "Medio"


# =========================================================
# LEITURA DO JOYSTICK
# =========================================================

def ler_joystick_y():

    valor = adc_y.read_u16()

    if JOY_INVERT_Y:
        valor = 65535 - valor

    if valor < 20000:
        return -1

    if valor > 45000:
        return 1

    return 0


# =========================================================
# LEITURA DOS BOTÕES
# =========================================================

def ler_botao(pino):

    if pino.value() == 0:

        time.sleep_ms(150)

        return True

    return False


# =========================================================
# TELA DE EDIÇÃO DOS HORÁRIOS
# =========================================================

def tela_refeicao(callback_verificacao=None):

    global horarios_edicao

    # -----------------------------------------------------
    # Cria cópia dos horários salvos
    # -----------------------------------------------------

    horarios_edicao = {
        chave: [
            horarios[chave][0],
            horarios[chave][1]
        ]

        for chave in chaves_refeicao
    }

    selecionado = 0

    ultimo_movimento = time.ticks_ms()


    while True:

        # -------------------------------------------------
        # Verifica alimentação automática
        # -------------------------------------------------

        if callback_verificacao:

            callback_verificacao()


        # -------------------------------------------------
        # DESENHA TELA
        # -------------------------------------------------

        oled.fill(0)

        oled.text(
            "EDITAR HORARIOS",
            4,
            0
        )

        oled.hline(
            0,
            10,
            128,
            1
        )


        y = 16

        for idx, chave in enumerate(
            chaves_refeicao
        ):

            h, m = horarios_edicao[chave]

            indicador = (
                ">"
                if idx == selecionado
                else " "
            )

            oled.text(
                f"{indicador}{chave}: {h:02d}:{m:02d}",
                0,
                y
            )

            y += 14


        oled.hline(
            0,
            54,
            128,
            1
        )

        oled.text(
            "A:+H B:+M C:Salvar",
            0,
            56
        )

        oled.show()


        # -------------------------------------------------
        # JOYSTICK
        # -------------------------------------------------

        direcao = ler_joystick_y()

        agora = time.ticks_ms()

        if (
            direcao != 0
            and
            time.ticks_diff(
                agora,
                ultimo_movimento
            ) > 250
        ):

            selecionado = (
                selecionado + direcao
            ) % len(chaves_refeicao)

            ultimo_movimento = agora


        chave_atual = (
            chaves_refeicao[selecionado]
        )


        # -------------------------------------------------
        # BOTÃO A = AUMENTA HORA
        # -------------------------------------------------

        if ler_botao(btn_a):

            horarios_edicao[
                chave_atual
            ][0] = (
                horarios_edicao[
                    chave_atual
                ][0] + 1
            ) % 24


        # -------------------------------------------------
        # BOTÃO B = AUMENTA MINUTO
        # -------------------------------------------------

        if ler_botao(btn_b):

            horarios_edicao[
                chave_atual
            ][1] = (
                horarios_edicao[
                    chave_atual
                ][1] + 1
            ) % 60


        # -------------------------------------------------
        # BOTÃO C = SALVAR
        # -------------------------------------------------

        if ler_botao(btn_c):

            for chave in chaves_refeicao:

                horarios[chave][0] = (
                    horarios_edicao[chave][0]
                )

                horarios[chave][1] = (
                    horarios_edicao[chave][1]
                )


            print(
                "Horários salvos:",
                horarios
            )


        # -------------------------------------------------
        # SW = SAIR
        #
        # Se não apertou C, as alterações são descartadas.
        # -------------------------------------------------

        if ler_botao(btn_sw):

            return


        time.sleep_ms(20)


# =========================================================
# TELA DE QUANTIDADE
# =========================================================

def tela_quantidade(
    callback_verificacao=None
):

    global quantidade_atual

    opcoes_qtd = [
        "Pouco",
        "Medio",
        "Muito"
    ]


    if quantidade_atual in opcoes_qtd:

        selecionado = (
            opcoes_qtd.index(
                quantidade_atual
            )
        )

    else:

        selecionado = 1


    ultimo_movimento = time.ticks_ms()


    while True:

        if callback_verificacao:

            callback_verificacao()


        # -------------------------------------------------
        # DESENHA TELA
        # -------------------------------------------------

        oled.fill(0)

        oled.text(
            "QUANTIDADE RACAO",
            0,
            0
        )

        oled.hline(
            0,
            10,
            128,
            1
        )


        y = 16

        for idx, opcao in enumerate(
            opcoes_qtd
        ):

            indicador = (
                ">"
                if idx == selecionado
                else " "
            )

            marcador = (
                "[*]"
                if opcao == quantidade_atual
                else "[ ]"
            )

            oled.text(
                f"{indicador}{opcao:<7} {marcador}",
                10,
                y
            )

            y += 13


        oled.hline(
            0,
            54,
            128,
            1
        )

        oled.text(
            "SW: Salvar/Sair",
            4,
            56
        )

        oled.show()


        # -------------------------------------------------
        # JOYSTICK
        # -------------------------------------------------

        direcao = ler_joystick_y()

        agora = time.ticks_ms()

        if (
            direcao != 0
            and
            time.ticks_diff(
                agora,
                ultimo_movimento
            ) > 250
        ):

            selecionado = (
                selecionado + direcao
            ) % len(opcoes_qtd)

            ultimo_movimento = agora


        # -------------------------------------------------
        # SW = SALVAR
        # -------------------------------------------------

        if ler_botao(btn_sw):

            quantidade_atual = (
                opcoes_qtd[selecionado]
            )

            return


        time.sleep_ms(20)


# =========================================================
# ACIONAMENTO MANUAL
# =========================================================
#
# O usuário controla diretamente o tempo.
#
# Primeiro SW:
#     inicia alimentação
#
# Segundo SW:
#     encerra alimentação
#
# =========================================================

def tela_alimentacao_manual(
    callback_acionar_manual=None
):

    # -----------------------------------------------------
    # Tela inicial
    # -----------------------------------------------------

    oled.fill(0)

    oled.text(
        "MODO MANUAL",
        25,
        5
    )

    oled.hline(
        0,
        18,
        128,
        1
    )

    oled.text(
        "A: INICIAR",
        20,
        30
    )

    oled.text(
        "B: PARAR",
        20,
        42
    )

    oled.text(
        "SW: VOLTAR",
        15,
        54
    )

    oled.show()


    # -----------------------------------------------------
    # Estado da alimentação manual
    # -----------------------------------------------------

    alimentando = False


    while True:

        # =================================================
        # A = INICIAR
        # =================================================

        if ler_botao(btn_a):

            if not alimentando:

                alimentando = True

                if callback_acionar_manual:

                    callback_acionar_manual(
                        True
                    )


        # =================================================
        # B = PARAR
        # =================================================

        if ler_botao(btn_b):

            if alimentando:

                alimentando = False

                if callback_acionar_manual:

                    callback_acionar_manual(
                        False
                    )


        # =================================================
        # SW = VOLTAR
        # =================================================

        if ler_botao(btn_sw):

            # ---------------------------------------------
            # Se ainda estiver alimentando, para primeiro
            # ---------------------------------------------

            if alimentando:

                alimentando = False

                if callback_acionar_manual:

                    callback_acionar_manual(
                        False
                    )

            return


        # =================================================
        # ATUALIZA DISPLAY
        # =================================================

        oled.fill(0)

        oled.text(
            "MODO MANUAL",
            25,
            5
        )

        oled.hline(
            0,
            18,
            128,
            1
        )


        if alimentando:

            oled.text(
                "ALIMENTANDO",
                18,
                27
            )

            oled.text(
                "B: PARAR",
                30,
                42
            )

            oled.text(
                "SW: VOLTAR",
                15,
                54
            )

        else:

            oled.text(
                "A: INICIAR",
                20,
                27
            )

            oled.text(
                "B: PARAR",
                20,
                40
            )

            oled.text(
                "SW: VOLTAR",
                15,
                54
            )


        oled.show()

        time.sleep_ms(20)

# =========================================================
# MENU PRINCIPAL
# =========================================================

def menu_principal(
    callback_verificacao=None,
    callback_acionar_manual=None
):

    opcoes = [
        "Refeicao",
        "Quantidade",
        "Manual"
    ]

    selecionado = 0

    ultimo_movimento = time.ticks_ms()


    while True:

        # -------------------------------------------------
        # Verifica alimentação automática
        # -------------------------------------------------

        if callback_verificacao:

            callback_verificacao()


        # -------------------------------------------------
        # DESENHA MENU
        # -------------------------------------------------

        oled.fill(0)

        oled.text(
            "MENU PRINCIPAL",
            8,
            0
        )

        oled.hline(
            0,
            10,
            128,
            1
        )


        for idx, opcao in enumerate(
            opcoes
        ):

            indicador = (
                ">"
                if idx == selecionado
                else " "
            )

            oled.text(
                f"{indicador}{opcao}",
                5,
                20 + idx * 13
            )


        oled.show()


        # -------------------------------------------------
        # JOYSTICK
        # -------------------------------------------------

        direcao = ler_joystick_y()

        agora = time.ticks_ms()

        if (
            direcao != 0
            and
            time.ticks_diff(
                agora,
                ultimo_movimento
            ) > 250
        ):

            selecionado = (
                selecionado + direcao
            ) % len(opcoes)

            ultimo_movimento = agora


        # -------------------------------------------------
        # SW = SELECIONAR
        # -------------------------------------------------

        if ler_botao(btn_sw):

            opcao_atual = (
                opcoes[selecionado]
            )


            # ---------------------------------------------
            # HORÁRIOS
            # ---------------------------------------------

            if opcao_atual == "Refeicao":

                tela_refeicao(
                    callback_verificacao
                )


            # ---------------------------------------------
            # QUANTIDADE
            # ---------------------------------------------

            elif opcao_atual == "Quantidade":

                tela_quantidade(
                    callback_verificacao
                )


            # ---------------------------------------------
            # ALIMENTAÇÃO MANUAL
            # ---------------------------------------------

            elif opcao_atual == "Manual":

                tela_alimentacao_manual(
                    callback_acionar_manual
                )


        time.sleep_ms(20)
