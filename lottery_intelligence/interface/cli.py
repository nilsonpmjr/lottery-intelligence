
import argparse
import sys
import os

# Adiciona o diretório pai ao path para importar pacotes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from lottery_intelligence.core.config import CONFIG_LOTERIAS
from lottery_intelligence.core.etl import setup_db, baixar_e_salvar, get_db
from lottery_intelligence.core.generators import gerar_jogos
from lottery_intelligence.narrative.interpretation import interpretar_resultados
from lottery_intelligence.core.coverage import CoverageEngine

def main():
    parser = argparse.ArgumentParser(description="Lottery Intelligence V4.0 CLI")
    
    parser.add_argument('--loteria', type=str, default='lotofacil', 
                        choices=CONFIG_LOTERIAS.keys(),
                        help='Loteria alvo (default: lotofacil)')
                        
    parser.add_argument('--mode', type=str, default='strict', 
                        choices=['strict', 'creative'],
                        help='Modo de operação: strict (dados) ou creative (narrativa)')
                        
    parser.add_argument('--budget', type=float, 
                        help='Orçamento personalizado (R$)')
                        
    parser.add_argument('--offline', action='store_true',
                        help='Não baixar dados (usar DB local)')
                        
    args = parser.parse_args()
    
    print(f"=== LOTTERY INTELLIGENCE V4.0 [{args.mode.upper()}] ===")
    
    # 1. Setup & ETL
    if not args.offline:
        conn = setup_db()
        baixar_e_salvar(args.loteria, conn)
        conn.close()
    else:
        print("[OFFLINE] Usando base de dados local.")
        
    # 2. Geração (Core)
    print(f"[{args.loteria.upper()}] Gerando matrizes...")
    jogos = gerar_jogos(args.loteria, args.budget)
    
    # 3. Métricas de Cobertura (V5.0)
    # 3. Métricas de Cobertura (V5.1 - Manual Calculation)
    metric_engine = CoverageEngine()
    total_dist = 0
    pair_count = 0
    
    if len(jogos) > 1:
        for i in range(len(jogos)):
            for j in range(i + 1, len(jogos)):
                d = metric_engine.calculate_distance(jogos[i], jogos[j])
                total_dist += d
                pair_count += 1
                
    avg_coverage = total_dist / pair_count if pair_count > 0 else 0.0
    print(f"   [METRICS] Cobertura Média (Hamming): {avg_coverage:.2f}")

    # 4. Narrativa (UX)
    report = interpretar_resultados(jogos, args.loteria, args.mode)
    
    # Adicionar métricas ao relatório
    report += f"\n---\n**Avg Coverage (Diversity)**: {avg_coverage:.2f} (Target: >3.0)\n"
    
    # Output
    print("\n" + report)
    
    # Salvar relatório
    with open(f"relatorio_v5_{args.loteria}.md", "w") as f:
        f.write(report)
    print(f"\n[Artifact] Relatório salvo em: relatorio_v5_{args.loteria}.md")

if __name__ == "__main__":
    main()
