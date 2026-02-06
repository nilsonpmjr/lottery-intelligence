#!/bin/bash

# Lottery Intelligence - Initialization Script
# V5.3

echo "🦁 Lottery Intelligence Setup (Loto-AI)"
echo "======================================="

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

echo "✅ Python 3 detected."

# 2. Check/Create Venv
VENV_NAME="venv"
if [ -d "$VENV_NAME" ]; then
    echo "ℹ️  Virtual environment '$VENV_NAME' already exists."
else
    echo "🔨 Creating virtual environment..."
    python3 -m venv $VENV_NAME
fi

# 3. Activate and Install
echo "📦 Installing dependencies from requirements.txt..."
source $VENV_NAME/bin/activate

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1

# Install deps
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ Dependencies installed successfully."
    else
        echo "❌ Failed to install dependencies."
        exit 1
    fi
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# 4. Setup Database (Optional init)
# echo "🗄️ Initializing local database..."
# python3 lottery_intelligence/core/etl.py --init-only

echo "======================================="
echo "🚀 Setup Complete!"
echo "To activate manually: source $VENV_NAME/bin/activate"
echo "To run CLI: python3 lottery_intelligence/interface/cli.py --help"
