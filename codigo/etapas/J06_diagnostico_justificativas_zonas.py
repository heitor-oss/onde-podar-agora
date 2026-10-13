"""
Ranking "Onde podar agora" · J06 — Diagnóstico: justificativas, zonas e fechamento em massa
Tipo: principal

O que faz:
    Motivos de fechamento sem atendimento, perfil de registro por zona e ano, repetição após
    cada tipo de fechamento e teste dos pedidos fechados em massa.

Lê:
    P.pkl, df.pkl
Grava:
    nada (só imprime resultados)
Usado em:
    Limites; decisão de não incluir fechados em massa.
Escrito para este pacote a partir dos trechos rodados durante a análise.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np

df = pd.read_pickle('df.pkl')
df['fim'] = pd.to_datetime(df.data_fim, errors='coerce')
poda = df.subtipo.str.contains('Poda')

# 1) Por que os pedidos de poda foram fechados sem atendimento?
print('Status dos pedidos de poda:'); print(df[poda].status.value_counts().to_string())
for st in ['Sem possibilidade de atendimento', 'Pendente']:
    s = df[poda & df.status.eq(st)].justificativa_status
    print(f'\n== {st}: {len(s)} pedidos; {s.notna().mean():.1%} com justificativa')
    print(s.value_counts().head(8).to_string())

# 2) Como cada zona registra os pedidos de poda (base do "viés regional")
P = pd.read_pickle('P.pkl')
P['fim'] = pd.to_datetime(P.data_fim, errors='coerce'); P['dur'] = (P.fim - P.ini).dt.days
J_INFO = 'Informações'
J_PREV = 'Não há previsão para execução do serviço no local'
def perfil(x):
    j = x.justificativa_status
    return pd.Series({'pedidos': len(x),
        'fechado_info_incorreta': j.str.startswith(J_INFO, na=False).mean(),
        'fechado_sem_previsao': j.eq(J_PREV).mean(),
        'atendido': x.status.isin(['Fechado com solução', 'Fechado com providências']).mean(),
        'pendente_light': x.status.eq('Pendente').mean(),
        'aberto': x.status.isin(['Aberto', 'Em Andamento']).mean()})
print('\nPor zona:'); print(P.groupby('zona').apply(perfil).round(3).to_string())
print('\nPor ano de abertura:'); print(P.groupby(P.ini.dt.year).apply(perfil).round(3).to_string())
sp = P[P.justificativa_status.eq(J_PREV)]
print('\n"Não há previsão": dias até o fechamento (mediana):', sp.dur.median())

# 3) Depois de fechado, o mesmo trecho de rua volta a pedir em 12 meses?
#    (compara atendidos com fechados sem atendimento)
t = df[df.id_logradouro.notna() & (df.numero_logradouro > 0) & (df.numero_logradouro < 100000)].copy()
t['tr'] = t.id_logradouro.astype('int64').astype(str) + '_' + (t.numero_logradouro // 100).astype('int64').astype(str)
t = t.merge(P[['id_chamado', 'zona']], on='id_chamado', how='left')
tpoda = t.subtipo.str.contains('Poda'); tqueda = t.subtipo.eq('Retirada de árvore caída')
j = t.justificativa_status.fillna('')
t['classe'] = np.select([t.status.isin(['Fechado com solução', 'Fechado com providências']),
                         t.status.eq('Sem possibilidade de atendimento') & j.str.startswith(J_INFO),
                         t.status.eq('Sem possibilidade de atendimento') & j.str.startswith('Não há previsão')],
                        ['atendido', 'sem_poss_info', 'sem_poss_prev'], 'outro')
C = t[tpoda & t.fim.notna() & (t.fim >= '2023-01-01') & (t.fim < '2025-06-01') & t.classe.ne('outro')].copy()
gp = {k: v.ini.values for k, v in t[tpoda][['tr', 'ini']].sort_values('ini').groupby('tr')}
gq = {k: v.ini.values for k, v in t[tqueda][['tr', 'ini']].sort_values('ini').groupby('tr')}
def depois(g, tr, t0, dias):
    a = g.get(tr)
    if a is None: return False
    t0 = np.datetime64(t0); i = np.searchsorted(a, t0, side='right')
    return i < len(a) and a[i] <= t0 + np.timedelta64(dias, 'D')
C['pede_de_novo'] = [depois(gp, a, b, 365) for a, b in zip(C.tr, C.fim)]
C['queda'] = [depois(gq, a, b, 365) for a, b in zip(C.tr, C.fim)]
print('\nNovo pedido / queda no mesmo trecho em 12 meses, por tipo de fechamento:')
print(C.groupby('classe')[['pede_de_novo', 'queda']].mean().round(3).to_string())

# 4) Os pedidos fechados em massa em 13–14/10/2025 ainda indicam problema com a rede?
A = df[df.cep.notna()].copy(); A['cep'] = A.cep.astype('int64')
A['poda'] = A.subtipo.str.contains('Poda'); A['queda'] = A.subtipo.eq('Retirada de árvore caída')
A['massa'] = (A.status.eq('Fechado com providências') & A.fim.dt.date.astype(str).isin(['2025-10-13', '2025-10-14'])
              & ((A.fim - A.ini).dt.days > 180) & A.poda)
T, E = pd.Timestamp('2025-10-15'), pd.Timestamp('2026-09-20')
h = A[A.ini < T]
g = pd.DataFrame(index=A.cep.unique())
g['massa'] = h[h.massa].groupby('cep').size(); g['pend'] = h[h.poda & h.status.eq('Pendente')].groupby('cep').size()
g['poda_hist'] = h[h.poda].groupby('cep').size()
f = A[(A.ini >= T) & (A.ini <= E)]
g['y_light'] = f[f.poda & f.status.eq('Pendente')].groupby('cep').size()
g['y_queda'] = f[f.queda].groupby('cep').size()
g = g.fillna(0); g = g[g.poda_hist > 0]
g['grupo'] = np.select([(g.massa > 0) & (g.pend == 0), (g.massa == 0) & (g.pend > 0), (g.massa > 0) & (g.pend > 0)],
                       ['só fechados em massa', 'só Pendentes', 'ambos'], 'nenhum')
g['faixa_hist'] = pd.cut(g.poda_hist, [0, 2, 5, 10, 1000])
print('\nPedidos de massa: fatia de CEPs com novo Pendente depois de out/2025')
print(g.groupby('grupo')[['y_light', 'y_queda']].apply(lambda x: (x > 0).mean()).round(3).join(g.grupo.value_counts()).to_string())
print(g.groupby(['faixa_hist', 'grupo'], observed=True).y_light.apply(lambda x: (x > 0).mean()).unstack().round(3).to_string())
