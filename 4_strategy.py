from flask import Flask, jsonify
import requests
import pandas as pd
import json
import time

app = Flask(__name__)

# Definir URL e parâmetros da API
url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
parameters = {
    'start': '1',
    'limit': '100'  # Aumentamos o limite para pegar mais tokens
}
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': 'ff716c6f-21b5-4f8c-850d-8c5b2792e9a2',  # Substitua com sua chave
}

# Função para pegar os dados da API
def fetch_data():
    response = requests.get(url, params=parameters, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao fazer requisição: {response.status_code}")
        return None

# Função para calcular a pontuação de cada token
def calculate_score(token):
    # Pegando os dados principais
    price = token['quote']['USD']['price']
    volume_24h = token['quote']['USD']['volume_24h']
    percent_change_24h = token['quote']['USD'].get('percent_change_24h', 0)
    market_cap = token['quote']['USD']['market_cap']
    market_cap_dominance = token['quote']['USD']['market_cap_dominance']
    
    # A pontuação pode ser uma média ponderada dos critérios
    score = 0
    
    # Critério 1: Variação de preço nas últimas 24h (maior variação = melhor)
    score += percent_change_24h * 0.3
    
    # Critério 2: Volume de negociação nas últimas 24h (maior volume = melhor)
    score += (volume_24h / 1e6) * 0.2  # Normalizando o volume
    
    # Critério 3: Market Cap (maior market cap = maior estabilidade)
    score += (market_cap / 1e9) * 0.2  # Normalizando o market cap
    
    # Critério 4: Liquidez (volume 24h / market cap), maior liquidez pode indicar mais fácil negociação
    if market_cap > 0:
        liquidity = volume_24h / market_cap
        score += liquidity * 0.3  # A liquidez é um critério importante
    
    return score

# Função para obter os melhores tokens
def get_best_tokens():
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
                #'tvl_ratio': token['tvl_ratio'],
                'last_updated': token['last_updated'],
                'price': token['quote']['USD']['price'],
                'volume_24h': token['quote']['USD']['volume_24h'],
                'volume_change_24h': token['quote']['USD'].get('volume_change_24h', None),
                'percent_change_1h': token['quote']['USD'].get('percent_change_1h', None),
                'percent_change_24h': token['quote']['USD'].get('percent_change_24h', None),
                'percent_change_7d': token['quote']['USD'].get('percent_change_7d', None),
                'percent_change_30d': token['quote']['USD'].get('percent_change_30d', None),
                'percent_change_60d': token['quote']['USD'].get('percent_change_60d', None),
                'percent_change_90d': token['quote']['USD'].get('percent_change_90d', None),
                'market_cap': token['quote']['USD']['market_cap'],
                'market_cap_dominance': token['quote']['USD']['market_cap_dominance'],
                'fully_diluted_market_cap': token['quote']['USD']['fully_diluted_market_cap'],
                #'tvl': token['quote']['USD']['tvl'],
                'last_updated': token['quote']['USD']['last_updated']
        }

        # Calcular a pontuação do token
        token_data['score'] = calculate_score(token)

        # Adicionar o token com a pontuação ao DataFrame
        row = pd.DataFrame([token_data])
        all_data = pd.concat([all_data, row], ignore_index=True)

    # Ordenando os tokens pela pontuação, da maior para a menor
    best_tokens = all_data.sort_values(by='score', ascending=False).head(10)
    
    # Retornando os 10 melhores tokens
    melhores_tokens = best_tokens[['name', 'symbol', 'cmc_rank','score', 'percent_change_24h', 'volume_24h', 'market_cap']].to_dict(orient='records')
    #print(json.dumps(melhores_tokens, indent=4))  # Imprime o JSON com indentação
    
    return melhores_tokens

@app.route('/best-tokens', methods=['GET'])
def get_best_tokens_endpoint():
    # Chama a função que obtém os tokens mais promissores e retorna como JSON
    best_tokens = get_best_tokens()
    
    if best_tokens:
        return jsonify(best_tokens), 200
    else:
        return jsonify({'error': 'Unable to fetch data'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
