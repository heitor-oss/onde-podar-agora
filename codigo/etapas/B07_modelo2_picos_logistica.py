"""
Picos de chamados por CEP · B07 — Modelo 2: regressão logística para picos por CEP
Tipo: principal

O que faz:
    Regressão logística (log(1+x), padronização, C=0,3, pesos balanceados) com camadas de
    informação: só o CEP, + vizinhança, + cidade até ontem, + quedas na cidade no dia
    (referência). Mede AUC e quantos picos caem nos 0,1%, 1%, 5% e 10% de maior risco.

Lê:
    código de B06_modelo2_picos_gbm.py
Grava:
    model_lr.json
Usado em:
    Documento de aprendizado de máquina; página de picos.
Script original da análise: a7.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

exec(open(etapa('a6.py')).read().split("res={}")[0])
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, FunctionTransformer
res={}
for tname,LAB in [('Emergencial',EVT),('Volume (≥5, não emergencial)',VOL)]:
    X,y,di=build(LAB); tr=di<split; te=~tr; res[tname]={}
    for gname,cols in groups.items():
        cols=[c for c in cols if c!='mes']
        m=make_pipeline(FunctionTransformer(np.log1p),StandardScaler(),LogisticRegression(C=0.3,class_weight='balanced',max_iter=2000))
        m.fit(X.loc[tr,cols],y[tr]); p=m.predict_proba(X.loc[te,cols])[:,1]
        neg=p[y[te]==0]; pos=p[y[te]==1]
        rec={str(q):float((pos>np.quantile(neg,1-q)).mean()) for q in [0.001,0.01,0.05,0.10]}
        res[tname][gname]={'auc':float(roc_auc_score(y[te],p)),'recall_top':rec}
        print(tname,gname,round(res[tname][gname]['auc'],3),rec)
json.dump(res,open('model_lr.json','w'),ensure_ascii=False)
