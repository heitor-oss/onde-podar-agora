"""
Ranking "Onde podar agora" · J13 — Deixar um período de fora
Tipo: principal

O que faz:
    Otimiza com 7 períodos e testa no oitavo, para cada período.

Lê:
    código de J12_robustez_dos_pesos.py
Grava:
    nada (só imprime resultados)
Usado em:
    Decisão de manter os pesos.
Script original da análise: light/pri_loo.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

exec(open(etapa('pri_rob.py')).read().split("R={}")[0])
cand={'atuais':[25,15,40,10,10],'ótimo conjunto':[25,10,50,10,5]}
res=[]
for T in CUTS:
    others=[t for t in CUTS if t!=T]
    blocked=[t for t in CUTS if abs((pd.Timestamp(t)-pd.Timestamp(T)).days)>=365]
    w1,_=optm(others); r={'T':T,'LOO pesos':w1,'LOO':obj(T,w1)}
    if blocked: w2,_=optm(blocked); r.update({'bloq pesos':w2,'bloq':obj(T,w2)})
    for n,w in cand.items(): r[n]=obj(T,w)
    res.append(r); print({k:(round(v*100,1) if isinstance(v,float) else v) for k,v in r.items()},flush=True)
D=pd.DataFrame(res)
print('médias:',{c:round(D[c].mean()*100,2) for c in ['LOO','atuais','ótimo conjunto']}, 'bloq (só onde existe):',round(D['bloq'].dropna().mean()*100,2),'atuais nesses:',round(D.loc[D['bloq'].notna(),'atuais'].mean()*100,2))
# per-outcome hit rates at top-500 averaged over periods for atuais vs ótimo conjunto vs anteriores
for n,w in {'atuais':[25,15,40,10,10],'ótimo conjunto':[25,10,50,10,5],'anteriores':[30,25,20,15,10]}.items():
    H=np.mean([hits(T,w) for T in CUTS],0)  # 3 outcomes x 3 ks
    print(n,'@200',np.round(H[:,0]*100,1),'@500',np.round(H[:,1]*100,1))
# how much existing backlog (com) and waiting the top-500 covers, current data
