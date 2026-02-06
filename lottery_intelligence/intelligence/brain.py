
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

class LotteryAI:
    def __init__(self, history):
        """
        history: Lista de listas, ex: [[1,2,...], [3,4,...]]
        """
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.train(history)
        
    def _vectorize(self, jogo, total_nums=25):
        # One-hot encoding do jogo
        vec = np.zeros(total_nums)
        for n in jogo:
            if 1 <= n <= total_nums:
                vec[n-1] = 1
        return vec
        
    def train(self, history):
        if not history: return
        
        # 1. Dataset Real (Label 1)
        X_real = [self._vectorize(h) for h in history]
        y_real = [1] * len(X_real)
        
        # 2. Dataset Fake (Label 0) - Gerar jogos aleatórios para contrapor
        X_fake = []
        import random # Local import to keep clean
        sample_len = len(history[0]) if history else 15
        total_nums = 25 # Default Lotofacil
        
        for _ in range(len(history)):
            fake_game = random.sample(range(1, total_nums+1), sample_len)
            X_fake.append(self._vectorize(fake_game))
        y_fake = [0] * len(X_fake)
        
        # Treino
        X = np.array(X_real + X_fake)
        y = np.array(y_real + y_fake)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        self.model.fit(X_train, y_train)
        
        # print(f"   [AI] Acurácia Teste: {self.model.score(X_test, y_test):.2f}")

    def predict_score(self, jogo):
        """
        Retorna probabilidade de ser um jogo 'Real' (0.0 a 1.0)
        """
        vec = self._vectorize(jogo).reshape(1, -1)
        return self.model.predict_proba(vec)[0][1]
