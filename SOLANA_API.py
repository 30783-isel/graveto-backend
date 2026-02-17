from flask import Blueprint, jsonify, request
from SOLANA import *

solana_api = Blueprint("solana_api", __name__)

@solana_api.before_request
def limit_remote_addr():
    client_ip = request.remote_addr  #100.100.94.97
    if client_ip.startswith('87.') or client_ip.startswith('89.')  or client_ip.startswith('172.') or client_ip.startswith('192.168.')  or client_ip == '100.100.94.97'  or client_ip == '100.105.58.42'  or client_ip == '127.0.0.1':
        return None
    logger.error('Bloqueado Ip - ' + client_ip)
    return jsonify({"estado": "Erro", "mensagem": "IP não autorizado"}), 403


@solana_api.route('/best-tokens', methods=['GET'])
def get_best_tokens_endpoint():
    try:
        global pools
        if pools is None:
            pools = get_pools() 
        top_tokens = buy_tokens(pools)
        sell_tokens(pools) 
        return jsonify(top_tokens), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500



@solana_api.route('/buy-sell-tokens', methods=['GET'])
def buy_sell_tokens_call():
    try:
        global pools
        if pools is None:
            pools = get_pools() 
        top_tokens = buy_sell_tokens(pools)
        return jsonify(top_tokens), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500 
    

@solana_api.route('/buy-tokens', methods=['GET'])
def buy_tokens_call():
    try:
        global pools
        fetch_data()
        if pools is None:
            pools = get_pools() 
        top_tokens = buy_tokens(pools)
        return jsonify(top_tokens), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500   

@solana_api.route('/sell-tokens', methods=['GET'])
def sell_tokens_call():
    try:
        global pools
        fetch_data()
        tokens_vendidos = sell_tokens(pools) 
        return jsonify(tokens_vendidos), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500   

@solana_api.route('/get-tokens', methods=['GET'])
def getTokens():
    resultados_formatados = get_tokens_analyzed_from_db()
    return jsonify(resultados_formatados), 200


@solana_api.route('/get-btc-quote', methods=['GET'])
def getBTCQuote():
    try:
        data = processTokenQuote('1')
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500


@solana_api.route('/get-solana-quote', methods=['GET'])
def getSolanaQuote():
    try:
        data = processTokenQuote('5426')
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500



@solana_api.route('/get-value-quantity', methods=['GET'])
def getValueQuantity():
    try:
        solana = processTokenQuote('5426')
        token = processTokenQuote('21870')
        data = get_price_in_solana(solana['price'], token['price'], float(get_config_value('BUY_VALUE_IN_USD')))
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500



@solana_api.route('/get-sol-wallet', methods=['GET'])
def get_sol_wallet_value():
    try:
        data = val_sol_wallet()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500
    

@solana_api.route('/clean-slate', methods=['GET'])
def getCleanSlate():
    try:
        data = database.clean_slate()
        return jsonify({"estado": "Sucesso"}), 200
    except Exception as e:
        logger.error(f"Error: {e}.")
        return jsonify({"estado": "Erro"}), 500
    






@solana_api.route('/get-config', methods=['GET'])
def get_config_endpoint():
    try:
        config_data = {
            "SCHEDULER_EXECUTION_BUY": int(get_config_value('SCHEDULER_EXECUTION_BUY')),
            "SWAP_EXECUTION": int(get_config_value('SWAP_EXECUTION')),
            "PERCENTAGE_LOSS": float(get_config_value('PERCENTAGE_LOSS')),
            "NUM_TOKENS_PROCESSED": int(get_config_value('NUM_TOKENS_PROCESSED')),
            "NUM_TOKENS_COINMARKETCAP": int(get_config_value('NUM_TOKENS_COINMARKETCAP')),
            "BTC_1H_PERCENT": float(get_config_value('BTC_1H_PERCENT')),
            "NAME_MAIN_TOKEN": str(get_config_value('NAME_MAIN_TOKEN')),
            "BUY_VALUE_IN_USD":float( get_config_value('BUY_VALUE_IN_USD')),
            "EXECUTE_OPERATIONS": int(get_config_value('EXECUTE_OPERATIONS')),
            "EXECUTE_SCHEDULER": int(get_config_value('EXECUTE_SCHEDULER')),
            "ADD_REPEATED": int(get_config_value('ADD_REPEATED')),
            "EXECUTE_SWAP": int(get_config_value('EXECUTE_SWAP'))
        }
        return jsonify(config_data), 200

    except Exception as e:
        return jsonify({"estado": "Erro", "mensagem": str(e)}), 500






