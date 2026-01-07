
import secrets
import collections
import time
from typing import List, Tuple

# Configurações da Mega da Virada
NUMER0S_TOTAIS = 60
DEZENAS_POR_JOGO = 6
TOTAL_SIMULACOES = 1_000_000

def gerar_jogo_aleatorio() -> List[int]:
    """Gera um jogo aleatório simples usando secrets (CSPRNG)."""
    jogo = set()
    while len(jogo) < DEZENAS_POR_JOGO:
        # secrets.randbelow(60) retorna 0-59, então somamos 1
        jogo.add(secrets.randbelow(NUMER0S_TOTAIS) + 1)
    return sorted(list(jogo))

def simular_sorteios(n_simulacoes: int) -> collections.Counter:
    """
    Simula n sorteios e contabiliza a frequência de cada dezena.
    Retorna um Counter com as frequências.
    """
    frequencia = collections.Counter()
    print(f"Iniciando simulação de {n_simulacoes} sorteios...")
    start_time = time.time()
    
    for i in range(n_simulacoes):
        jogo = gerar_jogo_aleatorio()
        frequencia.update(jogo)
        
        if (i + 1) % (n_simulacoes // 10) == 0:
            print(f"Progresso: {(i + 1) / n_simulacoes * 100:.0f}%")
            
    end_time = time.time()
    duration = end_time - start_time
    print(f"Simulação concluída em {duration:.2f} segundos.")
    return frequencia

def selecionar_melhores_dezenas(frequencia: collections.Counter, qtd: int) -> List[int]:
    """Retorna as 'qtd' dezenas mais frequentes."""
    return sorted([num for num, _ in frequencia.most_common(qtd)])

def analisar_paridade(jogo: List[int]) -> Tuple[int, int]:
    """Retorna (pares, impares)."""
    pares = sum(1 for n in jogo if n % 2 == 0)
    impares = len(jogo) - pares
    return pares, impares

def main():
    print("="*50)
    print(f"SIMULADOR MEGA DA VIRADA 2025 (R$ 1 BILHÃO)")
    print("="*50)
    print(f"Gerador: Python secrets (Criptograficamente Seguro)")
    print(f"Simulações: {TOTAL_SIMULACOES}")
    print("-" * 50)
    
    # 1. Executar Simulação
    freq = simular_sorteios(TOTAL_SIMULACOES)
    
    # 2. Analisar Resultados
    print("\n--- ANÁLISE E PALPITES ---")
    
    # Palpite 1: As 6 mais quentes (Estatística Pura)
    palpite_quente = selecionar_melhores_dezenas(freq, 6)
    pares, impares = analisar_paridade(palpite_quente)
    print(f"\n[PALPITE ESTATÍSTICO] (Baseado em frequência):")
    print(f"Dezenas: {palpite_quente}")
    print(f"Paridade: {pares} Pares / {impares} Ímpares")
    
    # Palpite 2: Jogo Equilibrado (Estratégia)
    # Pega top 10 e busca um jogo com paridade 3/3 ou 4/2
    top_20 = selecionar_melhores_dezenas(freq, 20)
    palpite_equilibrado = []
    
    # Tenta montar um jogo equilibrado 3 pares / 3 ímpares das top 20
    pares_disp = [n for n in top_20 if n % 2 == 0]
    impares_disp = [n for n in top_20 if n % 2 != 0]
    
    if len(pares_disp) >= 3 and len(impares_disp) >= 3:
        palpite_equilibrado = sorted(pares_disp[:3] + impares_disp[:3])
    else:
        palpite_equilibrado = top_20[:6] # Fallback
        
    print(f"\n[PALPITE EQUILIBRADO] (Top frequentes + Paridade 3/3):")
    print(f"Dezenas: {palpite_equilibrado}")
    
    # Palpite 3: Bolão (Mais dezenas)
    palpite_bolao = selecionar_melhores_dezenas(freq, 10) # 10 Dezenas
    print(f"\n[SUGESTÃO P/ BOLÃO] (10 Dezenas mais frequentes):")
    print(f"Dezenas: {palpite_bolao}")
    
    print("\n" + "="*50)
    print("Boa sorte! Lembre-se: Loteria é jogo de azar.")
    print("="*50)

if __name__ == "__main__":
    main()
