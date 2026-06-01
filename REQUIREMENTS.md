# REQUIREMENTS — `protocentral-micropython-tla20xx`

Canonical Python driver for the TLA2022/TLA2024 ADC breakout — serves MicroPython MCUs **and** Raspberry Pi from one codebase, per [ADR-001](../../../strategy/ADR_001_MicroPython_Library_Strategy.md). License **MIT**. **This is also the dependency for the tinyGSR driver** (tinyGSR is a TLA2024 + GSR front-end; its library wraps this one).

## Source of truth

Mirror the **ProtoCentral TLA20xx Arduino library** (<https://github.com/Protocentral/protocentral_tla20XX_arduino>): the `MUX_*`/`FSR_*`/`DR_*`/`OP_*` constants and the `begin/setMux/setFSR/setDataRate/setMode/read` surface. Register layout follows the TI TLA2024 datasheet.

## Architecture

Driver (`protocentral_tla20xx.py`) uses only `readfrom_mem`/`writeto_mem`. MicroPython passes `machine.I2C`; Raspberry Pi passes `protocentral_tla20xx_linux.I2C` (smbus2 shim). Same file both places.

## Status — scaffolded

Present: driver, Pi shim, examples (`simpletest`, `4channel_scan`, `raspberrypi`), mocked-bus + parity tests, `package.json` (mip), `pyproject.toml` (PyPI), README, LICENSE.md, `publish.yml`.

## Reconciled against the Arduino source (header + .cpp)

Confirmed from `src/protocentral_TLA20xx.{h,cpp}` (fully read):
- I2C address **`0x49`** ✓
- Registers: CONV `0x00`, CONF `0x01`; 16-bit big-endian I/O ✓
- Methods: `begin()`, `read_adc()`, `setFSR()`, `setMode()`, `setDR()`, `setMux()` — mirrored 1:1 as `begin`/`read_adc`/`set_fsr`/`set_mode`/`set_dr`/`set_mux`.
- **`read_adc()` returns the RAW signed 12-bit code** (`(int16_t)conv >> 4`), **not** volts. Mirrored exactly; added `read_voltage()` as a MicroPython-only convenience (mV via current FSR).
- All enum constants confirmed and matched: `DR_128SPS…DR_3300SPS`, `FSR_6_144V…FSR_0_256V`, `MUX_AIN0_AIN1…MUX_AIN3_GND`, `OP_CONTINUOUS`/`OP_SINGLE`.
- `begin()` writes config word **`0x8683`** (continuous, ±1.024 V, 1600 SPS, AIN0-AIN1) — mirrored literally.

Note: the Arduino `setDR()` does not clear the DR field before OR-ing (a latent quirk). The MicroPython driver rebuilds the full config word from cached state each call, so DR/MUX/FSR/MODE always reflect the last call — a deliberate, documented improvement over the read-modify-write sequence.

## Acceptance criteria

1. `mip install` (Pico/ESP32) and `pip install protocentral-tla20xx` (Pi) both work.
2. Reads a known input voltage within tolerance on MicroPython and Pi (same driver).
3. Negative codes and FSR scaling correct — covered by unit tests.
4. Constants/methods/examples line up 1:1 with the Arduino library.
5. Mocked-bus + Pi-shim parity tests + ruff green in CI.

## Downstream

`protocentral-micropython-tinygsr` depends on this package and adds only the GSR conversion (see the first-wave build plan). Keep the public API stable for that consumer.
