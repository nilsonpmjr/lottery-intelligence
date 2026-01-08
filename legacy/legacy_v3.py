
import pandas as pd
import numpy as np
import requests
import sqlite3
import json
import os
from collections import Counter
import itertools
import time
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

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
        "orcamento_alvo": 35.00, # ~10 jogos
        "fixed_core": 4,
        "variable_selection": 11
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

# --- FILTROS AVANÇADOS V3 ---
class AdvancedFilters:
    @staticmethod
    def count_primes(jogo):
        # Primos até 100 (cobre todas as loterias)
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
        return len([x for x in jogo if x in primes])

    @staticmethod
    def count_fibonacci(jogo):
        # Fibonacci até 100
        fibs = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        return len([x for x in jogo if x in fibs])

    @staticmethod
    def count_consecutive(jogo):
        sorted_jogo = sorted(jogo)
        max_seq = 0
        current_seq = 1
        for i in range(1, len(sorted_jogo)):
            if sorted_jogo[i] == sorted_jogo[i-1] + 1:
                current_seq += 1
            else:
                max_seq = max(max_seq, current_seq)
                current_seq = 1
        return max(max_seq, current_seq)

    @staticmethod
    def validar_v3(jogo, loteria, ultimo_resultado=None):
        soma = sum(jogo)
        
        if loteria == 'lotofacil':
            # 1. Filtro de Soma (Normal: 180-210)
            # Vamos usar 160-230 para não ser restritivo demais, mas cortar lixo
            if not (160 <= soma <= 230): return False
            
            # 2. Filtro de Primos (Normal: 4-6)
            n_primos = AdvancedFilters.count_primes(jogo)
            if not (3 <= n_primos <= 8): return False
            
            # 3. Filtro de Fibonacci (Normal: 3-5)
            n_fib = AdvancedFilters.count_fibonacci(jogo)
            if not (2 <= n_fib <= 7): return False
            
            # 4. Filtro de Sequência (Evita bursts gigantes tipo 1,2,3,4,5,6)
            max_seq = AdvancedFilters.count_consecutive(jogo)
            if max_seq > 6: return False
            
            # 5. Filtro de Repetentes (Normal: 8-10)
            if ultimo_resultado:
                repetidas = len(set(jogo).intersection(set(ultimo_resultado)))
                if not (7 <= repetidas <= 11): return False 
        
        
        return True

# --- MOTOR DE INTELIGÊNCIA ARTIFICIAL (V3) ---
class LotteryAI:
    def __init__(self, history):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        self.train(history)
        
    def _vectorize(self, jogo, total_nums=25):
        # Cria vetor binário [0, 1, 0, 0, 1...] para as dezenas
        vec = np.zeros(total_nums)
        for n in jogo:
            if 1 <= n <= total_nums:
                vec[n-1] = 1
        return vec
        
    def train(self, history):
        print("   [AI] Treinando Brain (Random Forest)...")
        X = []
        y = []
        
        # 1. Exemplos Positivos (Jogos Reais)
        for jogo in history:
            X.append(self._vectorize(jogo))
            y.append(1) # Classe 1 = Real
            
        # 2. Exemplos Negativos (Jogos Aleatórios/Ruídos)
        # Geramos a mesma quantidade de jogos aleatórios para balancear
        for _ in range(len(history)):
            ruido = np.random.choice(range(1, 26), 15, replace=False)
            X.append(self._vectorize(ruido))
            y.append(0) # Classe 0 = Fake
            
        self.model.fit(X, y)
        self.is_trained = True
        print(f"   [AI] Modelo treinado com {len(X)} amostras.")
        
    def predict_score(self, jogo):
        if not self.is_trained: return 0.5
        vec = self._vectorize(jogo)
        # Retorna a probabilidade de ser Classe 1 (Real)
        return self.model.predict_proba([vec])[0][1]

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

