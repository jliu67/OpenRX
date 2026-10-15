// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_blake2b_micro #(parameter integer ORIGINAL=0,DIGEST_BYTES=64);
 reg clk=0,rst=1;always #5 clk=~clk;
 reg [2047:0] message;reg [511:0] gold64,gold32;reg [4095:0] path;integer f,n,c;
 reg init=0,next=0,final_block=0;reg [1023:0] block;reg [127:0] length;
 wire ready,valid;wire [511:0] digest;wire [511:0] little_digest;
 genvar b;generate for(b=0;b<64;b=b+1)begin assign little_digest[8*b+:8]=b<DIGEST_BYTES?digest[511-8*b-:8]:8'b0;end endgenerate
 generate if(ORIGINAL)begin:original
  blake2_core #(.DIGEST_LENGTH(DIGEST_BYTES)) dut(clk,!rst,init,next,final_block,block,length,ready,digest,valid);
 end else begin:corrected
  randomx_blake2b_chain_core #(.DIGEST_LENGTH(DIGEST_BYTES)) dut(clk,!rst,init,next,final_block,block,length,ready,digest,valid);
 end endgenerate
 task set_block;input second;begin for(n=0;n<128;n=n+1)block[1023-8*n-:8]=message[(second?1024:0)+8*n+:8];end endtask
 task tick;begin @(posedge clk);#1;end endtask
 initial begin
  if(!$value$plusargs("vectors=%s",path))$fatal(1,"vectors");f=$fopen(path,"r");if($fscanf(f,"%h %h %h",message,gold64,gold32)!=3)$fatal(1,"native vector");$fclose(f);
  tick;tick;rst=0;set_block(0);length=128;final_block=0;init=1;tick;init=0;
  c=0;while(!valid)begin tick;c=c+1;if(c>40)$fatal(1,"first block timeout");end
  set_block(1);length=256;final_block=1;next=1;tick;next=0;
  c=0;while(!valid)begin tick;c=c+1;if(c>40)$fatal(1,"second block timeout");end
  if(little_digest!==(DIGEST_BYTES==64?gold64:gold32))$fatal(1,"native two-block mismatch original=%0d got=%h expected=%h",ORIGINAL,little_digest,DIGEST_BYTES==64?gold64:gold32);
  $display("PASS blake2b_micro original=%0d digest_bytes=%0d two_block_native=1",ORIGINAL,DIGEST_BYTES);$finish;
 end
 initial begin #10000;$fatal(1,"deadlock");end
endmodule
