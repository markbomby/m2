# 4-bit Adder with Muxed-D Full Scan

Ready-to-submit Tiny Tapeout assignment for DIGITAL IC TESTING. The project contains both:

1. a combinational 4-bit ripple-carry adder without DFT, and
2. a 4-bit ripple-carry adder with a 6-bit muxed-D scan chain, three control points, and three observation points.

## Architecture

The DFT adder inserts control-point multiplexers on the three internal carry nodes `c1`, `c2`, and `c3`. In normal operation (`test_mode=0`), each MUX passes its native carry and the DFT adder is functionally identical to the non-DFT adder. In test mode (`test_mode=1`), scan cells `CP0`, `CP1`, and `CP2` override `c1`, `c2`, and `c3` respectively.

Observation cells `OP0`, `OP1`, and `OP2` capture the effective values of `c1`, `c2`, and `c3` on a rising clock edge when `scan_enable=0`. The complete scan chain is:

```text
scan_in -> CP0 -> CP1 -> CP2 -> OP0 -> OP1 -> OP2 -> scan_out
```

The six physical scan bits are `scan_q[5:0] = {OP2, OP1, OP0, CP2, CP1, CP0}`. During shift (`scan_enable=1`), one bit moves toward `scan_out` on every rising edge. During capture (`scan_enable=0`), the CP cells capture native carry-generation values and the OP cells capture the effective carry nodes. Reset is asynchronous and active low.

## Tiny Tapeout pin mapping

| Pin | Function |
|---|---|
| `ui_in[3:0]` | Operand A |
| `ui_in[7:4]` | Operand B |
| `uio_in[0]` | Carry input `Cin` |
| `uio_in[1]` | Output select: 0 = non-DFT adder, 1 = DFT adder |
| `uio_in[2]` | `test_mode`: enables carry override in the DFT adder |
| `uio_in[3]` | `scan_enable`: 1 = shift, 0 = capture |
| `uio_in[4]` | `scan_in` |
| `uo_out[3:0]` | Selected sum |
| `uo_out[4]` | Selected carry output |
| `uo_out[5]` | `scan_out` (`OP2`) |
| `uo_out[7:6]` | Reserved, tied to 0 |
| `clk` | Scan/capture clock |
| `rst_n` | Active-low asynchronous reset |

All bidirectional pins are inputs: `uio_oe=0` and `uio_out=0`. `ena` is intentionally unused.

## Test operation

1. Assert `rst_n=0`, then release it.
2. Set `scan_enable=1` and shift six bits into `scan_in`. To load a target vector `{OP2,OP1,OP0,CP2,CP1,CP0}`, send its bits from bit 5 down to bit 0, one per rising edge.
3. Set `test_mode=1` to let CP0-CP2 override the internal carries.
4. Apply A, B, and Cin. Set `scan_enable=0` and pulse the clock once to capture the effective carries into OP0-OP2.
5. Set `scan_enable=1`. Read `scan_out` before each rising edge while shifting six cycles; the order is OP2, OP1, OP0, CP2, CP1, CP0.

## Running the cocotb tests

From the `test` directory:

```sh
python -m pip install -r requirements.txt
make
```

The testbench exhaustively checks all 512 input combinations for both implementations in normal mode. It also checks scan reset, six-bit shift ordering, control-point overrides, and observation-point capture/readout.

## File layout

```text
src/adder4_nodft.v     plain 4-bit adder
src/adder4_dft.v       DFT adder and six scan cells
src/project.v          Tiny Tapeout top module
test/test_adder.py     cocotb verification
test/Makefile          Icarus/cocotb runner
info.yaml              Tiny Tapeout metadata and pinout
REPORT.md              concise assignment report
```

## Assumptions

- The assignment asks for one submission containing both versions; `uio_in[1]` selects which result appears on the output pins.
- “Test mode” and “scan enable” are separate controls. This permits loaded CP values to remain active during capture.
- Observation points sample the effective carry nodes after their control-point MUXes. This directly demonstrates whether the overrides propagate.
- The CP capture inputs are the corresponding native carry-generation values. Only the OP capture values are required for the assignment; exposing all six cells in one chain keeps the implementation a conventional muxed-D full-scan structure.
- Inputs and outputs are combinational except for the six scan cells.
- The student name was not provided, so `info.yaml` uses `Student` as the author placeholder; replace only that value before submission if a real name is required.

The top-level interface follows the official [Tiny Tapeout digital GPIO specification](https://tinytapeout.com/specs/gpio/).

