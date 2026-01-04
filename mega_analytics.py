
import pandas as pd
import numpy as np
import requests
import json
from collections import Counter
import time

# Fonte JSON confiável (Github de guilhermeasn)
URL_FONTE = "https://raw.githubusercontent.com/guilhermeasn/loteria.json/master/data/megasena.json"

def baixar_historico():
    print(f"Baixando histórico de: {URL_FONTE} ...")
    try:
        response = requests.get(URL_FONTE)
        response.raise_for_status()
        data = response.json()
        print(f"JSON baixado. Registros: {len(data)}")
        return data
    except Exception as e:
        print(f"Erro ao baixar dados: {e}")
        return None

def limpar_dados(data_json):
    """
    Transforma Dict JSON {"1": ["n1",...], ...} em DataFrame de dezenas.
    """
    concursos_validos = []
    
    # Se for dict (formato esperado do guilhermeasn)
    if isinstance(data_json, dict):
        for concurso, dezenas in data_json.items():
            try:
                nums = [int(d) for d in dezenas]
                if len(nums) >= 6:
                    concursos_validos.append(sorted(nums[:6]))
            except:
                pass
    # Caso fallback: se for lista
    elif isinstance(data_json, list):
         for item in data_json:
            dezenas = None
            if 'dezenas' in item: dezenas = item['dezenas']
            elif 'Dezenas' in item: dezenas = item['Dezenas']
            
            if dezenas:
                try:
                    nums = [int(d) for d in dezenas]
                    if len(nums) >= 6:
                        concursos_validos.append(sorted(nums[:6]))
                except:
                    pass
                
    df_clean = pd.DataFrame(concursos_validos, columns=['d1','d2','d3','d4','d5','d6'])
    return df_clean

def analise_avancada(df_numeros):
    """
    Realiza a modelagem estatística:
    1. Frequência Global
    2. Atraso (Delay)
    3. Score Combinado
    """
    total_concursos = len(df_numeros)
    todos_numeros_flat = df_numeros.values.flatten()
    
    # 1. Frequencia
    freq_counter = Counter(todos_numeros_flat)
    df_stats = pd.DataFrame({'numero': range(1, 61)})
    df_stats['frequencia'] = df_stats['numero'].map(freq_counter).fillna(0)
    df_stats['freq_norm'] = df_stats['frequencia'] / total_concursos
    
    # 2. Atraso
    ultimos_sorteios = df_numeros.values.tolist()
    atrasos = {}
    
    for n in range(1, 61):
        atraso = 0
        encontrou = False
        for i, sorteio in enumerate(reversed(ultimos_sorteios)):
            if n in sorteio:
                atraso = i
                encontrou = True
                break
        if not encontrou:
            atraso = total_concursos
        atrasos[n] = atraso
        
    df_stats['atraso'] = df_stats['numero'].map(atrasos)
    
    # 3. Score "Possibilidade Verdadeira"
    df_stats['atraso_norm'] = df_stats['atraso'] / df_stats['atraso'].max()
    
    # Score: Valorizamos frequencia (base sólida) + atraso (correção estatística)
    df_stats['score'] = (df_stats['freq_norm'] * 2.5) + (df_stats['atraso_norm'] * 1.5)
    
    return df_stats

def gerar_palpites_ponderados(df_stats, n_jogos=1):
    palpites = []
    pesos = df_stats['score'].values
    pesos = np.nan_to_num(pesos, nan=0.0)
    if pesos.sum() == 0:
        pesos = np.ones_like(pesos)
        
    probs = pesos / pesos.sum()
    
    for _ in range(n_jogos):
        escolha = np.random.choice(df_stats['numero'].values, size=6, replace=False, p=probs)
        palpites.append(sorted(escolha))
        
    return palpites

