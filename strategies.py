STRATEGIES = {
    'momentum_agressivo': {
        'percent_change_1h': 0.4,
        'percent_change_24h': 0.3,
        'volume_24h': 0.2,
        'market_cap': 0.0,
        'liquidity': 0.1
    },
    'momentum_conservador': {
        'percent_change_1h': 0.2,
        'percent_change_24h': 0.3,
        'volume_24h': 0.3,
        'market_cap': 0.1,
        'liquidity': 0.1
    },
    'so_variacao': {
        'percent_change_1h': 0.5,
        'percent_change_24h': 0.5,
        'volume_24h': 0.0,
        'market_cap': 0.0,
        'liquidity': 0.0
    }
}

def get_strategy(name: str) -> dict:
    if name not in STRATEGIES:
        raise ValueError(f"Estratégia '{name}' não existe. Disponíveis: {list(STRATEGIES.keys())}")
    return STRATEGIES[name]