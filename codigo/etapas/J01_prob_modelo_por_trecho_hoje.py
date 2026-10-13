"""
Ranking "Onde podar agora" · J01 — Ranking: previsão do modelo 1 hoje
Tipo: principal

O que faz:
    Aplica o modelo 1 em 21/09/2026 e associa cada trecho ao seu CEP.

Lê:
    gb.pkl, código de H02_modelo1_dados.py
Grava:
    prob_now.pkl
Usado em:
    Sinal "previsão" da nota.
Script original da análise: light/rank1.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json, pickle
src=open(etapa('m1.py')).read(); exec(src.split("def label")[0])
END=pd.Timestamp('2026-09-21')
F=feats(END); gb=pickle.load(open('gb.pkl','rb'))
c=(F.poda_all+F.risk+F.queda+F.remo+F.rua_poda>0); Fc=F[c].copy()
Fc['prob']=gb.predict_proba(Fc[list(F.columns)])[:,1]
# trecho -> cep (mode)
tc=df[df.cep.notna()].groupby('tr').cep.agg(lambda s:s.mode().iloc[0])
Fc['cep']=tc.reindex(Fc.index)
Fc[['prob','cep']].to_pickle('prob_now.pkl')
print(Fc.prob.describe(), Fc.cep.notna().mean())
