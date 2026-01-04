
import pandas as pd
import numpy as np
import requests
import sqlite3
import json
import os
from collections import Counter
import itertools
import time

# --- CONFIGURAÇÃO ---
DB_PATH = "loterias.db"
URL_BASE = "https://raw.githubusercontent.com/guilhermeasn/loteria.json/master/data/"

CONFIG_LOTERIAS = {
    "megasena": {
        "url": URL_BASE + "megasena.json", 
        "preco": 6.00, 
        "total_nums": 60, 
        "escolhe": 6,
        "orcamento_alvo": 12.00 # ~2 jogos
    },
    "lotofacil": {
        "url": URL_BASE + "lotofacil.json", 
        "preco": 3.50, 
        "total_nums": 25, 
        "escolhe": 15,
        "orcamento_alvo": 35.00 # ~10 jogos
    },
    "lotomania": {
        "url": URL_BASE + "lotomania.json", 
        "preco": 3.00, 
        "total_nums": 100, 
        "escolhe": 50,
        "orcamento_alvo": 15.00 # ~5 jogos
    },
    "diadesorte": {
        "url": URL_BASE + "diadesorte.json", 
        "preco": 2.50, 
        "total_nums": 31, 
        "escolhe": 7,
        "orcamento_alvo": 35.00 # ~14 jogos
    }
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def setup_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabela simples para cada loteria (armazenamos como string JSON as dezenas para simplificar)
    for loteria in CONFIG_LOTERIAS:
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {loteria} (
                concurso INTEGER PRIMARY KEY,
                data TEXT,
                dezenas TEXT
            )
        ''')
    conn.commit()
    return conn

# --- ETL ---
def baixar_e_salvar(loteria, conn):
    print(f"[{loteria.upper()}] Baixando dados...")
    url = CONFIG_LOTERIAS[loteria]["url"]
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        cursor = conn.cursor()
        registros = 0
        
        # O formato do JSON pode variar (dict ou list)
        items = []
        if isinstance(data, dict):
            for k, v in data.items():
                items.append({'concurso': k, 'dezenas': v})
        elif isinstance(data, list):
            items = data
            
        for item in items:
            # Tentar normalizar chaves
            concurso = item.get('Concurso') or item.get('concurso')
            dezenas = item.get('Dezenas') or item.get('dezenas')
            data_sorteio = item.get('Data') or item.get('data') or ""
            
            # As vezes concurso é chave no dict pai, mas aqui tentamos pegar do item se for lista
            # Se for dict-based loop acima, 'k' é concurso
            
            if not concurso or not dezenas: continue
            
            # Limpar dezenas
            try:
                # Filtrar apenas inteiros (ignora Mês do Dia de Sorte ou lixo)
                dezenas_clean = []
                for d in dezenas:
                    try:
                        val = int(d)
                        dezenas_clean.append(val)
                    except:
                        pass
                
                # Validação básica
                min_nums = CONFIG_LOTERIAS[loteria]['escolhe']
                if len(dezenas_clean) < min_nums:
                    continue
                    
                # Se tiver mais numeros que o total (ex: Lotofacil tem 15, mas se tivesse lixo extra)
                # Mantemos todos os inteiros válidos. 
                # Dia de Sorte tem 7 numeros. Se pegou 7 ints, ta ok.
                
                dezenas_json = json.dumps(sorted(dezenas_clean))
                
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {loteria} (concurso, data, dezenas) 
                    VALUES (?, ?, ?)
                ''', (int(concurso), data_sorteio, dezenas_json))
                registros += 1
            except Exception as ex:
                # print(f"Erro item: {ex}")
                continue
                
        conn.commit()
        print(f"[{loteria.upper()}] {registros} registros salvos/atualizados.")
        return True
    except Exception as e:
        print(f"[{loteria.upper()}] Erro no ETL: {e}")
        return False

