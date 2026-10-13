"""
Árvores e rede elétrica: trechos e modelo 1 · H03 — Modelo 1: treino e avaliação
Tipo: principal

O que faz:
    Treina o gradient boosting (400 árvores, taxa 0,04, 31 folhas, 40 por folha, L2=1) e
    mede precisão no topo, AUC, calibração e importância por permutação, comparando com
    regras simples.

Lê:
    m_data.pkl
Grava:
    gb.pkl, m_res.json
Usado em:
    Documento de aprendizado de máquina; página Light.
Script original da análise: light/m2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json, pickle
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
Z=pickle.load(open('m_data.pkl','rb')); D=Z['D']; meta=Z['meta']
def cand(F): return (F.poda_all+F.risk+F.queda+F.remo+F.rua_poda>0)
Xtr=pd.concat([D['tr1'][0][cand(D['tr1'][0])],D['tr2'][0][cand(D['tr2'][0])]]); ytr=pd.concat([D['tr1'][1][cand(D['tr1'][0])],D['tr2'][1][cand(D['tr2'][0])]])>0
cols=list(Xtr.columns)
gb=HistGradientBoostingClassifier(max_iter=400,learning_rate=0.04,max_leaf_nodes=31,min_samples_leaf=40,l2_regularization=1.0,random_state=0).fit(Xtr[cols],ytr)
K=[50,100,200,300,500,1000]
out={}
for te in ['te1','te2']:
    F,y=D[te]; c=cand(F); Fc=F[c]; yc=(y[c]>0); tot=(y>0).sum()
    p=gb.predict_proba(Fc[cols])[:,1]
    base=Fc.pend_all*1000+Fc.pend_365*10+Fc.poda_all*0.01
    res={}
    for nm,s in [('Modelo',p),('Regra: mais pedidos dependentes da Light',base.values),('Regra: mais pedidos de poda',Fc.poda_all.values+1e-3*Fc.pend_all.values)]:
        o=np.argsort(-s); r={}
        for k in K: r[k]=dict(prec=float(yc.values[o[:k]].mean()),rec=float(yc.values[o[:k]].sum()/tot))
        res[nm]=r
    # new-trecho target: no pendente before T
    nw=Fc.pend_all==0; yn=yc[nw]; pn=p[nw.values]; o=np.argsort(-pn)
    res['Modelo, só trechos sem pendente anterior']={k:dict(prec=float(yn.values[o[:k]].mean()),rec=float(yn.values[o[:k]].sum()/max(yn.sum(),1))) for k in K}
    o2=np.argsort(-(Fc[nw].poda_all.values+0.001*Fc[nw].viz_pend.values)); res['Regra, só trechos sem pendente anterior']={k:dict(prec=float(yn.values[o2[:k]].mean())) for k in K}
    res['_info']=dict(cand=int(c.sum()),pos_total=int(tot),pos_in_cand=int(yc.sum()),auc=float(roc_auc_score(yc,p)),pos_new=int(yn.sum()),base_rate=float(yc.mean()))
    out[te]=res
    print(te,res['_info'])
    for nm in res:
        if nm!='_info': print('  ',nm,{k:(round(v['prec'],3),round(v.get('rec',np.nan),3)) for k,v in res[nm].items()})
# calibration on te1
F,y=D['te1']; c=cand(F); p=gb.predict_proba(F[c][cols])[:,1]; yc=(y[c]>0).values
q=pd.qcut(p,10,labels=False,duplicates='drop'); cal=pd.DataFrame({'p':p,'y':yc,'q':q}).groupby('q').agg(p=('p','mean'),y=('y','mean'))
print(cal.round(3))
# importance via permutation quick
from sklearn.inspection import permutation_importance
Fs=F[c][cols].sample(8000,random_state=0); ys=(y[c]>0).loc[Fs.index]
pi=permutation_importance(gb,Fs,ys,scoring='average_precision',n_repeats=3,random_state=0)
imp=pd.Series(pi.importances_mean,index=cols).sort_values(ascending=False); print(imp.round(4))
out['cal']=cal.reset_index().to_dict('records'); out['imp']=imp.round(4).to_dict()
pickle.dump(gb,open('gb.pkl','wb')); json.dump(out,open('m_res.json','w'),ensure_ascii=False,default=float)
