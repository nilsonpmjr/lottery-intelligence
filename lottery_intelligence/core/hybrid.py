"""
Gerador Híbrido V6.0 (30% V3 Legacy / 70% V5 Calibrated)
Anti-Vibe Implementation - SPEC Driven
"""

import itertools
import numpy as np
from typing import List, Dict, Tuple
from ..core.config import CONFIG_LOTERIAS
from ..core.etl import get_db
from ..core.generators import gerar_jogos, carregar_stats
from ..core.filters import AdvancedFilters
from ..intelligence.brain import LotteryAI
from ..core.coverage import CoverageEngine

def gerar_v3_legacy_batch(loteria: str, qtd_jogos: int, stats, history) -> List[List[int]]:
    """
    Gera jogos usando lógica V3 Legacy (Sweet Spot).
    Núcleo Fixo + Pool Híbrido + Sem Coverage Engine.
    """
    custo = CONFIG_LOTERIAS[loteria]['preco']
    sorted_stats = stats.sort_values('score', ascending=False)
    
    if loteria == 'lotofacil':
        nucleo_fixo = sorted_stats.head(4)['numero'].values
        mornas = sorted_stats.iloc[4:16]['numero'].values
        frias = sorted_stats.tail(5)['numero'].values
        cobertura_pool = np.concatenate([mornas, frias])
        
        # Treinar AI
        ai_model = None
        if history and len(history) > 100:
            ai_model = LotteryAI(history)
        
        ultimo_resultado = history[-1] if history else None
        jogos = []
        attempts = 0
        max_attempts = 20000
        
        while len(jogos) < qtd_jogos and attempts < max_attempts:
            attempts += 1
            variaveis = np.random.choice(cobertura_pool, 11, replace=False)
            cand = sorted(list(np.concatenate([nucleo_fixo, variaveis])))
            
            if not AdvancedFilters.validar_v3(cand, 'lotofacil', ultimo_resultado):
                continue
            
            if ai_model:
                score = ai_model.predict_score(cand)
                if score < 0.5:
                    continue
            
            cand_list = [int(x) for x in cand]
            if cand_list not in jogos:
                jogos.append(cand_list)
        
        return jogos
    
    elif loteria == 'lotomania':
        pool_stats = sorted_stats.head(80)['numero'].values
        jogos = []

        for _ in range(qtd_jogos):
            attempts = 0
            while attempts < 1000:
                attempts += 1
                quentes = np.random.choice(pool_stats, 40, replace=False)
                resto = [x for x in range(1, 101) if x not in quentes]
                frias = np.random.choice(resto, 10, replace=False)
                cand = sorted(list(np.concatenate([quentes, frias])))
                cand_list = [int(x) for x in cand]

                if cand_list not in jogos:
                    jogos.append(cand_list)
                    break

        return jogos

    elif loteria == 'megasena':
        top_nums = sorted_stats.head(20)['numero'].values
        combs = list(itertools.combinations(top_nums, 6))
        np.random.shuffle(combs)
        jogos = []
        for c in combs:
            if len(jogos) >= qtd_jogos:
                break
            pares = sum(1 for n in c if n % 2 == 0)
            if 2 <= pares <= 4:
                jogos.append(sorted([int(x) for x in c]))
        return jogos

    elif loteria == 'diadesorte':
        pool = sorted_stats.head(15)['numero'].values
        jogos = []
        attempts = 0
        while len(jogos) < qtd_jogos and attempts < 1000:
            attempts += 1
            cand = sorted([int(x) for x in np.random.choice(pool, 7, replace=False)])
            if cand not in jogos:
                jogos.append(cand)
        return jogos

    return []

