"""
Prontidão em dias de temporal (modelo 3) · F04 — Exemplos de dias para a página
Tipo: principal

O que faz:
    Separa exemplos de dias com os quadrados em alerta e as quedas reais.

Lê:
    cityday2.pkl, full.pkl, q2_rows.pkl, q7_days.pkl, q7_pred.pkl, q7_res.json
Grava:
    q7_out.json
Usado em:
    Página de picos.
Script original da análise: q7c.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle, json
P=pickle.load(open('q7_pred.pkl','rb')); p=P['pred']['+ clima do dia']; pf=P['pred']['Histórico + pedidos recentes']
Yt,dte,cte=P['Yt'],P['dte'],P['cte']; days=pd.date_range('2022-09-01','2026-09-20')
cells=pickle.load(open('q2_rows.pkl','rb'))['cells']
g=pd.read_pickle('q7_days.pkl'); d2=pd.read_pickle('cityday2.pkl')
thr=float(np.quantile(p,0.95))
df=pd.DataFrame({'d':dte,'c':cte,'p':p,'pf':pf,'y':Yt})
full=pd.read_pickle('full.pkl'); full=full[full.latitude_usada.notna()].copy()
full['cell']=((full.longitude_usada+43.8)*102.5).astype(int)*100+((full.latitude_usada+23.1)*110.6).astype(int)
full['dd']=pd.to_datetime(full.data_inicio).dt.normalize()
ex=[]
for ds in ['2026-07-29','2025-04-05','2026-04-02','2025-06-10']:
    di=(pd.Timestamp(ds)-days[0]).days; s=df[df.d==di]
    al=s[s.p>=thr].c.tolist()
    q=full[(full.dd==ds)&(full.subtipo=='Retirada de árvore caída')]
    r=d2.loc[ds]
    ex.append(dict(d=ds,al=al,pts=q[['latitude_usada','longitude_usada']].round(4).values.tolist(),n=int(len(q)),
       cap=float(s[s.p>=thr].y.sum()/max(s.y.sum(),1)),chuva=round(float(r.chuva_media),1),chuva_h=round(float(r.chuva_hora_max),1),rajada=int(r.rajada_max),ontem=int(d2.quedas.shift(1).loc[ds])))
    print(ds,len(al),ex[-1]['cap'],len(q))
# daily series
ser=dict(d=[str(days[i].date()) for i in g.index],q=g.y.astype(int).tolist(),n=g.n_al.astype(int).tolist(),al=g.alerta.astype(int).tolist(),cap=g.cap.astype(int).tolist())
# top areas list (latest day ranking by pf)
last=df[df.d==df.d.max()].sort_values('pf',ascending=False).head(12)
top=[]
for c in last.c:
    sub=full[full.cell==cells[c]]
    top.append(dict(bairro=sub.cep_bairro_ref.mode().iloc[0] if sub.cep_bairro_ref.notna().any() else '',rua=sub.cep_logradouro_ref.mode().iloc[0] if sub.cep_logradouro_ref.notna().any() else '',
                    n=int(len(sub)),q=int((sub.subtipo=='Retirada de árvore caída').sum()),lat=round(float(sub.latitude_usada.median()),4),lon=round(float(sub.longitude_usada.median()),4)))
print(pd.DataFrame(top))
res=json.load(open('q7_res.json'))
out=dict(res=res,ex=ex,ser=ser,top=top,cells=[int(c) for c in cells],
  ops=dict(normal_dias=501,normal_cel=26.4,normal_med=1,alerta_dias=127,alerta_cel=137,alerta_med=90,storm_dias=18,storm_cel=235,storm_cap=988/1726,
           normal_q=2577,normal_capt=675,alerta_q=2429,alerta_capt=1271),
  regra=dict(lo=10,hi=200,budget=0.057,cap=0.378))
json.dump(out,open('q7_out.json','w'),ensure_ascii=False)
