"""
Picos de chamados por CEP · B03 — Tabela CEP × dia e matrizes de chamados
Tipo: principal

O que faz:
    Monta matrizes CEP × dia com todos os chamados, as quedas e os pedidos de avaliação de
    risco, a tabela cepday (chamados, pontos, quedas, horário, bairro, rua) e marca os dias
    de temporal (40 ou mais quedas na cidade).

Lê:
    full.pkl
Grava:
    cepday.pkl, mats.npz, peaks.pkl
Usado em:
    Picos por CEP, modelo 2, clima.
Script original da análise: a3.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
df=pd.read_pickle('full.pkl')
df=df[df.cep.notna()].copy()
df['cep']=df.cep.astype(int)
df['pt']=df.latitude_usada.round(5).astype(str)+'_'+df.longitude_usada.round(5).astype(str)+'_'+df.numero_logradouro.fillna(-1).astype(str)
days=pd.date_range(df.d.min(),df.d.max()); D=len(days)
ceps=np.sort(df.cep.unique()); C=len(ceps)
ci=np.searchsorted(ceps,df.cep.values); di=((df.d-days[0]).dt.days).values
def mat(mask):
    M=np.zeros((C,D),np.int16); np.add.at(M,(ci[mask],di[mask]),1); return M
ALL=mat(np.ones(len(df),bool)); FALL=mat((df.subtipo=='Retirada de árvore caída').values)
RISK=mat((df.subtipo=='Avaliação de risco de queda da árvore').values)
np.savez_compressed('mats.npz',ALL=ALL,FALL=FALL,RISK=RISK,ceps=ceps,days=days.values.astype('datetime64[D]'))
# citywide
city=ALL.sum(0); cityfall=FALL.sum(0)
cs=pd.Series(city,days); cf=pd.Series(cityfall,days)
storm=cf>=40
print('storm days',storm.sum(), list(cf[storm].index.date))
# peak table
df['isfall']=(df.subtipo=='Retirada de árvore caída').astype(int)
df['isem']=df.subtipo.isin(['Retirada de árvore caída','Avaliação de risco de queda da árvore']).astype(int)
df['ts']=pd.to_datetime(df.data_inicio)
g=df.groupby(['cep','d']).agg(n=('id_chamado','size'),pts=('pt','nunique'),fall=('isfall','sum'),emerg=('isem','mean'),
   tmin=('ts','min'),tmax=('ts','max'),bairro=('cep_bairro_ref','first'),rua=('cep_logradouro_ref','first'),
   lat=('latitude_usada','median'),lon=('longitude_usada','median'),orig=('id_origem_ocorrencia','first')).reset_index()
g['hspan']=(g.tmax-g.tmin).dt.total_seconds()/3600
g['storm']=g.d.map(storm).fillna(False)
g.to_pickle('cepday.pkl')
P=g[g.n>=5].copy()
def cls(r):
    if r.storm or r.emerg>=0.5: return 'Evento emergencial (queda/risco)'
    if r.pts<=2: return 'Lote no mesmo endereço'
    return 'Mutirão de rua (vários endereços)'
P['classe']=P.apply(cls,axis=1)
print(P.classe.value_counts())
print(P[P.classe.str.startswith('Evento')].sort_values('n',ascending=False).head(30)[['cep','d','n','pts','fall','emerg','storm','bairro','rua']])
P.to_pickle('peaks.pkl')
# fallen tree hot spots
F=g[g.fall>=3]; print('cep-days fall>=3',len(F)); print(F.sort_values('fall').tail(10)[['cep','d','n','fall','bairro','rua']])
