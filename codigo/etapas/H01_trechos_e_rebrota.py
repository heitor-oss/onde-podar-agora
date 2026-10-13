"""
Árvores e rede elétrica: trechos e modelo 1 · H01 — Trechos de rua e volta do problema depois da poda
Tipo: principal

O que faz:
    Cria o trecho (logradouro + faixa de 100 números), mede quantos pedidos da Light surgem
    onde já havia outro e, depois de uma poda atendida, em quanto tempo o trecho volta a ter
    qualquer pedido ou pedido que depende da Light (curvas de Kaplan–Meier).

Lê:
    P.pkl
Grava:
    Ptr.pkl, c2.json, surv.pkl
Usado em:
    Página "Árvores e rede elétrica"; base do modelo 1.
Script original da análise: light/c1.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
P=pd.read_pickle('P.pkl'); END=pd.Timestamp('2026-09-20')
P=P[P.id_logradouro.notna()&(P.numero_logradouro>0)&(P.numero_logradouro<100000)].copy()
P['tr']=P.id_logradouro.astype('int64').astype(str)+'_'+(P.numero_logradouro//100).astype('int64').astype(str)
P['lg']=P.id_logradouro.astype('int64')
print('podas com trecho',len(P),'trechos',P.tr.nunique(),'logradouros',P.lg.nunique())
print('podas por trecho',P.groupby('tr').size().describe(percentiles=[.5,.9,.99]))
P=P.sort_values(['tr','ini']).reset_index(drop=True)
P['served']=P.status.isin(['Fechado com solução','Fechado com providências'])
# next request on same trecho
P['next_ini']=P.groupby('tr').ini.shift(-1)
# (a) after served poda: time from fim to next request
S=P[P.served & P.fim.notna()].copy()
S['t']=(S.next_ini-S.fim).dt.days; S['obs']=S.next_ini.notna()&(S.t>0)
S.loc[~S.obs,'t']=(END-S.fim).dt.days
S=S[S.t>0]
def km(t,e,grid):
    t=np.asarray(t); e=np.asarray(e); order=np.argsort(t); t=t[order]; e=e[order]
    surv=1; out={}; n=len(t); i=0; uniq=np.unique(t[e])
    s=[];times=[]
    at=n
    import bisect
    res=[]
    cur=1.0
    # vectorized KM
    ts,idx=np.unique(t,return_index=True)
    d=pd.DataFrame({'t':t,'e':e}).groupby('t').agg(d=('e','sum'),n=('e','size'))
    d['atrisk']=n-d.n.cumsum().shift(1,fill_value=0)
    d['s']=(1-d.d/d.atrisk).cumprod()
    return [float(1-d.s[d.index<=g].iloc[-1]) if (d.index<=g).any() else 0.0 for g in grid]
grid=[30,90,180,365,540,730,1095]
print('apos poda atendida: prob de novo pedido no trecho', dict(zip(grid,np.round(km(S.t,S.obs,grid),3))))
# (b) Pendente: share of new pendente requests where trecho already had an open (pendente) request earlier
P['prev_pend_open']=P.groupby('tr').pend.transform(lambda s: s.shift(1).fillna(False).astype(bool).cummax())
Pe=P[P.pend]
print('pendentes',len(Pe),'em trecho que ja tinha pendente anterior',Pe.prev_pend_open.mean())
# any earlier poda request in trecho
P['prev_any']=P.groupby('tr').cumcount()>0
print('pendentes com qualquer pedido anterior no trecho',P[P.pend].prev_any.mean(), 'nao pend', P[~P.pend].prev_any.mean())
# trechos with pendente: count of pendente per trecho
c=Pe.groupby('tr').size(); print('trechos com pendente',len(c),'pendentes por trecho',c.describe(percentiles=[.5,.9]), 'share pendentes in trechos with >=2', c[c>=2].sum()/c.sum())
P.to_pickle('Ptr.pkl'); S[['tr','t','obs']].to_pickle('surv.pkl')

# --- Curvas usadas na página (c2.json): depois de uma poda atendida, chance de o mesmo trecho
#     ter qualquer novo pedido ("any") ou novo pedido que depende da Light ("light") em até N dias.
#     Conta o primeiro pedido aberto depois da data de fechamento; dias arredondados para cima.
import json
grid=[30,90,180,270,365,540,730,900,1095]
Sv=P[P.served & P.fim.notna()].copy()
def primeiro_depois(por_trecho, tr, t0):
    a=por_trecho.get(tr)
    if a is None: return np.datetime64('NaT')
    i=np.searchsorted(a,np.datetime64(t0),side='right'); return a[i] if i<len(a) else np.datetime64('NaT')
curvas={}
for nome,base in [('any',P),('light',P[P.pend])]:
    por_trecho={k:np.sort(v.ini.values) for k,v in base.groupby('tr')}
    nx=np.array([primeiro_depois(por_trecho,a,b) for a,b in zip(Sv.tr,Sv.fim)],dtype='datetime64[ns]')
    obs=~np.isnat(nx)
    t=np.where(obs,np.ceil((nx-Sv.fim.values.astype('datetime64[ns]'))/np.timedelta64(1,'D')),(END-Sv.fim).dt.days.values)
    m=t>=0
    curvas[nome]=km(t[m],obs[m],grid)
    print('depois de poda atendida, novo pedido',nome,dict(zip(grid,np.round(curvas[nome],3))))
json.dump(dict(grid=grid,any=curvas['any'],light=curvas['light'],n=int(m.sum())),open('c2.json','w'))
