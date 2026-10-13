"""
Clima · C03 — Modelo 2 com clima
Tipo: principal

O que faz:
    Acrescenta o clima do dia (como se a previsão fosse perfeita) e o da véspera ao modelo
    2.

Lê:
    clima.pkl, código de B06_modelo2_picos_gbm.py
Grava:
    model_clima.json
Usado em:
    Documento de aprendizado de máquina.
Script original da análise: w3.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

exec(open(etapa('a6.py')).read().split("res={}")[0])
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, FunctionTransformer
w=pd.read_pickle('clima.pkl').reindex(pd.date_range('2022-08-01',periods=1512))
off=(days[0]-pd.Timestamp('2022-08-01')).days
W={c:w[c].values for c in w.columns}
def wfeat(X,di):
    i=di+off
    X['chuva_hoje']=W['chuva_media'][i]; X['chuva_hora_hoje']=W['chuva_hora_max'][i]; X['rajada_hoje']=W['rajada_max'][i]
    X['chuva_ontem']=W['chuva_media'][i-1]; X['chuva_hora_ontem']=W['chuva_hora_max'][i-1]; X['rajada_ontem']=W['rajada_max'][i-1]
    X['chuva_7d_ant']=W['chuva_7d_ant'][i]
    return X
base=[c for c in groups['+ cidade até ontem'] if c!='mes']
loc=[c for c in groups['Só histórico do próprio CEP'] if c!='mes']
G={'Só o próprio CEP':loc,'+ cidade até a véspera':base,
   '+ clima do dia (previsão perfeita)':base+['chuva_hoje','chuva_hora_hoje','rajada_hoje','chuva_ontem','chuva_hora_ontem','rajada_ontem','chuva_7d_ant'],
   '+ clima só da véspera (observado)':base+['chuva_ontem','chuva_hora_ontem','rajada_ontem','chuva_7d_ant'],
   'Referência: quedas na cidade no dia':base+['cidade_queda_HOJE']}
res={}
for tname,LAB in [('Emergencial',EVT),('Volume (≥5, não emergencial)',VOL)]:
    X,y,di=build(LAB); X=wfeat(X,di); tr=di<split; te=~tr; res[tname]={}
    for gname,cols in G.items():
        m=make_pipeline(FunctionTransformer(np.log1p),StandardScaler(),LogisticRegression(C=0.3,class_weight='balanced',max_iter=3000))
        m.fit(X.loc[tr,cols],y[tr]); p=m.predict_proba(X.loc[te,cols])[:,1]
        neg=p[y[te]==0]; pos=p[y[te]==1]
        rec={str(q):float((pos>np.quantile(neg,1-q)).mean()) for q in [0.001,0.01,0.05,0.10]}
        res[tname][gname]={'auc':float(roc_auc_score(y[te],p)),'recall_top':rec}
        print(tname,'|',gname,round(res[tname][gname]['auc'],3),{k:round(v,2) for k,v in rec.items()})
json.dump(res,open('model_clima.json','w'),ensure_ascii=False)
