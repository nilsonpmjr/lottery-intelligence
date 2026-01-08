from typing import List, Set

class CoverageEngine:
    def __init__(self, min_distance: int = 4):
        """
        min_distance: Quantidade mínima de números diferentes exigida entre jogos.
        Ex: Se min_distance=4, um novo jogo não pode ter mais de 11 números iguais a nenhum jogo anterior.
        """
        self.min_distance = min_distance

    def calculate_distance(self, game_a: List[int], game_b: List[int]) -> int:
        """Calcula quantos números são DIFERENTES entre dois jogos."""
        set_a = set(game_a)
        set_b = set(game_b)
        # Diferença simétrica: números que estão em A ou B, mas não em ambos
        # Para lotofácil, queremos garantir que a interseção não seja muito alta.
        # Distância aqui = 15 - (tamanho da interseção)
        intersection = len(set_a.intersection(set_b))
        return 15 - intersection

    def is_diverse(self, new_game: List[int], portfolio: List[List[int]]) -> bool:
        """Retorna True se o jogo tem a distância mínima de TODOS os jogos do portfolio."""
        if not portfolio:
            return True
            
        for existing_game in portfolio:
            dist = self.calculate_distance(new_game, existing_game)
            if dist < self.min_distance:
                return False # Rejeitado: muito parecido com um jogo existente
        return True
