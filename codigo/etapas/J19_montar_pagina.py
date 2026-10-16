"""
Ranking "Onde podar agora" · J19 — Montar a página e o site
Tipo: principal

O que faz:
    Insere o ranking (com as áreas de 150 m), o mapa e a comparação por área × por CEP no
    modelo HTML e gera a versão do artefato e o index.html do GitHub Pages.

Lê:
    rank_data.json, cell_quedas.json, area_bt.json, pagina/onde_podar_agora_modelo.html
Grava:
    saidas/onde_podar_agora_artefato.html, saidas/site/index.html, saidas/site/barra.js (barra do topo e rodapé) e saidas/site/dados/*.csv
Usado em:
    Página e site.
Escrito para este pacote a partir dos trechos rodados durante a análise.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import re, shutil, json

# O modelo da página fica em pagina/onde_podar_agora_modelo.html. Ele já contém o texto,
# o estilo, o código JavaScript e as tabelas fixas (faixas de nota, atendido × não atendido,
# validação e robustez), cujos números vêm dos passos J12, J14, J15 e J17.
# Aqui só entram os dados que mudam a cada atualização: o ranking com as áreas (J04, J18), os quadrados (J16)
# e a comparação por área × por CEP no teste de 2025 (J18, média das duas datas de corte).
modelo = open(os.path.join(RAIZ, 'pagina', 'onde_podar_agora_modelo.html'), encoding='utf-8').read()
dados = open('rank_data.json', encoding='utf-8').read().replace('</', '<\\/')
celulas = open('cell_quedas.json', encoding='utf-8').read().replace('</', '<\\/')
bt = json.load(open('area_bt.json', encoding='utf-8'))
med = lambda grupo, k: int(round(sum(v[grupo][k] for v in bt.values()) / len(bt)))
d, m = '100 destinos', 'mesmo nº de CEPs'
comparacao = dict(
    d100=dict(n=100, area_ceps=med(d, 'areas_ceps'), area_q=med(d, 'areas_quedas'), area_l=med(d, 'areas_light'),
              cep_q=med(d, 'ceps_quedas'), cep_l=med(d, 'ceps_light')),
    mesmo=dict(ceps=med(m, 'ceps'), areas=med(m, 'areas'), area_q=med(m, 'areas_quedas'), area_l=med(m, 'areas_light'),
               cep_q=med(m, 'ceps_quedas'), cep_l=med(m, 'ceps_light')))
print('por área × por CEP:', comparacao)
pagina = (modelo.replace('__DATA__', dados).replace('__CELLS__', celulas)
          .replace('__AREABT__', json.dumps(comparacao, ensure_ascii=False)))

# Versão para publicar como artefato (sem <html>/<head>, o publicador acrescenta)
open(os.path.join(SAIDAS, 'onde_podar_agora_artefato.html'), 'w', encoding='utf-8').write(pagina)

# Versão autônoma para o GitHub Pages (index.html)
titulo = re.search(r'<title>.*?</title>', pagina).group(0)
resto = pagina.replace(titulo, '', 1)
cab = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
       + titulo.replace('<title>Onde podar agora', '<title>Onde podar agora · Rio de Janeiro') + '\n'
       '<meta name="description" content="Os lugares do Rio onde a poda de árvores é mais urgente, por que, '
       'o que pode acontecer se não podar e quem precisa agir, a partir dos chamados abertos do 1746.">\n'
       '<style>body{margin:0}[hidden]{display:none!important}</style>\n')
i = resto.index('<div class="wrap">')
# No site, a página ganha a barra do topo (abas entre as páginas do projeto) e o rodapé com os
# colaboradores; os dois ficam em barra.js
barra = '<site-barra atual="poda"></site-barra>\n<script src="barra.js"></script>\n'
rodape = '\n<site-rodape></site-rodape>'
site = cab + resto[:i] + '</head>\n<body>\n' + barra + resto[i:] + rodape + '\n</body>\n</html>\n'
os.makedirs(os.path.join(SAIDAS, 'site', 'dados'), exist_ok=True)
shutil.copy(os.path.join(RAIZ, 'pagina', 'barra_do_site.js'), os.path.join(SAIDAS, 'site', 'barra.js'))
open(os.path.join(SAIDAS, 'site', 'index.html'), 'w', encoding='utf-8').write(site)
for f in ['ranking_ceps_poda.csv', 'ranking_areas_150m.csv']:
    if os.path.exists(os.path.join(SAIDAS, f)):
        shutil.copy(os.path.join(SAIDAS, f), os.path.join(SAIDAS, 'site', 'dados', f))
print('página:', os.path.join(SAIDAS, 'site', 'index.html'), f'({len(site)/1e6:.1f} MB)')

# Quedas no verão por quadrado, em CSV, para quem quiser usar fora da página
import csv
cel = json.load(open('cell_quedas.json', encoding='utf-8'))
with open(os.path.join(SAIDAS, 'site', 'dados', 'quedas_verao_quadrados_1km.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh)
    w.writerow(['gx', 'gy', 'lon_min', 'lat_min', 'lon_max', 'lat_max', 'bairro_predominante', 'quedas_dez_abr_2022_2026'])
    for gx, gy, n, b in cel:
        w.writerow([gx, gy, round(-43.8 + gx / 102.5, 5), round(-23.1 + gy / 110.6, 5),
                    round(-43.8 + (gx + 1) / 102.5, 5), round(-23.1 + (gy + 1) / 110.6, 5), b, n])
