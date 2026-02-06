
from collections import Counter

class AdvancedFilters:
    @staticmethod
    def is_prime(n):
        if n < 2: return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0: return False
        return True

    @staticmethod
    def count_primes(jogo):
        return sum(1 for n in jogo if AdvancedFilters.is_prime(n))

    @staticmethod
    def count_fibonacci(jogo):
        fibs = {1, 2, 3, 5, 8, 13, 21, 34, 55, 89}
        return sum(1 for n in jogo if n in fibs)

    @staticmethod
    def count_consecutive(jogo):
        if not jogo: return 0
        sorted_jogo = sorted(jogo)
        max_seq = 0
        current_seq = 1
        for i in range(1, len(sorted_jogo)):
            if sorted_jogo[i] == sorted_jogo[i-1] + 1:
                current_seq += 1
            else:
                max_seq = max(max_seq, current_seq)
                current_seq = 1
        return max(max_seq, current_seq)

    @staticmethod
    def validar_v3(jogo, loteria, ultimo_resultado=None):
        """
        Aplica filtros V3 (Soma, Primos, Fibonacci, Repetentes)
        Retorna: True (Aprovado) ou False (Reprovado)
        """
        # Apenas Lotofácil por enquanto
        if loteria != 'lotofacil':
            return True
            
        # 1. Soma (Normal: 180-210, margem 160-230)
        soma = sum(jogo)
        if not (160 <= soma <= 230):
            return False
            
        # 2. Primos (Normal: 4-6, margem 3-8)
        primos = AdvancedFilters.count_primes(jogo)
        if not (3 <= primos <= 8):
            return False
            
        # 3. Fibonacci (Normal: 3-5, margem 2-7)
        fib = AdvancedFilters.count_fibonacci(jogo)
        if not (2 <= fib <= 7):
            return False
            
        # 4. Sequências (Max 5-6 consecutivas)
        seq = AdvancedFilters.count_consecutive(jogo)
        if seq > 6: # Sequencia de 7 é muito rara
            return False
            
        # 5. Repetentes do Anterior (Se disponível)
        if ultimo_resultado:
            repetidas = len(set(jogo).intersection(set(ultimo_resultado)))
            # Normal é 8-10. Aceitamos 7-11
            if not (7 <= repetidas <= 11):
                return False
                
        return True
