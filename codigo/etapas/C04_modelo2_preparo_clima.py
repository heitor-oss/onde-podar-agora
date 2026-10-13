"""
Clima · C04 — Preparo comum do modelo 2 com clima
Tipo: biblioteca

O que faz:
    Mesmo preparo de C03, sem treinar; usado por C05.

Lê:
    clima.pkl, código de B06_modelo2_picos_gbm.py
Grava:
    nada (só imprime resultados)
Usado em:
    C05.
Script original da análise: w3_head.py
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
