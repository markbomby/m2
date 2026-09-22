import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


def majority(a, b, c):
    return (a & b) | (a & c) | (b & c)


def dft_model(a, b, cin, cp):
    """Return (five-bit result, effective carries, native carries)."""
    a_bits = [(a >> i) & 1 for i in range(4)]
    b_bits = [(b >> i) & 1 for i in range(4)]
    cp_bits = [(cp >> i) & 1 for i in range(3)]

    c1_native = majority(a_bits[0], b_bits[0], cin)
    c1 = cp_bits[0]
    c2_native = majority(a_bits[1], b_bits[1], c1)
    c2 = cp_bits[1]
    c3_native = majority(a_bits[2], b_bits[2], c2)
    c3 = cp_bits[2]
    cout = majority(a_bits[3], b_bits[3], c3)

    sums = [
        a_bits[0] ^ b_bits[0] ^ cin,
        a_bits[1] ^ b_bits[1] ^ c1,
        a_bits[2] ^ b_bits[2] ^ c2,
        a_bits[3] ^ b_bits[3] ^ c3,
    ]
    result = sum(bit << i for i, bit in enumerate(sums)) | (cout << 4)
    return result, (c1, c2, c3), (c1_native, c2_native, c3_native)


async def reset_dut(dut):
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.ena.value = 1
    dut.rst_n.value = 0
    await Timer(2, units="ns")
    dut.rst_n.value = 1
    await Timer(1, units="ns")


def drive(dut, a=0, b=0, cin=0, select_dft=0, test_mode=0,
          scan_enable=0, scan_in=0):
    dut.ui_in.value = ((b & 0xF) << 4) | (a & 0xF)
    dut.uio_in.value = (
        (cin & 1)
        | ((select_dft & 1) << 1)
        | ((test_mode & 1) << 2)
        | ((scan_enable & 1) << 3)
        | ((scan_in & 1) << 4)
    )


async def scan_load(dut, value):
    """Load scan_q[5:0]; serial input order is bit 5 down to bit 0."""
    for bit_index in range(5, -1, -1):
        drive(dut, select_dft=1, scan_enable=1,
              scan_in=(value >> bit_index) & 1)
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")


async def scan_read(dut):
    """Read old scan_q as OP2,OP1,OP0,CP2,CP1,CP0 while shifting zeros."""
    value = 0
    for _ in range(6):
        drive(dut, select_dft=1, test_mode=1, scan_enable=1, scan_in=0)
        scan_out = (int(dut.uo_out.value) >> 5) & 1\n        value = (value << 1) | scan_out
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
    return value


@cocotb.test()
async def test_normal_mode_exhaustive(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    for select_dft in (0, 1):
        for a in range(16):
            for b in range(16):
                for cin in (0, 1):
                    drive(dut, a, b, cin, select_dft=select_dft,
                          test_mode=0, scan_enable=0)
                    await Timer(1, units="ns")
                    expected = a + b + cin
                    actual = int(dut.uo_out.value) & 0x1F
                    assert actual == expected, (
                        f"normal mode mismatch: select={select_dft}, "
                        f"A={a}, B={b}, Cin={cin}, got={actual}, expected={expected}"
                    )


@cocotb.test()
async def test_scan_shift_control_and_capture(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    assert ((int(dut.uo_out.value) >> 5) & 1) == 0

    cases = [
        (0x0, 0x0, 0, 0b101),
        (0x3, 0x6, 1, 0b010),
        (0xA, 0x5, 0, 0b111),
        (0xF, 0x1, 1, 0b000),
    ]

    for a, b, cin, cp in cases:
        # CP2:CP0 occupy scan_q[2:0]; OP preload bits are don't-care zeros.
        await scan_load(dut, cp)

        drive(dut, a, b, cin, select_dft=1, test_mode=1,
              scan_enable=1, scan_in=0)
        await Timer(1, units="ns")
        expected_result, carries, native = dft_model(a, b, cin, cp)
        actual_result = int(dut.uo_out.value) & 0x1F
        assert actual_result == expected_result, (
            f"CP override mismatch: cp={cp:03b}, got={actual_result:05b}, "
            f"expected={expected_result:05b}"
        )

        # Capture: OP cells sample effective carries while CP cells sample native carries.
        drive(dut, a, b, cin, select_dft=1, test_mode=1,
              scan_enable=0, scan_in=0)
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

        shifted = await scan_read(dut)
        c1, c2, c3 = carries
        n1, n2, n3 = native
        expected_scan = (
            (c3 << 5) | (c2 << 4) | (c1 << 3)
            | (n3 << 2) | (n2 << 1) | n1
        )
        assert shifted == expected_scan, (
            f"scan capture mismatch: got={shifted:06b}, expected={expected_scan:06b}"
        )


