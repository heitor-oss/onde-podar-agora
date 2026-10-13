"""
Ranking "Onde podar agora" · J04 — Ranking: planilha e dados da página
Tipo: principal

O que faz:
    Gera ranking_ceps_poda.csv (com posição na zona e ação sugerida) e o JSON usado pela
    página.

Lê:
    P.pkl, cep_rank.pkl, df.pkl
Grava:
    rank_data.json, ranking_ceps_poda.csv
Usado em:
    Planilha e página.
Script original da análise: light/rank4.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
g=pd.read_pickle('cep_rank.pkl')
END=pd.Timestamp('2026-09-21')
df=pd.read_pickle('df.pkl'); df=df[df.cep.notna()].copy(); df['cep']=df.cep.astype('int64'); df['age']=(END-pd.to_datetime(df.data_inicio)).dt.days
lp=df[df.subtipo.str.contains('Poda')&df.status.eq('Pendente')].groupby('cep').age.max()
g['lmax']=lp.reindex(g.index).fillna(0)
P=pd.read_pickle('P.pkl'); z=P.groupby('ra').zona.agg(lambda s:s.mode().iloc[0])
g['zona']=g.ra.map(z).fillna('')
print(g.zona.value_counts())
g=g[g.lat.notna()]
rows=[[f'{c:08d}',r.rua,r.bairro,r.ra.title() if isinstance(r.ra,str) else '',r.zona,round(r.lat,4),round(r.lon,4),int(r.comlurb),int(r.light),int(r.risco12),int(r.queda12),int(r.espera_com),int(r.lmax),round(r.prob,2)] for c,r in g.iterrows()]
json.dump(dict(cols=['cep','rua','bairro','ra','zona','lat','lon','com','light','risco','queda','esp','lmax','prob'],rows=rows,ate='20/09/2026'),open('rank_data.json','w'),ensure_ascii=False,separators=(',',':'))
import os; print(len(rows), os.path.getsize('rank_data.json'))
# csv export
out=g.copy(); out.insert(0,'posicao',np.arange(1,len(out)+1))
def acao(r):
    if r.light>0 and r.comlurb>0: return 'COMLURB + agendar Light'
    if r.light>0: return 'Depende da Light'
    if r.comlurb>0: return 'COMLURB pode ir'
    return 'Vistoria de risco'
out['acao']=out.apply(acao,axis=1)
out['pct_zona']=out.groupby('zona').score.rank(ascending=False,pct=True).mul(100).round(2)
out['pos_zona']=out.groupby('zona').score.rank(ascending=False,method='first').astype(int)
out['cep_fmt']=[f'{c:08d}'[:5]+'-'+f'{c:08d}'[5:] for c in out.index]
cs=out[['posicao','cep_fmt','rua','bairro','ra','zona','score','pos_zona','pct_zona','acao','comlurb','light','risco12','queda12','espera_com','lmax','prob','c_risco','c_com','c_light','c_prev','c_esp','lat','lon']].copy()
cs.columns=['posicao','cep','logradouro_ref','bairro','regiao_administrativa','zona','nota_0a100','posicao_na_zona','top_pct_na_zona','acao_sugerida','poda_aberta_comlurb','pedidos_travados_light','risco_queda_remocao_12m','quedas_12m','dias_pedido_comlurb_mais_antigo','dias_pedido_light_mais_antigo','chance_novo_pedido_light_12m','pts_risco_0a1','pts_comlurb_0a1','pts_light_0a1','pts_previsao_0a1','pts_espera_0a1','lat','lon']
cs['nota_0a100']=cs.nota_0a100.round(1)
for c in ['pts_risco_0a1','pts_comlurb_0a1','pts_light_0a1','pts_previsao_0a1','pts_espera_0a1','chance_novo_pedido_light_12m']: cs[c]=cs[c].round(3)
cs.to_csv(os.path.join(SAIDAS,'ranking_ceps_poda.csv'),index=False,encoding='utf-8-sig')
top=out.head(50); print(top.acao.value_counts()); print(top[['comlurb','light','risco12','queda12']].sum())
t100=out.head(100); print(t100.bairro.value_counts().head(10)); print(t100.zona.value_counts())
print(out.acao.value_counts())
