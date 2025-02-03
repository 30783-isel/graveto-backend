import os
import requests
import json
import time
import logging
import importlib
import functools
import pandas as pd
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

config_file_path = 'config.centralized.properties'

def get_config_value(key):
    try:
        config = configparser.ConfigParser(interpolation=None)
        config.read(config_file_path)
        val = config.get(type, key)
        #print(key + ' -' + val)
        return val
    except ValueError:
        return config.get(type, key)

type = 'CENTRALIZED'

parameters = {
    'start': '1',
    'limit': get_config_value('NUM_TOKENS_COINMARKETCAP') 
}
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': 'ff716c6f-21b5-4f8c-850d-8c5b2792e9a2',  
}



# Obter a URL do arquivo de configurações
urlGetLatestSpotPairs = get_config_value('urlGetListingLatest')
urlGetTokenByBaseAssetContractAddress = get_config_value('urlGetTokenByBaseAssetContractAddress')
serverUrl = get_config_value('serverUrl')
SCHEDULER_EXECUTION_BTC_QUOTE = int(get_config_value('SCHEDULER_EXECUTION_BTC_QUOTE'))
SCHEDULER_EXECUTION_BUY = int(get_config_value('SCHEDULER_EXECUTION_BUY'))
SCHEDULER_EXECUTION_SELL = int(get_config_value('SCHEDULER_EXECUTION_SELL'))
SWAP_EXECUTION = int(get_config_value('SWAP_EXECUTION'))
PERCENTAGE_LOSS = float(get_config_value('PERCENTAGE_LOSS'))
NUM_TOKENS_PROCESSED = int(get_config_value('NUM_TOKENS_PROCESSED'))
NUM_TOKENS_COINMARKETCAP = int(get_config_value('NUM_TOKENS_COINMARKETCAP'))
BTC_1H_PERCENT = float(get_config_value('BTC_1H_PERCENT'))
BUY_VALUE_IN_USD = float(get_config_value('BUY_VALUE_IN_USD'))
ADD_REPEATED = int(get_config_value('ADD_REPEATED'))



list_tokens = []





@app.before_request
def limit_remote_addr():
    client_ip = request.remote_addr
    if client_ip.startswith('87.') or client_ip.startswith('89.') or client_ip.startswith('192.168.') or client_ip == '127.0.0.1':
        return None
    logger.error('Bloqueado Ip - ' + client_ip)
    return jsonify({"estado": "Erro", "mensagem": "IP não autorizado"}), 403



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
        global pools
        top_tokens = buy_tokens(pools)
        return jsonify(top_tokens), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500   

@app.route('/sell-tokens', methods=['GET'])
def sell_tokens_call():
    try:
        global pools
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
        data = processTokenQuote('1')
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500


@app.route('/get-solana-quote', methods=['GET'])
def getSolanaQuote():
    try:
        data = processTokenQuote('5426')
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500



@app.route('/get-value-quantity', methods=['GET'])
def getValueQuantity():
    try:
        solana = processTokenQuote('5426')
        token = processTokenQuote('21870')
        data = get_price_in_solana(solana['price'], token['price'], float(get_config_value('BUY_VALUE_IN_USD')))
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500



@app.route('/get-sol-wallet', methods=['GET'])
def get_sol_wallet_value():
    try:
        data = val_sol_wallet()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500
    

@app.route('/clean-slate', methods=['GET'])
def getCleanSlate():
    try:
        data = database.clean_slate()
        return jsonify({"estado": "Sucesso"}), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500
    






