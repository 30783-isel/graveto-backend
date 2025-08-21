import requests



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
        
        
        
def get_pair(token_address, pools, logger):
    try:        
        for pool in pools:
            if 'pair_id' in pool:
                pair_id = pool['pair_id']
                if token_address in pair_id and 'So11111111111111111111111111111111111111112' in pair_id:
                    logger.info(f"Par encontrado: {pool['name']} {pool['pair_id']}")
                    return pool
        
        logger.info("Par com SOL não encontrado!")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição à API: {e}")
















    




