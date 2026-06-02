# SPDX-License-Identifier: MIT
# Mocked-bus unit tests for the TLA20xx driver + Pi-shim parity.
# Runs on desktop CPython: `python tests/test_tla20xx.py`.

import importlib.util
import math
import os
import sys
import types

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)

from protocentral_tla20xx import (
    TLA20XX, MUX_AIN0_GND, FSR_2_048V, FSR_4_096V, DR_128SPS, OP_CONTINUOUS,
    _REG_CONFIG, _REG_CONVERSION,
)


class FakeI2C:
    def __init__(self):
        self.regs = {}
        self.writes = []

    def store(self, reg, value):
        self.regs[reg] = bytes([(value >> 8) & 0xFF, value & 0xFF])

    def readfrom_mem(self, addr, reg, n):
        return self.regs.get(reg, b"\x00\x00")[:n]

    def writeto_mem(self, addr, reg, buf):
        self.regs[reg] = bytes(buf)
        self.writes.append((reg, (buf[0] << 8) | buf[1]))


def test_begin_writes_default_word():
    bus = FakeI2C()
    TLA20XX(bus, 0x48).begin()
    assert bus.writes[-1] == (_REG_CONFIG, 0x8683), hex(bus.writes[-1][1])


def test_config_word():
    bus = FakeI2C()
    adc = TLA20XX(bus, 0x48)
    adc.set_mux(MUX_AIN0_GND)      # 4
    adc.set_fsr(FSR_2_048V)        # 2
    adc.set_dr(DR_128SPS)          # 0
    adc.set_mode(OP_CONTINUOUS)    # 0
    expected = (4 << 12) | (2 << 9) | (0 << 8) | (0 << 5) | 0x03   # 0x4403
    assert bus.writes[-1] == (_REG_CONFIG, expected), hex(bus.writes[-1][1])


def test_read_adc_raw_positive():
    bus = FakeI2C()
    adc = TLA20XX(bus, 0x48)
    bus.store(_REG_CONVERSION, 100 << 4)   # conv reg = code << 4
    assert adc.read_adc() == 100


def test_read_adc_raw_negative():
    bus = FakeI2C()
    adc = TLA20XX(bus, 0x48)
    bus.store(_REG_CONVERSION, 0xFFF0)     # code -1
    assert adc.read_adc() == -1


def test_read_voltage_scaling():
    bus = FakeI2C()
    adc = TLA20XX(bus, 0x48)
    bus.store(_REG_CONVERSION, 100 << 4)
    adc.set_fsr(FSR_2_048V)                # 1 mV / count
    assert math.isclose(adc.read_voltage(), 100.0, rel_tol=1e-9)
    adc.set_fsr(FSR_4_096V)                # 2 mV / count
    assert math.isclose(adc.read_voltage(), 200.0, rel_tol=1e-9)


# --- Pi shim parity ----------------------------------------------------------
class _FakeMsg:
    def __init__(self, kind, addr, data=None, length=0):
        self.kind = kind; self.addr = addr
        self.data = list(data) if data else []
        self.length = length; self.buf = bytearray(length)
    def __bytes__(self):
        return bytes(self.buf)


class _i2c_msg:
    @staticmethod
    def write(addr, data):
        return _FakeMsg("w", addr, data=data)
    @staticmethod
    def read(addr, n):
        return _FakeMsg("r", addr, length=n)


class _SMBus:
    def __init__(self, bus):
        self.regfile = {}
    def i2c_rdwr(self, *msgs):
        w = msgs[0]; reg = w.data[0]
        if len(msgs) == 1:
            self.regfile[reg] = bytes(w.data[1:])
        else:
            r = msgs[1]
            r.buf = bytearray(self.regfile.get(reg, b"\x00" * r.length)[: r.length])
    def close(self):
        pass


def test_pi_shim_parity():
    fake = types.ModuleType("smbus2")
    fake.SMBus = _SMBus; fake.i2c_msg = _i2c_msg
    sys.modules["smbus2"] = fake
    spec = importlib.util.spec_from_file_location(
        "pc_tla_linux", os.path.join(ROOT, "protocentral_tla20xx_linux.py"))
    shim = importlib.util.module_from_spec(spec); spec.loader.exec_module(shim)

    backend = _SMBus(1)
    backend.regfile[_REG_CONVERSION] = bytes([0x06, 0x40])   # code 100
    adc = TLA20XX(shim.I2C(bus=backend), 0x48)
    assert adc.read_adc() == 100


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("ALL PASSED")