@app.route('/get-config', methods=['GET'])
def get_config_endpoint():
    try:
        config_data = {
            "SCHEDULER_EXECUTION_BTC_QUOTE": int(get_config_value('SCHEDULER_EXECUTION_BTC_QUOTE')),
            "SCHEDULER_EXECUTION_SELL": int(get_config_value('SCHEDULER_EXECUTION_SELL')),
            "SCHEDULER_EXECUTION_BUY": int(get_config_value('SCHEDULER_EXECUTION_BUY')),
            "SWAP_EXECUTION": int(get_config_value('SWAP_EXECUTION')),
            "PERCENTAGE_LOSS": float(get_config_value('PERCENTAGE_LOSS')),
            "NUM_TOKENS_PROCESSED": int(get_config_value('NUM_TOKENS_PROCESSED')),
            "NUM_TOKENS_COINMARKETCAP": int(get_config_value('NUM_TOKENS_COINMARKETCAP')),
            "BTC_1H_PERCENT": float(get_config_value('BTC_1H_PERCENT')),
            "BUY_VALUE_IN_USD":float( get_config_value('BUY_VALUE_IN_USD')),
            "EXECUTE_OPERATIONS": int(get_config_value('EXECUTE_OPERATIONS')),
            "EXECUTE_SCHEDULER": int(get_config_value('EXECUTE_SCHEDULER')),
            "PAUSE_TOKEN_METRICS": int(get_config_value('PAUSE_TOKEN_METRICS')),
            "ADD_REPEATED": int(get_config_value('ADD_REPEATED')),
            "EXECUTE_SWAP": int(get_config_value('EXECUTE_SWAP'))
        }
        return jsonify(config_data), 200

    except Exception as e:
        return jsonify({"estado": "Erro", "mensagem": str(e)}), 500






@app.route('/update-config', methods=['POST'])
def update_config_endpoint():
    try:
        print('teste')
        data = request.get_json()

        if not data:
            return jsonify({"estado": "Erro", "mensagem": "Nenhum dado enviado."}), 400

        config = read_config()

        if 'SCHEDULER_EXECUTION_BTC_QUOTE' in data:
            config.set('CENTRALIZED', 'SCHEDULER_EXECUTION_BTC_QUOTE', str(data['SCHEDULER_EXECUTION_BTC_QUOTE']))
        if 'SCHEDULER_EXECUTION_SELL' in data:
            config.set('CENTRALIZED', 'SCHEDULER_EXECUTION_SELL', str(data['SCHEDULER_EXECUTION_SELL']))
        if 'SCHEDULER_EXECUTION_BUY' in data:
            config.set('CENTRALIZED', 'SCHEDULER_EXECUTION_BUY', str(data['SCHEDULER_EXECUTION_BUY']))
        if 'SWAP_EXECUTION' in data:
            config.set('CENTRALIZED', 'SWAP_EXECUTION', str(data['SWAP_EXECUTION']))
        if 'PERCENTAGE_LOSS' in data:
            config.set('CENTRALIZED', 'PERCENTAGE_LOSS', str(data['PERCENTAGE_LOSS']))
        if 'NUM_TOKENS_PROCESSED' in data:
            config.set('CENTRALIZED', 'NUM_TOKENS_PROCESSED', str(data['NUM_TOKENS_PROCESSED']))
        if 'NUM_TOKENS_COINMARKETCAP' in data:
            config.set('CENTRALIZED', 'NUM_TOKENS_COINMARKETCAP', str(data['NUM_TOKENS_COINMARKETCAP']))
        if 'BTC_1H_PERCENT' in data:
            config.set('CENTRALIZED', 'BTC_1H_PERCENT', str(data['BTC_1H_PERCENT']))
        if 'BUY_VALUE_IN_USD' in data:
            config.set('CENTRALIZED', 'BUY_VALUE_IN_USD', str(data['BUY_VALUE_IN_USD']))
        if 'EXECUTE_OPERATIONS' in data:
            config.set('CENTRALIZED', 'EXECUTE_OPERATIONS', str(data['EXECUTE_OPERATIONS']))
        if 'PAUSE_TOKEN_METRICS' in data:
            config.set('CENTRALIZED', 'PAUSE_TOKEN_METRICS', str(data['PAUSE_TOKEN_METRICS']))
        if 'ADD_REPEATED' in data:
            config.set('CENTRALIZED', 'ADD_REPEATED', str(data['ADD_REPEATED']))
        if 'EXECUTE_SCHEDULER' in data:
            config.set('CENTRALIZED', 'EXECUTE_SCHEDULER', str(data['EXECUTE_SCHEDULER']))
        if 'EXECUTE_SWAP' in data:
            config.set('CENTRALIZED', 'EXECUTE_SWAP', str(data['EXECUTE_SWAP']))

        save_config(config)

        return jsonify({"estado": "Sucesso", "mensagem": "Propriedades atualizadas com sucesso."}), 200

    except Exception as e:
        return jsonify({"estado": "Erro", "mensagem": str(e)}), 500


def read_config():
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config

def save_config(config):
    with open(config_file_path, 'w') as configfile:
        config.write(configfile)



