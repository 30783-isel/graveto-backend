import mysql.connector
import importlib
import configparser

commons = importlib.import_module("commons")

config_file_path = 'config.centralized.properties'

def get_config_value(key, section='CENTRALIZED'):
    try:
        config = configparser.ConfigParser(interpolation=None)
        config.read(config_file_path)
        return config.get(section, key)
    except Exception as e:
        print(f"Erro ao obter valor de configuração: {e}")
        return None
    
# Configuração da conexão ao MySQL
config = {
    'host': get_config_value('DB_URL'),
    'user': 'janganga',       # Seu nome de usuário no MySQL
    'password': 'Terelowmow.123',     # Sua senha do MySQL
    'database': 'degen'  # Nome do banco de dados
}


    
def getToken(token):
    # Conectando ao banco de dados MySQL
    try:
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():

            # Criando um cursor para executar a consulta
            cursor = connection.cursor()

            # Consulta à tabela 'teste'
            query = "SELECT * FROM degen.buy WHERE name = %s"
            cursor.execute(query, (token,)) 

            # Recuperando os resultados
            resultados = cursor.fetchall()
            
            return resultados

    except mysql.connector.Error as err:
        print(f"Erro: {err}")

    finally:
        # Fechando a conexão com o banco de dados
        if connection.is_connected():
            cursor.close()
            connection.close()





def insert_buy(data):
    """
    Função para inserir dados na tabela 'buy_centralized'.
    :param data: Tupla com os dados a serem inseridos na tabela
    Exemplo de 'data': {'symbol': 'token_example', 'price': 100, 'name': 'example_name', ...}
    """
    try:
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            cursor = connection.cursor()
    
            # Comando SQL para inserção
            query = """
                INSERT INTO degen.buy_centralized (`id`, `contract_address`, `platform_token_address`,`symbol`,`name`,`platform_name`,`price`,`min_price`,`max_price`,`percent_change_1h`,`percent_change_24h`,`volume_24h`,`market_cap`,`score`,`quantity`, `comprado`, `val_sol_sell`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """


            # Criar uma tupla a partir do dicionário `data`
            values = (
                commons.to_int(data.get('id', '')),
                commons.convert_2_string(data.get('contract_address', '')),
                commons.convert_2_string(data.get('platform_token_address', '')),
                commons.convert_2_string(data.get('symbol', '')),
                commons.convert_2_string(data.get('name', '')),
                commons.convert_2_string(data.get('platform_name', '')), 
                commons.to_float(data.get('price', 0.0)), 
                commons.to_float(data.get('price', 0.0)), 
                commons.to_float(data.get('price', 0.0)), 
                commons.to_float(data.get('percent_change_1h', 0.0)),
                commons.to_float(data.get('percent_change_24h', 0.0)),
                commons.to_float(data.get('volume_24h', 0.0)),
                commons.to_float(data.get('market_cap', 0.0)),
                commons.to_float(data.get('score', 0.0)),
                commons.to_float(data.get('token_quantity', 0.0)),
                commons.to_float(data.get('comprado', True)),
                commons.to_float(data.get('val_sol_sell', 0.0)),
            )
            
            # Executando o comando de inserção com os valores extraídos do dicionário
            cursor.execute(query, values)

            # Confirmando a transação
            connection.commit()
            return True

    except mysql.connector.Error as err:
        print(f"Erro ao inserir dados: {err}")
        return False
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()




def get_existing_tokens():
    try:
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():

            # Criando um cursor para executar a consulta
            cursor = connection.cursor()

            # Consulta para pegar os tokens da tabela 'top10'
            query = "SELECT * FROM buy_centralized"
            cursor.execute(query)

            # Recuperando os resultados
            resultados = cursor.fetchall()

            existing_tokens = []
            for row in resultados:
                existing_tokens.append({
                    'idk': row[0],
                    'id': row[1],
                    'platform_token_address': row[3],
                    'symbol': row[4],
                })
                
            return existing_tokens

    except mysql.connector.Error as err:
        print(f"Erro ao recuperar tokens: {err}")
        return []

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()