def carregar_stats(loteria, conn):
    df = pd.read_sql(f"SELECT dezenas FROM {loteria}", conn)
    nums_flat = []
    historico = []
    
    for _, row in df.iterrows():
        try:
            d = json.loads(row['dezenas'])
            nums_flat.extend(d)
            historico.append(d)
        except: pass
        
    total_concursos = len(historico)
    freq = Counter(nums_flat)
    
    # Calcular Atraso
    # Se num não saiu, atraso = total_concursos
    ultimos = historico
    atrasos = {}
    total_nums = CONFIG_LOTERIAS[loteria]["total_nums"]
    
    for n in range(1, total_nums + 1):
        atraso = 0
        encontrou = False
        for i, sorteio in enumerate(reversed(ultimos)):
            if n in sorteio:
                atraso = i
                encontrou = True
                break
        if not encontrou:
            atraso = total_concursos
        atrasos[n] = atraso
            
    # DataFrame de Stats
    stats = pd.DataFrame({'numero': range(1, total_nums + 1)})
    stats['freq'] = stats['numero'].map(freq).fillna(0)
    stats['atraso'] = stats['numero'].map(atrasos)
    
    # --- TUNING 2.0: TENDÊNCIA RECENTE (HOT STREAK) ---
    # Analisar apenas os últimos 30 concursos para pegar "ondas"
    ultimos_30 = historico[-30:] if len(historico) > 30 else historico
    nums_recentes = []
    for s in ultimos_30:
        nums_recentes.extend(s)
    freq_rec = Counter(nums_recentes)
    stats['freq_recente'] = stats['numero'].map(freq_rec).fillna(0)
    
    # Normalização
    stats['freq_norm'] = stats['freq'] / stats['freq'].max()
    stats['atraso_norm'] = stats['atraso'] / (stats['atraso'].max() or 1)
    stats['freq_rec_norm'] = stats['freq_recente'] / (stats['freq_recente'].max() or 1)
    
    # Score Tunado 2.0
    # Valoriza: Longo Prazo (40%) + Momento Atual (30%) + Atraso/Correção (30%)
    stats['score'] = (stats['freq_norm'] * 0.4) + (stats['freq_rec_norm'] * 0.3) + (stats['atraso_norm'] * 0.3)
        
    return stats, historico

# --- HELPER: FILTRO DE PARIDADE ---
def validar_paridade(jogo, loteria):
    pares = len([x for x in jogo if x % 2 == 0])
    impares = len(jogo) - pares
    
    if loteria == 'megasena': # 6 nums
        # Aceita equilibrio total (3/3) ou leve viés (4/2)
        return pares in [2, 3, 4]
    
    elif loteria == 'diadesorte': # 7 nums
        # Aceita 3/4 ou 4/3
        return pares in [3, 4]

    return True # Outras loterias aceita tudo por enqto

# --- GERADORES DE JOGOS ---

