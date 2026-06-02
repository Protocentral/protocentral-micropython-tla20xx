# SPDX-License-Identifier: MIT
# TLA2024 single-channel read (AIN0 vs GND) on MicroPython.
# Mirrors the ProtoCentral Arduino Example1/Example2.

import time
from machine import Pin, I2C
from protocentral_tla20xx import (
    TLA20XX, MUX_AIN0_GND, FSR_2_048V, DR_128SPS, OP_CONTINUOUS,
)

i2c = I2C(0, scl=Pin(6), sda=Pin(5), freq=400000)   # Adafruit QT Py ESP32-C3; set pins for your board

TLA20XX_I2C_ADDR = 0x48        # ADDR strap: GND=0x48, VDD=0x49, SDA=0x4A, SCL=0x4B
adc = TLA20XX(i2c, TLA20XX_I2C_ADDR)
adc.begin()
adc.set_mode(OP_CONTINUOUS)
adc.set_dr(DR_128SPS)
adc.set_fsr(FSR_2_048V)        # at +/-2.048 V, 1 LSB ~= 1 mV
adc.set_mux(MUX_AIN0_GND)

while True:
    print("AIN0  count={:>6}   {:.2f} mV".format(adc.read_adc(), adc.read_voltage()))
    time.sleep(0.5)
