
import sqlite3
import requests
import json
import os
from .config import CONFIG_LOTERIAS, DB_PATH

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def setup_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabela simples para cada loteria
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
        
        # O formato do JSON pode variar
        items = []
        if isinstance(data, dict):
            for k, v in data.items():
                items.append({'concurso': k, 'dezenas': v})
        elif isinstance(data, list):
            items = data
            
        for item in items:
            concurso = item.get('Concurso') or item.get('concurso')
            dezenas = item.get('Dezenas') or item.get('dezenas')
            data_sorteio = item.get('Data') or item.get('data') or ""
            
            if not concurso or not dezenas: continue
            
            try:
                dezenas_clean = []
                for d in dezenas:
                    try:
                        val = int(d)
                        dezenas_clean.append(val)
                    except:
                        pass
                
                min_nums = CONFIG_LOTERIAS[loteria]['escolhe']
                if len(dezenas_clean) < min_nums:
                    continue
                    
                dezenas_json = json.dumps(sorted(dezenas_clean))
                
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {loteria} (concurso, data, dezenas) 
                    VALUES (?, ?, ?)
                ''', (int(concurso), data_sorteio, dezenas_json))
                registros += 1
            except Exception as ex:
                continue
                
        conn.commit()
        print(f"[{loteria.upper()}] {registros} registros salvos/atualizados.")
        return True
    except Exception as e:
        print(f"[{loteria.upper()}] Erro no ETL: {e}")
        return False
