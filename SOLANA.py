import os
import requests
import pandas as pd
import json
import time
import importlib
import logging
import configparser
from datetime import datetime
from flask import Flask, jsonify, request
from pairs import get_pair_with_sol, get_pools 
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


database = importlib.import_module("1_database")

app = Flask(__name__)

# Configurar o nível de log para ERROR para ocultar logs de requisição
app.logger.setLevel(logging.INFO)

# Configuração do logger
log_file = 'app.log'  # Defina o caminho do arquivo de log

# Cria um logger
logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)

# Cria um handler para escrever no arquivo
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)

# Cria um handler para escrever no console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Define o formato das mensagens de log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Adiciona os handlers ao logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


config = configparser.ConfigParser()
config.read('config.centralized.properties')

type = 'CENTRALIZED'

# Obter a URL do arquivo de configurações
urlGetLatestSpotPairs = config.get(type, 'urlGetListingLatest')
urlGetTokenByBaseAssetContractAddress = config.get(type, 'urlGetTokenByBaseAssetContractAddress')
serverUrl = config.get(type, 'serverUrl')
SCHEDULER_EXECUTION_BTC_QUOTE = config.get(type, 'SCHEDULER_EXECUTION_BTC_QUOTE')
SCHEDULER_EXECUTION_BUY = config.get(type, 'SCHEDULER_EXECUTION_BUY')
SCHEDULER_EXECUTION_SELL = config.get(type, 'SCHEDULER_EXECUTION_SELL')
SWAP_EXECUTION = config.get(type, 'SWAP_EXECUTION')
PERCENTAGE_LOSS = config.get(type, 'PERCENTAGE_LOSS')
NUM_TOKENS_PROCESSED = config.get(type, 'NUM_TOKENS_PROCESSED')
NUM_TOKENS_COINMARKETCAP = config.get(type, 'NUM_TOKENS_COINMARKETCAP')

# Definir URL e parâmetros da API
# https://sandbox-api.coinmarketcap.com

parameters = {
    'start': '1',
    'limit': NUM_TOKENS_COINMARKETCAP  # Aumentamos o limite para pegar mais tokens
}
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': 'ff716c6f-21b5-4f8c-850d-8c5b2792e9a2',  # Substitua com sua chave
}



















@app.route('/best-tokens', methods=['GET'])
def get_best_tokens_endpoint():
    try:
        pools = get_pools() 
        top_tokens = buy_tokens(pools)
        sell_tokens(pools) 
        return jsonify(top_tokens), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500

@app.route('/buy-tokens', methods=['GET'])
def buy_tokens_call():
    try:
        logger.info('buy_tokens - start get_pools')
        pools = get_pools() 
        logger.info('buy_tokens - end get_pools')
        top_tokens = buy_tokens(pools)
        return jsonify(top_tokens), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500   

@app.route('/sell-tokens', methods=['GET'])
def sell_tokens_call():
    try:
        logger.info('sell_tokens - start get_pools')
        pools = get_pools() 
        logger.info('sell_tokens - end get_pools')
        tokens_vendidos = sell_tokens(pools) 
        return jsonify(tokens_vendidos), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500   

@app.route('/get-tokens', methods=['GET'])
def getTokens():
    resultados_formatados = get_tokens_analyzed_from_db()
    return jsonify(resultados_formatados), 200


@app.route('/get-btc-quote', methods=['GET'])
def getBTCQuote():
    try:
        data = processBTCQuote()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500