def gerar_lotofacil(stats, orcamento, ultimo_resultado=None, history=None):
    custo = CONFIG_LOTERIAS['lotofacil']['preco']
    qtd_jogos = int(orcamento // custo)
    print(f"   -> Gerando {qtd_jogos} jogos (Matriz V3 + ML Random Forest)...")
    
    
    # ESTRATÉGIA V3.2: MATRIZ DINÂMICA (CAOS AMPLIADO)
    sorted_stats = stats.sort_values('score', ascending=False)
    
    # 1. Núcleo Fixo Reduzido (Top 4): Aumenta variância.
    nucleo_fixo = sorted_stats.head(4)['numero'].values
    
    # 2. Pool de Cobertura Híbrido:
    #    - 12 dezenas "Mornas" (Posição 5 a 16)
    #    - 5 dezenas "Frias/Zebras" (Do fundo da tabela) para pegar as surpresas
    mornas = sorted_stats.iloc[4:16]['numero'].values
    frias = sorted_stats.tail(5)['numero'].values # As zebras
    
    cobertura_pool = np.concatenate([mornas, frias])
    
    print(f"      [V3.2] Núcleo Fixo (4): {nucleo_fixo}")
    print(f"      [V3.2] Cobertura ({len(cobertura_pool)}): {len(cobertura_pool)} dezenas (Inclui {len(frias)} Zebras)")
    
    # TREINAR AI SE HISTÓRICO DISPONÍVEL
    ai_model = None
    if history and len(history) > 100:
        ai_model = LotteryAI(history)

    jogos = []
    attempts = 0
    max_attempts = 10000 
    
    while len(jogos) < qtd_jogos and attempts < max_attempts:
        attempts += 1
        
        # ESTRATÉGIA V3.2: REINVESTIMENTO (CAOS AMPLIADO)
        # Gera jogo: 4 Fixas + 11 Variáveis (para dar 15)
        # Isso reduz a dependência do núcleo e aumenta a chance de pegar zebras
        variaveis = np.random.choice(cobertura_pool, 11, replace=False)
        j = sorted(list(np.concatenate([nucleo_fixo, variaveis])))
        variaveis = np.random.choice(cobertura_pool, 10, replace=False)
        j = sorted(list(np.concatenate([nucleo_fixo, variaveis])))
        
        # --- APLICANDO FILTROS V3 (Estatística Clássica) ---
        if not AdvancedFilters.validar_v3(j, 'lotofacil', ultimo_resultado):
            continue
            
        # --- APLICANDO FILTRO AI (Machine Learning) ---
        if ai_model:
            score = ai_model.predict_score(j)
            # Aceita apenas se parecer "real" (Score > 0.5)
            # Como a AI tende a ser muito cética, 0.5 é um bom cutoff
            if score < 0.5:
                continue 
            
        # Converte para lista pura
    attempts = 0
    max_attempts = 10000 
    
    while len(jogos) < qtd_jogos and attempts < max_attempts:
        attempts += 1
        
        # Gera jogo: 7 Fixas + 8 Variáveis (escolhidas das 13)
        variaveis = np.random.choice(cobertura_pool, 8, replace=False)
        j = sorted(list(np.concatenate([nucleo_fixo, variaveis])))
        
        # --- APLICANDO FILTROS V3 (Estatística Clássica) ---
        if not AdvancedFilters.validar_v3(j, 'lotofacil', ultimo_resultado):
            continue
            
        # --- APLICANDO FILTRO AI (Machine Learning) ---
        # Se AI estiver ativa, exige score > 0.6
        # Como não passamos AI ainda, vamos deixar o placeholder
            
        # Converte para lista pura para garantir comparação e armazenamento
        j_list = [int(x) for x in j] 
        
        if j_list not in jogos:
            jogos.append(j_list)
            
    print(f"      [DEBUG] Tentativas necessárias: {attempts}")
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
    
    # 1. Atualizar DB (Disabled for offline generation)
    # for loteria in CONFIG_LOTERIAS:
    #     baixar_e_salvar(loteria, conn)
        
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
        
        last_result = hist[-1] if hist else None

        # Dispatcher - Passando history para Lotofacil
        if loteria == 'megasena': jogos = gerar_mega(stats, orcamento)
        elif loteria == 'lotofacil': jogos = gerar_lotofacil(stats, orcamento, last_result, hist)
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
