from typing import List, Set

class CoverageEngine:
    def __init__(self, min_distance: int = 4, game_type: str = 'lotofacil'):
        """
        min_distance: Quantidade mínima de números diferentes exigida entre jogos.
        game_type: 'lotofacil', 'lotomania', etc.
        
        V6 Hybrid: Ajuste específico para Lotomania
        """
        self.base_min_distance = min_distance
        self.game_type = game_type
        
        # Ajuste específico para Lotomania (permitir clusters mais densos)
        if game_type == 'lotomania':
            # Reduzir limiar para permitir jogos mais parecidos
            self.min_distance = max(6, min_distance // 2)
        else:
            self.min_distance = min_distance

    def calculate_distance(self, game_a: List[int], game_b: List[int]) -> int:
        """Calcula quantos números de A não estão em B."""
        set_a = set(game_a)
        set_b = set(game_b)
        
        # Hamming Distance (assimétrica para conjuntos de mesmo tamanho)
        diff = len(set_a.difference(set_b))
        return diff

    def is_diverse(self, new_game: List[int], portfolio: List[List[int]]) -> bool:
        """Retorna True se o jogo tem a distância mínima de TODOS os jogos do portfolio."""
        if not portfolio:
            return True
            
        for existing_game in portfolio:
            dist = self.calculate_distance(new_game, existing_game)
            if dist < self.min_distance:
                return False  # Rejeitado: muito parecido com um jogo existente
        return True
