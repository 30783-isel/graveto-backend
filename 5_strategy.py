from flask import Flask, jsonify, request
import requests
import pandas as pd
import json
import time
import importlib
from datetime import datetime
import logging
import configparser
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
SCHEDULER_EXECUTION = config.get(type, 'SCHEDULER_EXECUTION')
SWAP_EXECUTION = config.get(type, 'SWAP_EXECUTION')
PERCENTAGE_LOSS = config.get(type, 'PERCENTAGE_LOSS')

# Definir URL e parâmetros da API
# https://sandbox-api.coinmarketcap.com

parameters = {
    'start': '1',
    'limit': '300'  # Aumentamos o limite para pegar mais tokens
}
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': 'ff716c6f-21b5-4f8c-850d-8c5b2792e9a2',  # Substitua com sua chave
}


# Função para pegar os dados da API
def fetch_data():
    response = requests.get(urlGetLatestSpotPairs, params=parameters, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao fazer requisição: {response.status_code}")
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
        else:
            platform_id = platform_name = platform_slug = platform_symbol = None

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
        all_data = pd.concat([all_data, row], ignore_index=True)

    # Ordenando os tokens pela pontuação, da maior para a menor
    best_tokens = all_data.sort_values(by='score', ascending=False).head(10)
    
    # Retornando os 10 melhores tokens
    melhores_tokens = best_tokens[['id',
                                    'name',
                                    'symbol',
                                    'slug',
                                    'num_market_pairs',
                                    'date_added',
                                    'max_supply',
                                    'circulating_supply',
                                    'total_supply',
                                    'infinite_supply',
                                    'platform_id',
                                    'platform_name',
                                    'platform_slug',
                                    'platform_symbol',
                                    'cmc_rank',
                                    'self_reported_circulating_supply',
                                    'self_reported_market_cap',
									'last_updated',
                                    'price',
                                    'volume_24h',
                                    'percent_change_1h',
                                    'percent_change_24h',
                                    'market_cap',
									'market_cap_dominance',
                                    'fully_diluted_market_cap',
                                    'last_updated_quote',
    'score']].to_dict(orient='records')
    #print(json.dumps(melhores_tokens, indent=4))  # Imprime o JSON com indentação
    
    return best_tokens.to_dict(orient='records')

    
    
def get_top_10_1h():
    # Pesos para os tokens "best"
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
        print("Novos tokens detectados:")
        for token in new_tokens:
            print(token['name'])
            symbol = token['symbol'],
            name = token['name'],
            platform_name = token['platform_name'],
            price = token['price'],
            percent_change_1h = token.get('percent_change_1h', None),
            percent_change_24h = token.get('percent_change_24h', None),
            volume_24h = token['volume_24h'],
            market_cap = token['market_cap'],
            score = token['score'],
            data = {
                'symbol': symbol,
                'name': name,
                'platform_name': platform_name,
                'price': price,
                'percent_change_1h': percent_change_1h,
                'percent_change_24h': percent_change_24h,
                'volume_24h': volume_24h,
                'market_cap': market_cap,
                'score': score,
                'comprado': True,
            }

            sucess = swapToken(data)
            #sucess = True
            if(sucess):
                isInserted = database.insert_buy(data)
            else:
                logger.error("Erro ao comprar " + data['name'])
            time.sleep(int(SWAP_EXECUTION)) 

        # Atualizar banco de dados para ter apenas os 10 tokens mais recentes
        database.save_tokens_to_db(top_tokens)

    else:
        print("Nenhuma alteração nos tokens detectada.")
    return top_tokens



def getTokenMetrics(symbol):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    params = {
        'symbol': symbol,
        'convert': 'USD'
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        
        token_price = data['data'][symbol]['quote']['USD']['price']
        print(f" ${symbol} - ${token_price}")
        return data
    else:
        print(f"Erro ao acessar a API: {response.status_code}")
















def get_tokens_analyzed_from_db():
    resultados = database.getTokens()
    
    if resultados:
        resultados_formatados = []
        for row in resultados:
            symbol = row[0]
            name = row[1]
            platform_name = row[2]
            price = row[3]
            percent_change_1h = row[4]
            percent_change_24h = row[5]
            volume_24h = row[6]
            market_cap = row[7]
            score = row[8]
            comprado = row[9]

            try:
                # Chama a função fetch_token_data para obter os dados atualizados
                token_atual = getTokenMetrics(symbol)
                
                # Verifica se a resposta foi válida e contém os dados esperados
                if token_atual and 'data' in token_atual and len(token_atual['data']) > 0:
                    quote = token_atual['data'][symbol]['quote']['USD']
                    if quote:
                        price_atual = quote.get('price')  # Aqui você usa o get para evitar erros se a chave não existir
                    
                    # Calcula a percentagem de ganho
                    if price_atual and price:
                        ganho_percentual = ((price_atual - price) / price) * 100
                    else:
                        ganho_percentual = 0

                    # Formata o resultado com os valores e a percentagem de ganho
                    resultado_formatado = {
                        'symbol': symbol,
                        'name': name,
                        'platform_name': platform_name,
                        'price': price,
                        'percent_change_1h': percent_change_1h,
                        'percent_change_24h': percent_change_24h,
                        'volume_24h': volume_24h,
                        'market_cap': market_cap,
                        'score': score,
                        'comprado': comprado,
                        "gain_percentage": ganho_percentual
                    }
                    
                    resultados_formatados.append(resultado_formatado)
                else:
                    continue   
            except Exception as e:
                # Caso ocorra algum erro, ele será capturado aqui
                print(f"Erro ao processar o token {symbol}: {e}. Continuando para o próximo token.")
                logger.error(f"Erro ao processar o token {symbol}: {e}. Continuando para o próximo token.")
                continue
        return resultados_formatados
    else:
        return []





def sell_tokens():
    resultados_formatados = get_tokens_analyzed_from_db()
    
    if resultados_formatados:
        for resultado in resultados_formatados:
            symbol = resultado.get('symbol', None)
            name = resultado["name"]
            platform_name = resultado["platform_name"]
            price = resultado["price"]
            percent_change_1h = resultado["percent_change_1h"]
            percent_change_24h = resultado["percent_change_24h"]
            volume_24h = resultado["volume_24h"]
            market_cap = resultado["market_cap"]
            score = resultado["score"]
            comprado = resultado["comprado"]
            gain_percentage = resultado["gain_percentage"]

            if(gain_percentage < -float(PERCENTAGE_LOSS)):
                data = {
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
                sucess = swapToken(data)

                if(sucess):
                    updatedData  = {
                        'comprado': comprado
                    } 
                    #sucess = database.update_buy(updatedData, symbol)
                    time.sleep(int(SWAP_EXECUTION)) 
                else:
                    print("Erro ao comprar " + name)
                    logger.error("Erro ao comprar " + name)
            else:
                print(name + f' tem saldo positivo {gain_percentage}%' )
    else:
        print("DB buy centralized empty.")















def swapToken(swapPairs):
    data = {
        'symbol': swapPairs['symbol'], 
        'name': swapPairs['name'],
    }
    response = requests.post(serverUrl, json=data)
    if response.status_code == 200:
        if swapPairs.get('comprado'):  # Aqui assumimos que 'comprado' é uma string 'true'
            # Usamos códigos ANSI para colorir "comprado" em vermelho
            print(f"Swap com sucesso --- Token: {data['name']} \033[92mcomprado\033[0m.")
        else:
            print(f"Swap com sucesso --- Token: {data['name']} \033[91mvendido\033[0m.")
        return True
    else:
        print(f'Erro na requisição: {response.status_code}')
        print('Detalhes:', response.json())
        logger.error(f'Erro na requisição: {response.status_code}')
        logger.error('Detalhes:', response.json())
        return False



def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduler_worker, 'interval', minutes=int(SCHEDULER_EXECUTION))  # Executar a cada 10 minutos
    scheduler.start()

is_running = False

def scheduler_worker():
    global is_running

    # Verificar se já está em execução
    if is_running:
        print("Scheduler já está em execução. Pulando execução.")
        return

    try:
        # Marcar como em execução
        is_running = True
        print("Iniciando execução do scheduler...")

        # Funções do scheduler
        get_top_10_1h()
        sell_tokens()

        print("Execução do scheduler finalizada.")

    except Exception as e:
        print(f"Erro ao executar o scheduler: {e}")

    finally:
        # Marcar como não em execução
        is_running = False


@app.route('/best-tokens', methods=['GET'])
def get_best_tokens_endpoint():
    try:
        top_tokens = get_top_10_1h()
        sell_tokens() 
        return jsonify(top_tokens), 200
    except Exception as e:
        print(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500
    


if __name__ == '__main__':
    try:
        # Verifique se a aplicação está sendo executada diretamente e não através de importação
        if not hasattr(app, 'has_started'):
            app.has_started = True
            #start_scheduler()  # Inicia o scheduler uma única vez
    except Exception as e:
        print(f"Error: {e}.")

    app.run(host='0.0.0.0', port=5000, debug=True)














































@app.route('/top-tokens', methods=['GET'])
def get_top_tokens_endpoint():
    # Pesos para os tokens "top"
    score_weights = {
        'percent_change_1h': 0.5,
        'percent_change_24h': 0.5,
        'volume_24h': 0.0,
        'market_cap': 0.0,
        'liquidity': 0.0
    }

    top_tokens = process_tokens(score_weights)
    
    if top_tokens:
        return jsonify(top_tokens), 200
    else:
        return jsonify({'error': 'Unable to fetch data'}), 500


@app.route('/get-token', methods=['GET'])
def getToken():
    name = request.args.get('name')
    resultados = database.getToken(name)
    
    print(resultados)
    
    if resultados:
        # Transformando os resultados para uma lista de dicionários
        resultados_formatados = [{"id": row[0], "cmc_rank": row[1], "name": row[2], "market_cap": row[3], 
                                  "price": row[4], "buy_date": row[5], "quantity": row[6]} for row in resultados]
        return jsonify(resultados_formatados), 200
    else:
        return jsonify({'error': 'Unable to fetch data'}), 500


@app.route('/buy-token', methods=['GET'])
def getBuyToken():
    
    name = request.args.get('name')
    cmc_rank = int(request.args.get('cmc_rank'))
    market_cap = float(request.args.get('market_cap'))
    price = float(request.args.get('price'))
    buy_date = datetime.now()
    quantity = int(1)
    
    data = (name, cmc_rank, market_cap, price, buy_date, quantity) 
    isInserted = database.insert_buy(data)
    
    if isInserted:
        return jsonify({'sucess': 'Buy realized'}), 200
    else:
        return jsonify({'error': 'Unable to buy'}), 500