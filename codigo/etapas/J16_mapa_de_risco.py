"""
Ranking "Onde podar agora" · J16 — Mapa de risco
Tipo: principal

O que faz:
    Quedas de dezembro a abril por quadrado de 1 km e teste no verão 2025–26.

Lê:
    df.pkl, full.pkl
Grava:
    cell_quedas.json
Usado em:
    Página: mapa de risco.
Escrito para este pacote a partir dos trechos rodados durante a análise.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json

# Quadrados de ~1 km: gx = (lon + 43,8) × 102,5 e gy = (lat + 23,1) × 110,6 (parte inteira)
def quadrados(x):
    x = x[x.latitude_usada.notna()]
    x = x[x.latitude_usada.between(-23.1, -22.73) & x.longitude_usada.between(-43.8, -43.09)].copy()
    x['gx'] = ((x.longitude_usada + 43.8) * 102.5).astype(int)
    x['gy'] = ((x.latitude_usada + 23.1) * 110.6).astype(int)
    x['ini'] = pd.to_datetime(x.data_inicio)
    return x

# 1) Teste: o histórico de quedas no verão antecipa as quedas do verão seguinte?
df = quadrados(pd.read_pickle('full.pkl'))
q = df[df.subtipo.eq('Retirada de árvore caída')].copy()
q['verao'] = q.ini.dt.month.isin([12, 1, 2, 3, 4])
print('quedas de dezembro a abril:', round(q.verao.mean(), 3))
celulas = df.groupby(['gx', 'gy']).size().index
hist = q[(q.ini < '2025-12-01') & q.verao].groupby(['gx', 'gy']).size().reindex(celulas, fill_value=0)
teste = q[(q.ini >= '2025-12-01') & (q.ini < '2026-05-01')].groupby(['gx', 'gy']).size().reindex(celulas, fill_value=0)
for frac in [.05, .1, .2]:
    k = int(len(celulas) * frac); top = hist.sort_values(ascending=False).index[:k]
    print(f'{frac:.0%} dos quadrados com mais quedas no histórico ({k}) → {teste[top].sum() / teste.sum():.1%} das quedas do verão 2025–26')

# 2) Camada "quedas no verão" da página: quedas de dezembro a abril em todas as temporadas,
#    com o bairro predominante de cada quadrado
d = quadrados(pd.read_pickle('df.pkl'))
bairro = d[d.bairro.notna()].groupby(['gx', 'gy']).bairro.agg(lambda s: s.mode().iloc[0])
qv = d[d.subtipo.eq('Retirada de árvore caída') & d.ini.dt.month.isin([12, 1, 2, 3, 4])].groupby(['gx', 'gy']).size()
out = [[int(x), int(y), int(qv.get((x, y), 0)), bairro[(x, y)]] for x, y in bairro.index]
print('quadrados:', len(out), '| quedas no verão somadas:', sum(o[2] for o in out))
json.dump(out, open('cell_quedas.json', 'w'), ensure_ascii=False, separators=(',', ':'))