def gerar_v5_calibrated_batch(loteria: str, qtd_jogos: int, stats, history) -> List[List[int]]:
    """
    Gera jogos usando lógica V5.5 Calibrated (Coverage Engine + AI).
    """
    custo = CONFIG_LOTERIAS[loteria]['preco']
    sorted_stats = stats.sort_values('score', ascending=False)
    
    if loteria == 'lotofacil':
        # Núcleo A / B alternado
        nucleo_a = sorted_stats.head(4)['numero'].values
        nucleo_b = sorted_stats.iloc[2:6]['numero'].values
        
        mornas = sorted_stats.iloc[4:16]['numero'].values
        frias = sorted_stats.tail(5)['numero'].values
        cobertura_pool = np.concatenate([mornas, frias])
        
        ai_model = None
        if history and len(history) > 100:
            ai_model = LotteryAI(history)
        
        ultimo_resultado = history[-1] if history else None
        jogos = []
        attempts = 0
        max_attempts = 10000
        
        coverage_engine = CoverageEngine(min_distance=4, game_type='lotofacil')
        
        while len(jogos) < qtd_jogos and attempts < max_attempts:
            attempts += 1
            
            if attempts == 5000:
                coverage_engine.min_distance = 3
            
            current_nucleo = nucleo_a if len(jogos) % 2 == 0 else nucleo_b
            pool_filtrado = [x for x in cobertura_pool if x not in current_nucleo]
            variaveis = np.random.choice(pool_filtrado, 11, replace=False)
            cand = sorted(list(np.concatenate([current_nucleo, variaveis])))
            
            if not AdvancedFilters.validar_v3(cand, 'lotofacil', ultimo_resultado):
                continue
            
            if ai_model:
                score = ai_model.predict_score(cand)
                if score < 0.5:
                    continue
            
            cand_list = [int(x) for x in cand]
            
            if not coverage_engine.is_diverse(cand_list, jogos):
                continue
            
            if cand_list not in jogos:
                jogos.append(cand_list)
        
        return jogos
    
    elif loteria == 'lotomania':
        pool = sorted_stats.head(80)['numero'].values
        jogos = []
        attempts = 0
        max_attempts = 5000

        coverage_engine = CoverageEngine(min_distance=10, game_type='lotomania')

        while len(jogos) < qtd_jogos and attempts < max_attempts:
            attempts += 1
            cand = sorted(list(np.random.choice(pool, 50, replace=False)))
            cand_list = [int(x) for x in cand]

            if not coverage_engine.is_diverse(cand_list, jogos):
                continue

            if cand not in jogos:
                jogos.append(cand_list)

        return jogos

    elif loteria == 'megasena':
        top_nums = sorted_stats.head(20)['numero'].values
        combs = list(itertools.combinations(top_nums, 6))
        np.random.shuffle(combs)
        jogos = []
        coverage_engine = CoverageEngine(min_distance=2, game_type='megasena')
        for c in combs:
            if len(jogos) >= qtd_jogos:
                break
            pares = sum(1 for n in c if n % 2 == 0)
            if 2 <= pares <= 4:
                cand = sorted([int(x) for x in c])
                if coverage_engine.is_diverse(cand, jogos):
                    jogos.append(cand)
        return jogos

    elif loteria == 'diadesorte':
        pool = sorted_stats.head(15)['numero'].values
        jogos = []
        attempts = 0
        coverage_engine = CoverageEngine(min_distance=2, game_type='diadesorte')
        while len(jogos) < qtd_jogos and attempts < 5000:
            attempts += 1
            cand = sorted([int(x) for x in np.random.choice(pool, 7, replace=False)])
            if coverage_engine.is_diverse(cand, jogos) and cand not in jogos:
                jogos.append(cand)
        return jogos

    return []

def gerar_jogos_hybrid(loteria: str, orcamento: float) -> Tuple[List[Dict], Dict]:
    """
    Orquestrador Híbrido V6.0.
    
    Returns:
        Tuple[games_with_metadata, stats_info]
    """
    custo = CONFIG_LOTERIAS[loteria]['preco']
    total_jogos = int(orcamento // custo)
    
    # SPEC: 30% V3, 70% V5
    slots_v3 = int(total_jogos * 0.30)
    slots_v5 = total_jogos - slots_v3
    
    print(f"   [Hybrid V6] Split: {slots_v3} V3 Legacy + {slots_v5} V5 Calibrated")
    
    # Carregar estatísticas
    stats, history = carregar_stats(loteria)
    if stats is None:
        return [], {}
    
    # Gerar batches
    v3_games = gerar_v3_legacy_batch(loteria, slots_v3, stats, history)
    v5_games = gerar_v5_calibrated_batch(loteria, slots_v5, stats, history)
    
    # Merge com metadados
    games_with_meta = []
    for game in v3_games:
        games_with_meta.append({
            'numbers': game,
            'source': 'v3_legacy',
            'tag': '[V3]'
        })
    
    for game in v5_games:
        games_with_meta.append({
            'numbers': game,
            'source': 'v5_calibrated',
            'tag': '[V5]'
        })
    
    stats_info = {
        'total_games': len(games_with_meta),
        'v3_count': len(v3_games),
        'v5_count': len(v5_games)
    }
    
    return games_with_meta, stats_info
