# SPDX-License-Identifier: MIT
# Scan all four single-ended inputs (AINx vs GND) on the TLA2024.
# Continuous mode; switch the mux and allow one conversion before reading.

import time
from machine import Pin, I2C
from protocentral_tla20xx import (
    TLA20XX, MUX_AIN0_GND, MUX_AIN1_GND, MUX_AIN2_GND, MUX_AIN3_GND,
    FSR_4_096V, DR_3300SPS, OP_CONTINUOUS,
)

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)

adc = TLA20XX(i2c)
adc.begin()
adc.set_mode(OP_CONTINUOUS)
adc.set_dr(DR_3300SPS)
adc.set_fsr(FSR_4_096V)

channels = (MUX_AIN0_GND, MUX_AIN1_GND, MUX_AIN2_GND, MUX_AIN3_GND)

while True:
    out = []
    for ch, mux in enumerate(channels):
        adc.set_mux(mux)
        time.sleep_ms(2) if hasattr(time, "sleep_ms") else time.sleep(0.002)  # settle 1 conversion
        out.append("AIN{}={:>6}".format(ch, adc.read_adc()))
    print("  ".join(out))
    time.sleep(0.5)
