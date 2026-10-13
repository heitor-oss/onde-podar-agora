"""
Ranking "Onde podar agora" · J12 — Robustez dos pesos
Tipo: principal

O que faz:
    Ótimo por período, 3.000 combinações sorteadas, ótimo conjunto, teste rolante, curva do
    peso da Light, metas alternativas e bootstrap.

Lê:
    pri_roll.pkl
Grava:
    pri_rob.pkl
Usado em:
    Página: "Os pesos valem em outros períodos?".
Script original da análise: light/pri_rob.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle, json
O=pickle.load(open('pri_roll.pkl','rb'))
L=lambda v,cap: np.clip(np.log1p(v)/np.log1p(cap),0,1)
K=['risco','com','light','prev','esp']
def comps(g):
    return np.stack([L(g.risco+g.queda12,12),L(g.com,8),L(g.light,12),np.clip((g.prob-0.07)/0.48,0,1),np.clip(g.esp/365,0,1)],1)
Y=['y_queda','y_rq','y_light']; KS=(200,500,1000)
P={}
for T,g in O.items():
    a=g.active.values; P[T]=dict(X=comps(g)[a],Y=np.stack([(g[y].values[a]>0) for y in Y],1))
def hits(T,w):
    X,Yv=P[T]['X'],P[T]['Y']; s=X@np.asarray(w,float); o=np.argsort(-s,kind='stable')
    return np.array([[Yv[o[:k],j].mean() for k in KS] for j in range(3)])   # 3 x 3
def obj(T,w,goal=None):
    h=hits(T,w); return h.mean() if goal is None else h[goal].mean()
CUTS=list(O)
W={'atuais':[25,15,40,10,10],'anteriores':[30,25,20,15,10],'iguais':[20,20,20,20,20],'só Light':[0,0,100,0,0],'só risco':[100,0,0,0,0]}
def opt(Ts,w0,goal=None,step=5):
    w=list(w0); f=lambda w: np.mean([obj(T,w,goal) for T in Ts]); best=f(w); imp=True
    while imp:
        imp=False
        for i in range(5):
            for j in range(5):
                if i==j or w[j]<step: continue
                w2=w.copy(); w2[i]+=step; w2[j]-=step; v=f(w2)
                if v>best+1e-5: best,w,imp=v,w2,True
    return w,best
def optm(Ts,goal=None):
    c=[opt(Ts,w0,goal) for w0 in ([25,15,40,10,10],[20,20,20,20,20],[30,25,20,15,10],[10,10,60,10,10])]
    return max(c,key=lambda x:x[1])
R={}
# A + C: per-period optimum and regret
rows=[]
for T in CUTS:
    w,b=optm([T]); r={'corte':T,'ótimo do período':w,'obj ótimo':b}
    for n,ww in W.items(): r[n]=obj(T,ww)
    rows.append(r); print(T,w,round(b*100,1),{n:round(r[n]*100,1) for n in W},flush=True)
A=pd.DataFrame(rows); R['A']=rows
# random weights: rank of atuais per period
rng=np.random.default_rng(0); RW=rng.dirichlet(np.ones(5),3000)*100
RS=np.array([[obj(T,w) for T in CUTS] for w in RW])
rank_at=[(RS[:,i]<obj(T,W['atuais'])).mean() for i,T in enumerate(CUTS)]
rank_an=[(RS[:,i]<obj(T,W['anteriores'])).mean() for i,T in enumerate(CUTS)]
print('percentil atuais entre 3000 aleatórios',np.round(rank_at,3)); print('percentil anteriores',np.round(rank_an,3))
pooled=RS.mean(1); top=np.argsort(-pooled)[:30]
print('melhor aleatório no conjunto',np.round(RW[top[0]]),round(pooled[top[0]]*100,2),'atuais',round(np.mean([obj(T,W['atuais']) for T in CUTS])*100,2))
print('faixa dos 30 melhores aleatórios (média por sinal, min, max):'); print(pd.DataFrame(RW[top],columns=K).describe().loc[['mean','min','max']].round(0))
R['rank_at']=rank_at; R['rank_an']=rank_an
# pooled optimum over all periods
wp,bp=optm(CUTS); print('ótimo conjunto (todos os períodos)',wp,round(bp*100,2),flush=True); R['pooled']=(wp,bp)
# B: rolling honest test
roll=[]
for T in CUTS:
    tr=[t for t in CUTS if pd.Timestamp(t)+pd.Timedelta(days=365)<=pd.Timestamp(T)]
    if not tr: continue
    w,_=optm(tr); roll.append({'teste':T,'treino':tr,'pesos':w,'obj rolante':obj(T,w),'obj atuais':obj(T,W['atuais']),'obj anteriores':obj(T,W['anteriores']),'obj ótimo':A.set_index('corte').loc[T,'obj ótimo']})
    print('rolante',T,'treino',tr,'pesos',w,{k:round(v*100,1) for k,v in roll[-1].items() if k.startswith('obj')},flush=True)
R['roll']=roll
# D: light sweep (others in proportion 25:15:10:10)
sweep={}
for lw in range(0,85,5):
    rest=100-lw; w=[rest*25/60,rest*15/60,lw,rest*10/60,rest*10/60]
    sweep[lw]=[obj(T,w) for T in CUTS]
S=pd.DataFrame(sweep,index=CUTS).T; print((S*100).round(1)); R['sweep']={k:v for k,v in sweep.items()}
# E: goal-specific optima (pooled)
for gi,gn in enumerate(['quedas','risco/queda','novo Light']):
    w,b=optm(CUTS,gi); print('ótimo para',gn,w,round(b*100,1),'| atuais nesse objetivo',round(np.mean([obj(T,W['atuais'],gi) for T in CUTS])*100,1),flush=True)
    R['goal_'+gn]=(w,b,np.mean([obj(T,W['atuais'],gi) for T in CUTS]))
# bootstrap SE for atuais vs anteriores and atuais vs optimum (per period)
def boot(T,w1,w2,n=200):
    X,Yv=P[T]['X'],P[T]['Y']; d=[]
    for _ in range(n):
        i=rng.integers(0,len(X),len(X)); Xb,Yb=X[i],Yv[i]
        def ob(w):
            o=np.argsort(-(Xb@np.asarray(w,float)),kind='stable'); return np.mean([[Yb[o[:k],j].mean() for k in KS] for j in range(3)])
        d.append(ob(w1)-ob(w2))
    return np.mean(d),np.percentile(d,[2.5,97.5])
for T in CUTS:
    wopt=A.set_index('corte').loc[T,'ótimo do período']
    m1,ci1=boot(T,W['atuais'],W['anteriores']); m2,ci2=boot(T,wopt,W['atuais'])
    print('boot',T,'atuais-anteriores',round(m1*100,1),np.round(ci1*100,1),'| ótimo-atuais',round(m2*100,1),np.round(ci2*100,1),flush=True)
pickle.dump(R,open('pri_rob.pkl','wb'))
