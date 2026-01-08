
# --- CONFIGURAÇÃO ---
DB_PATH = "loterias.db"
URL_BASE = "https://raw.githubusercontent.com/guilhermeasn/loteria.json/master/data/"

CONFIG_LOTERIAS = {
    "megasena": {
        "url": URL_BASE + "megasena.json", 
        "preco": 6.00, 
        "total_nums": 60, 
        "escolhe": 6,
        "orcamento_alvo": 12.00 # ~2 jogos
    },
    "lotofacil": {
        "url": URL_BASE + "lotofacil.json", 
        "preco": 3.50, 
        "total_nums": 25, 
        "escolhe": 15,
        "orcamento_alvo": 35.00, # ~10 jogos
        "fixed_core": 4,
        "variable_selection": 11
    },
    "lotomania": {
        "url": URL_BASE + "lotomania.json", 
        "preco": 3.00, 
        "total_nums": 100, 
        "escolhe": 50,
        "orcamento_alvo": 15.00 # ~5 jogos
    },
    "diadesorte": {
        "url": URL_BASE + "diadesorte.json", 
        "preco": 2.50, 
        "total_nums": 31, 
        "escolhe": 7,
        "orcamento_alvo": 35.00 # ~14 jogos
    }
}
