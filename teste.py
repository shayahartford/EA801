from machine import Pin, time_pulse_us
from time import sleep, sleep_us

trig = Pin(1, Pin.OUT)  # SCL da BitDogLab
echo = Pin(0, Pin.IN)   # SDA da BitDogLab
trig.value(0)

while True:
    trig.value(0)
    sleep_us(2)
    trig.value(1)
    sleep_us(20)
    trig.value(0)

    tempo = time_pulse_us(echo, 1, 30000)

    if tempo >= 0:
        distancia_cm = tempo / 58
        print("Distância: {:.1f} cm".format(distancia_cm))
    else:
        print("Sem eco: confira a ligação ou a posição do objeto")

    sleep(0.2)