def fetch_data():
    global list_tokens
    response = requests.get(urlGetLatestSpotPairs, params=parameters, headers=headers)
    if response.status_code == 200:
        list_tokens = response.json()
    else:
        logger.error(f"Erro ao fazer requisição: {response.status_code}")

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
    global list_tokens
    data = list_tokens
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
    best_tokens = all_data.sort_values(by='score', ascending=False).head(int(get_config_value('NUM_TOKENS_PROCESSED')))
    
    return best_tokens.to_dict(orient='records')

    
    
def buy_tokens(pools):
    logger.info('INICIAR BUY ######################################################################################################################')
    if(int(get_config_value("EXECUTE_OPERATIONS")) == 1):
        top_tokens = []
        global global_percent_change_1h 
        logger.info("BTC 1h % : " + str(global_percent_change_1h))
        if global_percent_change_1h > float(get_config_value('BTC_1H_PERCENT')):
        
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
            if int(get_config_value('ADD_REPEATED')) == 1:
                new_tokens = top_tokens
            else:
                
                for token in top_tokens:
                    if token['symbol'] not in [existing['symbol'] for existing in existing_tokens]:
                        new_tokens.append(token)


            if new_tokens:
                solana_quote = processTokenQuote('5426')

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

                    data = get_price_in_solana(solana_quote['price'], token['price'], float(get_config_value('BUY_VALUE_IN_USD')))
                    solana_amount = data['solana_amount']
                    token_quantity = data['token_quantity']
                    executeSwap = get_config_value("EXECUTE_SWAP")

                    data = {
                        'id': id,
                        'platform_token_address': platform_token_address[0],
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
                        'solana_amount' : solana_amount,
                        'token_amount' : token_quantity,
                        'comprado': '1',
                        'executeSwap': executeSwap
                    }

                    logger.info("--------------------------------------------------------------------------------------------------------------------------- a comprar " + name[0])
                    response = swapToken(data, pools)
                    if response is not None:
                        if(response.status_code == 200):
                            #if response.json().get('txid') is not None:
                            if response.json().get('data') is not None:
                                data['token_amount'] = response.json().get('data').get('quantidadeTokenSaida')
        
                            isInserted = database.insert_buy(data)
                            database.updateNumberBuys()
                        elif response == False or response.status_code != 200:
                            logger.error("Erro ao comprar " + data['name'][0])
                            for token in top_tokens:
                                if token['name'] == data['name'][0]:
                                    top_tokens.remove(token)
                                    break 
                        time.sleep(int(get_config_value('SWAP_EXECUTION'))) 
                database.save_tokens_to_db(top_tokens)
            else:
                logger.info("Nenhuma alteração nos tokens detectada.")
        return top_tokens









