import importlib
from flask import Flask, jsonify, request, g
import requests
import pandas as pd
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import logging
import configparser

database = importlib.import_module("dex_database")

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

# Leitura do arquivo de configurações
config = configparser.ConfigParser()
config.read('config.centralized.properties')

# Obter a URL do arquivo de configurações
urlGetLatestSpotPairs = config.get('SOLANA', 'urlGetLatestSpotPairs')
urlGetTokenByBaseAssetContractAddress = config.get('SOLANA', 'urlGetTokenByBaseAssetContractAddress')
serverUrl = config.get('SOLANA', 'serverUrl')
SCHEDULER_EXECUTION = config.get('SOLANA', 'SCHEDULER_EXECUTION')
SWAP_EXECUTION = config.get('SOLANA', 'SWAP_EXECUTION')
PERCENTAGE_LOSS = config.get('SOLANA', 'PERCENTAGE_LOSS')

parameters = {
    'start': '1',
    'limit': '100'  # Aumentamos o limite para pegar mais tokens TODO - Aumentar
}
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': 'ff716c6f-21b5-4f8c-850d-8c5b2792e9a2',  # Substitua com sua chave
}



@app.route('/top10', methods=['GET'])
def get_top10():
    get_top_10_1h()
    return jsonify({'sucess': 'Operation with sucess'}), 200
    

@app.route('/best-tokens', methods=['GET'])
def get_best_tokens_endpoint():
    # Pesos para os tokens "best"
    score_weights = {
        'percent_change_1h': 0.5,
        'percent_change_24h': 0.5,
        'volume_24h': 0.2,
        'market_cap': 0.2,
        'liquidity': 0.3
    }
    
    best_tokens = process_tokens(score_weights)

    if best_tokens:
        return jsonify(best_tokens), 200
    else:
        return jsonify({'error': 'Unable to fetch data'}), 500
    
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
    

@app.route('/get-tokens', methods=['GET'])
def getTokens():
    resultados_formatados = get_tokens_analyzed_from_db()
    return jsonify(resultados_formatados), 200



@app.route('/buy-token', methods=['GET'])
def getBuyToken():
    
    base_asset_contract_address = request.args.get('baseAssetContractAddress')
    name = request.args.get('name')
    price = float(request.args.get('price'))
    buy_date = datetime.now()
    
    data = (base_asset_contract_address, name, price, buy_date) 
    isInserted = database.insert_buy(data)
    
    if isInserted:
        return jsonify({'sucess': 'Buy realized'}), 200
    else:
        return jsonify({'error': 'Unable to buy'}), 500
    

@app.route('/delete-token', methods=['GET'])
def deleteToken():
    """
    Rota para excluir um token da tabela 'dex' com base no 'contract_address'.
    :return: Resposta de sucesso ou erro
    """
    # Obtém o 'contract_address' a partir dos parâmetros de consulta da URL
    contract_address = request.args.get('baseAssetContractAddress')

    if not contract_address:
        return jsonify({'error': 'contractAddress is required'}), 400

    # Chama a função delete_token para excluir o token da tabela 'dex'
    isDeleted = database.delete_token(contract_address)

    if isDeleted:
        return jsonify({'success': 'Token deleted successfully'}), 200
    else:
        return jsonify({'error': 'Unable to delete token'}), 500
    













































