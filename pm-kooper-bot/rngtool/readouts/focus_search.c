/* Brute-force gRandSeed from star-power shimmer particle colours.
   For every 32-bit state s (= gRandSeed just before particle J0's r draw), simulate the colour draws of
   particles J0..55 (status_star_shimmer.c: r=rand_int(127), g=rand_int(127-r), b=rand_int(127-r-g)) and
   score them against measured capture colours with a capped (robust) chi-square. Early rejection.
   input file (stdin): first line: BASE SAT  A(3x4 row-major: Y,U,V rows over R',G',B',1)  sY sU sV  CAP  T0 TSLOPE
                       then lines: j w Y U V      (w=0: particle not measured)
   R' = min(SAT, BASE + raw) per channel. cost_j = min(CAP, sum_c ((meas-pred)/s_c)^2) * w
   output: top candidates "state cost" sorted by cost; survivor count on stderr.  build: gcc -O3 -march=native -fopenmp -o focus_search focus_search.c
   (focus_seed.py builds it in the temp dir and drives it) */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
static inline uint32_t adv(uint32_t s){ return s*0x5D588B65u+1u; }
static inline uint32_t rii(uint32_t *s, uint32_t mx){ uint32_t p=0xFFFFFFFFu/(mx+1); if(!p)p=1; uint32_t r; do{ *s=adv(*s); r=*s/p; }while(r>=mx+1); return r; }
static inline uint32_t rint_(uint32_t *s, int mx){ if(mx<0)mx=-mx; if(mx==0) return 0; if(mx==1) return rii(s,1000)>500; if(mx==100) return rii(s,1009)/10; return rii(s,mx); }
static float P[128][128][128][3]; /* pred YUV by raw r,g,b (only valid r+g+b<=127) */
int main(int argc,char**argv){
  double BASE,SAT,A[12],sg[3],CAP,T0,TS; int J0=argc>1?atoi(argv[1]):5; int KEEP=argc>2?atoi(argv[2]):64;
  if(scanf("%lf %lf",&BASE,&SAT)!=2) return 1; for(int i=0;i<12;i++) if(scanf("%lf",&A[i])!=1) return 1;
  if(scanf("%lf %lf %lf %lf %lf %lf",&sg[0],&sg[1],&sg[2],&CAP,&T0,&TS)!=6) return 1;
  float w[56]={0}, M[56][3]; int j; double ww,y,u,v;
  while(scanf("%d %lf %lf %lf %lf",&j,&ww,&y,&u,&v)==5){ w[j]=ww; M[j][0]=y; M[j][1]=u; M[j][2]=v; }
  for(int r=0;r<128;r++)for(int g=0;g+r<128;g++)for(int b=0;b+g+r<128;b++){
    double c[3]={r,g,b}; for(int k=0;k<3;k++){ c[k]+=BASE; if(c[k]>SAT)c[k]=SAT; }
    for(int o=0;o<3;o++) P[r][g][b][o]=A[o*4]*c[0]+A[o*4+1]*c[1]+A[o*4+2]*c[2]+A[o*4+3]; }
  float is[3]={1/sg[0]/sg[0],1/sg[1]/sg[1],1/sg[2]/sg[2]};
  int nth=omp_get_max_threads(); 
  typedef struct{uint32_t s; float c; } C; C *best=calloc((size_t)nth*KEEP,sizeof(C)); int *nb=calloc(nth,sizeof(int));
  for(int i=0;i<nth*KEEP;i++) best[i].c=1e30f;
  uint64_t survivors=0;
  #pragma omp parallel reduction(+:survivors)
  { int t=omp_get_thread_num(); C*B=best+(size_t)t*KEEP; float worst=1e30f; int nbt=0;
    #pragma omp for schedule(dynamic,1<<16)
    for(int64_t ss=0; ss<(1ll<<32); ss++){
      uint32_t s=(uint32_t)ss; float cost=0; int n=0; int dead=0;
      for(int jj=J0; jj<56; jj++){
        int r=rint_(&s,127), g=rint_(&s,127-r), b=rint_(&s,127-r-g);
        if(w[jj]>0){ const float*p=P[r][g][b]; float d0=M[jj][0]-p[0],d1=M[jj][1]-p[1],d2=M[jj][2]-p[2];
          float c=d0*d0*is[0]+d1*d1*is[1]+d2*d2*is[2]; if(c>CAP)c=CAP; cost+=c*w[jj]; n++;
          if(cost>T0+TS*n){ dead=1; break; } }
      }
      if(dead) continue; survivors++;
      if(nbt<KEEP){ B[nbt].s=(uint32_t)ss; B[nbt].c=cost; nbt++; }
      else { int wi=0; for(int i=1;i<KEEP;i++) if(B[i].c>B[wi].c) wi=i; if(cost<B[wi].c){B[wi].s=(uint32_t)ss;B[wi].c=cost;} }
    }
    nb[t]=nbt; (void)worst;
  }
  /* merge */
  int tot=0; C*all=malloc(sizeof(C)*nth*KEEP); for(int t=0;t<nth;t++) for(int i=0;i<nb[t];i++) all[tot++]=best[(size_t)t*KEEP+i];
  for(int i=0;i<tot;i++) for(int k=i+1;k<tot;k++) if(all[k].c<all[i].c){C x=all[i];all[i]=all[k];all[k]=x;}
  fprintf(stderr,"survivors %llu\n",(unsigned long long)survivors);
  for(int i=0;i<tot && i<KEEP;i++) printf("%08x %.3f\n",all[i].s,all[i].c);
  return 0;
}
