# 🎱 Lottery Intelligence (Loto-AI)

Sistema de inteligência de dados para análise e geração de palpites otimizados para loterias da Caixa (Mega-Sena, Lotofácil, Lotomania e Dia de Sorte).

## 🚀 Funcionalidades

*   **ETL Automatizado**: Baixa e atualiza o histórico de sorteios diretamente do GitHub e armazena em SQLite (`loterias.db`).
*   **LotteryAI (Machine Learning)**: Um "cérebro" treinado com Random Forest que aprende o padrão dos sorteios reais e bloqueia palpites falsos/aleatórios.
*   **Matriz de Caos (V3.1)**: Geração de jogos usando a técnica de "Núcleo Fixo" (Top 5 estatístico) + "Injeção de Zebras" (Dezenas frias) para maximizar a diversidade.
*   **Firewall Estatístico**: Filtros rigorosos que eliminam jogos com Soma, Primos ou Fibonacci fora da curva normal.
*   **Gestão de Orçamento**: Otimiza os jogos para caber em um budget definido (padrão R$ 100).

## 🛠️ Instalação

1.  Clone o repositório:
    ```bash
    git clone https://github.com/nilsonpmjr/lottery-intelligence.git
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


## 🚀 Changelog (Versões)

### v3.1 (Current) - Chaos Matrix & ML
- **LotteryAI**: Machine Learning (RandomForest) treinado para detectar jogos "falsos".
- **Chaos Matrix**: Núcleo Fixo (5 dezenas) + Injeção de Zebras (Dezenas frias).
- **Firewall V3**: Filtros avançados de Soma, Primos e Fibonacci.

### v2.0 - Hot Streak
- Peso de Recência (Hot Streak).
- Filtro de Paridade (Equilíbrio Par/Ímpar).
- Suporte multi-loteria.

### v1.0 - Statistical Base
- Análise estatística pura (Frequência e Atraso).

## 📊 Estratégia "Sniper" (Economia)

Este projeto recomenda seguir um **Calendário de Apostas**:
*   Focar em sorteios com final **0 ou 5** (Prêmios maiores).
*   Evitar apostar em concursos "comuns" com prêmios baixos.
*   Priorizar Lotofácil e Dia de Sorte para retorno financeiro (cashback).

---
*Disclaimer: Loterias são jogos de azar. Este software utiliza matemática e estatística para otimizar escolhas, mas não garante premiação. Jogue com responsabilidade.*
