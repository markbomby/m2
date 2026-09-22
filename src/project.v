`default_nettype none

module tt_um_muxed_d_full_scan_adder (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    wire [3:0] a = ui_in[3:0];
    wire [3:0] b = ui_in[7:4];
    wire       cin = uio_in[0];
    wire       select_dft = uio_in[1];
    wire       test_mode = uio_in[2];
    wire       scan_enable = uio_in[3];
    wire       scan_in = uio_in[4];

    wire [3:0] sum_nodft;
    wire       cout_nodft;
    wire [3:0] sum_dft;
    wire       cout_dft;
    wire       scan_out;

    adder4_nodft u_adder_nodft (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum_nodft),
        .cout(cout_nodft)
    );

    adder4_dft u_adder_dft (
        .a(a),
        .b(b),
        .cin(cin),
        .clk(clk),
        .rst_n(rst_n),
        .test_mode(test_mode),
        .scan_enable(scan_enable),
        .scan_in(scan_in),
        .sum(sum_dft),
        .cout(cout_dft),
        .scan_out(scan_out)
    );

    assign uo_out[3:0] = select_dft ? sum_dft : sum_nodft;
    assign uo_out[4]   = select_dft ? cout_dft : cout_nodft;
    assign uo_out[5]   = scan_out;
    assign uo_out[7:6] = 2'b00;

    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // Tiny Tapeout requires ena in the interface; this design is always active.
    wire _unused = &{ena, uio_in[7:5], 1'b0};
endmodule

`default_nettype wire