def gerar_mega(stats, orcamento):
    custo = CONFIG_LOTERIAS['megasena']['preco']
    qtd_jogos = int(orcamento // custo)
    print(f"   -> Gerando {qtd_jogos} jogos (Sniper 2.0 - Tendência + Paridade)...")
    
    jogos = []
    # Estratégia Sniper Tunada
    # Pega Top 20 (expandiu um pouco pra ter margem de paridade)
    top_pool = stats.sort_values('score', ascending=False).head(20)['numero'].values
    
    attempts = 0
    while len(jogos) < qtd_jogos and attempts < 1000:
        attempts += 1
        j = sorted(list(np.random.choice(top_pool, 6, replace=False)))
        
        # Filtro de Paridade
        if not validar_paridade(j, 'megasena'):
            continue
            
        if j not in jogos:
            jogos.append(j)
        
    return jogos

def gerar_lotofacil(stats, orcamento):
    custo = CONFIG_LOTERIAS['lotofacil']['preco']
    qtd_jogos = int(orcamento // custo)
    print(f"   -> Gerando {qtd_jogos} jogos (Fechamento/Ciclos 2.0)...")
    
    top_18 = stats.sort_values('score', ascending=False).head(18)['numero'].values
    
    jogos = []
    attempts = 0
    while len(jogos) < qtd_jogos and attempts < 1000:
        attempts += 1
        j = sorted(list(np.random.choice(top_18, 15, replace=False)))
        # Lotofacil paridade ideal: 7p/8i ou 8p/7i (as vezes 6/9)
        pares = len([x for x in j if x % 2 == 0])
        if pares < 6 or pares > 9: # Filtra extremos
            continue
            
        if j not in jogos:
            jogos.append(j)
    return jogos

def gerar_lotomania(stats, orcamento):
    custo = CONFIG_LOTERIAS['lotomania']['preco']
    qtd_jogos = int(orcamento // custo)
    # Mantem logica de espelho, mas usando o score novo
    print(f"   -> Gerando {qtd_jogos} jogos (Espelho 2.0)...")
    
    top_80 = stats.sort_values('score', ascending=False).head(80)['numero'].values
    
    jogos = []
    for _ in range(qtd_jogos):
        quentes = np.random.choice(top_80, 40, replace=False)
        resto = [x for x in range(1, 101) if x not in quentes]
        frias = np.random.choice(resto, 10, replace=False)
        j = sorted(list(np.concatenate([quentes, frias])))
        jogos.append(j)
        
    return jogos

def gerar_diadesorte(stats, orcamento):
    custo = CONFIG_LOTERIAS['diadesorte']['preco']
    qtd_jogos = int(orcamento // custo)
    print(f"   -> Gerando {qtd_jogos} jogos (Fechamento Matemático 2.0)...")
    
    # Expansão inteligente: Top 13 em vez de 12 para dar mais margem
    top_pool = stats.sort_values('score', ascending=False).head(13)['numero'].values
    
    combs = list(itertools.combinations(top_pool, 7))
    np.random.shuffle(combs)
    
    jogos = []
    for c in combs:
        if len(jogos) >= qtd_jogos: break
        
        cand = sorted(list(c))
        
        # Filtro Paridade (Dia de Sorte)
        if not validar_paridade(cand, 'diadesorte'):
            continue
            
        # Filtro Similaridade
        aceita = True
        for j in jogos:
            if len(set(cand).intersection(set(j))) >= 6:
                aceita = False 
                break
        
        if aceita or len(jogos) < 2:
            jogos.append(cand)
            
    # Fallback se filtro for muito rígido
    idx = 0
    while len(jogos) < qtd_jogos and idx < len(combs):
        cand = sorted(list(combs[idx]))
        if cand not in jogos:
             # Relaxa paridade no fallback
            jogos.append(cand)
        idx += 1
        
    return jogos

def main():
    print("=== CENTRAL MULTI-LOTERIA (R$ 100) ===")
    conn = setup_db()
    
    # 1. Atualizar DB
    for loteria in CONFIG_LOTERIAS:
        baixar_e_salvar(loteria, conn)
        
    # 2. Gerar Jogos
    relatorio = "# Palpites Otimizados (Orçamento R$ 100)\n\n"
    
    total_gasto = 0
    
    for loteria, cfg in CONFIG_LOTERIAS.items():
        print(f"\nProcessando {loteria.upper()}...")
        stats, hist = carregar_stats(loteria, conn)
        
        if stats.empty:
            print("Sem dados. Pulando.")
            continue
            
        print(f"   Base Histórica: {len(hist)} sorteios.")
        orcamento = cfg['orcamento_alvo']
        
        # Dispatcher
        if loteria == 'megasena': jogos = gerar_mega(stats, orcamento)
        elif loteria == 'lotofacil': jogos = gerar_lotofacil(stats, orcamento)
        elif loteria == 'lotomania': jogos = gerar_lotomania(stats, orcamento)
        elif loteria == 'diadesorte': jogos = gerar_diadesorte(stats, orcamento)
        
        custo_real = len(jogos) * cfg['preco']
        total_gasto += custo_real
        
        # Adicionar ao Relatório
        relatorio += f"## {loteria.upper()} ({len(jogos)} Jogos - R$ {custo_real:.2f})\n"
        relatorio += f"**Estratégia**: Baseada em {len(hist)} sorteios.\n"
        
        relatorio += "| Jogo | Dezenas |\n| :--- | :--- |\n"
        for i, j in enumerate(jogos, 1):
            # Converter numpy ints para python ints
            j_clean = [int(x) for x in j]
            # Formatar bonito com zero à esquerda se precisar? O padrão str(list) é ok, mas sem 'np.int64'
            j_str = str(j_clean).replace('[','').replace(']','')
            relatorio += f"| {i:02d} | `{j_str}` |\n"
        relatorio += "\n"
        
    relatorio += f"---\n**Investimento Total Estimado**: R$ {total_gasto:.2f}\n"
    
    print("\nGeração Concluída!")
    print(f"Total Gasto: R$ {total_gasto:.2f}")
    
    with open("relatorio_multiloteria.md", "w") as f:
        f.write(relatorio)

if __name__ == "__main__":
    main()
