from lottery_intelligence.intelligence.auditor import LotteryAuditor
import os

artifact_path = "/home/nilsonpmjr/.gemini/antigravity/brain/63f35d50-99e2-4006-8990-db688c1457cf/apostas_realizadas_20_jan.md"
log_path = "audit_20_jan.log"

try:
    auditor = LotteryAuditor()
    print(">>> Iniciando Auditoria Jackpot Hunter (16/Jan)...")
    
    # The artifact contains multiple lotteries. 
    # The default audit_file might confuse them if they are in one file without splitting.
    # Current audit_file implementation picks the FIRST detected lottery or specific one.
    # cacador_jackpot_16_jan.md has Mega, Lotofacil, Lotomania.
    # I need to split them or update auditor to handle multi-lottery files.
    # For now, I will extract them manually in this script and audit individually.
    
    with open(artifact_path, 'r') as f:
        content = f.read()
        
    sections = {
        'megasena': [],
        'lotofacil': [],
        'lotomania': []
    }
    
    current_section = None
    lines = content.split('\n')
    for line in lines:
        if 'Mega Sena' in line: current_section = 'megasena'
        elif 'Lotofácil' in line: current_section = 'lotofacil'
        elif 'Lotomania' in line: current_section = 'lotomania'
        
        if current_section and '|' in line and '`' in line:
            sections[current_section].append(line)

    output = ""
    
    for loteria, lines in sections.items():
        if not lines: continue
        print(f"Auditing {loteria.upper()}...")
        
        # Create temp file for auditor
        temp_file = f"temp_{loteria}.md"
        with open(temp_file, 'w') as f:
            f.write(f"# Audit {loteria}\n")
            for line in lines:
                f.write(line + "\n")
        
        # Run Audit
        try:
            # determining contest might be tricky if "latest" isn't the right one.
            # 16/Jan was Friday.
            # Lotofacil: Friday draw.
            # Lotomania: Friday draw.
            # Mega Sena: Saturday (17/Jan)? Or was there a draw on 15/16? 
            # Usually Mega is Tue/Thu/Sat or Wed/Sat. 
            # I will try 'latest' and see the date, or check specific if needed.
            
            report = auditor.audit_file(temp_file, concurso_input='latest')
            output += f"\n=== {loteria.upper()} ===\n{report}\n"
            
        except Exception as e:
            output += f"\n=== {loteria.upper()} ===\n❌ Error: {e}\n"
            
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)

    print(output)
    
except Exception as e:
    print(f"❌ Fatal Error: {e}")
