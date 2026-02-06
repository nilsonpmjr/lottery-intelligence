
import pandas as pd
import numpy as np
import itertools
import json
from collections import Counter
from ..core.config import CONFIG_LOTERIAS
from ..core.filters import AdvancedFilters
from ..intelligence.brain import LotteryAI
from ..core.etl import get_db
from ..core.coverage import CoverageEngine

def carregar_stats(loteria):
    conn = get_db()
    df = pd.read_sql(f"SELECT dezenas FROM {loteria}", conn)
    conn.close()
    
    nums_flat = []
    historico = []
    
    for _, row in df.iterrows():
        try:
            d = json.loads(row['dezenas'])
            nums_flat.extend(d)
            historico.append(d)
        except: pass
        
    if not nums_flat: return None, None
    
    # Frequencia
    counts = Counter(nums_flat)
    total_sorteios = len(df)
    
    stats_data = []
    for n in range(1, CONFIG_LOTERIAS[loteria]['total_nums'] + 1):
        freq = counts[n]
        prob = freq / total_sorteios
        
        # Atraso (Delay)
        delay = 0
        for h in reversed(historico):
            if n in h: break
            delay += 1
            
        stats_data.append({'numero': n, 'frequencia': freq, 'prob': prob, 'atraso': delay})
        
    stats_df = pd.DataFrame(stats_data)
    
    # --- SCORING V2.0 ---
    max_delay = stats_df['atraso'].max()
    stats_df['score_freq'] = stats_df['prob'] # Quanto mais sai, melhor
    stats_df['score_delay'] = stats_df['atraso'] / max_delay if max_delay > 0 else 0 # Quanto mais atrasado, melhor (teoria do retorno)
    
    # Peso de Recência (Hot Streak - Ultimos 30) - V2
    ultimos_30 = historico[-30:] if len(historico) > 30 else historico
    flat_30 = [n for sub in ultimos_30 for n in sub]
    count_30 = Counter(flat_30)
    stats_df['score_recent'] = stats_df['numero'].apply(lambda x: count_30[x] / 30)
    
    # Score Final: 40% Freq Global + 30% Atraso + 30% Recência
    stats_df['score'] = (0.4 * stats_df['score_freq']) + (0.3 * stats_df['score_delay']) + (0.3 * stats_df['score_recent'])
    
    return stats_df, historico

# --- GERADORES ---

