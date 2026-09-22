`default_nettype none

module adder4_dft (
    input  wire [3:0] a,
    input  wire [3:0] b,
    input  wire       cin,
    input  wire       clk,
    input  wire       rst_n,
    input  wire       test_mode,
    input  wire       scan_enable,
    input  wire       scan_in,
    output wire [3:0] sum,
    output wire       cout,
    output wire       scan_out
);
    // scan_q = {OP2, OP1, OP0, CP2, CP1, CP0}
    reg [5:0] scan_q;

    wire c1_native;
    wire c2_native;
    wire c3_native;
    wire c1;
    wire c2;
    wire c3;

    // Bit 0 and control point CP0 on c1.
    assign sum[0]   = a[0] ^ b[0] ^ cin;
    assign c1_native = (a[0] & b[0]) | (a[0] & cin) | (b[0] & cin);
    assign c1        = test_mode ? scan_q[0] : c1_native;

    // Bit 1 and control point CP1 on c2.
    assign sum[1]   = a[1] ^ b[1] ^ c1;
    assign c2_native = (a[1] & b[1]) | (a[1] & c1) | (b[1] & c1);
    assign c2        = test_mode ? scan_q[1] : c2_native;

    // Bit 2 and control point CP2 on c3.
    assign sum[2]   = a[2] ^ b[2] ^ c2;
    assign c3_native = (a[2] & b[2]) | (a[2] & c2) | (b[2] & c2);
    assign c3        = test_mode ? scan_q[2] : c3_native;

    // Final stage has no internal-carry control point.
    assign sum[3] = a[3] ^ b[3] ^ c3;
    assign cout   = (a[3] & b[3]) | (a[3] & c3) | (b[3] & c3);

    assign scan_out = scan_q[5];

    // Muxed-D scan behavior: shift when SE=1, functional capture when SE=0.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            scan_q <= 6'b0;
        end else if (scan_enable) begin
            scan_q <= {scan_q[4:0], scan_in};
        end else begin
            scan_q[0] <= c1_native; // CP0 functional data input
            scan_q[1] <= c2_native; // CP1 functional data input
            scan_q[2] <= c3_native; // CP2 functional data input
            scan_q[3] <= c1;        // OP0 observes effective c1
            scan_q[4] <= c2;        // OP1 observes effective c2
            scan_q[5] <= c3;        // OP2 observes effective c3
        end
    end
endmodule

`default_nettype wire


