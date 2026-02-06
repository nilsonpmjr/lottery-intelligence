"""
Módulo de Backtest para validação pré-aposta (V6 Hybrid)
Testa jogos gerados contra os últimos N sorteios históricos.
"""

import pandas as pd
import json
from typing import List, Dict
from ..core.etl import get_db

def run_backtest(games: List[List[int]], loteria: str, last_n: int = 50) -> Dict:
    """
    Executa backtest dos jogos contra os últimos N concursos.
    Se last_n=0, carrega TODO o histórico (pode ser lento).
    
    Args:
        games: Lista de jogos gerados
        loteria: Nome da loteria
        last_n: Concursos a verificar (0 = Todos)
        
    Returns:
        Dict com estatísticas: {
            'avg_hits': média de acertos,
            'max_hits': melhor resultado,
            'min_hits': pior resultado,
            'per_game_stats': lista de dict por jogo
        }
    """
    conn = get_db()
    query = f"SELECT dezenas FROM {loteria} ORDER BY concurso DESC"
    if last_n > 0:
        query += f" LIMIT {last_n}"
        
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        return {'error': 'No historical data'}
    
    # Extrair resultados históricos
    historical_results = []
    for _, row in df.iterrows():
        try:
            result = json.loads(row['dezenas'])
            historical_results.append(set(result))
        except:
            continue
    
    if not historical_results:
        return {'error': 'Failed to parse historical data'}
    
    # Testar cada jogo
    per_game_stats = []
    for idx, game in enumerate(games):
        game_set = set(game)
        hits_list = []
        
        for hist_result in historical_results:
            hits = len(game_set.intersection(hist_result))
            hits_list.append(hits)
        
        avg = sum(hits_list) / len(hits_list) if hits_list else 0
        per_game_stats.append({
            'game_index': idx,
            'avg_hits': round(avg, 1),
            'max_hits': max(hits_list) if hits_list else 0,
            'min_hits': min(hits_list) if hits_list else 0
        })
    
    # Estatísticas globais
    all_avgs = [s['avg_hits'] for s in per_game_stats]
    all_maxs = [s['max_hits'] for s in per_game_stats]
    
    return {
        'global_avg': round(sum(all_avgs) / len(all_avgs), 1) if all_avgs else 0,
        'global_max': max(all_maxs) if all_maxs else 0,
        'per_game_stats': per_game_stats,
        'tested_draws': len(historical_results)
    }
