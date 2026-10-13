"""
Preparação dos dados · A02 — Base de poda com datas, bairros, RAs e zonas
Tipo: principal

O que faz:
    Converte datas de abertura e fechamento, calcula a duração (pedidos abertos contam até
    20/09/2026), traz bairro e região administrativa pelo setor censitário, separa os
    pedidos de poda e marca pend = status Pendente (aproximação de "depende da Light").
    Classifica a zona da cidade pela RA; RA desconhecida entra como Norte.

Lê:
    full.pkl, setor censitário (dados_entrada)
Grava:
    P.pkl, df.pkl
Usado em:
    Todas as análises de poda e Light; ranking.
Script original da análise: light/v1.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
df=pd.read_pickle('full.pkl'); df['ini']=pd.to_datetime(df.data_inicio); df['fim']=pd.to_datetime(df.data_fim,errors='coerce')
END=pd.Timestamp('2026-09-20'); df['dur']=((df.fim.fillna(END))-df.ini).dt.days
S=pd.read_csv(SETOR)
ra=S.groupby('codbairro').regiao_adm.first(); bn=S.groupby('codbairro').bairro.first()
s2=S.set_index('cd_setor')
df['ra']=df.cd_setor.map(s2.regiao_adm); df['bairro']=df.cd_setor.map(s2.bairro)
P=df[df.subtipo.str.contains('Poda')].copy(); P['pend']=P.status.eq('Pendente')
print(P.ra.value_counts().head(3))
# zones: map RA to zone
zona={'CENTRO':'Centro','PORTUARIA':'Centro','RIO COMPRIDO':'Centro','SANTA TERESA':'Centro','PAQUETA':'Centro',
 'BOTAFOGO':'Sul','COPACABANA':'Sul','LAGOA':'Sul','ROCINHA':'Sul',
 'TIJUCA':'Tijuca/Grande Tijuca','VILA ISABEL':'Tijuca/Grande Tijuca',
 'BARRA DA TIJUCA':'Oeste (Barra/Jacarepaguá)','JACAREPAGUA':'Oeste (Barra/Jacarepaguá)','CIDADE DE DEUS':'Oeste (Barra/Jacarepaguá)',
 'BANGU':'Oeste','CAMPO GRANDE':'Oeste','SANTA CRUZ':'Oeste','GUARATIBA':'Oeste','REALENGO':'Oeste'}
P['zona']=P.ra.map(zona).fillna('Norte')
g=P.groupby('zona').agg(poda=('id_chamado','size'),pend=('pend','sum')); g['share_pend']=g.pend/g.pend.sum(); g['taxa']=g.pend/g.poda
print(g.sort_values('pend',ascending=False))
print('dur pend mean',P[P.pend].dur.mean(), 'nao pend fechados mean',P[~P.pend & P.fim.notna()].dur.mean())
# complaints per chamado
print(P.groupby('pend').reclamacoes.agg(['mean',lambda s:(s>0).mean()]))
# ouvidoria unit
print(pd.crosstab(P.nome_unidade_organizacional,P.pend,normalize='index'))
print(P.groupby('nome_unidade_organizacional').reclamacoes.mean())
# monthly pend share by month of opening
m=P.groupby(P.ini.dt.to_period('M')).agg(n=('id_chamado','size'),pend=('pend','sum'),andam=('status',lambda s:s.isin(['Em Andamento','Aberto']).sum()),rec=('reclamacoes','sum'))
print(m.tail(14))
P.to_pickle('P.pkl'); df.to_pickle('df.pkl')