def swapToken(swapPairs, pools):
    data = {
        'symbol': swapPairs['symbol'], 
        'name': swapPairs['name'],
    }
    pair_address = get_pair_with_sol(swapPairs['platform_token_address'], pools, logger)

    url = "http://localhost:3000/swap"

    if swapPairs['comprado'] == '1':
        token_amount = swapPairs['solana_amount']
    else:
        token_amount = swapPairs['token_amount']

      
    payload = {
        "pairAdress": pair_address,
        "quoteAsset": swapPairs['platform_token_address'],
        "baseAsset": "So11111111111111111111111111111111111111112",
        "tokenAmount": token_amount,
        "buy": swapPairs['comprado'],
        "executeSwap": swapPairs['executeSwap'],
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        pair_address = payload.get('pairAdress')
        if pair_address is not None:
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            if response.status_code == 200:
                if swapPairs.get('comprado') == '1': 
                    logger.info(f"Swap com sucesso --- {swapPairs['solana_amount']} de SOLANA por {swapPairs['token_amount']} {swapPairs['name']} \033[92mcomprado\033[0m.")
                else:
                    logger.info(f"Swap com sucesso --- {swapPairs['token_amount']} de {swapPairs['name']} por {swapPairs['solana_amount']} de SOLANA \033[91mvendido\033[0m.")
                if(response.json().get('txid') is not None):
                    print(response.json().get('txid'))
            else:
                logger.error(f"Falha na requisição: {response.json()}")
            return response    
        else:
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição: {e}")
        return False


























def sell_tokens(pools):
    logger.info('INICIAR SELL #####################################################################################################################')
    if(int(get_config_value("EXECUTE_OPERATIONS")) == 1):
        tokens_vendidos = []
        resultados_formatados = get_tokens_analyzed_from_db()

        lista_tokens = [token for token in resultados_formatados if token['comprado'] == True]
        
        if lista_tokens:
            solana_quote = processTokenQuote('5426')
            for resultado in lista_tokens:
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
                token_amount = resultado["token_amount"]
                comprado = 0
                gain_percentage_with_current_price = resultado["gain_percentage_with_current_price"]
                gain_percentage_with_max_price = resultado["gain_percentage_with_max_price"]

                solana_amount = get_solana_from_token(solana_quote['price'], current_price, token_amount)

                if(gain_percentage_with_max_price < float(get_config_value('PERCENTAGE_LOSS'))):
                    executeSwap = get_config_value("EXECUTE_SWAP")
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
                        'solana_amount' : solana_amount,
                        'token_amount': token_amount,
                        'comprado': '0',
                        'executeSwap': executeSwap
                    }

                    logger.info("--------------------------------------------------------------------------------------------------------------------------- a vender " + name)
                    response = swapToken(data, pools)
                    if response is not None:
                        if(response.status_code == 200):
                            updatedData  = {
                                'comprado': '0',
                                'val_sol_sell': response.json().get('data').get('quantidadeTokenSaida') if response.json().get('data') is not None else solana_amount
                            } 
                            #sucess = database.delete_buy_token(data)
                            sucess = database.update_buy(updatedData, symbol)
                            tokens_vendidos.append(data)
                            time.sleep(int(get_config_value('SWAP_EXECUTION'))) 
                        elif response == False or response.status_code != 200:
                            logger.error("Erro ao vender " + name)
                else:
                    logger.info(name + f' - ganho:  {gain_percentage_with_current_price}%' )
        else:
            logger.info("DB buy centralized empty.")
        return tokens_vendidos

def get_tokens_analyzed_from_db():
    resultados = database.getTokens()
    
    if resultados:
        resultados_formatados = []
        for row in resultados:
            idk = row[0]
            id = row[1]
            platform_token_address = row[2]
            symbol = row[3]
            name = row[4]
            platform_name = row[5]
            price = row[6]
            min_price = row[7]
            max_price = row[8]
            percent_change_1h = row[9]
            percent_change_24h = row[10]
            volume_24h = row[11]
            market_cap = row[12]
            score = row[13]
            token_amount = row[14]
            comprado = row[15]
            val_sol_sell = row[16]
            
            try:
                token_atual = getTokenMetrics(id)
                time.sleep(int(get_config_value('PAUSE_TOKEN_METRICS')))
                if token_atual:
                    quote = token_atual['quote']['USD']
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
                        'token_amount': token_amount,
                        'comprado': comprado,
                        "gain_percentage_with_current_price": gain_percentage_with_current_price,
                        "gain_percentage_with_max_price": gain_percentage_with_max_price,
                        "val_sol_sell": val_sol_sell
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

    global list_tokens

    token = [element for element in list_tokens["data"] if element["id"] == int(id)]
    if token:
        return token[0]
    """"
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
    """





def processTokenQuote(id):
    global global_percent_change_1h 
    QUOTE = getTokenMetrics(id)
    if QUOTE:
        token_quote = QUOTE

        data = {
            'id': token_quote['id'],
            'symbol': token_quote['symbol'],
            'name': token_quote['name'],
            'platform_name': token_quote['platform'], 
            'price': token_quote['quote']['USD']['price'],
            'percent_change_1h': token_quote['quote']['USD']['percent_change_1h'],
            'percent_change_24h': token_quote['quote']['USD']['percent_change_24h'],
            'percent_change_7d': token_quote['quote']['USD']['percent_change_7d'], 
            'percent_change_30d': token_quote['quote']['USD']['percent_change_30d'],
            'percent_change_60d': token_quote['quote']['USD']['percent_change_60d'],
            'percent_change_90d': token_quote['quote']['USD']['percent_change_90d'],
            'volume_24h': token_quote['quote']['USD']['volume_24h'],
            'market_cap': token_quote['quote']['USD']['market_cap'],
            'slug': token_quote['slug'], 
            'num_market_pairs': token_quote['num_market_pairs'], 
            'date_added': token_quote['date_added'], 
            'max_supply': token_quote['max_supply'],  
            'circulating_supply': token_quote['circulating_supply'], 
            'total_supply': token_quote['total_supply'], 
            'infinite_supply': token_quote['infinite_supply'], 
            'self_reported_circulating_supply': token_quote['self_reported_circulating_supply'],
            'self_reported_market_cap': token_quote['self_reported_market_cap'], 
            'tvl_ratio': token_quote['tvl_ratio'], 
            'last_updated': token_quote['last_updated'], 
        }

        if(token_quote['name'] == 'Bitcoin'):
            global_percent_change_1h = token_quote['quote']['USD']['percent_change_1h']
        

        return data


