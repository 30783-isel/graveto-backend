from flask import Flask, jsonify
import requests
import pandas as pd
import time

app = Flask(__name__)

# Definir URL e parâmetros da API
url = 'https://sandbox-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
parameters = {
    'start': '1',
    'limit': '5'
}
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': 'b54bcf4d-1bca-4e8e-9a24-22ff2c3d462c',  # Substitua com sua chave
}

# Função para pegar os dados da API
def fetch_data():
    response = requests.get(url, params=parameters, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao fazer requisição: {response.status_code}")
        return None

# Função para obter os 10 tokens com maior variação de preço (24h)
def get_top_tokens():
    data = fetch_data()
    if not data:
        return []

    all_data = pd.DataFrame()  # Cria um DataFrame vazio

    # Iterando sobre a resposta dos tokens
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
            'cmc_rank': token['cmc_rank'],
            'last_updated': token['last_updated'],
            'price': token['quote']['USD']['price'],
            'volume_24h': token['quote']['USD']['volume_24h'],
            'volume_change_24h': token['quote']['USD'].get('volume_change_24h', None),
            'percent_change_1h': token['quote']['USD'].get('percent_change_1h', None),
            'percent_change_24h': token['quote']['USD'].get('percent_change_24h', None),
            'percent_change_7d': token['quote']['USD'].get('percent_change_7d', None),
            'market_cap': token['quote']['USD']['market_cap'],
            'market_cap_dominance': token['quote']['USD']['market_cap_dominance'],
            'fully_diluted_market_cap': token['quote']['USD']['fully_diluted_market_cap']
        }
        
        # Convertendo o dicionário em um DataFrame de uma linha
        row = pd.DataFrame([token_data])
        
        # Usando pd.concat() para adicionar a linha ao DataFrame
        all_data = pd.concat([all_data, row], ignore_index=True)

    # Exibindo os 10 tokens com maior variação de preço em 24h
    top_tokens = all_data.sort_values(by='percent_change_24h', ascending=False).head(10)
    
    # Transformar o DataFrame em uma lista de dicionários para o retorno JSON
    return top_tokens[['name', 'symbol', 'percent_change_24h']].to_dict(orient='records')

@app.route('/top-tokens', methods=['GET'])
def get_top_tokens_endpoint():
    # Chama a função que obtém os tokens com maior variação e retorna como JSON
    top_tokens = get_top_tokens()
    
    if top_tokens:
        return jsonify(top_tokens), 200
    else:
        return jsonify({'error': 'Unable to fetch data'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Escuta em todas as interfaces de rede na porta 5000
