# 🎱 Lottery Intelligence (Loto-AI)

Sistema de inteligência de dados para análise e geração de palpites otimizados para loterias da Caixa (Mega-Sena, Lotofácil, Lotomania e Dia de Sorte).

## 🚀 Funcionalidades

*   **ETL Automatizado**: Baixa e atualiza o histórico de sorteios diretamente do GitHub (fonte open-data).
*   **Análise Estatística**: Calcula frequência global, atraso (delay) e tendência recente (Hot Streak).
*   **Algoritmos de Geração**:
    *   **Mega-Sena**: Sniper (Foco em dezenas quentes com equilíbrio de paridade).
    *   **Lotofácil**: Ciclos + Tendência Recente.
    *   **Lotomania**: Espelho Otimizado (Cerca 20 ou 0 acertos).
    *   **Dia de Sorte**: Fechamento Matemático (12 dezenas em 14 jogos).
*   **Gestão de Orçamento**: Otimiza os jogos para caber em um budget definido (padrão R$ 100).

## 🛠️ Instalação

1.  Clone o repositório:
    ```bash
    git clone https://github.com/SEU_USUARIO/lottery-intelligence.git
    cd lottery-intelligence
    ```

2.  Crie um ambiente virtual (recomendado):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

## 🎮 Como Usar

Para gerar o relatório completo com todos os palpites:

```bash
python3 multi_lottery_analytics.py
```

O script irá:
1.  Baixar os dados mais recentes.
2.  Processar as estatísticas (v2.0 com paridade e hot streak).
3.  Gerar o arquivo `relatorio_multiloteria.md` com os jogos prontos para copiar.

## 📊 Estratégia "Sniper" (Economia)

Este projeto recomenda seguir um **Calendário de Apostas**:
*   Focar em sorteios com final **0 ou 5** (Prêmios maiores).
*   Evitar apostar em concursos "comuns" com prêmios baixos.
*   Priorizar Lotofácil e Dia de Sorte para retorno financeiro (cashback).

---
*Disclaimer: Loterias são jogos de azar. Este software utiliza matemática e estatística para otimizar escolhas, mas não garante premiação. Jogue com responsabilidade.*