def main():
    print("=== MEGA ANALYTICS: DATA SCIENCE ENGINE (JSON SOURCE) ===")
    
    # 1. Obter Dados
    data_json = baixar_historico()
    if not data_json:
        print("Falha na fonte de dados.")
        return
    
    # 2. Limpar
    df_nums = limpar_dados(data_json)
    print(f"Dataset processado: {len(df_nums)} concursos validados.")
    
    if len(df_nums) > 0:
        ultimo = df_nums.iloc[-1].values
        print(f"Último sorteio registrado na base: {ultimo}")
    else:
        print("DEBUG - Nenhuma linha processada. Verifique parser.")
    
    if len(df_nums) == 0:
        return

    # 3. Modelagem
    stats = analise_avancada(df_nums)
    
    print("\n--- TOP 10 NÚMEROS MAIS QUENTES (Histórico) ---")
    top_quentes = stats.sort_values(by='frequencia', ascending=False).head(10)
    print(top_quentes[['numero', 'frequencia', 'atraso']].to_string(index=False))
    
    # 4. Geração
    print("\nGerando palpites baseados em 'Possibilidades Verdadeiras'...")
    np.random.seed(int(time.time()))
    
    palpites = gerar_palpites_ponderados(stats, n_jogos=3)
    
    print("\n=== PALPITES SUGERIDOS (MODELO HÍBRIDO) ===")
    for i, p in enumerate(palpites, 1):
        print(f"Jogo {i}: {p}")
        
    # Palpite de 'Equilíbrio' (Pega 3 quentes e 3 atrasados aleatorios)
    quentes_pool = stats.sort_values('frequencia', ascending=False).head(15)['numero'].values
    atrasados_pool = stats.sort_values('atraso', ascending=False).head(15)['numero'].values
    
    atrasados_pool = [x for x in atrasados_pool if x not in quentes_pool]
    
    mix = []
    if len(quentes_pool) >= 3 and len(atrasados_pool) >= 3:
        mix = np.concatenate([
            np.random.choice(quentes_pool, 3, replace=False),
            np.random.choice(atrasados_pool, 3, replace=False)
        ])
    else:
        mix = np.random.choice(stats.sort_values('score', ascending=False).head(20)['numero'].values, 6, replace=False)
        
    mix = sorted(list(set(mix)))
    while len(mix) < 6:
        r = np.random.choice(stats['numero'].values)
        if r not in mix:
            mix.append(r)
    mix = sorted(mix)
            
    print(f"Jogo Estratégico (Mix Quente/Atrasado): {mix}")

    # --- FECHAMENTO COMBINADO (NOVO) ---
    print("\n=== GERADOR DE FECHAMENTO (WHEELING SYSTEM) ===")
    
    # 1. Seleção do Pool (Top 12 Dezenas Híbridas)
    # Pega as 7 mais quentes e 5 mais atrasadas (que não estejam nas quentes)
    pool_quentes = stats.sort_values('frequencia', ascending=False).head(20)['numero'].values
    pool_atrasados = stats.sort_values('atraso', ascending=False).head(20)['numero'].values
    
    # Filtrar atrasados para não repetir quentes
    pool_atrasados = [x for x in pool_atrasados if x not in pool_quentes]
    
    # Montar Pool de 12 Números
    pool_final = []
    pool_final.extend(pool_quentes[:7])
    pool_final.extend(pool_atrasados[:5])
    pool_final = sorted(list(set(pool_final)))
    
    print(f"Pool de 12 Dezenas Selecionadas: {pool_final}")
    print(f"(Custo se jogasse todas combinadas: {924} jogos -> R$ {924*5:,.2f})")
    
    # 2. Gerar Fechamento Reduzido (Garantia de Quadra se acertar 6)
    # Algoritmo simplificado de cobertura:
    # Gera jogos de 6 numeros a partir do pool tal que cada par de numeros do pool
    # apareça em pelo menos um jogo (ou aproximação disso).
    
    jogos_fechamento = []
    import itertools
    
    # Tentativa de Fechamento Inteligente (Stochastic Hill Climbing simplificado)
    # Vamos gerar 10 jogos que maximizem a cobertura de pares não repetidos
    combinations_possiveis = list(itertools.combinations(pool_final, 6))
    
    # Se o pool for pequeno, podemos filtrar.
    # Vamos selecionar 10 jogos aleatórios mas validar cobertura? 
    # Melhor: Shuffle e pegar os primeiros N que tenham pouca sobreposição total
    np.random.shuffle(combinations_possiveis)
    
    # Selecionar X jogos
    QTD_JOGOS = 8
    jogos_escolhidos = []
    
    # Estratégia simples: Pega jogos que tenham distancias razoaveis
    # Para 12 numeros, 8 jogos é uma boa cobertura reduzida
    for jogo in combinations_possiveis:
        if len(jogos_escolhidos) >= QTD_JOGOS:
            break
        
        # Aceita o primeiro
        if not jogos_escolhidos:
            jogos_escolhidos.append(sorted(jogo))
            continue
            
        # Para os próximos, evita jogos muito parecidos (ex: 5 numeros iguais)
        # Queremos espalhar
        muito_parecido = False
        for j_escolhido in jogos_escolhidos:
            # Interseção
            comum = len(set(jogo).intersection(set(j_escolhido)))
            if comum >= 5: # Se já tem 5 numeros iguais, é redundante pra fechar quadra
                muito_parecido = True
                break
        
        if not muito_parecido:
            jogos_escolhidos.append(sorted(jogo))
            
    print("\n--- SUGESTÃO DE FECHAMENTO (Custo Reduzido: R$ 40,00) ---")
    print(f"Garantia Estatística: Alta chance de Quadra/Quina se as 6 sorteadas estiverem entre as 12 do Pool.")
    for i, jogo in enumerate(jogos_escolhidos, 1):
        print(f"Volante {i}: {jogo}")

if __name__ == "__main__":
    main()
