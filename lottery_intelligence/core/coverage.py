
import numpy as np

class CoverageEngine:
    @staticmethod
    def calculate_hamming_distance(game_a, game_b):
        """
        Calcula a distância de Hamming entre dois jogos (conjuntos de números).
        A distância é o número de elementos diferentes dividida por 2?
        Não, simplificando: Hamming Distance em sets fixos é (tamanho - interseção).
        Se jogo A = {1,2,3} e B = {1,2,4}. Interseção {1,2} (tam 2). Distância = 3 - 2 = 1.
        Retorna quantos números DIFERENTES o jogo A tem em relação ao B.
        """
        set_a = set(game_a)
        set_b = set(game_b)
        # Números em A que não estão em B (diferença)
        diff = len(set_a.difference(set_b))
        return diff

    @staticmethod
    def validate_diversity(new_game, portfolio, min_distance=3):
        """
        Verifica se o novo jogo respeita a distância mínima contra TODO o portfólio.
        Retorna (True, None) se aprovado.
        Retorna (False, distance) se falhar (distância do jogo mais próximo).
        """
        if not portfolio:
            return True, 0
            
        min_dist_found = float('inf')
        
        for existing_game in portfolio:
            dist = CoverageEngine.calculate_hamming_distance(new_game, existing_game)
            if dist < min_dist_found:
                min_dist_found = dist
            
            if dist < min_distance:
                return False, dist
                
        return True, min_dist_found

    @staticmethod
    def calculate_portfolio_coverage(portfolio):
        """
        Retorna a cobertura média (distância média) do portfólio.
        Quanto maior, melhor a diversidade.
        """
        if len(portfolio) < 2:
            return 0.0
            
        distances = []
        for i in range(len(portfolio)):
            for j in range(i + 1, len(portfolio)):
                dist = CoverageEngine.calculate_hamming_distance(portfolio[i], portfolio[j])
                distances.append(dist)
                
        return sum(distances) / len(distances) if distances else 0.0