def fetch_token_data(base_asset_contract_address):
    url = urlGetTokenByBaseAssetContractAddress + base_asset_contract_address + '&quote_asset_contract_address=So11111111111111111111111111111111111111112'
    response = requests.get(url, params=parameters, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao fazer requisição: {response.status_code}")
        print(f"Response Text: {response.text}")
        logger.error(f"Erro ao fazer requisição: {response.status_code}")
        logger.error(f"Response Text: {response.text}")
        return None
    
# Função para pegar os dados da API
def fetch_data():
    response = requests.get(urlGetLatestSpotPairs, params=parameters, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao fazer requisição: {response.status_code}")
        print(f"Response Text: {response.text}")
        logger.error(f"Erro ao fazer requisição: {response.status_code}")
        logger.error(f"Response Text: {response.text}")
        return None

# Função comum para calcular a pontuação do token
def calculate_score(token, score_weights):
    # Pegando os dados principais do 'quote'
    quote = token['quote'][0]  # Aqui pegamos o primeiro item de 'quote' para compatibilidade com o novo formato
    price = quote['price']
    volume_24h = quote['volume_24h']
    percent_change_1h = quote.get('percent_change_price_1h', 0)
    percent_change_24h = quote.get('percent_change_price_24h', 0)
    market_cap = quote.get('fully_diluted_value', 0)

    # A pontuação será calculada com base nas variações e volume de mercado
    score = 0
    
    # Aplicando os pesos configurados para cada critério
    score += percent_change_1h * score_weights['percent_change_1h']
    score += percent_change_24h * score_weights['percent_change_24h']
    score += (volume_24h / 1e6) * score_weights['volume_24h']
    score += ((market_cap or 0) / 1e9) * score_weights['market_cap']
    

    # Liquidez (volume 24h / market cap), se market_cap for maior que 0
    if market_cap is not None and market_cap > 0:
        liquidity = volume_24h / market_cap
        score += liquidity * score_weights['liquidity']
    
    return score

# Função para processar os tokens e calcular suas pontuações
def process_tokens(score_weights):
    data = fetch_data()
    if not data:
        return []

    all_data = pd.DataFrame()

    # Iterando sobre os dados e calculando a pontuação
    for token in data['data']:
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
            'platform': token['platform'],
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
            'last_updated': token['quote']['USD']['last_updated']
        }

        # Calcular a pontuação do token
        token_data['score'] = calculate_score(token, score_weights)

        # Adicionar o token com a pontuação ao DataFrame
        row = pd.DataFrame([token_data])

            # Remover colunas com todos os valores NaN
        row = row.dropna(axis=1, how='all')

        all_data = pd.concat([all_data, row], ignore_index=True)

    # Ordenando os tokens pela pontuação, da maior para a menor
    best_tokens = all_data.sort_values(by='score', ascending=False).head(10)
    
    # Retornando os 10 melhores tokens
    melhores_tokens = best_tokens[['id',
                                    'contract_address',
                                    'name',
                                    'symbol',
                                    'slug',
                                    'num_market_pairs',
                                    'date_added',
                                    'max_supply',
                                    'circulating_supply',
                                    'total_supply',
                                    'infinite_supply',
                                    'platform',
                                    'cmc_rank',
                                    'self_reported_circulating_supply',
                                    'self_reported_market_cap',
                                    'network_id',
                                    'network_slug',
                                    'last_updated',
                                    'created_at',
                                    'convert_id',
                                    'price',
                                    'volume_24h',
                                    'percent_change_1h',
                                    'percent_change_24h',
                                    'percent_change_price_24h',
                                    'market_cap',
                                    'fully_diluted_market_cap',
                                    'last_updated']].to_dict(orient='records')
    #print(json.dumps(melhores_tokens, indent=4))  # Imprime o JSON com indentação
    
    return melhores_tokens















































def get_top_10_1h():
    score_weights = {
        'percent_change_1h': 1.0,
        'percent_change_24h': 0.0,
        'volume_24h': 0.0,
        'market_cap': 0.0,
        'liquidity': 0.0
    }

    top_tokens = process_tokens(score_weights)

    # Aqui você deve fazer a comparação com os tokens antigos na base de dados
    # Vou assumir que a função 'save_tokens_to_db' vai salvar no banco e 'get_existing_tokens' vai pegar os tokens existentes
    existing_tokens = database.get_existing_tokens()

    new_tokens = []
    for token in top_tokens:
        if token['base_asset_contract_address'] not in [existing['base_asset_contract_address'] for existing in existing_tokens]:
            new_tokens.append(token)

    if new_tokens:
        print("Novos tokens detectados:")
        for token in new_tokens:
            print(token['name'])
            base_asset_contract_address = token['base_asset_contract_address']
            contract_address = token['contract_address']
            quote_asset_contract_address = token['quote_asset_contract_address']
            name = token['name']
            price = float(token['price'])
            buy_date = datetime.now()
            created_at = token['created_at']
            volume_24h = float(token['volume_24h'])
            liquidity = float(token['liquidity'])
            quantity = 0.05
            comprado = 'true'
            data = {
                'base_asset_contract_address': base_asset_contract_address,
                'contract_address': contract_address,
                'quote_asset_contract_address': quote_asset_contract_address,
                'name': name,
                'price': price,
                'buy_date': buy_date,
                'created_at': created_at,
                'volume_24h': volume_24h,
                'liquidity': liquidity,
                'quantity': quantity,
                'comprado': comprado
            }
            sucess = swapToken(data)
            #sucess = True
            if(sucess):
                isInserted = database.insert_buy(data)
            else:
                print("Erro ao comprar " + data['name'])
                logger.error("Erro ao comprar " + data['name'])
            time.sleep(int(SWAP_EXECUTION)) 

        # Atualizar banco de dados para ter apenas os 10 tokens mais recentes
        database.save_tokens_to_db(top_tokens)

    else:
        print("Nenhuma alteração nos tokens detectada.")


def swapToken(swapPairs):
    data = {
        'pairAdress': swapPairs['contract_address'],  
        'quoteAsset': swapPairs['quote_asset_contract_address'], 
        'baseAsset': swapPairs['base_asset_contract_address'], 
        'name': swapPairs['name'],
        'buy': swapPairs['comprado'],
    }
    response = requests.post(serverUrl, json=data)
    if response.status_code == 200:
        if data['buy'] == 'true':  # Aqui assumimos que 'comprado' é uma string 'true'
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



def get_tokens_analyzed_from_db():
    resultados = database.getTokens()
    
    if resultados:
        resultados_formatados = []

        for row in resultados:
            base_asset_contract_address = row[0]
            contract_address = row[1]
            quote_asset_contract_address = row[2]
            name = row[3]
            price = row[4]
            buy_date = row[5]
            created_at = row[6]
            volume_24h = row[7]
            liquidity = row[8]
            quantity = row[9]
            comprado = row[10]

            try:
                # Chama a função fetch_token_data para obter os dados atualizados
                token_atual = fetch_token_data(base_asset_contract_address)
                
                # Verifica se a resposta foi válida e contém os dados esperados
                if token_atual and 'data' in token_atual and len(token_atual['data']) > 0:
                    quote = token_atual['data'][0].get('quote', [])
                    if quote:
                        price_atual = quote[0].get('price')  # Aqui você usa o get para evitar erros se a chave não existir
                    
                    # Calcula a percentagem de ganho
                    if price_atual and price:
                        ganho_percentual = ((price_atual - price) / price) * 100
                    else:
                        ganho_percentual = 0

                    # Formata o resultado com os valores e a percentagem de ganho
                    resultado_formatado = {
                        "base_asset_contract_address": base_asset_contract_address,
                        "contract_address": contract_address,
                        "quote_asset_contract_address": quote_asset_contract_address,
                        "name": name,
                        "price": price,
                        "buy_date": buy_date,
                        "created_at" : created_at,
                        "volume_24h" : volume_24h,
                        "liquidity" : liquidity,
                        "quantity" : quantity,
                        "comprado" : comprado,
                        "current_price": price_atual,
                        "gain_percentage": ganho_percentual
                    }
                    resultados_formatados.append(resultado_formatado)
                else:
                    continue   
            except Exception as e:
                # Caso ocorra algum erro, ele será capturado aqui
                print(f"Erro ao processar o token {base_asset_contract_address}: {e}. Continuando para o próximo token.")
                logger.error(f"Erro ao processar o token {base_asset_contract_address}: {e}. Continuando para o próximo token.")
                continue
        return resultados_formatados
    else:
        return "wallet vazia"
    



def sell_tokens():
    resultados_formatados = get_tokens_analyzed_from_db()

    # Iterando sobre cada dicionário na lista
    for resultado in resultados_formatados:
        # Acessando os dados dentro de cada dicionário
        base_asset_contract_address = resultado["base_asset_contract_address"]
        contract_address = resultado["contract_address"]
        quote_asset_contract_address = resultado["quote_asset_contract_address"]
        name = resultado["name"]
        price = resultado["price"]
        buy_date = resultado["buy_date"]
        created_at = resultado["created_at"]
        volume_24h = resultado["volume_24h"]
        liquidity = resultado["liquidity"]
        quantity = resultado["quantity"]
        comprado = resultado["comprado"]
        current_price = resultado["current_price"]
        gain_percentage = resultado["gain_percentage"]

        if(gain_percentage < -PERCENTAGE_LOSS):
            resultado["comprado"] = False

            comprado = 'false'
            data = {
                'base_asset_contract_address': base_asset_contract_address,
                'contract_address': contract_address,
                'quote_asset_contract_address': quote_asset_contract_address,
                'name': name,
                'comprado': comprado
            }
            sucess = swapToken(data)

            if(sucess):
                updatedData  = {
                    'comprado': comprado
                } 
                sucess = database.update_buy(updatedData, contract_address)
                time.sleep(SWAP_EXECUTION) 
            else:
                print("Erro ao comprar " + name)
                logger.error("Erro ao comprar " + name)
        else:
            print(name + " tem saldo positivo.")


























































def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduler_worker, 'interval', minutes=SCHEDULER_EXECUTION)  # Executar a cada 10 minutos
    scheduler.start()

# Variável global para controlar se o processo está em execução
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



@app.route('/teste-scheduler', methods=['GET'])
def testeScheduler():
    try:
        get_top_10_1h()
        sell_tokens()
        return jsonify({"estado": "Sucesso"}), 200
    except Exception as e:
        print(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500
    

        
@app.route('/teste-vender', methods=['GET'])
def testeVender():
    try:
        sell_tokens()
        return jsonify({"estado": "Sucesso"}), 200
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
    
    print("-------")
    #app.run(host='0.0.0.0', port=5002, debug=True) TODO
    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)
    
