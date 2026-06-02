# SPDX-License-Identifier: MIT
# TLA2024 on a Raspberry Pi — same driver, smbus2 shim instead of machine.I2C.
# Setup:  sudo raspi-config (enable I2C), pip install protocentral-tla20xx
#         i2cdetect -y 1   ->  should show 0x48

import time
from protocentral_tla20xx_linux import I2C
from protocentral_tla20xx import TLA20XX, MUX_AIN0_GND, FSR_2_048V, DR_128SPS, OP_CONTINUOUS

TLA20XX_I2C_ADDR = 0x48        # ADDR strap: GND=0x48, VDD=0x49, SDA=0x4A, SCL=0x4B

with I2C(bus=1) as i2c:
    adc = TLA20XX(i2c, TLA20XX_I2C_ADDR)
    adc.begin()
    adc.set_mode(OP_CONTINUOUS)
    adc.set_dr(DR_128SPS)
    adc.set_fsr(FSR_2_048V)
    adc.set_mux(MUX_AIN0_GND)
    while True:
        print("AIN0  count={:>6}   {:.2f} mV".format(adc.read_adc(), adc.read_voltage()))
        time.sleep(0.5)
