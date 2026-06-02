# ProtoCentral TLA20xx MicroPython Library

MicroPython library for the ProtoCentral TLA20xx breakout — a TI **TLA2024 / TLA2022** 12-bit, 4-channel I²C ADC (ADS101x-class) with a programmable input mux, gain (PGA), and data rate. The same driver also runs on a Raspberry Pi (via a lightweight `smbus2` shim), so one codebase covers MCUs (Raspberry Pi Pico, ESP32) and Linux SBCs alike.

## Don't have one? [Buy it here](https://protocentral.com/)

## Features

- TI TLA2024 (4-channel) / TLA2022 (1-channel) 12-bit delta-sigma ADC
- Programmable input mux: 4 single-ended or differential pairs (AIN0–AIN3)
- Programmable gain / full-scale range from ±6.144 V down to ±0.256 V
- Selectable data rate, 128 SPS to 3300 SPS
- Continuous and single-shot conversion modes
- I²C interface, default address `0x48`
- Qwiic / STEMMA QT connector for solder-free wiring
- One driver for MicroPython **and** Raspberry Pi / Linux

## Installation

### MicroPython (Raspberry Pi Pico, ESP32, …)

Install over the network with [`mip`](https://docs.micropython.org/en/latest/reference/packages.html):

```bash
mpremote mip install github:Protocentral/protocentral-micropython-tla20xx
```

Or copy [`protocentral_tla20xx.py`](protocentral_tla20xx.py) to the board manually (e.g. `mpremote cp protocentral_tla20xx.py :`).

### Raspberry Pi / Linux

```bash
sudo raspi-config            # Interface Options -> enable I2C
pip install protocentral-tla20xx
i2cdetect -y 1               # confirm the ADC shows up at 0x48
```

## Hardware Setup

The board uses I²C. Connect power, ground, and the two I²C lines; the default address is `0x48` (ADDR strap: GND→`0x48`, VDD→`0x49`, SDA→`0x4A`, SCL→`0x4B`). Set the address in your own script to match the strap. Analog inputs are AIN0–AIN3.

### Adafruit QT Py ESP32-C3 (MicroPython)

The examples default to this board — plug the breakout into the STEMMA QT / Qwiic connector for solder-free wiring, or wire it by hand:

| TLA20xx Pin | QT Py C3 Pin | Notes |
|---|---|---|
| VIN | 3V3 | 3.3 V supply |
| GND | GND | Ground |
| SDA | GPIO5 | I2C SDA |
| SCL | GPIO6 | I2C SCL |

### Raspberry Pi Pico (MicroPython)

| TLA20xx Pin | Pico Pin | Notes |
|---|---|---|
| VIN | 3V3 (OUT) | 3.3 V supply |
| GND | GND | Ground |
| SDA | GP4 | I2C0 SDA |
| SCL | GP5 | I2C0 SCL |

### ESP32 (MicroPython)

| TLA20xx Pin | ESP32 Pin | Notes |
|---|---|---|
| VIN | 3V3 | 3.3 V supply |
| GND | GND | Ground |
| SDA | GPIO21 | default I2C SDA |
| SCL | GPIO22 | default I2C SCL |

### Raspberry Pi (Linux)

| TLA20xx Pin | RPi Header | Notes |
|---|---|---|
| VIN | Pin 1 (3V3) | 3.3 V supply |
| GND | Pin 6 (GND) | Ground |
| SDA | Pin 3 (GPIO2 / SDA1) | I2C bus 1 |
| SCL | Pin 5 (GPIO3 / SCL1) | I2C bus 1 |

## Quick Start

### MicroPython

```python
import time
from machine import Pin, I2C
from protocentral_tla20xx import TLA20XX, MUX_AIN0_GND, FSR_2_048V, DR_128SPS, OP_CONTINUOUS

i2c = I2C(0, scl=Pin(6), sda=Pin(5), freq=400000)   # Adafruit QT Py ESP32-C3; set pins for your board

TLA20XX_I2C_ADDR = 0x48        # ADDR strap: GND=0x48, VDD=0x49, SDA=0x4A, SCL=0x4B
adc = TLA20XX(i2c, TLA20XX_I2C_ADDR)
adc.begin()
adc.set_mode(OP_CONTINUOUS)
adc.set_dr(DR_128SPS)
adc.set_fsr(FSR_2_048V)        # at +/-2.048 V, 1 LSB ~= 1 mV
adc.set_mux(MUX_AIN0_GND)

while True:
    print("count={:>6}   {:.2f} mV".format(adc.read_adc(), adc.read_voltage()))
    time.sleep(0.5)
```

### Raspberry Pi / Linux

Same driver — swap `machine.I2C` for the `smbus2` shim:

```python
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
        print("count={:>6}   {:.2f} mV".format(adc.read_adc(), adc.read_voltage()))
        time.sleep(0.5)
```

## API Reference

### Constructor

| Constructor | Description |
|---|---|
| `TLA20XX(i2c, address)` | Create an ADC on a `machine.I2C` (or Pi shim) bus; `address` set by the ADDR strap (0x48 default) |

### Methods

| Method | Returns | Description |
|---|---|---|
| `begin()` | — | Initialise to the default config word (`0x8683`) |
| `set_mux(MUX_*)` | — | Select input channel / differential pair |
| `set_fsr(FSR_*)` | — | Set full-scale range / PGA |
| `set_dr(DR_*)` | — | Set data rate |
| `set_mode(OP_CONTINUOUS / OP_SINGLE)` | — | Set conversion mode |
| `read_adc()` | `int` | Raw signed 12-bit conversion code (mirrors the Arduino `read_adc()`) |
| `read_voltage()` | `float` | Convenience: measured voltage in mV (uses the current FSR) |

Method and constant names mirror the [ProtoCentral TLA20xx Arduino library](https://github.com/Protocentral/protocentral_tla20XX_arduino) so sketches translate directly.

### Constants

| Group | Values |
|---|---|
| Mux | `MUX_AIN0_AIN1`, `MUX_AIN0_AIN3`, `MUX_AIN1_AIN3`, `MUX_AIN2_AIN3`, `MUX_AIN0_GND`, `MUX_AIN1_GND`, `MUX_AIN2_GND`, `MUX_AIN3_GND` |
| Full-scale range | `FSR_6_144V`, `FSR_4_096V`, `FSR_2_048V`, `FSR_1_024V`, `FSR_0_512V`, `FSR_0_256V` |
| Data rate | `DR_128SPS`, `DR_250SPS`, `DR_490SPS`, `DR_920SPS`, `DR_1600SPS`, `DR_2400SPS`, `DR_3300SPS` |
| Mode | `OP_CONTINUOUS`, `OP_SINGLE` |

## Examples

| Example | Platform | Description |
|---|---|---|
| [`tla20xx_simpletest.py`](examples/tla20xx_simpletest.py) | MicroPython | Single-channel read (count + mV) |
| [`tla20xx_4channel_scan.py`](examples/tla20xx_4channel_scan.py) | MicroPython | Scan AIN0–AIN3 vs GND |
| [`tla20xx_raspberrypi.py`](examples/tla20xx_raspberrypi.py) | Raspberry Pi | Same read loop using the `smbus2` shim |

## License

**Software:** [MIT License](http://opensource.org/licenses/MIT) — see [LICENSE.md](LICENSE.md).

**Hardware:** the TLA20xx breakout board is open-source hardware licensed under [CERN-OHL-P v2](https://ohwr.org/cern_ohl_p_v2.txt).