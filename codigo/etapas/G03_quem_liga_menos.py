"""
Cobertura de árvores · G03 — Setores que pedem menos do que o esperado
Tipo: principal

O que faz:
    Estima quantos pedidos cada setor "deveria" ter pela árvore e ocupação e compara quedas
    por pedido entre quem liga menos e quem liga mais.

Lê:
    t1_mats.npz, setor censitário (dados_entrada)
Grava:
    t3_bairro.json, t3_terc.json
Usado em:
    Viés de sub-notificação (limites).
Script original da análise: t3.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
from sklearn.linear_model import PoissonRegressor
S=pd.read_csv(SETOR).sort_values('cd_setor').reset_index(drop=True)
z=np.load('t1_mats.npz'); A=z['A']; Q=z['Q']
S['chamados_tot']=A.sum(1); S['quedas']=Q.sum(1); S['pedidos']=S.chamados_tot-S.quedas
X=np.c_[S.arvore_urbana, S.arvore, S.construido, S.peso_urbano, np.log(S.area_km2.clip(lower=1e-4)), S.log_pop, S.arvore_urbana*np.log(S.area_km2.clip(lower=1e-4))]
mu=X.mean(0); sd=X.std(0)
m=PoissonRegressor(alpha=1e-4,max_iter=1000).fit((X-mu)/sd,S.pedidos); S['esperado']=m.predict((X-mu)/sd)
S['razao']=(S.pedidos+1)/(S.esperado+1)
from scipy.stats import spearmanr
print('spearman pedidos vs esperado',spearmanr(S.pedidos,S.esperado))
# terciles of reporting ratio among setores with expected>=5 (some trees)
T=S[S.esperado>=5].copy(); T['grupo']=pd.qcut(T.razao,3,labels=['Liga menos que o esperado','Dentro do esperado','Liga mais que o esperado'])
g=T.groupby('grupo',observed=True).agg(setores=('cd_setor','size'),arv=('arvore_urbana','mean'),pedidos=('pedidos','sum'),esperado=('esperado','sum'),quedas=('quedas','sum'),pop=('total_de_p','sum'))
g['quedas_por_100_pedidos']=g.quedas/g.pedidos*100; g['quedas_por_esperado']=g.quedas/g.esperado*100
print(g)
# bairro level
B=S.groupby('bairro').agg(setores=('cd_setor','size'),pedidos=('pedidos','sum'),esperado=('esperado','sum'),quedas=('quedas','sum'),arv=('arvore_urbana','mean'),ra=('regiao_adm','first'))
B['razao']=B.pedidos/B.esperado; B['q100']=B.quedas/B.pedidos.clip(lower=1)*100
B=B[B.esperado>=200]
print(B.sort_values('razao').head(12).round(2)); print(B.sort_values('razao').tail(8).round(2))
print('spearman bairro razao vs quedas/100 pedidos',spearmanr(B.razao,B.q100))
g.reset_index().to_json('t3_terc.json',orient='records',force_ascii=False)
B.reset_index().to_json('t3_bairro.json',orient='records',force_ascii=False)
