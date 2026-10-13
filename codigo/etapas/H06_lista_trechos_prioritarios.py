"""
Árvores e rede elétrica: trechos e modelo 1 · H06 — Lista de 500 trechos prioritários
Tipo: principal

O que faz:
    Aplica o modelo 1 aos dados atuais e gera a lista de trechos com mais pedidos esperando
    a Light.

Lê:
    gb.pkl, código de H02_modelo1_dados.py
Grava:
    L.pkl, lista_prioridade_trechos_light.csv, pilot.json
Usado em:
    Planilha lista_prioridade_trechos_light.csv.
Script original da análise: light/b1.py
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
L=Fc.join(meta.drop(columns=['arv','constr']))
L['faixa']=(L.blk*100).astype(int).astype(str)+'–'+(L.blk*100+99).astype(int).astype(str)
last=df[df.pend].groupby('tr').ini.max()
L['ultimo_pedido_light']=last.reindex(L.index).dt.date
L=L.sort_values(['pend_all','prob'],ascending=False)
L['prioridade']=np.arange(1,len(L)+1)
out=L[L.pend_all>0].head(500)[['prioridade','bairro','ra','rua','faixa','pend_all','ultimo_pedido_light','poda_all','served_all','viz_pend','prob','lat','lon']]
out.columns=['prioridade','bairro','regiao_administrativa','logradouro','faixa_numeracao','pedidos_aguardando_light','ultimo_pedido_light','pedidos_poda_total','podas_atendidas','pedidos_light_trechos_vizinhos','prob_novo_pedido_light_12m','lat','lon']
out['prob_novo_pedido_light_12m']=out.prob_novo_pedido_light_12m.round(3)
out.to_csv(os.path.join(SAIDAS,'lista_prioridade_trechos_light.csv'),index=False)
print(out.head(15).to_string())
# also list of new-risk trechos (no pendente yet) top 200 by prob
nw=L[L.pend_all==0].sort_values('prob',ascending=False).head(200)
print(nw[['bairro','rua','faixa','prob','poda_all','viz_pend','rua_pend']].head(10))
# bairro summary for pilot
P=df[df.pend]
B=P.groupby('bairro').agg(pend_total=('id_chamado','size'),trechos=('tr','nunique'),pend_2025=('ini',lambda s:((s>='2025-01-01')&(s<'2026-01-01')).sum()),ra=('ra','first'))
allp=df[df.ispoda].groupby('bairro').size(); B['poda_total']=allp.reindex(B.index); B['taxa_light']=B.pend_total/B.poda_total
B['conc_top10']=P.groupby('bairro').tr.apply(lambda s: s.value_counts().head(10).sum()/len(s))
B=B.sort_values('pend_total',ascending=False)
print(B.head(15).round(3))
B.head(15).reset_index().to_json('pilot.json',orient='records',force_ascii=False)
L[['lat','lon','pend_all','prob']].to_pickle('L.pkl')
