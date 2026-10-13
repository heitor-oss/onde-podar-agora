"""
Ranking "Onde podar agora" · J17 — Números fixos da página
Tipo: principal

O que faz:
    Tabela de validação, faixas de nota e gráfico de robustez.

Lê:
    pri_feats.pkl, pri_rob.pkl, pri_roll.pkl
Grava:
    bands8.json, pri_page.json, rob_rows.json
Usado em:
    Página.
Escrito para este pacote a partir dos trechos rodados durante a análise.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle, json

L = lambda v, cap: np.clip(np.log1p(v) / np.log1p(cap), 0, 1)   # contagem → 0..1 em escala log
SINAIS = ['risco', 'com', 'light', 'prev', 'esp']
def componentes(g):
    return np.stack([L(g.risco + g.queda12, 12), L(g.com, 8), L(g.light, 12),
                     np.clip((g.prob - 0.07) / 0.48, 0, 1), np.clip(g.esp / 365, 0, 1)], 1)
ATUAIS = np.array([25, 15, 40, 10, 10]); ANTERIORES = np.array([30, 25, 20, 15, 10])
nota = lambda g, w: componentes(g) @ w / w.sum() * 100

# 1) Tabela "Esse ranking teria acertado?" (cortes jan e jul/2025, 200 CEPs do topo)
O = pickle.load(open('pri_feats.pkl', 'rb'))
def acertos(g, s, k=200):
    a = g.active.values; s = np.where(a, s, -1); top = np.argsort(-s)[:k]
    return {'queda': (g.y_queda.values[top] > 0).mean(), 'rq': (g.y_rq.values[top] > 0).mean(),
            'light': (g.y_light.values[top] > 0).mean(), 'poda2': (g.y_poda.values[top] >= 2).mean()}
val = {}
for nome, f in [('novo', lambda g: nota(g, ATUAIS)), ('antigo', lambda g: nota(g, ANTERIORES)),
                ('risco', lambda g: componentes(g)[:, 0]), ('light', lambda g: componentes(g)[:, 2])]:
    hs = [acertos(O[T], f(O[T])) for T in ['2025-01-01', '2025-07-01']]
    val[nome] = {k: round(np.mean([h[k] for h in hs]) * 100) for k in hs[0]}
bs = []
for T in ['2025-01-01', '2025-07-01']:
    g = O[T][O[T].active]
    bs.append({'queda': (g.y_queda > 0).mean(), 'rq': (g.y_rq > 0).mean(), 'light': (g.y_light > 0).mean(), 'poda2': (g.y_poda >= 2).mean()})
val['base'] = {k: round(np.mean([b[k] for b in bs]) * 100) for k in bs[0]}
print(pd.DataFrame(val).to_string())
json.dump({'val': val}, open('pri_page.json', 'w'), ensure_ascii=False)

# 2) Faixas de nota → o que aconteceu no ano seguinte (8 cortes de 2024 e 2025)
R8 = pickle.load(open('pri_roll.pkl', 'rb'))
B = pd.concat([pd.DataFrame({'s': nota(g, ATUAIS)[g.active.values],
                             'q': (g.y_queda[g.active] > 0).values, 'l': (g.y_light[g.active] > 0).values,
                             'r': (g.y_rq[g.active] > 0).values}) for g in R8.values()])
B['faixa'] = pd.cut(B.s, [0, 20, 40, 60, 80, 101], right=False, labels=['0–19', '20–39', '40–59', '60–79', '80–100'])
t = B.groupby('faixa', observed=True).agg(n=('s', 'size'), queda=('q', 'mean'), light=('l', 'mean'), risco=('r', 'mean'))
t['n'] = (t.n / len(R8)).round()
print(t.round(3).to_string())
json.dump([[i, int(r.n), round(r.queda, 3), round(r.light, 3), round(r.risco, 3)] for i, r in t.iterrows()],
          open('bands8.json', 'w'), ensure_ascii=False)

# 3) Gráfico "Os pesos valem em outros períodos?"
rob = pickle.load(open('pri_rob.pkl', 'rb'))
linhas = [[r['corte'], round(r['atuais'] * 100, 1), round(r['anteriores'] * 100, 1), round(r['obj ótimo'] * 100, 1)] for r in rob['A']]
print(linhas)
json.dump(linhas, open('rob_rows.json', 'w'))
