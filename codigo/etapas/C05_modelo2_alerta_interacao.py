"""
Clima · C05 — Modelo 2 com alerta × histórico
Tipo: teste descartado

O que faz:
    Testa variáveis de interação entre o alerta de clima e o histórico do CEP. Não melhorou.

Lê:
    model_clima.json, código de C04_modelo2_preparo_clima.py
Grava:
    model_clima.json
Usado em:
    Comparação.
Script original da análise: w4.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

exec(open(etapa('w3_head.py')).read())
res=json.load(open('model_clima.json'))
for tname,LAB in [('Emergencial',EVT),('Volume (≥5, não emergencial)',VOL)]:
    X,y,di=build(LAB); X=wfeat(X,di); tr=di<split; te=~tr
    al=((np.maximum(X.rajada_hoje,X.rajada_ontem)>=60)|(np.maximum(X.chuva_hoje,X.chuva_ontem)>=15)|(np.maximum(X.chuva_hora_hoje,X.chuva_hora_ontem)>=8)).astype(float)
    X['alerta']=al; X['alerta_x_hist']=al*np.log1p(X.cep_tot_365d); X['alerta_x_emerg']=al*np.log1p(X.cep_emerg_365d)
    X['rajada_x_hist']=np.log1p(X.rajada_hoje)*np.log1p(X.cep_tot_365d)
    cols=G['+ clima do dia (previsão perfeita)']+['alerta','alerta_x_hist','alerta_x_emerg']
    Xl=np.log1p(X[cols].clip(lower=0))
    m=make_pipeline(StandardScaler(),LogisticRegression(C=0.3,class_weight='balanced',max_iter=3000)).fit(Xl[tr],y[tr]); p=m.predict_proba(Xl[te])[:,1]
    neg=p[y[te]==0]; pos=p[y[te]==1]; rec={str(q):float((pos>np.quantile(neg,1-q)).mean()) for q in [0.001,0.01,0.05,0.10]}
    print(tname,'alert-interaction',round(roc_auc_score(y[te],p),3),rec)
    res[tname]['+ clima com alertas e interação']={'auc':float(roc_auc_score(y[te],p)),'recall_top':rec}
json.dump(res,open('model_clima.json','w'),ensure_ascii=False)
