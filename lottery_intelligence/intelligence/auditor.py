import requests
import hashlib
import json
import os
import re
from typing import List, Dict, Any, Optional
import urllib3

# Suppress SSL warnings for official Caixa API (often has cert issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LotteryAuditor:
    # List of API providers in order of preference
    PROVIDERS = [
        {
            "name": "GuidiDev",
            "url_template": "https://api.guidi.dev.br/loteria/{loteria}/{concurso}",
            "latest_url": "https://api.guidi.dev.br/loteria/{loteria}/ultimo",
            "parser": "parse_guidi"
        },
        {
            "name": "CaixaOfficial",
            "url_template": "https://servicebus2.caixa.gov.br/portaldeloterias/api/{loteria}/{concurso}",
            "latest_url": "https://servicebus2.caixa.gov.br/portaldeloterias/api/{loteria}",
            "parser": "parse_caixa"
        }
    ]

    PRIZE_TABLE = {
        'lotofacil': {11: 6.00, 12: 12.00, 13: 30.00, 14: 1500.00, 15: 2000000.00},
        'lotomania': {15: 12.00, 16: 52.00, 17: 300.00, 18: 2500.00, 19: 60000.00, 20: 5000000.00, 0: 200000.00},
        'megasena': {4: 1000.00, 5: 40000.00, 6: 15000000.00},
        'diadesorte': {4: 2.50, 5: 25.00, 6: 2000.00, 7: 1000000.00}
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_official_result(self, loteria: str, concurso: str = 'latest') -> Dict[str, Any]:
        """
        Fetches official result using multiple providers with fallback.
        """
        last_error = None
        for provider in self.PROVIDERS:
            try:
                # Prepare URL
                if concurso == 'latest':
                    url = provider['latest_url'].format(loteria=loteria)
                else:
                    url = provider['url_template'].format(loteria=loteria, concurso=concurso)

                print(f"[Auditor] Trying provider: {provider['name']} ({url})...")
                
                response = self.session.get(url, timeout=10, verify=False)
                response.raise_for_status()
                data = response.json()
                
                # Dynamic dispatch to parser
                parser_method = getattr(self, provider['parser'])
                return parser_method(data, loteria)

            except Exception as e:
                print(f"[Auditor] Provider {provider['name']} failed: {e}")
                last_error = e
                continue
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    def parse_guidi(self, data: Dict, loteria: str) -> Dict:
        """Parser for GuidiDev API"""
        lista = data.get('listaDezenas', [])
        if not lista: # Maybe 'dezenas'
            lista = data.get('dezenas', [])
            
        return {
            'loteria': loteria,
            'concurso': data.get('numero'),
            'data': data.get('dataApuracao'),
            'dezenas': [int(x) for x in lista],
            'acumulou': data.get('acumulado')
        }

    def parse_caixa(self, data: Dict, loteria: str) -> Dict:
        """Parser for Official Caixa API"""
        return {
            'loteria': loteria,
            'concurso': data.get('numero'),
            'data': data.get('dataApuracao'),
            'dezenas': [int(x) for x in data.get('listaDezenas', [])],
            'acumulou': data.get('acumulado')
        }

    def _calculate_profit(self, loteria: str, hits: int) -> float:
        table = self.PRIZE_TABLE.get(loteria, {})
        return table.get(hits, 0.0)

    def audit_file(self, filepath: str, concurso_input: str = None) -> str:
        """
        Audits a markdown file containing bets.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, 'r') as f:
            content = f.read()

        # Detect Lottery
        loteria = None
        if 'lotomania' in content.lower() or 'lotomania' in filepath.lower(): loteria = 'lotomania'
        elif 'lotofacil' in content.lower() or 'lotofacil' in filepath.lower(): loteria = 'lotofacil'
        elif 'megasena' in content.lower() or 'megasena' in filepath.lower(): loteria = 'megasena'
        
        if not loteria:
            # Default fallback if unknown, check content specific headers
            if '🟣' in content: loteria = 'lotofacil'
            elif '🟠' in content: loteria = 'lotomania'
            else: raise ValueError("Could not detect lottery type from file content.")

        # Fetch Result
        try:
            official_data = self.fetch_official_result(loteria, concurso_input or 'latest')
        except RuntimeError as e:
            return f"❌ AUDIT ERROR: {str(e)}"

        winning_numbers = set(official_data['dezenas'])
        concurso_real = official_data['concurso']
        
        # Parse numbers from MD
        # Supporting formats: '`01, 02...`' or '`[1, 2...]`'
        jogos = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '|' in line and '`' in line:
                try:
                    raw_nums = line.split('`')[1]
                    # Clean brackets if present
                    raw_nums = raw_nums.replace('[','').replace(']','')
                    # Split and int
                    nums = [int(x.strip()) for x in raw_nums.split(',') if x.strip()]
                    jogos.append((i, nums)) # Store index for reference if needed
                except:
                    continue
        
        if not jogos:
            return "❌ No valid games found to audit."

        # Generate Report
        report = f"# 🛡️ Audit Report V5.4\n"
        report += f"**File**: `{os.path.basename(filepath)}`\n"
        report += f"**Contest**: {concurso_real} ({official_data['data']})\n"
        report += f"**Winning Numbers**: `{sorted(list(winning_numbers))}`\n\n"
        report += "---\n\n"
        
        total_prize = 0.0
        header = "| Game | Hits | Matched | Status |\n| :--- | :--- | :--- | :--- |\n"
        rows = ""
        
        for idx, (line_idx, jogo) in enumerate(jogos):
            hits = set(jogo).intersection(winning_numbers)
            qtd = len(hits)
            prize = self._calculate_profit(loteria, qtd)
            
            # Mirror rule for Lotomania
            if loteria == 'lotomania' and qtd == 0:
                prize = self._calculate_profit(loteria, 0)

            total_prize += prize
            
            icon = "❌"
            if prize > 0: icon = f"💰 R$ {prize:.2f}"
            if loteria == 'lotomania' and qtd >= 14 and prize == 0: icon = "🔥 (Near Miss)"
            if loteria == 'lotofacil' and qtd >= 10 and prize == 0: icon = "🔥 (Near Miss)"

            rows += f"| {idx+1:02d} | **{qtd:02d}** | `{sorted(list(hits))}` | {icon} |\n"

        report += header + rows + "\n"
        report += "---\n"
        report += f"### 💰 Financial Summary\n"
        report += f"**Estimated Prize**: R$ {total_prize:.2f}\n"
        
        audit_hash = hashlib.sha256(report.encode('utf-8')).hexdigest()[:16]
        report += f"\n> **Integrity Hash**: `{audit_hash}`\n"
        
        return report
