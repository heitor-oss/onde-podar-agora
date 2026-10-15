"""
Ranking "Onde podar agora" · J18 — Áreas de 150 m (grupos de CEPs)
Tipo: principal

O que faz:
    Junta CEPs vizinhos em áreas de até 150 m de raio, com o mesmo algoritmo guloso das
    frentes de desligamento (I03): pega o CEP cujo entorno de 150 m soma mais nota, forma a
    área com os CEPs desse entorno que ainda não têm área, tira-os da lista e repete. A
    prioridade da área é a soma das notas dos seus CEPs. Compara, no teste de 2025, o que se
    ganha olhando por área ou por CEP.

Lê:
    rank_data.json, pri_feats.pkl
Grava:
    rank_data.json (acrescenta a coluna area), area_bt.json, ranking_areas_150m.csv (saidas),
    coluna area_150m em ranking_ceps_poda.csv (saidas)
Usado em:
    Página: seletor "por CEP / por área de 150 m".
Escrito para este pacote.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import json, heapq, pickle
import numpy as np, pandas as pd
from sklearn.neighbors import BallTree

RAIO_M = 150
L = lambda v, cap: np.clip(np.log1p(v) / np.log1p(cap), 0, 1)
def nota(risco, queda, com, light, prob, esp):
    """Nota 0–100 com os pesos sugeridos (25/15/40/10/10), igual à da página."""
    return (25 * L(risco + queda, 12) + 15 * L(com, 8) + 40 * L(light, 12)
            + 10 * np.clip((prob - 0.07) / 0.48, 0, 1) + 10 * np.clip(esp / 365, 0, 1))

def areas_gulosas(lat, lon, score, raio_m=RAIO_M):
    """Agrupa pontos em discos de raio_m: a cada passo, o ponto cujo entorno (ainda sem área)
    soma mais score vira o centro de uma nova área. Devolve o número da área de cada ponto."""
    X = np.radians(np.c_[lat, lon])
    viz = BallTree(X, metric='haversine').query_radius(X, raio_m / 6371000)
    vivo = np.ones(len(score), bool); area = np.full(len(score), -1)
    fila = [(-score[v].sum(), i) for i, v in enumerate(viz)]; heapq.heapify(fila); a = 0
    while fila:
        m, i = heapq.heappop(fila)
        if not vivo[i]: continue
        atual = score[viz[i][vivo[viz[i]]]].sum()
        if abs(atual + m) > 1e-9:            # o entorno mudou desde que entrou na fila: recoloca
            heapq.heappush(fila, (-atual, i)); continue
        membros = viz[i][vivo[viz[i]]]
        area[membros] = a; vivo[membros] = False; a += 1
    return area

# 1) Áreas com os dados de hoje
R = json.load(open('rank_data.json', encoding='utf-8'))
cols = [c for c in R['cols'] if c != 'area']
df = pd.DataFrame([r[:len(cols)] for r in R['rows']], columns=cols)
df['s'] = nota(df.risco, df.queda, df.com, df.light, df.prob, df.esp)
df['area'] = areas_gulosas(df.lat.values, df.lon.values, df.s.values)
A = df.groupby('area').agg(n=('cep', 'size'), soma=('s', 'sum'), maior=('s', 'max'), com=('com', 'sum'),
                           light=('light', 'sum'), risco=('risco', 'sum'), queda=('queda', 'sum')).sort_values('soma', ascending=False)
print('CEPs:', len(df), '| áreas:', len(A), '| CEPs por área:', A.n.value_counts().sort_index().to_dict())
for k in [10, 50, 100]:
    a = A.head(k); c = df.sort_values('s', ascending=False).head(k)
    print(f'{k} áreas do topo: {a.n.sum()} CEPs, {a.com.sum()} pedidos na COMLURB, {a.light.sum()} na Light | '
          f'{k} CEPs do topo: {c.com.sum()} na COMLURB, {c.light.sum()} na Light')
R['cols'] = cols + ['area']
R['rows'] = [r[:len(cols)] + [int(a)] for r, a in zip(R['rows'], df.area)]
json.dump(R, open('rank_data.json', 'w'), ensure_ascii=False, separators=(',', ':'))

# Planilha das áreas (pesos sugeridos)
def acao(com, light):
    if light > 0 and com > 0: return 'COMLURB + Light'
    if light > 0: return 'Precisa da Light'
    if com > 0: return 'COMLURB pode ir já'
    return 'Vistoria de risco'
df['cep_fmt'] = df.cep.str[:5] + '-' + df.cep.str[5:]
linhas = []
for pos, (aid, a) in enumerate(A.iterrows(), 1):
    m = df[df.area == aid].sort_values('s', ascending=False); c = m.iloc[0]
    linhas.append(dict(posicao=pos, area_150m=int(aid), cep_de_maior_nota=c.cep_fmt, logradouro_ref=c.rua, bairro=c.bairro,
                       zona=c.zona, n_ceps=int(a.n), prioridade_soma_das_notas=round(a.soma, 1), maior_nota=round(a.maior, 1),
                       acao_sugerida=acao(a.com, a.light), poda_aberta_comlurb=int(a.com), pedidos_travados_light=int(a.light),
                       risco_queda_remocao_12m=int(a.risco), quedas_12m=int(a.queda), ceps=' '.join(m.cep_fmt),
                       lat=round(m.lat.mean(), 6), lon=round(m.lon.mean(), 6)))
pd.DataFrame(linhas).to_csv(os.path.join(SAIDAS, 'ranking_areas_150m.csv'), index=False, encoding='utf-8-sig')
f = os.path.join(SAIDAS, 'ranking_ceps_poda.csv')
if os.path.exists(f):
    rc = pd.read_csv(f, encoding='utf-8-sig', dtype={'cep': str})
    rc['area_150m'] = rc.cep.str.replace('-', '').map(dict(zip(df.cep, df.area)))
    rc.to_csv(f, index=False, encoding='utf-8-sig')

# 2) Teste de 2025: olhar por área ou por CEP?
O = pickle.load(open('pri_feats.pkl', 'rb'))
pos_cep = df.set_index(df.cep.astype('int64'))[['lat', 'lon']]
bt = {}
for T in ['2025-01-01', '2025-07-01']:
    g = O[T][O[T].active].join(pos_cep, how='inner').copy()
    g['s'] = nota(g.risco, g.queda12, g.com, g.light, g.prob, g.esp)
    g['area'] = areas_gulosas(g.lat.values, g.lon.values, g.s.values)
    Ag = g.groupby('area').agg(n=('s', 'size'), soma=('s', 'sum'), quedas=('y_queda', 'sum'), light=('y_light', 'sum')).sort_values('soma', ascending=False)
    top = g.sort_values('s', ascending=False)
    r = {}
    for k in [50, 100, 200]:
        a = Ag.head(k); c = top.head(k)
        r[f'{k} destinos'] = dict(areas_ceps=int(a.n.sum()), areas_quedas=int(a.quedas.sum()), areas_light=int(a.light.sum()),
                                 ceps_quedas=int(c.y_queda.sum()), ceps_light=int(c.y_light.sum()))
    a = Ag[Ag.n.cumsum() <= 500]; c = top.head(int(a.n.sum()))
    r['mesmo nº de CEPs'] = dict(ceps=int(a.n.sum()), areas=len(a), areas_quedas=int(a.quedas.sum()), areas_light=int(a.light.sum()),
                               ceps_quedas=int(c.y_queda.sum()), ceps_light=int(c.y_light.sum()))
    bt[T] = r; print(T, r)
json.dump(bt, open('area_bt.json', 'w'), ensure_ascii=False, indent=1)
