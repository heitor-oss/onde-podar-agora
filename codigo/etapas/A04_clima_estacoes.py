"""
Preparação dos dados · A04 — Pluviômetros do Alerta Rio e WebSirene (Data.Rio)
Tipo: principal

O que faz:
    Lê os arquivos diários dos pluviômetros baixados do BigQuery do Data.Rio (notebook em
    notebooks/), filtra dias com registros suficientes e junta com as coordenadas das
    estações.

Lê:
    pluviômetros Data.Rio (dados_entrada)
Grava:
    estacoes.pkl, estacoes_diario.pkl
Usado em:
    Pergunta "dado um temporal, onde caem as árvores" (E).
Script original da análise: q2prep.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
import zipfile
C=os.path.join(TRABALHO,'clima')+os.sep
if not os.path.exists(C):
    zipfile.ZipFile(CLIMA_ESTACOES_ZIP).extractall(C)   # arquivos do Data.Rio (ver notebooks/)
a=pd.read_csv(C+'diario__clima_pluviometro__taxa_precipitacao_alertario.csv',parse_dates=['data'])
b=pd.read_csv(C+'diario__clima_pluviometro__taxa_precipitacao_alertario_5min.csv',parse_dates=['data'])
a=a[a.n_registros>=80].rename(columns={'acumulado_chuva_15_min__soma_dia':'chuva_dia','acumulado_chuva_1_h__max':'max1h'})[['id_estacao','data','chuva_dia','max1h']]
b=b[(b.n_registros>=240)&(b.data>'2024-06-03')].rename(columns={'acumulado_chuva_15min__soma_dia':'chuva_dia','acumulado_chuva_1h__max':'max1h'})[['id_estacao','data','chuva_dia','max1h']]
ar=pd.concat([a,b]); ar['rede']='alertario'
w=pd.read_csv(C+'diario__clima_pluviometro__taxa_precipitacao_websirene.csv',parse_dates=['data'])
w=w[w.n_registros>=48].rename(columns={'acumulado_chuva_1_h__max':'max1h'})[['id_estacao','data','max1h']]; w['chuva_dia']=np.nan; w['rede']='websirene'
ea=pd.read_csv(C+'estacoes__clima_pluviometro__estacoes_alertario.csv'); ea['rede']='alertario'
ew=pd.read_csv(C+'estacoes__clima_pluviometro__estacoes_websirene.csv'); ew['rede']='websirene'
est=pd.concat([ea[['id_estacao','estacao','latitude','longitude','rede']],ew[['id_estacao','estacao','latitude','longitude','rede']]])
st=pd.concat([ar,w]).merge(est,on=['id_estacao','rede'])
st['sid']=st.rede+'_'+st.id_estacao.astype(str)
st.to_pickle('estacoes_diario.pkl'); est.to_pickle('estacoes.pkl')
print(st.groupby('rede').agg(n=('sid','nunique'),ini=('data','min'),fim=('data','max'),rows=('sid','size')))
print(st[st.data=='2023-01-23'].sort_values('max1h').tail(5)[['estacao','rede','chuva_dia','max1h']])
