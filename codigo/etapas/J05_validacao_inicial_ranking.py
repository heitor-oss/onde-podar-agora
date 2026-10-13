"""
Ranking "Onde podar agora" · J05 — Validação da primeira versão da nota
Tipo: exploratório

O que faz:
    Teste de 2025 da nota com os pesos antigos e o status de hoje (versão superada por
    J07–J13).

Lê:
    df.pkl, gb.pkl, código de H02_modelo1_dados.py
Grava:
    nada (só imprime resultados)
Usado em:
    Histórico.
Script original da análise: light/rank_bt.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle
src=open(etapa('m1.py')).read(); exec(src.split("def label")[0])
gb=pickle.load(open('gb.pkl','rb'))
tc=df[df.cep.notna()].groupby('tr').cep.agg(lambda s:s.mode().iloc[0]).astype('int64')
A=pd.read_pickle('df.pkl'); A=A[A.cep.notna()].copy(); A['cep']=A.cep.astype('int64'); A['ini']=pd.to_datetime(A.data_inicio)
poda=A.subtipo.str.contains('Poda'); opn=A.status.isin(['Aberto','Em Andamento'])
riskq=A.subtipo.isin(['Avaliação de risco de queda da árvore','Retirada de árvore caída'])|A.subtipo.str.contains('Remoção')
Lg=lambda v,cap: np.clip(np.log1p(v)/np.log1p(cap),0,1)
def score(T):
    h=A[A.ini<T]; age=(T-h.ini).dt.days; p=poda[h.index]; o=opn[h.index]
    g=pd.DataFrame(index=A.cep.unique())
    g['comlurb']=h[p&o&(age<=730)].groupby('cep').size(); g['light']=h[p&h.status.eq('Pendente')].groupby('cep').size()
    g['risco12']=h[riskq[h.index]&(age<=365)].groupby('cep').size(); g['queda12']=h[h.subtipo.eq('Retirada de árvore caída')&(age<=365)].groupby('cep').size()
    g['espera_com']=age[p&o&(age<=730)].groupby(h.cep[p&o&(age<=730)]).max()
    F=feats(T); c=(F.poda_all+F.risk+F.queda+F.remo+F.rua_poda>0); Fc=F[c]
    pr=pd.Series(gb.predict_proba(Fc)[:,1],index=Fc.index); pr=pd.DataFrame({'p':pr,'cep':tc.reindex(pr.index)}).dropna()
    g['prob']=pr.groupby('cep').p.max(); g=g.fillna(0)
    g['c_risco']=Lg(g.risco12+g.queda12,12); g['c_com']=Lg(g.comlurb,8); g['c_light']=Lg(g.light,12)
    g['c_prev']=np.clip((g.prob-0.07)/0.48,0,1); g['c_esp']=np.clip(g.espera_com/365,0,1)
    g['score']=30*g.c_risco+25*g.c_com+20*g.c_light+15*g.c_prev+10*g.c_esp
    return g[(g.comlurb+g.light+g.risco12)>0]
for T in [pd.Timestamp('2025-01-01'),pd.Timestamp('2025-07-01')]:
    g=score(T); f=A[(A.ini>=T)&(A.ini<T+pd.Timedelta(days=365))]
    y_q=f[f.subtipo.eq('Retirada de árvore caída')].groupby('cep').size().reindex(g.index,fill_value=0)>0
    y_r=f[riskq[f.index]].groupby('cep').size().reindex(g.index,fill_value=0)>0
    y_l=f[poda[f.index]&f.status.eq('Pendente')].groupby('cep').size().reindex(g.index,fill_value=0)>0
    y_p=f[poda[f.index]].groupby('cep').size().reindex(g.index,fill_value=0)>=2
    print(T.date(),'CEPs ativos',len(g))
    for nm,y in [('queda',y_q),('risco/queda/remocao',y_r),('novo Light',y_l),('>=2 pedidos poda',y_p)]:
        row={'base':round(y.mean(),3)}
        for col in ['score','c_risco','c_com','c_light','c_prev']:
            o=g[col].rank(method='first',ascending=False); row[col]=round(y[o<=200].mean(),3)
        print(' ',nm,row)