def get_price_in_solana(solana_value, token_value, amount_in_usd):
    solana_amount = amount_in_usd / solana_value
    token_quantity = amount_in_usd / token_value
    data = {
        'solana_amount': solana_amount,
        'token_quantity': token_quantity
    }
    return data


def get_solana_from_token(solana_value, token_value, token_quantity):
    solana_amount = (token_quantity * token_value) / solana_value
    return solana_amount





def val_sol_wallet():
    lista_tokens = get_tokens_analyzed_from_db()
    soma_total_sol = 0
    if lista_tokens:
        solana_quote = processTokenQuote('5426')
        for token in lista_tokens:
            if token.get('comprado') == True:
                sol_amount = get_solana_from_token(solana_quote['price'], token.get('current_price', 0), token.get('token_amount', 0))
            else:    
                sol_amount = token.get('val_sol_sell', 0)

            soma_total_sol += sol_amount
    data = {}
    numberBuys = database.getNumberBuys()
    if soma_total_sol:
        data = {
            'valor_investido_usd': int(numberBuys) * float(get_config_value('BUY_VALUE_IN_USD')),
            'valor_total_sol': soma_total_sol,
            'valor_total_usd': soma_total_sol * int(solana_quote['price']),
        }
    return data
























def exec_geral(pools):
    fetch_data()
    processTokenQuote('1')
    top_tokens = buy_tokens(pools)
    tokens_vendidos = sell_tokens(pools)
    print('end')


geral_scheduler = None
btc_quote_scheduler = None
buy_scheduler = None
sell_scheduler = None
global_percent_change_1h = 0
pools = None

