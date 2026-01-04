
import pandas as pd
import numpy as np
import requests
import json
from collections import Counter

# Fonte JSON (mesma do anterior)
URL_FONTE = "https://raw.githubusercontent.com/guilhermeasn/loteria.json/master/data/megasena.json"

# Jogos do Combo (Extraídos da imagem)
JOGOS_COMBO = [
    [16, 18, 46, 47, 55, 56],
    [3, 9, 10, 15, 32, 44],
    [2, 3, 15, 16, 18, 54],
    [8, 21, 23, 50, 54, 58]
]

def baixar_historico():
    try:
        response = requests.get(URL_FONTE)
        response.raise_for_status()
        return response.json()
    except:
        return None

def processar_stats(data_json):
    concursos_validos = []
    if isinstance(data_json, dict):
        for _, dezenas in data_json.items():
            try:
                concursos_validos.append([int(d) for d in dezenas][:6])
            except: pass
            
    df = pd.DataFrame(concursos_validos)
    all_nums = df.values.flatten()
    freq = Counter(all_nums)
    
    # Calcular atraso
    ultimos = df.values.tolist()
    atrasos = {}
    for n in range(1, 61):
        for i, sorteio in enumerate(reversed(ultimos)):
            if n in sorteio:
                atrasos[n] = i
                break
        if n not in atrasos: atrasos[n] = len(df)
            
    return freq, atrasos

def avaliar_jogo(jogo, freq, atrasos):
    score_freq = sum([freq[n] for n in jogo])
    score_atraso = sum([atrasos[n] for n in jogo])
    
    # Médias para contexto
    media_freq = score_freq / 6
    media_atraso = score_atraso / 6
    
    return {
        "jogo": jogo,
        "score_total": score_freq + (score_atraso * 2), # Exemplo de métrica
        "media_freq": media_freq,
        "media_atraso": media_atraso,
        "analise": []
    }

def main():
    print("=== AVALIADOR DE COMBOS CAIXA ===")
    data = baixar_historico()
    if not data: return
    
    freq, atrasos = processar_stats(data)
    
    # Stats globais para base de comparação
    max_freq = max(freq.values())
    avg_freq = sum(freq.values()) / 60
    
    print(f"Média de Frequência Global: {avg_freq:.1f}")
    
    for i, jogo in enumerate(JOGOS_COMBO, 1):
        res = avaliar_jogo(jogo, freq, atrasos)
        print(f"\nJOGO {i}: {jogo}")
        print(f"-> Força Histórica (Freq Média): {res['media_freq']:.1f} (Ideal > {avg_freq:.1f})")
        print(f"-> índice de Atraso Médio: {res['media_atraso']:.1f}")
        
        # Ponto forte
        top_n = [n for n in jogo if freq[n] > avg_freq * 1.05]
        if top_n: print(f"-> Dezenas Fortes: {top_n}")
        
        # Veredito Simples
        if res['media_freq'] > avg_freq and res['media_atraso'] > 10:
            print("VEREDITO: ⭐ BOM (Equilibrado)")
        elif res['media_freq'] > avg_freq:
            print("VEREDITO: ✅ OK (Conservador)")
        elif res['media_atraso'] > 20:
             print("VEREDITO: ⚠️ ARRISCADO (Muitos Atrasados)")
        else:
            print("VEREDITO: ❌ FRACO (Estatisticamente abaixo da média)")

if __name__ == "__main__":
    main()
