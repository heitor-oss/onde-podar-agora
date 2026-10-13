"""
Preparação dos dados · A03 — Clima diário da cidade (Open-Meteo)
Tipo: principal

O que faz:
    Lê o clima diário (chuva média, chuva máxima, maior chuva em 1 hora, maior rajada, chuva
    dos 3 e 7 dias anteriores) e confere as somas.

Lê:
    clima Open-Meteo (dados_entrada)
Grava:
    clima.pkl
Usado em:
    Modelos 2 e 3, sazonalidade.
Escrito para este pacote a partir dos trechos rodados durante a análise.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd

# Colunas do arquivo (uma linha por dia, de 01/08/2022 a 20/09/2026):
#   chuva_media     chuva do dia (mm), média entre os pontos consultados na cidade
#   chuva_max       chuva do dia (mm) no ponto mais chuvoso
#   chuva_hora_max  maior chuva em 1 hora no dia (mm)
#   rajada_max      maior rajada de vento do dia (km/h)
#   chuva_3d_ant    soma de chuva_media nos 3 dias anteriores (sem o próprio dia)
#   chuva_7d_ant    soma de chuva_media nos 7 dias anteriores
w = pd.read_csv(CLIMA_OPENMETEO, parse_dates=['data'], index_col='data').asfreq('D')
w.index.name = None

# Conferência: as somas dos dias anteriores batem com a chuva média
chk3 = w.chuva_media.shift(1).rolling(3).sum()
assert ((chk3 - w.chuva_3d_ant).abs().dropna() < 1e-6).all()

print(w.describe().round(1).to_string())
w.to_pickle('clima.pkl')