def schedule_execute(pools):
    logger.info(' A iniciar schedule_execute +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    return functools.partial(exec_geral, pools)

def schedule_btc_quote(id):
    logger.info(' A iniciar schedule_btc_quote ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    return functools.partial(processTokenQuote, id)

def schedule_buy_tokens(pools):
    logger.info(' A iniciar schedule_buy_tokens +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    return functools.partial(buy_tokens, pools)

def schedule_sell_tokens(pools):
    logger.info(' A iniciar schedule_sell_tokens ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    return functools.partial(sell_tokens, pools)

def start_scheduler():
    if(int(get_config_value("EXECUTE_SCHEDULER")) == 1):
        global geral_scheduler
        global pools
        if geral_scheduler is None:
            execute_every_x_minutes = int(get_config_value("SCHEDULER_EXECUTION_BUY"))
            logger.info(f'A iniciar BUY scheduler!!! - Executa de {execute_every_x_minutes} minutos')
            if pools is None: 
                pools = get_pools()
            geral_scheduler = BackgroundScheduler()
            geral_scheduler.add_job(
                schedule_execute(pools), 
                'interval', 
                minutes=execute_every_x_minutes, 
                next_run_time=datetime.now()
            )
            geral_scheduler.start()
            logger.info("Scheduler buy iniciado com sucesso.")
        else:
            geral_scheduler.remove_all_jobs()
            geral_scheduler.shutdown()
            geral_scheduler = None  
            logger.info("Scheduler buy reiniciado com sucesso.")
            start_scheduler_buy()
            
def start_scheduler_btc_quote():
    if(int(get_config_value("EXECUTE_SCHEDULER")) == 1):
        global btc_quote_scheduler
        if btc_quote_scheduler is None:
            execute_every_x_minutes = int(get_config_value("SCHEDULER_EXECUTION_BTC_QUOTE"))
            logger.info(f'A iniciar BTC-Quote scheduler!!! - Executa de {execute_every_x_minutes} minutos')
            btc_quote_scheduler = BackgroundScheduler()
            btc_quote_scheduler.add_job(
                schedule_btc_quote('1'), 
                'interval', 
                minutes=execute_every_x_minutes, 
                next_run_time=datetime.now()
            )
            btc_quote_scheduler.start()
            logger.info("Scheduler btc quote iniciado com sucesso.")
        else:
            btc_quote_scheduler.remove_all_jobs()
            btc_quote_scheduler.shutdown() 
            btc_quote_scheduler = None 
            logger.info("Scheduler btc quote reiniciado com sucesso.")
            start_scheduler_btc_quote()

def start_scheduler_buy():
    if(int(get_config_value("EXECUTE_SCHEDULER")) == 1):
        global buy_scheduler
        global pools
        if buy_scheduler is None:
            execute_every_x_minutes = int(get_config_value("SCHEDULER_EXECUTION_BUY"))
            logger.info(f'A iniciar BUY scheduler!!! - Executa de {execute_every_x_minutes} minutos')
            if pools is None: 
                pools = get_pools()
            buy_scheduler = BackgroundScheduler()
            buy_scheduler.add_job(
                schedule_buy_tokens(pools), 
                'interval', 
                minutes=execute_every_x_minutes, 
                next_run_time=datetime.now()
            )
            buy_scheduler.start()
            logger.info("Scheduler buy iniciado com sucesso.")
        else:
            buy_scheduler.remove_all_jobs()
            buy_scheduler.shutdown()
            buy_scheduler = None  
            logger.info("Scheduler buy reiniciado com sucesso.")
            start_scheduler_buy()

def start_scheduler_sell():
    if(int(get_config_value("EXECUTE_SCHEDULER")) == 1):
        global sell_scheduler
        global pools
        if sell_scheduler is None:
            execute_every_x_minutes = int(get_config_value("SCHEDULER_EXECUTION_SELL"))
            logger.info(f'A iniciar SELL scheduler!!! - Executa de {execute_every_x_minutes} minutos')
            if pools is None:
                pools = get_pools()
            sell_scheduler = BackgroundScheduler()
            sell_scheduler.add_job(
                schedule_sell_tokens(pools), 
                'interval', 
                minutes=execute_every_x_minutes, 
                next_run_time=datetime.now()
            )
            sell_scheduler.start()
            logger.info("Scheduler sell iniciado com sucesso.")
        else:
            sell_scheduler.remove_all_jobs()
            sell_scheduler.shutdown() 
            sell_scheduler = None
            logger.info("Scheduler sell reiniciado com sucesso.")
            start_scheduler_sell()

def restart_all_schedulers():
    global btc_quote_scheduler, buy_scheduler, sell_scheduler, geral_scheduler, pools
    if geral_scheduler:
        geral_scheduler.remove_all_jobs()
        geral_scheduler.shutdown() 
        geral_scheduler = None 
        logger.info("Scheduler btc quote removido.")
    if btc_quote_scheduler:
        btc_quote_scheduler.remove_all_jobs()
        btc_quote_scheduler.shutdown() 
        btc_quote_scheduler = None 
        logger.info("Scheduler btc quote removido.")
    if buy_scheduler:
        buy_scheduler.remove_all_jobs()
        buy_scheduler.shutdown() 
        buy_scheduler = None  
        logger.info("Scheduler buy removido.")
    if sell_scheduler:
        sell_scheduler.remove_all_jobs()
        sell_scheduler.shutdown()  
        sell_scheduler = None 
        logger.info("Scheduler sell removido.")

    start_scheduler()
    #start_scheduler_btc_quote()
    #start_scheduler_buy()
    #start_scheduler_sell()

@app.route('/restart-schedulers', methods=['GET'])
def restart_schedulers():
    try:
        restart_all_schedulers()
        return jsonify({"estado": "Sucesso", "mensagem": "Todos os schedulers foram reiniciados com sucesso."}), 200
    except Exception as e:
        return jsonify({"estado": "Erro", "mensagem": f"Erro ao reiniciar schedulers: {str(e)}"}), 500

if __name__ == '__main__':
    try:
        pools = get_pools()
        start_scheduler()
        #start_scheduler_btc_quote()
        #start_scheduler_buy()
        #start_scheduler_sell()
        #print('Schedulers iniciados com sucesso!')
    except Exception as e:
        logger.error(f"Error: {e}.")

    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

