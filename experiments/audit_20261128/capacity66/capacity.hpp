// SPDX-License-Identifier: BSD-3-Clause
// Additive policies over locality37's unchanged source-event stream.
// Counts a declared uncombined 16B macro interface, not measured silicon traffic.
namespace capacity66 {
using namespace locality37;
struct PhaseCount {
 uint64_t events=0,read16=0,write16=0,partial8=0,read_events=0,write_events=0,read64=0,write64=0,partial64=0;
};
struct Prefix {
 Static policy;std::array<PhaseCount,NP> phase{};
 explicit Prefix(unsigned n):policy(n){need(n%64==0&&n<=SP,"aligned static prefix");}
 void flush(){
  if(!policy.pending)return;auto& p=phase[policy.phase];
  if(policy.wr){++p.write64;if(policy.words!=255)++p.partial64;}else ++p.read64;
  policy.flush();
 }
 void access(unsigned ph,bool write,unsigned a,unsigned w){
  need(ph<NP,"phase");mask(a,w);auto& p=phase[ph];++p.events;
  bool local=a<policy.bytes;
  if(policy.pending&&(local||policy.ln!=a/64||policy.wr!=write||policy.phase!=ph))flush();
  if(local){if(write){++p.write16;p.partial8+=(w==8);}else ++p.read16;}
  else{if(write)++p.write_events;else ++p.read_events;}
  policy.access(a,w,write,ph);
 }
 void emit(std::ostream&o)const{
  o<<"{\"local_bytes\":"<<policy.bytes<<",\"logical_policy\":";policy.emit(o);
  o<<",\"phase_counts\":[";
  for(unsigned i=0;i<NP;i++){const auto&p=phase[i];
   o<<(i?",":"")<<"{\"phase\":\""<<phase_names[i]<<"\",\"events\":"<<p.events
    <<",\"local_read16\":"<<p.read16<<",\"local_write16\":"<<p.write16
    <<",\"local_partial_write8\":"<<p.partial8<<",\"external_read_events\":"<<p.read_events
    <<",\"external_write_events\":"<<p.write_events<<",\"external_read64\":"<<p.read64
    <<",\"external_write64\":"<<p.write64<<",\"external_partial_write64\":"<<p.partial64<<"}";
  }
  o<<"],\"refill16\":0,\"writeback16\":0,\"tag_metadata16\":0}";
 }
};
struct Traffic:locality37::Traffic {
 std::array<Prefix,7> prefixes={Prefix(0),Prefix(16384),Prefix(262144),Prefix(524288),Prefix(1048576),Prefix(1572864),Prefix(SP)};
 void event(unsigned ph,bool write,unsigned a,unsigned w,unsigned prog=255,unsigned iter=65535){
  locality37::Traffic::event(ph,write,a,w,prog,iter);
  for(auto& p:prefixes)p.access(ph,write,a,w);
 }
 void scan(unsigned ph,bool write){for(unsigned a=0;a<SP;a+=16)event(ph,write,a,16);}
 void snapshot(unsigned i){locality37::Traffic::snapshot(i);for(auto& p:prefixes)p.flush();}
 void finish(){for(auto& p:prefixes)p.flush();locality37::Traffic::finish();}
 void emit(std::ostream&o)const{
  std::ostringstream legacy;locality37::Traffic::emit(legacy);std::string s=legacy.str();
  need(!s.empty()&&s.back()=='}',"closed inherited stream");s.pop_back();o<<s;
  o<<",\"static_capacity66\":[";for(unsigned i=0;i<prefixes.size();i++){if(i)o<<',';prefixes[i].emit(o);}o<<"]}";
 }
};
inline int selftest(){
 // Preserve all ten old cache/coalescer checks, then test only added accounting.
 locality37::selftest();
 for(unsigned n:{524288u,1048576u,1572864u}){
  Prefix p(n);p.access(ENTRY_R,false,n-16,16);p.access(BC_WRITE,true,n-8,8);
  p.access(BC_READ,false,n,8);p.access(BC_WRITE,true,n+8,8);p.flush();
  need(p.policy.events==4&&p.policy.local==2,"capacity boundary routing");
  need(p.phase[ENTRY_R].read16==1&&p.phase[BC_WRITE].write16==1&&p.phase[BC_WRITE].partial8==1,"local16B accounting");
  need(p.phase[BC_READ].read64==1&&p.phase[BC_WRITE].write64==1&&p.phase[BC_WRITE].partial64==1,"external64B phase accounting");
 }
 {Prefix p(0);for(unsigned i=0;i<8;i++)p.access(TAIL_R,true,8*i,8);p.flush();need(p.phase[TAIL_R].write64==1&&p.phase[TAIL_R].partial64==0,"full external line combines");}
 {Prefix p(SP);p.access(BC_WRITE,true,0,8);p.access(TAIL_F,true,0,16);p.access(FINAL,false,0,16);p.flush();
  need(p.policy.local==3&&p.policy.read_runs==0&&p.policy.write_runs==0,"all local no backing");
  need(p.phase[BC_WRITE].partial8==1&&p.phase[TAIL_F].partial8==0,"mask versus RMW sensitivity");}
 {Prefix p(0);p.access(ENTRY_R,false,0,8);p.access(ENTRY_FP,false,8,8);p.flush();need(p.phase[ENTRY_R].read64==1&&p.phase[ENTRY_FP].read64==1,"phase boundary cannot combine");}
 {bool rejected=false;try{Prefix p(524288);p.access(BC_READ,false,524284,8);}catch(const std::runtime_error&){rejected=true;}need(rejected,"misalignment rejected");}
 std::cout<<"PASS capacity66 directed_groups=7 inherited_groups=10 no_native_or_dataset_allocation=1\n";return 0;
}
}