def gerar_megasena(stats, orcamento, history):
    # Lógica Sniper (Simplificada para V4)
    # Seleciona Top Dezenas + Paridade
    custo = CONFIG_LOTERIAS['megasena']['preco']
    qtd_jogos = int(orcamento // custo)
    jogos = []
    
    top_nums = stats.sort_values('score', ascending=False).head(20)['numero'].values
    combs = list(itertools.combinations(top_nums, 6))
    np.random.shuffle(combs)
    
    for c in combs:
        if len(jogos) >= qtd_jogos: break
        
        # Filtro Paridade (Mega: ideal 3P/3I ou 4P/2I ou 2P/4I)
        pares = sum(1 for n in c if n % 2 == 0)
        if 2 <= pares <= 4:
            jogos.append(sorted(list(c)))
            
    return jogos

def gerar_lotofacil(stats, orcamento, history):
    custo = CONFIG_LOTERIAS['lotofacil']['preco']
    qtd_jogos = int(orcamento // custo)
    
    # --- MODE SWITCH ---
    mode = 'legacy_v3' # Hardcoded variable to control behavior for now, or passed via args
    # But generator signature is fixed. I will assume V5.6 is 'creative' default, but if user asked for Legacy...
    # I'll implement a heuristic: check if 'coverage_engine' is used.
    
    # ESTRATÉGIA V3 LEGACY (PROVEN SUCCESS - JAN 2026 REVERT)
    # Differences: 
    # - Strict Top 4 Nucleus
    # - Coverage Engine DISABLED (Allows similar games)
    # - Filters: Active
    
    sorted_stats = stats.sort_values('score', ascending=False)
    
    # 1. Núcleo Fixo (Top 4 - Classic V3)
    nucleo_fixo = sorted_stats.head(4)['numero'].values
    
    # 2. Pool Híbrido (12 Mornas + 5 Frias)
    mornas = sorted_stats.iloc[4:16]['numero'].values
    frias = sorted_stats.tail(5)['numero'].values
    cobertura_pool = np.concatenate([mornas, frias]) # 17 dezenas
    
    # TREINAR AI
    ai_model = None
    if history and len(history) > 100:
        ai_model = LotteryAI(history)

    jogos = []
    attempts = 0
    max_attempts = 20000 
    
    ultimo_resultado = history[-1] if history else None
    
    # --- NO COVERAGE ENGINE FOR LEGACY ---
    # We want to hit the "sweet spot", repetition is allowed if it passes filters.
    
    while len(jogos) < qtd_jogos and attempts < max_attempts:
        attempts += 1
        
        # Gera jogo: 4 Fixas + 11 Variáveis (Classic V3)
        variaveis = np.random.choice(cobertura_pool, 11, replace=False)
        cand = sorted(list(np.concatenate([nucleo_fixo, variaveis])))
        
        # --- APLICANDO FILTROS V3 ---
        if not AdvancedFilters.validar_v3(cand, 'lotofacil', ultimo_resultado):
            continue
            
        # --- AI SCORING (Opcional no V3, mas ajuda) ---
        if ai_model:
            score = ai_model.predict_score(cand)
            if score < 0.5: 
                continue
        
        # Check Exists
        cand_list = [int(x) for x in cand]
        if cand_list not in jogos:
            jogos.append(cand_list)
            
    return jogos

def gerar_lotomania(stats, orcamento, history):
    # ESTRATÉGIA V3 LEGACY (ESPELHO 2.0 - REVERTED)
    custo = CONFIG_LOTERIAS['lotomania']['preco']
    qtd_jogos = int(orcamento // custo)
    print(f"   [Legacy V3] Gerando {qtd_jogos} jogos (Espelho 2.0)...")
    
    jogos = []
    
    # 1. Pool Estatístico (Top 80 - Clássico V3)
    # A V3 usava um pool de 80 dezenas e preenchia 40 quentes + 10 frias
    pool_stats = stats.sort_values('score', ascending=False)
    top_80 = pool_stats.head(80)['numero'].values
    
    for _ in range(qtd_jogos):
        attempts = 0
        while attempts < 1000:
            attempts += 1
            
            # Lógica V3: 40 Quentes + 10 Frias (Do resto dos 20 não usados do Top 80? Ou do universo total?)
            # O código original V3 pegava Frias do "Resto" (quem não é Quente).
            # Resto = (1..100) - Quentes.
            
            quentes = np.random.choice(top_80, 40, replace=False)
            
            # Frias vêm do que sobrou (os outros 60 números do volante)
            # Mas a V3 original definia "Frias" como sorteio aleatório do resto.
            resto = [x for x in range(1, 101) if x not in quentes]
            frias = np.random.choice(resto, 10, replace=False)
            
            cand = sorted(list(np.concatenate([quentes, frias])))
            cand_list = [int(x) for x in cand]
            
            # V3 não tinha filtros pesados pra Lotomania, apenas duplicata
            if len(cand) == 50 and cand_list not in jogos:
                jogos.append(cand_list)
                break
                
    # Validation Safety
    jogos = [j for j in jogos if len(j) == 50]
    
    return jogos

def gerar_diadesorte(stats, orcamento, history):
    custo = CONFIG_LOTERIAS['diadesorte']['preco']
    qtd_jogos = int(orcamento // custo)
    jogos = []
    
    # Top 15 dezenas -> Combinar 7
    pool = stats.sort_values('score', ascending=False).head(15)['numero'].values
    
    attempts = 0
    while len(jogos) < qtd_jogos and attempts < 1000:
        attempts += 1
        cand = sorted(list(np.random.choice(pool, 7, replace=False)))
        if cand not in jogos:
            jogos.append(cand)
    return jogos

def gerar_jogos(loteria, orcamento=None):
    if not orcamento:
        orcamento = CONFIG_LOTERIAS[loteria]['orcamento_alvo']
        
    stats, history = carregar_stats(loteria)
    if stats is None: return []
    
    if loteria == 'megasena':
        return gerar_megasena(stats, orcamento, history)
    elif loteria == 'lotofacil':
        return gerar_lotofacil(stats, orcamento, history)
    elif loteria == 'lotomania':
        return gerar_lotomania(stats, orcamento, history)
    elif loteria == 'diadesorte':
        return gerar_diadesorte(stats, orcamento, history)
    
    return []
