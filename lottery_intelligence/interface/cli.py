
import argparse
import sys
import os
import datetime

# Adiciona o diretório pai ao path para importar pacotes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from lottery_intelligence.core.config import CONFIG_LOTERIAS
from lottery_intelligence.core.etl import setup_db, baixar_e_salvar, get_db
from lottery_intelligence.core.generators import gerar_jogos
from lottery_intelligence.narrative.interpretation import interpretar_resultados
from lottery_intelligence.core.coverage import CoverageEngine

def main():
    parser = argparse.ArgumentParser(description="Lottery Intelligence V6.0 CLI (Hybrid)")
    
    parser.add_argument('--loteria', type=str, default='lotofacil', 
                        choices=CONFIG_LOTERIAS.keys(),
                        help='Loteria alvo (default: lotofacil)')
                        
    parser.add_argument('--mode', type=str, default='strict', 
                        choices=['strict', 'creative', 'hybrid'],
                        help='Modo: strict, creative ou hybrid (V6)')
                        
    parser.add_argument('--budget', type=float, 
                        help='Orçamento personalizado (R$)')
                        
    parser.add_argument('--offline', action='store_true',
                        help='Não baixar dados (usar DB local)')

    parser.add_argument('--audit', type=str,
                        help='Arquivo para auditar (ignora geração)')
    parser.add_argument('--concurso', type=str, default='latest',
                        help='Número do concurso para auditoria (default: latest)')
    
    parser.add_argument('--skip-backtest', action='store_true',
                        help='Pular validação de backtest (modo híbrido)')
                        
    args = parser.parse_args()
    
    # 0. Audit Mode (V5.4)
    if args.audit:
        print(f"=== LOTTERY AUDITOR V5.4 ===")
        print(f"File: {args.audit}")
        from lottery_intelligence.intelligence.auditor import LotteryAuditor
        
        try:
            auditor = LotteryAuditor()
            report = auditor.audit_file(args.audit, args.concurso)
            print("\\n" + report)
            
            # Salvar log
            log_name = f"audit_{args.concurso}_{os.path.basename(args.audit).replace('.md', '')}.log"
            with open(log_name, "w") as f:
                f.write(report)
            print(f"\\n[Log] Salvo em: {log_name}")
            
        except Exception as e:
            print(f"❌ Erro na auditoria: {e}")
            sys.exit(1)
            
        return  # Exit after audit

    # V6.0 HYBRID MODE
    if args.mode == 'hybrid':
        print(f"=== LOTTERY INTELLIGENCE V6.0 [HYBRID] ===")
        
        if not args.offline:
            conn = setup_db()
            baixar_e_salvar(args.loteria, conn)
            conn.close()
        else:
            print("[OFFLINE] Usando base de dados local.")
        
        print(f"[{args.loteria.upper()}] Gerando portfólio híbrido...")
        
        from lottery_intelligence.core.hybrid import gerar_jogos_hybrid
        from lottery_intelligence.intelligence.backtest import run_backtest
        
        games_with_meta, stats_info = gerar_jogos_hybrid(args.loteria, args.budget or 30.0)
        
        # Extrair apenas os números para backtest
        games_only = [g['numbers'] for g in games_with_meta]
        
        # Backtest (se não pulado)
        backtest_results = None
        if not args.skip_backtest:
            print(f"   [Backtest] Validando contra TODO o histórico...")
            backtest_results = run_backtest(games_only, args.loteria, last_n=0)
        
        # Report híbrido
        print(f"\n# 🎱 Relatório Hybrid V6.0 - {args.loteria.upper()}")
        print(f"--------------------------------------------------")
        
        report = f"# 🎱 Relatório Hybrid V6.0\n"
        report += f"**Data**: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        report += f"**Loteria**: {args.loteria.upper()}\n"
        report += f"**Modo**: HYBRID (30% V3 Legacy / 70% V5 Calibrated)\n\n"
        
        report += f"## 📊 Composição do Portfólio\n"
        report += f"- **Total de Jogos**: {stats_info['total_games']}\n"
        report += f"- **V3 Legacy** (Safety): {stats_info['v3_count']} jogos\n"
        report += f"- **V5 Calibrated** (Hedge): {stats_info['v5_count']} jogos\n\n" 
        
        if backtest_results and 'error' not in backtest_results:
            hist_summary = f"- Backtest ({backtest_results['tested_draws']} Concursos): Média {backtest_results['global_avg']} pts | Max {backtest_results['global_max']} pts"
            print(hist_summary)
            report += f"## 🔬 Backtest ({backtest_results['tested_draws']} Concursos)\n"
            report += f"- **Média Global**: {backtest_results['global_avg']} pontos\n"
            report += f"- **Melhor Performance**: {backtest_results['global_max']} pontos\n\n"
        
        report += "## 📐 Jogos Gerados\n\n"
        report += "| # | Tag | Dezenas |\n"
        report += "| :--- | :--- | :--- |\n"
        
        print(f"\n{'#':<4} {'Tag':<6} {'Performance':<15} {'Dezenas'}")
        print("-" * 80)
        
        for idx, game_meta in enumerate(games_with_meta, 1):
            numbers = game_meta['numbers']
            tag = game_meta['tag']
            
            # Format numbers (wrapping if too long)
            nums_str = ""
            if len(numbers) > 20: # Likely Lotomania
                 # Split into chunks of 15 for readability
                 chunks = [numbers[i:i+15] for i in range(0, len(numbers), 15)]
                 formatted_chunks = []
                 for chunk in chunks:
                     formatted_chunks.append(', '.join([f"{n:02d}" for n in chunk]))
                 nums_str = '<br>'.join(formatted_chunks)
            else:
                 nums_str = ', '.join([f"{n:02d}" for n in numbers])
            
            # Adicionar backtest individual se disponível
            bt_info = ""
            bt_print = ""
            if backtest_results and 'per_game_stats' in backtest_results:
                game_bt = backtest_results['per_game_stats'][idx-1]
                bt_info = f" (BT: Avg {game_bt['avg_hits']})"
                bt_print = f"Avg {game_bt['avg_hits']}"
            
            report += f"| **{idx:02d}** {tag}{bt_info} | `{nums_str}` |\n"
            
            # Terminal Print (Clean)
            # Truncate numbers for terminal if too long (Lotomania)
            nums_term = ', '.join([f"{n:02d}" for n in numbers])
            if len(nums_term) > 60:
                nums_term = nums_term[:57] + "..."
            
            print(f"{idx:02d}   {tag:<6} {bt_print:<15} {nums_term}")
        
        report += "\n---\n"
        report += "*Legenda: [V3] = V3 Legacy (Sweet Spot), [V5] = V5 Calibrated (Coverage)*\n"
        
        # JS Script Generation
        report += "\n## 💻 Script JS para Aposta Rápida\n"
        report += "Copie e cole no console do navegador (F12) na página da Caixa:\n\n"
        report += "```javascript\n"
        
        # Prepare games array for JS
        js_games_str = "const JOGOS = [\n"
        for game_dict in games_with_meta:
             js_games_str += f"  {str(game_dict['numbers'])},\n"
        js_games_str = js_games_str.rstrip(",\n") + "\n];"
        
        report += js_games_str + "\n"
        report += "function x(i){let b=[...document.querySelectorAll('button')].find(e=>e.innerText.includes('Limpar'));if(b)b.click();JOGOS[i].forEach(n=>{let k=n.toString().padStart(2,'0');let el=document.getElementById(k)||document.getElementById('n'+k)||document.querySelector(`input[value='${k}']`);if(el)el.click()})}\n"
        report += 'console.log("🚀 V6 Hybrid Ready! Use x(0) para o primeiro jogo, x(1) para o segundo...");\n'
        report += "```\n"

        print("\\n" + report)
        
        with open(f"relatorio_v6_hybrid_{args.loteria}.md", "w") as f:
            f.write(report)
        print(f"\\n[Artifact] Relatório salvo em: relatorio_v6_hybrid_{args.loteria}.md")
        
        return

    # LEGACY MODES (V3/V5)
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
    report += f"\\n---\\n**Avg Coverage (Diversity)**: {avg_coverage:.2f} (Target: >3.0)\\n"
    
    # Output
    print("\\n" + report)
    
    # Salvar relatório
    with open(f"relatorio_v5_{args.loteria}.md", "w") as f:
        f.write(report)
    print(f"\\n[Artifact] Relatório salvo em: relatorio_v5_{args.loteria}.md")

if __name__ == "__main__":
    main()
