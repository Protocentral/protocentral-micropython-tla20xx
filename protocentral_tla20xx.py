# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Ashwin Whitchurch, ProtoCentral Electronics
#
# MicroPython driver for the ProtoCentral TLA20xx breakout (TI TLA2022 / TLA2024
# 12-bit I2C ADC, ADS101x-class). Also runs on Raspberry Pi via the smbus2 shim
# (protocentral_tla20xx_linux.py) with no driver changes.
#
# Ported from the ProtoCentral Arduino library (single source of truth):
#   https://github.com/Protocentral/protocentral_tla20XX_arduino
#
# The public surface mirrors the Arduino library exactly: begin(), read_adc(),
# set_fsr(), set_mode(), set_dr(), set_mux(), and the DR_* / FSR_* / MUX_* / OP_*
# constants. As in the Arduino library, read_adc() returns the RAW signed 12-bit
# conversion code (not volts); use read_voltage() for a millivolt convenience.

# ----------------------------------------------------------------- registers
_REG_CONVERSION = 0x00
_REG_CONFIG = 0x01

# ----------------------------------------------------------------- I2C address
# The address is not baked into the driver — pass it from your own script, since
# it depends on the board's ADDR strap:
#   GND -> 0x48 (board default), VDD -> 0x49, SDA -> 0x4A, SCL -> 0x4B.

# ----------------------------------------------------------------- constants (mirror Arduino enums)
# Data rate [7:5]
DR_128SPS = 0x00
DR_250SPS = 0x01
DR_490SPS = 0x02
DR_920SPS = 0x03
DR_1600SPS = 0x04
DR_2400SPS = 0x05
DR_3300SPS = 0x06

# Full-scale range / PGA [11:9]
FSR_6_144V = 0x00
FSR_4_096V = 0x01
FSR_2_048V = 0x02
FSR_1_024V = 0x03
FSR_0_512V = 0x04
FSR_0_256V = 0x05

# Input mux [14:12]
MUX_AIN0_AIN1 = 0x00
MUX_AIN0_AIN3 = 0x01
MUX_AIN1_AIN3 = 0x02
MUX_AIN2_AIN3 = 0x03
MUX_AIN0_GND = 0x04
MUX_AIN1_GND = 0x05
MUX_AIN2_GND = 0x06
MUX_AIN3_GND = 0x07

# Operating mode [8]
OP_CONTINUOUS = 0
OP_SINGLE = 1

# full-scale range in millivolts, indexed by FSR code (for read_voltage())
_FSR_MV = {
    FSR_6_144V: 6144.0, FSR_4_096V: 4096.0, FSR_2_048V: 2048.0,
    FSR_1_024V: 1024.0, FSR_0_512V: 512.0, FSR_0_256V: 256.0,
}

# Comparator bits [4:0] — TLA2024 has no comparator; datasheet default 0b00011.
_COMP_DEFAULT = 0x03


class TLA20XX:
    """Driver for the ProtoCentral TLA2022/TLA2024 12-bit I2C ADC.

    Example:
        from machine import Pin, I2C
        from protocentral_tla20xx import TLA20XX, MUX_AIN0_GND, FSR_2_048V, DR_128SPS, OP_CONTINUOUS
        i2c = I2C(0, scl=Pin(6), sda=Pin(5))   # Adafruit QT Py ESP32-C3
        adc = TLA20XX(i2c, 0x48)      # ADDR strap: GND=0x48, VDD=0x49, SDA=0x4A, SCL=0x4B
        adc.begin()
        adc.set_mode(OP_CONTINUOUS)
        adc.set_dr(DR_128SPS)
        adc.set_fsr(FSR_2_048V)
        adc.set_mux(MUX_AIN0_GND)
        print(adc.read_adc())         # raw signed 12-bit count
        print(adc.read_voltage())     # convenience: millivolts
    """

    def __init__(self, i2c, address):
        self.i2c = i2c
        self.address = address
        # defaults matching the Arduino begin() word 0x8683
        self._mux = MUX_AIN0_AIN1
        self._fsr = FSR_1_024V
        self._dr = DR_1600SPS
        self._mode = OP_CONTINUOUS

    # ------------------------------------------------------------- raw register I/O (big-endian)
    def _read16(self, reg):
        d = self.i2c.readfrom_mem(self.address, reg, 2)
        return (d[0] << 8) | d[1]

    def _write16(self, reg, value):
        self.i2c.writeto_mem(self.address, reg, bytes([(value >> 8) & 0xFF, value & 0xFF]))

    def _conf_word(self):
        return ((self._mux & 0x7) << 12) | ((self._fsr & 0x7) << 9) | \
               ((self._mode & 0x1) << 8) | ((self._dr & 0x7) << 5) | _COMP_DEFAULT

    def _apply(self):
        self._write16(_REG_CONFIG, self._conf_word())

    # ------------------------------------------------------------- config (mirror Arduino)
    def begin(self):
        """Initialise to the Arduino default config word (0x8683)."""
        self._write16(_REG_CONFIG, 0x8683)

    def set_fsr(self, fsr):
        self._fsr = fsr
        self._apply()

    def set_mode(self, mode):
        self._mode = mode
        self._apply()

    def set_dr(self, rate):
        self._dr = rate
        self._apply()

    def set_mux(self, mux):
        self._mux = mux
        self._apply()

    # ------------------------------------------------------------- read
    def read_adc(self):
        """Raw signed 12-bit conversion code (mirrors the Arduino read_adc())."""
        raw = self._read16(_REG_CONVERSION)
        if raw & 0x8000:                 # to signed 16-bit
            raw -= 1 << 16
        return raw >> 4                  # arithmetic shift -> signed 12-bit code

    def read_voltage(self):
        """Convenience (not in the Arduino lib): measured voltage in millivolts."""
        return self.read_adc() * (_FSR_MV[self._fsr] / 2048.0)
