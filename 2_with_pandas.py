import requests
import json
import pandas as pd
import time
from datetime import datetime

# Definir URL e parâmetros
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

# Função para armazenar os dados
def store_data():
    all_data = pd.DataFrame()  # Cria um DataFrame vazio
    start_time = time.time()  # Hora de início para controle de tempo
    iterations = 0  # Contador de iterações
    max_iterations = 50  # Número máximo de iterações
    file_path = "cryptocurrency_data.csv"  # Caminho do arquivo para salvar os dados
    
    while iterations < max_iterations:
        # Fetch the data
        data = fetch_data()
        if not data:
            print("Falha na coleta de dados. Tentando novamente...")
            time.sleep(30)  # Espera mais tempo antes de tentar novamente
            continue
        
        # Iterando sobre a resposta dos tokens
        for token in data['data']:
            # Preparando o dicionário com os dados dos tokens
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

        # Armazenar os dados em um arquivo CSV a cada ciclo
        all_data.to_csv(file_path, index=False)
        print(f"Dados armazenados em {file_path}")

        # Exibir os 10 tokens com maior variação de preço
        top_tokens = all_data.sort_values(by='percent_change_24h', ascending=False).head(10)
        print("Top 10 tokens com maior variação de preço (24h):")
        print(top_tokens[['name', 'symbol', 'percent_change_24h']])

        # Esperar 10 segundos antes da próxima requisição
        time.sleep(10)
        
        # Controle de iterações e tempo
        iterations += 1
        elapsed_time = time.time() - start_time
        print(f"Tempo de execução: {elapsed_time // 60:.0f} minutos e {elapsed_time % 60:.0f} segundos.")
    
    print("Coleta concluída.")

# Executando a coleta dos dados
collected_data = store_data()
