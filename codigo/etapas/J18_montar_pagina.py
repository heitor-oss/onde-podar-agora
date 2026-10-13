"""
Ranking "Onde podar agora" · J18 — Montar a página e o site
Tipo: principal

O que faz:
    Insere o ranking e o mapa no modelo HTML e gera a versão do artefato e o index.html do
    GitHub Pages.

Lê:
    cell_quedas.json
Grava:
    nada (só imprime resultados)
Usado em:
    Página e site.
Escrito para este pacote a partir dos trechos rodados durante a análise.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import re, shutil

# O modelo da página fica em pagina/onde_podar_agora_modelo.html. Ele já contém o texto,
# o estilo, o código JavaScript e as tabelas fixas (faixas de nota, atendido × não atendido,
# validação e robustez), cujos números vêm dos passos J12, J14, J15 e J17.
# Aqui só entram os dados que mudam a cada atualização: o ranking (J04) e os quadrados (J16).
modelo = open(os.path.join(RAIZ, 'pagina', 'onde_podar_agora_modelo.html'), encoding='utf-8').read()
dados = open('rank_data.json', encoding='utf-8').read().replace('</', '<\\/')
celulas = open('cell_quedas.json', encoding='utf-8').read().replace('</', '<\\/')
pagina = modelo.replace('__DATA__', dados).replace('__CELLS__', celulas)

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
site = cab + resto[:i] + '</head>\n<body>\n' + resto[i:] + '\n</body>\n</html>\n'
os.makedirs(os.path.join(SAIDAS, 'site', 'dados'), exist_ok=True)
open(os.path.join(SAIDAS, 'site', 'index.html'), 'w', encoding='utf-8').write(site)
for f in ['ranking_ceps_poda.csv']:
    if os.path.exists(os.path.join(SAIDAS, f)):
        shutil.copy(os.path.join(SAIDAS, f), os.path.join(SAIDAS, 'site', 'dados', f))
print('página:', os.path.join(SAIDAS, 'site', 'index.html'), f'({len(site)/1e6:.1f} MB)')

# Quedas no verão por quadrado, em CSV, para quem quiser usar fora da página
import json, csv
cel = json.load(open('cell_quedas.json', encoding='utf-8'))
with open(os.path.join(SAIDAS, 'site', 'dados', 'quedas_verao_quadrados_1km.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh)
    w.writerow(['gx', 'gy', 'lon_min', 'lat_min', 'lon_max', 'lat_max', 'bairro_predominante', 'quedas_dez_abr_2022_2026'])
    for gx, gy, n, b in cel:
        w.writerow([gx, gy, round(-43.8 + gx / 102.5, 5), round(-23.1 + gy / 110.6, 5),
                    round(-43.8 + (gx + 1) / 102.5, 5), round(-23.1 + (gy + 1) / 110.6, 5), b, n])
