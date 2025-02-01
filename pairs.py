import json
import requests


# URL da API pública Raydium para obter todos os pools de liquidez
raydium_api_url = "https://api.raydium.io/pairs"

def get_pools():
    try:
        raydium_api_url = "https://api.raydium.io/pairs"
        response = requests.get(raydium_api_url)
        response.raise_for_status()
        
        pools = response.json()
        #with open("pools.json", "w") as file:
        #    json.dump(pools, file, indent=4) 
        return pools
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")


def get_pair_with_sol(token_address, pools, logger):
    try:        
        # Iterar sobre os pools de liquidez e procurar o par com o token e SOL
        for pool in pools:
            # Verificar se o token fornecido está presente no par
            if 'pair_id' in pool:
                pair_id = pool['pair_id']
                
                # Verificar se o token fornecido e o SOL estão no par
                if token_address in pair_id and 'So11111111111111111111111111111111111111112' in pair_id:
                    logger.info(f"Par encontrado: {pool['name']} {pool['pair_id']}")
                    return pool['amm_id']
        
        logger.info("Par com SOL não encontrado!")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição à API: {e}")
















    




