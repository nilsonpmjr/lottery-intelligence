
import datetime

def interpretar_resultados(jogos, loteria, modo='strict'):
    """
    Recebe os jogos gerados e retorna uma string formatada (Markdown).
    Modo 'creative' adiciona flavor text.
    """
    if not jogos:
        return "Nenhum jogo gerado. Verifique os filtros ou base de dados."
    
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    report = f"# 🎱 Relatório Loto-Intelligence V4.0\n"
    report += f"**Data**: {timestamp}\n"
    report += f"**Loteria**: {loteria.upper()}\n"
    report += f"**Modo**: {modo.upper()}\n\n"
    
    if modo == 'creative':
        report += "## 🔮 Análise de Ressonância (Creative Mode)\n"
        report += "*Os vetores de probabilidade alinharam-se com a matriz de caos.*\n"
        report += "*Anomalias estatísticas detectadas e neutralizadas.*\n\n"
    
    report += "## 📐 Jogos Gerados (Immutable Core Output)\n\n"
    
    for i, jogo in enumerate(jogos):
        jogo_str = ", ".join([f"{n:02d}" for n in sorted(jogo)])
        report += f"| **{i+1:02d}** | `{jogo_str}` |\n"
        
    return report
