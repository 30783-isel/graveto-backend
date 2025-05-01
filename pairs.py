import os
import json
import requests
from typing import Union


def get_pools(use_cache: bool = True) -> Union[list, None]:
    cache_file = "pools.json"
    
    # Verifica se o cache existe e se deve usá-lo
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as file:
                pools = json.load(file)
            print("Dados carregados do cache.")
            return pools
        except (json.JSONDecodeError, IOError) as e:
            print(f"Erro ao carregar cache: {e}")
    
    # Se não há cache ou use_cache é False, faz a chamada à API
    try:
        raydium_api_url = "https://api.raydium.io/pairs"
        response = requests.get(raydium_api_url)
        response.raise_for_status()
        
        pools = response.json()
        
        # Salva os dados no arquivo
        try:
            with open(cache_file, "w") as file:
                json.dump(pools, file, indent=4)
            print("Dados salvos no cache.")
        except IOError as e:
            print(f"Erro ao salvar cache: {e}")
            
        return pools
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None


def get_pair_with_sol(token_address, pools, logger):
    try:        
        for pool in pools:
            if 'pair_id' in pool:
                pair_id = pool['pair_id']
                if token_address in pair_id and 'So11111111111111111111111111111111111111112' in pair_id:
                    logger.info(f"Par encontrado: {pool['name']} {pool['pair_id']}")
                    return pool['amm_id']
        
        logger.info("Par com SOL não encontrado!")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição à API: {e}")
















    




