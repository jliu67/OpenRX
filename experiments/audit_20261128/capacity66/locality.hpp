// SPDX-License-Identifier: BSD-3-Clause
// Streaming logical-SP traffic policies only; no modeled clocks or data mutation.
#include <algorithm>
#include <array>
#include <cstdint>
#include <ctime>
#include <vector>
#include <string>
namespace locality37 {
constexpr unsigned SP=2097152,NL=SP/64,NP=8;
enum Phase{INIT,ENTRY_R,ENTRY_FP,BC_READ,BC_WRITE,TAIL_R,TAIL_F,FINAL};
static const char* phase_names[]={"init","entry_R","entry_FP","bytecode_read","bytecode_write","tail_R","tail_F","final_scan"};
inline void need(bool b,const char*m){if(!b)throw std::runtime_error(m);}
inline unsigned region(unsigned a){return a<16384?0:a<262144?1:2;}
inline unsigned mask(unsigned a,unsigned w){need((w==8||w==16)&&a%w==0&&a+w<=SP&&(a/64)==((a+w-1)/64),"SP access width/alignment/bounds");return((1u<<(w/8))-1)<<((a%64)/8);}
struct Counts{
 uint64_t accesses=0,local=0,tag_hits=0,read_hits=0,read_fills=0,rfo=0,write_hits=0,write_misses=0,writebacks=0,partial_wb=0,dirty_evict=0,clean_evict=0,final_wb=0;
 void emit(std::ostream&o)const{o<<"{\"accesses\":"<<accesses<<",\"local_bypass\":"<<local<<",\"tag_hits\":"<<tag_hits<<",\"read_data_hits\":"<<read_hits<<",\"read_fills64\":"<<read_fills<<",\"RFO_reads64\":"<<rfo<<",\"write_hits\":"<<write_hits<<",\"write_misses\":"<<write_misses<<",\"writebacks64\":"<<writebacks<<",\"partial_writebacks64\":"<<partial_wb<<",\"dirty_evictions\":"<<dirty_evict<<",\"clean_evictions\":"<<clean_evict<<",\"final_flush_writebacks\":"<<final_wb<<",\"masked_backing_bytes\":"<<64*(read_fills+rfo+writebacks)<<",\"RMW_backing_bytes\":"<<64*(read_fills+rfo+writebacks+partial_wb)<<"}";}
};
struct Cache{
 struct Line{unsigned tag=0;uint8_t valid=0,dirty=0;bool present=false;uint64_t stamp=0;};
 std::string name;unsigned local_bytes,bytes,sets;bool eager;std::vector<Line>line;Counts c,snap[3];
 Cache(std::string n,unsigned l,unsigned b,bool e):name(n),local_bytes(l),bytes(b),sets(b/256),eager(e),line(b/64){need(b>=256&&b%256==0,"four-way cache size");}
 void evict(Line&v,bool final){if(!v.present)return;if(v.dirty){++c.writebacks;if(v.valid!=255)++c.partial_wb;if(final)++c.final_wb;else ++c.dirty_evict;}else if(!final)++c.clean_evict;}
 void access(unsigned a,unsigned w,bool write,uint64_t seq){
  ++c.accesses;if(a<local_bytes){++c.local;return;}unsigned m=mask(a,w),ln=a/64,set=ln%sets;Line* hit=nullptr;Line* victim=nullptr;
  for(unsigned i=0;i<4;i++){Line&v=line[set*4+i];if(v.present&&v.tag==ln)hit=&v;if(!victim||(!v.present&&victim->present)||(v.present==victim->present&&v.stamp<victim->stamp))victim=&v;}
  bool found=hit;if(found)++c.tag_hits;else{evict(*victim,false);*victim=Line{};victim->present=true;victim->tag=ln;hit=victim;}
  Line&v=*hit;v.stamp=seq;
  if(write){if(found)++c.write_hits;else{++c.write_misses;if(eager){++c.rfo;v.valid=255;}}v.valid|=m;v.dirty|=m;}
  else if((v.valid&m)==m)++c.read_hits;else{++c.read_fills;v.valid=255;}
 }
 void snapshot(unsigned i){need(i<3,"snapshot");snap[i]=c;}
 void flush(){for(auto&v:line)evict(v,true);}
 void emit(std::ostream&o)const{o<<"{\"name\":\""<<name<<"\",\"static_local_bytes\":"<<local_bytes<<",\"cache_bytes\":"<<bytes<<",\"ways\":4,\"sector_bytes\":8,\"eager_RFO\":"<<(eager?"true":"false")<<",\"stages\":[";for(unsigned i=0;i<3;i++){if(i)o<<',';snap[i].emit(o);}o<<"],\"after_final_flush\":";c.emit(o);o<<"}";}
};
struct Static{
 unsigned bytes;uint64_t events=0,local=0,read_req=0,write_req=0,read_runs=0,write_runs=0,partial_runs=0;bool pending=false,wr=false;unsigned ln=0,phase=0,words=0;
 explicit Static(unsigned b):bytes(b){}
 void flush(){if(!pending)return;if(wr){++write_runs;if(words!=255)++partial_runs;}else ++read_runs;pending=false;}
 void access(unsigned a,unsigned w,bool write,unsigned ph){++events;if(a<bytes){++local;flush();return;}if(write)++write_req;else ++read_req;unsigned l=a/64;if(!pending||l!=ln||wr!=write||phase!=ph){flush();pending=true;ln=l;wr=write;phase=ph;words=0;}words|=mask(a,w);}
 void emit(std::ostream&o)const{o<<"{\"local_bytes\":"<<bytes<<",\"events\":"<<events<<",\"local_events\":"<<local<<",\"external_read_events\":"<<read_req<<",\"external_write_events\":"<<write_req<<",\"read_runs64\":"<<read_runs<<",\"write_runs64\":"<<write_runs<<",\"partial_write_runs64\":"<<partial_runs<<",\"unmerged_masked_bytes\":"<<64*(read_req+write_req)<<",\"unmerged_RMW_bytes\":"<<64*(read_req+2*write_req)<<",\"adjacent_combined_masked_bytes\":"<<64*(read_runs+write_runs)<<",\"adjacent_combined_RMW_bytes\":"<<64*(read_runs+write_runs+partial_runs)<<"}";}
};
struct Sample{uint64_t seq;unsigned a,w,ph,prog,iter;bool write;};
struct Traffic{
 struct Stat{uint64_t events=0,bytes=0,width8=0,width16=0;};
 Stat stats[NP][2][3]{};uint64_t program[8][NP][2]{};uint64_t last[NL]{},gaps[10]{},same_line=0,same_beat=0,same_word=0;uint8_t words[NP][2][NL]{};
 uint64_t seq=0,rng=UINT64_C(0x6c6f63616c333700);unsigned last_addr=0;std::vector<Sample>sample;std::vector<Cache>cache;std::array<Static,4>fixed={Static(0),Static(16384),Static(262144),Static(SP)};
 blake2b_state hash;uint8_t buffer[3072]{};size_t used=0;std::array<uint8_t,32>hashout{};
 Traffic(){need(!blake2b_init(&hash,32),"stream hash init");for(bool e:{true,false}){std::string s=e?"_eager":"_sector";cache.emplace_back("cache16K"+s,0,16384,e);cache.emplace_back("cache256K"+s,0,262144,e);cache.emplace_back("static16K_cache256K"+s,16384,262144,e);cache.emplace_back("static256K_cache16K"+s,262144,16384,e);}sample.reserve(128);}
 void event(unsigned ph,bool write,unsigned a,unsigned w,unsigned prog=255,unsigned iter=65535){
  need(ph<NP,"phase");unsigned m=mask(a,w),r=region(a);need(region(a+w-1)==r,"no region straddle");++seq;Stat&s=stats[ph][write][r];++s.events;s.bytes+=w;if(w==8)++s.width8;else ++s.width16;if(prog<8)program[prog][ph][write]+=w;words[ph][write][a/64]|=m;
  if(seq>1){same_line+=(a/64==last_addr/64);same_beat+=(a/16==last_addr/16);same_word+=(a/8==last_addr/8);}last_addr=a;
  uint64_t old=last[a/64];if(!old)++gaps[0];else{uint64_t g=seq-old;unsigned k=g==1?1:g<=4?2:g<=16?3:g<=64?4:g<=256?5:g<=1024?6:g<=4096?7:g<=16384?8:9;++gaps[k];}last[a/64]=seq;
  for(auto&c:cache)c.access(a,w,write,seq);for(auto&s:fixed)s.access(a,w,write,ph);
  Sample e{seq,a,w,ph,prog,iter,write};if(sample.size()<128)sample.push_back(e);else{rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;uint64_t j=rng%seq;if(j<128)sample[j]=e;}
  uint8_t* p=buffer+used;for(unsigned k=0;k<8;k++)p[k]=uint8_t(seq>>(8*k));for(unsigned k=0;k<4;k++)p[8+k]=uint8_t(a>>(8*k));p[12]=uint8_t(iter);p[13]=uint8_t(iter>>8);p[14]=uint8_t(prog);p[15]=uint8_t(ph);p[16]=uint8_t(write);p[17]=uint8_t(w);for(unsigned k=18;k<24;k++)p[k]=0;used+=24;if(used==sizeof(buffer)){need(!blake2b_update(&hash,buffer,used),"stream update");used=0;}
 }
 void scan(unsigned ph,bool write){for(unsigned a=0;a<SP;a+=16)event(ph,write,a,16);}
 void snapshot(unsigned i){for(auto&s:fixed)s.flush();for(auto&c:cache)c.snapshot(i);}
 void finish(){snapshot(2);for(auto&c:cache)c.flush();if(used)need(!blake2b_update(&hash,buffer,used),"stream final update");need(!blake2b_final(&hash,hashout.data(),32),"stream final");std::sort(sample.begin(),sample.end(),[](const Sample&a,const Sample&b){return a.seq<b.seq;});}
 void emit(std::ostream&o)const{
  o<<"{\"events\":"<<seq<<",\"ordered_event_BLAKE2b256\":\"";static const char*hex="0123456789abcdef";for(auto x:hashout)o<<hex[x>>4]<<hex[x&15];o<<"\",\"phase_region_RW\":[";bool first=true;
  for(unsigned p=0;p<NP;p++)for(unsigned rw=0;rw<2;rw++)for(unsigned r=0;r<3;r++){const Stat&s=stats[p][rw][r];if(!s.events)continue;if(!first)o<<',';first=false;uint64_t hist[9]{};for(unsigned l=0;l<NL;l++){unsigned rr=region(l*64);if(rr==r&&words[p][rw][l])++hist[__builtin_popcount(unsigned(words[p][rw][l]))];}o<<"{\"phase\":\""<<phase_names[p]<<"\",\"write\":"<<rw<<",\"address_region\":"<<r<<",\"events\":"<<s.events<<",\"useful_bytes\":"<<s.bytes<<",\"width8\":"<<s.width8<<",\"width16\":"<<s.width16<<",\"distinct_words_per_touched64Bline_hist\":[";for(unsigned k=0;k<9;k++)o<<(k?",":"")<<hist[k];o<<"]}";}
  o<<"],\"program_phase_RW_bytes\":[";for(unsigned p=0;p<8;p++){if(p)o<<',';o<<'[';for(unsigned ph=0;ph<NP;ph++){if(ph)o<<',';o<<'['<<program[p][ph][0]<<','<<program[p][ph][1]<<']';}o<<']';}
  o<<"],\"line_interreference_event_gap_hist\":[";for(unsigned i=0;i<10;i++)o<<(i?",":"")<<gaps[i];o<<"],\"consecutive_same64Bline\":"<<same_line<<",\"consecutive_same16Bbeat\":"<<same_beat<<",\"consecutive_same8Bword\":"<<same_word<<",\"static_policies\":[";for(unsigned i=0;i<fixed.size();i++){if(i)o<<',';fixed[i].emit(o);}o<<"],\"cache_policies\":[";for(unsigned i=0;i<cache.size();i++){if(i)o<<',';cache[i].emit(o);}o<<"],\"reservoir128\":[";for(unsigned i=0;i<sample.size();i++){const auto&s=sample[i];o<<(i?",":"")<<'['<<s.seq<<','<<s.ph<<','<<s.write<<','<<s.a<<','<<s.w<<','<<s.prog<<','<<s.iter<<']';}o<<"]}";
 }
};
inline int selftest(){
 {Cache c("t",0,256,false);c.access(0,8,false,1);c.access(8,8,false,2);need(c.c.read_fills==1&&c.c.read_hits==1,"read miss/hit");}
 {Cache c("t",0,256,false);for(unsigned i=0;i<5;i++)c.access(i*64,8,true,i+1);need(c.c.dirty_evict==1&&c.c.partial_wb==1&&c.c.rfo==0,"partial dirty eviction");c.flush();need(c.c.writebacks==5&&c.c.partial_wb==5,"partial dirty flush");}
 {Cache c("t",0,256,true);for(unsigned i=0;i<5;i++)c.access(i*64,8,true,i+1);c.flush();need(c.c.rfo==5&&c.c.writebacks==5&&c.c.partial_wb==0,"eager RFO");}
 {Cache c("t",0,256,false);for(unsigned i=0;i<8;i++)c.access(i*8,8,true,i+1);c.flush();need(c.c.writebacks==1&&c.c.partial_wb==0&&c.c.rfo==0,"full overwrite combine");}
 {Cache c("t",0,256,false);c.access(0,8,true,1);c.access(8,8,false,2);c.flush();need(c.c.read_fills==1&&c.c.partial_wb==0,"read fills missing sector");}
 {Cache c("t",0,256,false);c.access(0,8,true,1);c.access(0,8,false,2);c.flush();need(c.c.read_hits==1&&c.c.read_fills==0&&c.c.partial_wb==1,"read hits written sector");}
 {Cache c("t",0,256,false);for(unsigned i=0;i<4;i++)c.access(i*64,8,false,i+1);c.access(0,8,false,5);c.access(256,8,false,6);c.access(64,8,false,7);need(c.c.read_fills==6&&c.c.read_hits==1,"true LRU not FIFO");}
 {Static s(16384);s.access(16376,8,false,ENTRY_R);s.access(16384,8,false,ENTRY_R);s.flush();need(s.local==1&&s.read_runs==1,"static boundary");}
 {Static s(0);for(unsigned i=0;i<8;i++)s.access(i*8,8,true,TAIL_R);s.flush();need(s.write_req==8&&s.write_runs==1&&s.partial_runs==0,"run full write");}
 {Static s(0);s.access(0,8,true,BC_WRITE);s.access(8,8,true,BC_WRITE);s.access(0,8,false,BC_READ);s.flush();need(s.write_runs==1&&s.partial_runs==1&&s.read_runs==1,"run direction boundary");}
 std::cout<<"PASS locality37 directed_tests=10 no_native_or_dataset_allocation=1\n";return 0;
}
}