def save_tokens_to_db(tokens):
    try:
        connection = mysql.connector.connect(**config)

        if connection.is_connected():

            cursor = connection.cursor()

            # Excluindo os tokens antigos (caso a tabela já tenha 10 tokens)
            delete_query = f"DELETE FROM top10_centralized"
            cursor.execute(delete_query)

            # Inserir os novos tokens no banco de dados
            for token in tokens:
                insert_query = """
                    INSERT INTO top10_centralized (`id`,`platform_token_address`, `symbol`, `name`, `platform_name`, `cmc_rank`, `date_added`, `fully_diluted_market_cap`, `infinite_supply`,`market_cap_dominance`,`total_supply`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                data = (token['id'], token['platform_token_address'], token['symbol'], token['name'], token['platform_name'], token['cmc_rank'], token['date_added'], token['fully_diluted_market_cap'], token['infinite_supply'], token['market_cap_dominance'], token['total_supply'])
                cursor.execute(insert_query, data)

            # Confirmando a transação
            connection.commit()

    except mysql.connector.Error as err:
        print(f"Erro ao salvar tokens: {err}")
        return False

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()









def getTokens():
    try:
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            cursor = connection.cursor()
            query = f"SELECT * FROM buy_centralized "
            cursor.execute(query, ()) 
            resultados = cursor.fetchall()
            return resultados
    except mysql.connector.Error as err:
        print(f"Erro: {err}")

    finally:
        # Fechando a conexão com o banco de dados
        if connection.is_connected():
            cursor.close()
            connection.close()


























def update_buy(data, symbol):
    """
    Função para atualizar dados na tabela 'buy_dex', levando em conta que alguns campos podem não ser fornecidos.
    :param data: Dicionário com os dados a serem atualizados (campos vazios ou ausentes não serão atualizados).
    :param contract_address: Endereço do contrato que identifica o registro a ser atualizado.
    Exemplo de 'data': {
        'base_asset_contract_address': 'novo_endereco',
        'quote_asset_contract_address': None,  # Este campo não será atualizado
        'name': 'novo_nome',
        'price': None,  # Este campo não será atualizado
        'buy_date': '2025-01-01',
        'created_at': '2025-01-01 12:00:00',
        'volume_24h': None,  # Este campo não será atualizado
        'liquidity': 150000,
        'quantity': 100,
        'comprado': True
    }
    """
    try:
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():

            cursor = connection.cursor()
    
            # Montando a parte do SET com base nos dados fornecidos
            set_clause = []
            values = []

            # Itera sobre os campos de data e monta o SET dinâmico
            for column, value in data.items():
                if value is not None:  # Só adiciona no SET se o valor não for None
                    set_clause.append(f"{column} = %s")
                    values.append(value)

            if not set_clause:
                print("Nenhum campo foi fornecido para atualização.")
                return False

            # Adiciona o WHERE com o contract_address
            set_clause_str = ", ".join(set_clause)
            query = f"""
                UPDATE buy_centralized
                SET {set_clause_str}
                WHERE symbol = %s
            """
            
            # Adiciona o contract_address no final dos valores
            values.append(symbol)

            # Executando o comando de atualização
            cursor.execute(query, tuple(values))

            # Confirmando a transação
            connection.commit()
            return True
        
    except mysql.connector.Error as err:
        print(f"Erro ao atualizar dados: {err}")
        return False
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def delete_buy_token(token):
    try:
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            cursor = connection.cursor()
            delete_query = f"DELETE FROM buy_centralized WHERE id = {token.get('id', None)}"
            cursor.execute(delete_query)
            connection.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao apagar tokens: {err}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def updateNumberBuys():
    try:
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            cursor = connection.cursor()
            query = "UPDATE number_buys SET number_buyscol = number_buyscol + 1 WHERE number = 1"
            cursor.execute(query)
            connection.commit()
    except mysql.connector.Error as err:
        print(f"Erro: {err}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def getNumberBuys():
    try:
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            cursor = connection.cursor()
            query = "SELECT number_buyscol FROM number_buys WHERE number = 1"
            cursor.execute(query)
            resultado = cursor.fetchone()
            if resultado:
                return resultado[0]
            else:
                print("Registro não encontrado.")
                return None
    except mysql.connector.Error as err:
        print(f"Erro: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()



import mysql.connector

def clean_slate():
    try:
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            cursor = connection.cursor()

            query = "UPDATE number_buys SET number_buyscol = 0"
            cursor.execute(query)

            tables_to_truncate = ["buy_centralized", "top10_centralized"]

            for table in tables_to_truncate:
                query = f"TRUNCATE TABLE {table}"
                cursor.execute(query)

            connection.commit()
            print("Tabelas truncadas com sucesso.")
    
    except mysql.connector.Error as err:
        print(f"Erro: {err}")
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


