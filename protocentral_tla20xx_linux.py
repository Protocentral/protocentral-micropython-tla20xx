# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Ashwin Whitchurch, ProtoCentral Electronics
"""Raspberry Pi / Linux I2C adapter for the TLA20xx MicroPython driver.

Implements the `machine.I2C` subset the driver uses (`readfrom_mem` /
`writeto_mem`) over `smbus2`, so the identical driver runs on a Pi. Not Blinka.

    from protocentral_tla20xx_linux import I2C
    from protocentral_tla20xx import TLA20XX
    adc = TLA20XX(I2C(bus=1), 0x48); adc.begin()
    print(adc.read(), "mV")
"""

from smbus2 import SMBus, i2c_msg


class I2C:
    """A `machine.I2C`-compatible (subset) bus backed by smbus2."""

    def __init__(self, bus=1):
        if isinstance(bus, SMBus):
            self._bus = bus
            self._owns = False
        else:
            self._bus = SMBus(bus)
            self._owns = True

    def readfrom_mem(self, addr, reg, nbytes):
        write = i2c_msg.write(addr, [reg & 0xFF])
        read = i2c_msg.read(addr, nbytes)
        self._bus.i2c_rdwr(write, read)
        return bytes(read)

    def writeto_mem(self, addr, reg, buf):
        self._bus.i2c_rdwr(i2c_msg.write(addr, bytes([reg & 0xFF]) + bytes(buf)))

    def scan(self):
        found = []
        for addr in range(0x08, 0x78):
            try:
                self._bus.i2c_rdwr(i2c_msg.read(addr, 1))
                found.append(addr)
            except OSError:
                pass
        return found

    def close(self):
        if self._owns:
            self._bus.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