@solana_api.route('/update-config', methods=['POST'])
def update_config_endpoint():
    try:
        print('teste')
        data = request.get_json()

        if not data:
            return jsonify({"estado": "Erro", "mensagem": "Nenhum dado enviado."}), 400

        config = read_config()

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
        if 'NAME_MAIN_TOKEN' in data:
            config.set('CENTRALIZED', 'NAME_MAIN_TOKEN', str(data['NAME_MAIN_TOKEN']))           
        if 'BTC_1H_PERCENT' in data:
            config.set('CENTRALIZED', 'BTC_1H_PERCENT', str(data['BTC_1H_PERCENT']))
        if 'BUY_VALUE_IN_USD' in data:
            config.set('CENTRALIZED', 'BUY_VALUE_IN_USD', str(data['BUY_VALUE_IN_USD']))
        if 'EXECUTE_OPERATIONS' in data:
            config.set('CENTRALIZED', 'EXECUTE_OPERATIONS', str(data['EXECUTE_OPERATIONS']))
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




# Função de chamada de API
@solana_api.route('/get-wallet-tokens', methods=['GET'])
def get_wallet_tokens():
    return getWalletTokensValuesX()
	
	
	
# Função de chamada de API
@solana_api.route('/get-sol-balance', methods=['GET'])
def get_sol_balance():
    return get_sol_bal()
	
@solana_api.route('/get-sol-reserved-balance', methods=['GET'])
def get_sol_reserved_balance():
    return getSOLReservedBalance()	
	
	
@solana_api.route('/infscl-init', methods=['POST'])
def getInfsclInit():
    try:
        global infisicaClient
        # Obter os dados do corpo da requisição (espera-se JSON)
        data = request.get_json()

        # Verificar se os dados foram enviados e extrair client_id e client_secret
        if not data or 'client_id' not in data or 'client_secret' not in data:
            return jsonify({
                "estado": "Erro",
                "mensagem": "client_id e client_secret são obrigatórios no corpo da requisição."
            }), 400

        client_id = data['client_id']
        client_secret = data['client_secret']

        # Inicializar o client
        infisicaClient = InfisicalSDKClient(host="https://eu.infisical.com")

        # Autenticar usando os valores fornecidos na requisição
        infisicaClient.auth.universal_auth.login(
            client_id=client_id, 
            client_secret=client_secret
        )
        
        return jsonify({
            "estado": "Sucesso"
        }), 200

    except Exception as e:
        return jsonify({
            "estado": "Erro",
            "mensagem": str(e)
        }), 500
        
                 
@solana_api.route('/infscl-get-secret', methods=['POST'])
def getInfsclGetSecret():
    try:
        global infisicaClient
        # Obter os dados do corpo da requisição (espera-se JSON)
        data = request.get_json()

        # Verificar se os dados foram enviados e extrair secret_name e project_id
        if not data or 'secret_name' not in data or 'project_id' not in data:
            return jsonify({
                "estado": "Erro",
                "mensagem": "secret_name e project_id são obrigatórios no corpo da requisição."
            }), 400

        secret_name = data['secret_name']
        project_id = data['project_id']

        # Buscar o segredo
        secret = infisicaClient.secrets.get_secret_by_name(
            secret_name=secret_name,
            project_id=project_id,
            environment_slug="dev",
            secret_path="/"
        )
        
        return jsonify({
            "estado": "Sucesso",
            "secret": secret.secretValue  # Inclui o valor do segredo na resposta
        }), 200

    except Exception as e:
        return jsonify({
            "estado": "Erro",
            "mensagem": str(e)
        }), 500




@solana_api.route('/get-token-data', methods=['GET'])
def getTokenDataEndpoint():
    response = getTokenData()
    return jsonify({"status": "ok", "data": response})
	

@solana_api.route('/update-token-data', methods=['GET'])
def updateTokenDataEndpoint():
    response = updateTokenData()
    return jsonify({"status": "ok", "data": response})


	
@solana_api.route('/restart-schedulers', methods=['GET'])
def restart_schedulers():
    try:
        restart_all_schedulers()
        return jsonify({"estado": "Sucesso", "mensagem": "Todos os schedulers foram reiniciados com sucesso."}), 200
    except Exception as e:
        return jsonify({"estado": "Erro", "mensagem": f"Erro ao reiniciar schedulers: {str(e)}"}), 500

@solana_api.route('/test-certificate')
def hello():
    cert = request.environ.get('SSL_CLIENT_CERT')
    if cert:
        return jsonify(message="Ligação segura com mTLS estabelecida!"), 200
    return jsonify(error="Certificado cliente não encontrado."), 403




@solana_api.route('/test')
def helloWordl():
    connection = getTestConnection()
    if connection:
        return jsonify(message="Ligação segura com mTLS estabelecida!"), 200
    return jsonify(error="Falha na ligação."), 403




@solana_api.route('/fear-and-greed')
def fear_and_greed_index():
    API_KEY = 'ff716c6f-21b5-4f8c-850d-8c5b2792e9a2'
    result = get_fear_and_greed_index(API_KEY)

    # ⚠️ Verifica se o resultado contém 'data'
    if result and "data" in result and isinstance(result["data"], list) and len(result["data"]) > 0:
        latest = result["data"][0]
        return jsonify({
            "value": latest.get("value"),
            "classification": latest.get("value_classification"),
            "timestamp": latest.get("timestamp")
        })
    else:
        return jsonify({"error": "Dados não encontrados ou estrutura inesperada."}), 500
		
		
		
