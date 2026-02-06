#!/bin/bash

# Configuration (Defaults)
BUDGET_LOTOFACIL=30.00
BUDGET_LOTOMANIA=30.00

echo "🦁 LOTTERY INTELLIGENCE V6 AUTOMATION 🦁"
echo "=========================================="

# 1. Lotofacil
echo "Running Lotofacil Generation..."
./mega_venv/bin/python3 lottery_intelligence/interface/cli.py --loteria lotofacil --mode hybrid --budget $BUDGET_LOTOFACIL --offline

# 2. Lotomania
echo -e "\nRunning Lotomania Generation..."
./mega_venv/bin/python3 lottery_intelligence/interface/cli.py --loteria lotomania --mode hybrid --budget $BUDGET_LOTOMANIA --offline

echo "=========================================="
echo "✅ PROCESS COMPLETE"
echo "Reports generated:"
ls -lh relatorio_v6_hybrid_*.md