# Função para pegar os dados da API
def fetch_data():
    response = requests.get(urlGetLatestSpotPairs, params=parameters, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Erro ao fazer requisição: {response.status_code}")
        return None

# Função comum para calcular a pontuação do token
def calculate_score(token, score_weights):
    # Pegando os dados principais
    price = token['quote']['USD']['price']
    volume_24h = token['quote']['USD']['volume_24h']
    percent_change_1h = token['quote']['USD'].get('percent_change_1h', 0)
    percent_change_24h = token['quote']['USD'].get('percent_change_24h', 0)
    market_cap = token['quote']['USD']['market_cap']
    
    # A pontuação será calculada com base nas variações e volume de mercado
    score = 0
    
    # Aplicando os pesos configurados para cada critério
    score += percent_change_1h * score_weights['percent_change_1h']
    score += percent_change_24h * score_weights['percent_change_24h']
    score += (volume_24h / 1e6) * score_weights['volume_24h']
    score += (market_cap / 1e9) * score_weights['market_cap']
    
    # Liquidez (volume 24h / market cap), se market_cap for maior que 0
    if market_cap > 0:
        liquidity = volume_24h / market_cap
        score += liquidity * score_weights['liquidity']
    
    return score

def process_tokens(score_weights):
    data = fetch_data()
    if not data:
        return []

    all_data = pd.DataFrame()
    for token in data['data']:
        platform = token.get('platform', None)
        if platform:
            platform_id = platform.get('id', None)
            platform_name = platform.get('name', None)
            platform_slug = platform.get('slug', None)
            platform_symbol = platform.get('symbol', None)
            platform_token_address = platform.get('token_address', None)

            if platform_slug != 'solana':
                continue

        else:
            continue
            #platform_id = platform_name = platform_slug = platform_symbol = platform_token_address = None

        token_data = {
            'id': token['id'],
            'name': token['name'],
            'symbol': token['symbol'],
            'slug': token['slug'],
            'num_market_pairs': token['num_market_pairs'],
            'date_added': token['date_added'],
            'max_supply': token['max_supply'],
            'circulating_supply': token['circulating_supply'],
            'total_supply': token['total_supply'],
            'infinite_supply': token['infinite_supply'],
            'platform_id': platform_id,
            'platform_name': platform_name,
            'platform_slug': platform_slug,
            'platform_symbol': platform_symbol,
            'platform_token_address': platform_token_address,
            'cmc_rank': token['cmc_rank'],
            'self_reported_circulating_supply': token['self_reported_circulating_supply'],
            'self_reported_market_cap': token['self_reported_market_cap'],
            'last_updated': token['last_updated'],
            'price': token['quote']['USD']['price'],
            'volume_24h': token['quote']['USD']['volume_24h'],
            'percent_change_1h': token['quote']['USD'].get('percent_change_1h', None),
            'percent_change_24h': token['quote']['USD'].get('percent_change_24h', None),
            'market_cap': token['quote']['USD']['market_cap'],
            'market_cap_dominance': token['quote']['USD']['market_cap_dominance'],
            'fully_diluted_market_cap': token['quote']['USD']['fully_diluted_market_cap'],
            'last_updated_quote': token['quote']['USD']['last_updated']
        }

        # Calcular a pontuação do token
        token_data['score'] = calculate_score(token, score_weights)

        # Adicionar o token com a pontuação ao DataFrame
        row = pd.DataFrame([token_data])
        row = row.dropna(axis=1, how='all')
        all_data = pd.concat([all_data, row], ignore_index=True)

    # Ordenando os tokens pela pontuação, da maior para a menor
    best_tokens = all_data.sort_values(by='score', ascending=False).head(int(NUM_TOKENS_PROCESSED))
    
    return best_tokens.to_dict(orient='records')

    
    
def buy_tokens(pools):
    top_tokens = []
    global global_percent_change_1h 
    if global_percent_change_1h > 0:
    
        score_weights = {
            'percent_change_1h': 0.5,
            'percent_change_24h': 0.5,
            'volume_24h': 0.0,
            'market_cap': 0.0,
            'liquidity': 0.0
        }

        top_tokens = process_tokens(score_weights)

        existing_tokens = database.get_existing_tokens()

        new_tokens = []
        for token in top_tokens:
            if token['symbol'] not in [existing['symbol'] for existing in existing_tokens]:
                new_tokens.append(token)


        if new_tokens:
            logger.info("Novos tokens detectados:")
            for token in new_tokens:
                id = token.get('id', None),
                symbol = token.get('symbol', None),
                name = token.get('name', None),
                platform_name = token.get('platform_name', None),
                platform_token_address = token.get('platform_token_address', None),
                price = token.get('price', None)
                percent_change_1h = token.get('percent_change_1h', None)
                percent_change_24h = token.get('percent_change_24h', None),
                volume_24h = token.get('volume_24h', None)
                market_cap = token.get('market_cap', None)
                score = token.get('score', None)
                data = {
                    'id': id,
                    'platform_token_address': platform_token_address,
                    'symbol': symbol,
                    'name': name,
                    'platform_name': platform_name,
                    'price': price,
                    'min_price': price,
                    'max_price': price,
                    'percent_change_1h': percent_change_1h,
                    'percent_change_24h': percent_change_24h,
                    'volume_24h': volume_24h,
                    'market_cap': market_cap,
                    'score': score,
                    'comprado': True,
                }
                logger.info("--------------------------------------------------------------------------------------------------------------------------- a comprar " + name[0])
                sucess = swapToken(data, pools)
                #sucess = True
                if(sucess):
                    isInserted = database.insert_buy(data)
                else:
                    logger.error("Erro ao comprar " + data['name'][0])
                    for token in top_tokens:
                        if token['name'] == data['name'][0]:
                            top_tokens.remove(token)
                            break  # Para garantir que remove o primeiro token com o nome "Orca"
                time.sleep(int(SWAP_EXECUTION)) 

            # Atualizar banco de dados para ter apenas os 10 tokens mais recentes
            database.save_tokens_to_db(top_tokens)

        else:
            logger.info("Nenhuma alteração nos tokens detectada.")
        return top_tokens
    return top_tokens









def swapToken(swapPairs, pools):
    data = {
        'symbol': swapPairs['symbol'], 
        'name': swapPairs['name'],
    }
    pair_address = get_pair_with_sol(swapPairs['platform_token_address'], pools, logger)

    url = "http://localhost:3000/swap"

    payload = {
        "pairAdress": pair_address,
        "quoteAsset": swapPairs['platform_token_address'],
        "baseAsset": "So11111111111111111111111111111111111111112",
        "buy": swapPairs['comprado']
    }
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        pair_address = payload.get('pairAdress')
        if pair_address is not None:
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            if response.status_code == 200:
                if swapPairs.get('comprado'): 
                    logger.info(f"Swap com sucesso --- Token: {data['name']} \033[92mcomprado\033[0m.")
                else:
                    logger.info(f"Swap com sucesso --- Token: {data['name']} \033[91mvendido\033[0m.")
                return True
            else:
                logger.error(f"Falha na requisição: {response.json()}")
                return False
        else:
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição: {e}")
        return False


























def sell_tokens(pools):
    tokens_vendidos = []
    resultados_formatados = get_tokens_analyzed_from_db()
    
    if resultados_formatados:
        for resultado in resultados_formatados:
            id = resultado.get('id', None) 
            platform_token_address = resultado.get('platform_token_address', None) 
            symbol = resultado.get('symbol', None)
            name = resultado["name"]
            platform_name = resultado["platform_name"]
            price = resultado["price"]
            min_price = resultado["min_price"]
            max_price = resultado["max_price"]
            current_price = resultado["current_price"]
            percent_change_1h = resultado["percent_change_1h"]
            percent_change_24h = resultado["percent_change_24h"]
            volume_24h = resultado["volume_24h"]
            market_cap = resultado["market_cap"]
            score = resultado["score"]
            comprado = 0
            gain_percentage_with_current_price = resultado["gain_percentage_with_current_price"]
            gain_percentage_with_max_price = resultado["gain_percentage_with_max_price"]

            if(gain_percentage_with_max_price < -float(PERCENTAGE_LOSS)):
                data = {
                    'id': id,
                    'platform_token_address': platform_token_address,
                    'symbol': symbol,
                    'name': name,
                    'platform_name': platform_name,
                    'price': price,
                    'percent_change_1h': percent_change_1h,
                    'percent_change_24h': percent_change_24h,
                    'volume_24h': volume_24h,
                    'market_cap': market_cap,
                    'score': score,
                    'comprado': False
                }
                logger.info("--------------------------------------------------------------------------------------------------------------------------- a vender " + name)
                sucess = swapToken(data, pools)

                if(sucess):
                    updatedData  = {
                        'comprado': comprado
                    } 
                    #sucess = database.delete_buy_token(data)
                    sucess = database.update_buy(updatedData, symbol)
                    tokens_vendidos.append(data)
                    time.sleep(int(SWAP_EXECUTION)) 
                else:
                    logger.error("Erro ao vender " + name)
            else:
                logger.info(name + f' tem saldo positivo {gain_percentage_with_current_price}%' )
    else:
        logger.info("DB buy centralized empty.")
    return tokens_vendidos

def get_tokens_analyzed_from_db():
    resultados = database.getTokens()
    
    if resultados:
        resultados_formatados = []
        for row in resultados:
            id = row[0]
            platform_token_address = row[1]
            symbol = row[2]
            name = row[3]
            platform_name = row[4]
            price = row[5]
            min_price = row[6]
            max_price = row[7]
            percent_change_1h = row[8]
            percent_change_24h = row[9]
            volume_24h = row[10]
            market_cap = row[11]
            score = row[12]
            comprado = row[13]
            try:
                token_atual = getTokenMetrics(id)
                if token_atual and 'data' in token_atual and len(token_atual['data']) > 0:
                    quote = token_atual['data'][str((id))]['quote']['USD']
                    if quote:
                        price_atual = quote.get('price') 
                        if price_atual > max_price:
                            max_price = price_atual
                            updatedData  = {
                                'max_price': price_atual
                            } 
                            sucess = database.update_buy(updatedData, symbol)
                            if sucess:
                                logger.info(f" ${symbol} - max_price updated from - ${max_price} - to - ${price_atual}")
                        if price_atual < min_price:
                            updatedData  = {
                                'min_price': price_atual
                            } 
                            sucess = database.update_buy(updatedData, symbol)
                            if sucess:
                                logger.info(f" ${symbol} - min_price updated from - ${min_price} - to - ${price_atual}")
                    if price_atual and price:
                        gain_percentage_with_current_price = ((price_atual - price) / price) * 100
                    else:
                        gain_percentage_with_current_price = 0

                    if price_atual and max_price:
                        gain_percentage_with_max_price = ((price_atual - max_price) / max_price) * 100
                    else:
                        gain_percentage_with_max_price = 0

                    resultado_formatado = {
                        'id': id,
                        'platform_token_address': platform_token_address,
                        'symbol': symbol,
                        'name': name,
                        'platform_name': platform_name,
                        'price': price,
                        'min_price': min_price,
                        'max_price': max_price,
                        'current_price':price_atual,
                        'percent_change_1h': percent_change_1h,
                        'percent_change_24h': percent_change_24h,
                        'volume_24h': volume_24h,
                        'market_cap': market_cap,
                        'score': score,
                        'comprado': comprado,
                        "gain_percentage_with_current_price": gain_percentage_with_current_price,
                        "gain_percentage_with_max_price": gain_percentage_with_max_price
                    }
                    
                    resultados_formatados.append(resultado_formatado)
                    #logger.info( json.dumps(resultados_formatados, indent=4))
                else:
                    continue   
            except Exception as e:
                logger.error(f"Erro ao processar o token {symbol}: {e}. Continuando para o próximo token.")
                continue
        return resultados_formatados
    else:
        return []



def getTokenMetrics(id):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    params = {
        'id': id,
        'convert': 'USD'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        logger.error(f"Erro ao acessar a API: {response.status_code}")





def processBTCQuote():
    global global_percent_change_1h 
    BTC_QUOTE = getTokenMetrics('1')
    if BTC_QUOTE and 'data' in BTC_QUOTE and len(BTC_QUOTE['data']) > 0:
        # Extraindo as informações relevantes da variável BTC_QUOTE e removendo o campo 'tags'
        btc_data = BTC_QUOTE['data']['1']

        data = {
            'id': btc_data['id'],
            'symbol': btc_data['symbol'],
            'name': btc_data['name'],
            'platform_name': 'Bitcoin',  # A plataforma é Bitcoin
            'price': btc_data['quote']['USD']['price'],
            'percent_change_1h': btc_data['quote']['USD']['percent_change_1h'],
            'percent_change_24h': btc_data['quote']['USD']['percent_change_24h'],
            'percent_change_7d': btc_data['quote']['USD']['percent_change_7d'], 
            'percent_change_30d': btc_data['quote']['USD']['percent_change_30d'],
            'percent_change_60d': btc_data['quote']['USD']['percent_change_60d'],
            'percent_change_90d': btc_data['quote']['USD']['percent_change_90d'],
            'volume_24h': btc_data['quote']['USD']['volume_24h'],
            'market_cap': btc_data['quote']['USD']['market_cap'],
            'slug': btc_data['slug'], 
            'num_market_pairs': btc_data['num_market_pairs'], 
            'date_added': btc_data['date_added'], 
            'max_supply': btc_data['max_supply'],  
            'circulating_supply': btc_data['circulating_supply'], 
            'total_supply': btc_data['total_supply'], 
            'is_active': btc_data['is_active'], 
            'infinite_supply': btc_data['infinite_supply'], 
            'is_fiat': btc_data['is_fiat'],
            'self_reported_circulating_supply': btc_data['self_reported_circulating_supply'],
            'self_reported_market_cap': btc_data['self_reported_market_cap'], 
            'tvl_ratio': btc_data['tvl_ratio'], 
            'last_updated': btc_data['last_updated'], 
        }

        global_percent_change_1h = btc_data['quote']['USD']['percent_change_1h']
        
        print(f"percent_change_1h: {global_percent_change_1h}")

























global_percent_change_1h = 0

def start_scheduler_btc_quote():
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: processBTCQuote(), 'interval', minutes=int(SCHEDULER_EXECUTION_BTC_QUOTE),next_run_time=datetime.now())
    scheduler.start()
    logger.info("Scheduler btc quote iniciado com sucesso.")

def start_scheduler_buy():
    pools = get_pools() 
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: buy_tokens(pools), 'interval', minutes=int(SCHEDULER_EXECUTION_BUY),next_run_time=datetime.now())
    scheduler.start()
    logger.info("Scheduler buy iniciado com sucesso.")

def start_scheduler_sell():
    pools = get_pools() 
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: sell_tokens(pools), 'interval', minutes=int(SCHEDULER_EXECUTION_SELL),next_run_time=datetime.now())
    scheduler.start()
    logger.info("Scheduler sell iniciado com sucesso.")


if __name__ == '__main__':
    try:
        start_scheduler_btc_quote()
        start_scheduler_buy()
        start_scheduler_sell()
    except Exception as e:
        logger.error(f"Error: {e}.")

    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)# TODO Alterar use_reloader=False



































