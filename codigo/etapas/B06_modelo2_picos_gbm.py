"""
Picos de chamados por CEP · B06 — Modelo 2 com gradient boosting (descartado)
Tipo: teste descartado

O que faz:
    Treina gradient boosting para prever picos por CEP-dia com amostragem de dias sem pico.
    Com só 57 picos no treino, decorou os exemplos e foi pior que a regressão logística.
    Define as variáveis usadas pelos passos seguintes.

Lê:
    ev.pkl, mats.npz, vol.pkl
Grava:
    model.json
Usado em:
    Comparação; base de B07 e C03.
Script original da análise: a6.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
z=np.load('mats.npz',allow_pickle=True); ALL=z['ALL'].astype(np.int32); FALL=z['FALL'].astype(np.int32); RISK=z['RISK'].astype(np.int32)
ceps=z['ceps']; days=pd.DatetimeIndex(z['days']); C,D=ALL.shape; EM=FALL+RISK
cum=lambda M: np.concatenate([np.zeros((M.shape[0],1),np.int32),M.cumsum(1)],1)
CA,CE=cum(ALL),cum(EM)
c5=ceps//1000; u5,inv=np.unique(c5,return_inverse=True)
A5=np.zeros((len(u5),D),np.int32); np.add.at(A5,inv,ALL); E5=np.zeros_like(A5); np.add.at(E5,inv,EM); CA5,CE5=cum(A5),cum(E5)
city=ALL.sum(0); cfall=FALL.sum(0); ccf=np.concatenate([[0],cfall.cumsum()])
ev=pd.read_pickle('ev.pkl'); vol=pd.read_pickle('vol.pkl')
EVT=np.zeros((C,D),np.int8); EVT[ev.ci,ev.di]=1; CEV=cum(EVT.astype(np.int32))
VOL=np.zeros((C,D),np.int8); VOL[vol.ci,vol.di]=1; VOL[ev.ci[ (ALL[ev.ci,ev.di]>=5)], ev.di[(ALL[ev.ci,ev.di]>=5)]]=1
CVO=cum(VOL.astype(np.int32))
active=np.where(ALL.sum(1)>0)[0]
rng=np.random.default_rng(0)
def seg(Cm,r,a,b): a=np.clip(a,0,D); b=np.clip(b,0,D); return Cm[r,b]-Cm[r,a]
def feats(ci,di):
    F={}
    for w in [1,7,30,90,365]:
        F[f'cep_tot_{w}d']=seg(CA,ci,di-w,di); F[f'cep_emerg_{w}d']=seg(CE,ci,di-w,di)
    for w in [1,7,30]:
        F[f'viz_tot_{w}d']=seg(CA5,inv[ci],di-w,di); F[f'viz_emerg_{w}d']=seg(CE5,inv[ci],di-w,di)
    F['cep_eventos_previos']=CEV[ci,di]+CVO[ci,di]
    F['cidade_tot_ontem']=city[np.maximum(di-1,0)]; F['cidade_queda_ontem']=cfall[np.maximum(di-1,0)]
    F['cidade_queda_3d']=ccf[di]-ccf[np.maximum(di-3,0)]
    F['mes']=days[di].month.values
    F['cidade_queda_HOJE']=cfall[di]
    return pd.DataFrame(F)
def build(LAB):
    pc,pd_=np.where(LAB==1); m=pd_>=365; pc,pd_=pc[m],pd_[m]
    N=1_500_000; nc=rng.choice(active,N); nd=rng.integers(365,D,N)
    keep=LAB[nc,nd]==0; nc,nd=nc[keep],nd[keep]
    ci=np.concatenate([pc,nc]); di=np.concatenate([pd_,nd]); y=np.concatenate([np.ones(len(pc)),np.zeros(len(nc))])
    X=feats(ci,di); return X,y,di
split=(pd.Timestamp('2025-01-01')-days[0]).days
groups={'Só histórico do próprio CEP':[c for c in ['cep_tot_1d','cep_tot_7d','cep_tot_30d','cep_tot_90d','cep_tot_365d','cep_emerg_1d','cep_emerg_7d','cep_emerg_30d','cep_emerg_90d','cep_emerg_365d','cep_eventos_previos','mes']]}
groups['+ vizinhança (CEP 5 dígitos)']=groups['Só histórico do próprio CEP']+['viz_tot_1d','viz_tot_7d','viz_tot_30d','viz_emerg_1d','viz_emerg_7d','viz_emerg_30d']
groups['+ cidade até ontem']=groups['+ vizinhança (CEP 5 dígitos)']+['cidade_tot_ontem','cidade_queda_ontem','cidade_queda_3d']
groups['+ sinal de temporal no dia (proxy de previsão do tempo)']=groups['+ cidade até ontem']+['cidade_queda_HOJE']
res={}
for tname,LAB in [('Emergencial',EVT),('Volume (≥5, não emergencial)',VOL)]:
    X,y,di=build(LAB); tr=di<split; te=~tr
    print(tname,'pos train/test',int(y[tr].sum()),int(y[te].sum()))
    res[tname]={'n_pos_train':int(y[tr].sum()),'n_pos_test':int(y[te].sum()),'models':{}}
    for gname,cols in groups.items():
        m=HistGradientBoostingClassifier(max_iter=300,learning_rate=0.05,max_leaf_nodes=31,class_weight='balanced',random_state=0)
        m.fit(X.loc[tr,cols],y[tr]); p=m.predict_proba(X.loc[te,cols])[:,1]
        auc=roc_auc_score(y[te],p)
        neg=p[y[te]==0]; pos=p[y[te]==1]
        rec={}
        for q in [0.001,0.01,0.05]:
            thr=np.quantile(neg,1-q); rec[str(q)]=float((pos>thr).mean())
        res[tname]['models'][gname]={'auc':float(auc),'recall_top':rec}
        print(' ',gname,round(auc,3),rec)
    # simple rules
    yt=y[te]; Xt=X[te]
    for rule,s in [('Teve ≥1 chamado no CEP nos 30 dias anteriores',Xt.cep_tot_30d>0),('Teve ≥1 chamado no CEP nos 365 dias anteriores',Xt.cep_tot_365d>0)]:
        tp=(s[yt==1]).mean(); fp=(s[yt==0]).mean()
        res[tname].setdefault('rules',{})[rule]={'recall':float(tp),'flag_rate':float(fp)}
        print('  rule',rule,round(tp,3),round(fp,3))
json.dump(res,open('model.json','w'),ensure_ascii=False)
