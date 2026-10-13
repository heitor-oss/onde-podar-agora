"""
Ranking "Onde podar agora" · J11 — Sinais em 8 datas, com modelo retreinado
Tipo: principal

O que faz:
    Reconstrói os sinais em 8 datas trimestrais (jan/2024 a set/2025), retreinando o modelo
    1 em cada uma só com o passado.

Lê:
    df.pkl, gb.pkl, código de H02_modelo1_dados.py, setor censitário (dados_entrada)
Grava:
    pri_roll.pkl
Usado em:
    Robustez dos pesos; nota como chance.
Script original da análise: light/pri_roll.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

# CEP-level features and outcomes at several cutoffs, for improving the priority score
import pandas as pd, numpy as np, pickle
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.neighbors import BallTree
src=open(etapa('m1.py')).read(); exec(src.split("origins=")[0])   # df (trechos), meta, feats, label
gb=pickle.load(open('gb.pkl','rb'))
tc=df[df.cep.notna()].groupby('tr').cep.agg(lambda s:s.mode().iloc[0]).astype('int64')
# all calls
A=pd.read_pickle('df.pkl'); A=A[A.cep.notna()].copy(); A['cep']=A.cep.astype('int64')
A['ini']=pd.to_datetime(A.data_inicio); A['fim']=pd.to_datetime(A.data_fim,errors='coerce')
A['poda']=A.subtipo.str.contains('Poda'); A['queda']=A.subtipo.eq('Retirada de árvore caída')
A['rq']=A.subtipo.isin(['Avaliação de risco de queda da árvore','Retirada de árvore caída'])|A.subtipo.str.contains('Remoção')
A['mass']=A.status.eq('Fechado com providências')&A.fim.dt.date.astype(str).isin(['2025-10-13','2025-10-14'])&((A.fim-A.ini).dt.days>180)&A.poda
print('mass closure cases',A.mass.sum())
A['pendnow']=A.poda&A.status.eq('Pendente')
A['semprev']=A.status.eq('Sem possibilidade de atendimento')&A.justificativa_status.fillna('').str.startswith('Não há previsão')&A.poda
A['addr']=A.id_logradouro.astype('Int64').astype(str)+'_'+A.numero_logradouro.astype('Int64').astype(str)
S=pd.read_csv(SETOR).set_index('cd_setor')
A['arv']=A.cd_setor.map(S.arvore_urbana)
ok=A.latitude_usada.notna()
cen=A[ok].groupby('cep').agg(lat=('latitude_usada','median'),lon=('longitude_usada','median'),arv=('arv','mean'))
cen['gx']=((cen.lon+43.8)*102.5).astype(int); cen['gy']=((cen.lat+23.1)*110.6).astype(int)
R=6371000
def at(T,model):
    h=A[A.ini<T]; age=(T-h.ini).dt.days
    openT=h.fim.isna()|(h.fim>T)
    lightT=h.pendnow|(h.mass&(h.fim>T))
    g=pd.DataFrame(index=cen.index)
    def cnt(m,col='cep'): return h[m].groupby('cep').size()
    def nun(m): return h[m].groupby('cep').addr.nunique()
    com=h.poda&openT&~lightT&(age<=730)&~h.status.isin(['Pendente'])
    g['com']=cnt(com); g['com_u']=nun(com)
    g['light']=cnt(h.poda&lightT); g['light_u']=nun(h.poda&lightT); g['light2y']=cnt(h.poda&lightT&(age<=730))
    g['risco']=cnt(h.rq&(age<=365)); g['queda12']=cnt(h.queda&(age<=365)); g['risco_u']=nun(h.rq&(age<=365))
    g['esp']=age[com].groupby(h.cep[com]).max()
    g['semprev']=cnt(h.semprev&(h.fim<T)&(age<=730))
    # gb prob
    F=feats(T); c=(F.poda_all+F.risk+F.queda+F.remo+F.rua_poda>0); Fc=F[c]
    pr=pd.Series(model.predict_proba(Fc)[:,1],index=Fc.index); pr=pd.DataFrame({'p':pr,'cep':tc.reindex(pr.index)}).dropna()
    g['prob']=pr.groupby('cep').p.max()
    # spatial: light pending and falls within 150 m / 300 m of CEP centroid (all CEPs incl own)
    pts=h[(h.poda&lightT)&h.latitude_usada.notna()]
    tree=BallTree(np.radians(pts[['latitude_usada','longitude_usada']].values),metric='haversine')
    X=np.radians(cen[['lat','lon']].values)
    g['light150']=tree.query_radius(X,150/R,count_only=True)
    qp=h[h.queda&h.latitude_usada.notna()]
    tq=BallTree(np.radians(qp[['latitude_usada','longitude_usada']].values),metric='haversine')
    g['queda300']=tq.query_radius(X,300/R,count_only=True)
    # rainy-season falls in the 1 km cell, before T
    qr=h[h.queda&h.ini.dt.month.isin([12,1,2,3,4])&h.latitude_usada.notna()].copy()
    qr['gx']=((qr.longitude_usada+43.8)*102.5).astype(int); qr['gy']=((qr.latitude_usada+23.1)*110.6).astype(int)
    qc=qr.groupby(['gx','gy']).size()
    g['qcell']=[qc.get((x,y),0) for x,y in zip(cen.gx,cen.gy)]
    g['arv']=cen.arv
    g=g.fillna({k:0 for k in g.columns if k!='arv'})
    g['active']=(g.com+g.light+g.risco)>0
    # outcomes in (T, T+365]
    f=A[(A.ini>=T)&(A.ini<T+pd.Timedelta(days=365))]
    g['y_queda']=f[f.queda].groupby('cep').size().reindex(g.index,fill_value=0)
    g['y_rq']=f[f.rq].groupby('cep').size().reindex(g.index,fill_value=0)
    g['y_light']=f[f.poda&(f.pendnow|f.mass)].groupby('cep').size().reindex(g.index,fill_value=0)
    g['y_poda']=f[f.poda].groupby('cep').size().reindex(g.index,fill_value=0)
    return g

import time
_fc={}
_feats=feats
def feats(T):
    k=str(pd.Timestamp(T).date())
    if k not in _fc: _fc[k]=_feats(T)
    return _fc[k]
Q=[pd.Timestamp(x) for x in ['2023-01-01','2023-04-01','2023-07-01','2023-10-01','2024-01-01','2024-04-01','2024-07-01','2024-10-01','2025-01-01','2025-04-01','2025-07-01']]
CUTS=[pd.Timestamp(x) for x in ['2024-01-01','2024-04-01','2024-07-01','2024-10-01','2025-01-01','2025-04-01','2025-07-01','2025-09-15']]
out={}
for T in CUTS:
    t0=time.time()
    origs=[o for o in Q if o+pd.Timedelta(days=365)<=T][-2:]
    Xs=[];ys=[]
    for o in origs:
        F=feats(o); y=label(o); c=(F.poda_all+F.risk+F.queda+F.remo+F.rua_poda>0); Xs.append(F[c]); ys.append((y[c]>0).astype(int))
    m=HistGradientBoostingClassifier(max_iter=400,learning_rate=0.04,max_leaf_nodes=31,min_samples_leaf=40,l2_regularization=1.0,random_state=0).fit(pd.concat(Xs),pd.concat(ys))
    g=at(T,m); out[str(T.date())]=g
    print(T.date(),'origens',[str(o.date()) for o in origs],'ativos',int(g.active.sum()),'base',{k:round((g[g.active][k]>0).mean(),3) for k in ['y_queda','y_rq','y_light']},round(time.time()-t0),'s',flush=True)
    pickle.dump(out,open('pri_roll.pkl','wb'))
print('fim')
