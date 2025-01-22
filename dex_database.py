import mysql.connector
from datetime import datetime
import configparser

config = configparser.ConfigParser()
config.read('config.properties')

# Obter a URL do arquivo de configurações
table_name_buy = config.get('SOLANA', 'table_name_buy')
table_name_top10 = config.get('SOLANA', 'table_name_top10')

# Configuração da conexão ao MySQL
config = {
    'host': 'localhost',         # Endereço do servidor MySQL
    'user': 'janganga',       # Seu nome de usuário no MySQL
    'password': 'Terelowmow.123',     # Sua senha do MySQL
    'database': 'degen'  # Nome do banco de dados
}

def getToken(base_asset_contract_address):
    # Conectando ao banco de dados MySQL
    try:
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():

            # Criando um cursor para executar a consulta
            cursor = connection.cursor()

            # Consulta à tabela 'teste' 
            query = f"SELECT * FROM `{table_name_buy}` WHERE base_asset_contract_address = %s"
            cursor.execute(query, (base_asset_contract_address,)) 

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



def getTokens():
    # Conectando ao banco de dados MySQL
    try:
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():

            # Criando um cursor para executar a consulta
            cursor = connection.cursor()

            # Consulta à tabela 'teste'
            query = f"SELECT * FROM `{table_name_buy}` "
            cursor.execute(query, ()) 

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
    Função para inserir dados na tabela 'buy'.
    :param data: Tupla com os dados a serem inseridos na tabela
    Exemplo de 'data': ('token_example', 100, 2.5, '2024-12-14')
    """
    try:
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():

            cursor = connection.cursor()
    
            # Comando SQL para inserção
            query = f"""
                INSERT INTO `{table_name_buy}` (base_asset_contract_address, contract_address, quote_asset_contract_address, name, price, buy_date, created_at, volume_24h, liquidity, quantity, comprado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                data['base_asset_contract_address'],
                data['contract_address'],
                data['quote_asset_contract_address'],
                data['name'],
                data['price'],
                data['buy_date'],
                data['created_at'],
                data['volume_24h'],
                data['liquidity'],
                data['quantity'],
                data['comprado']
            )

            # Executando o comando de inserção
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



def delete_token(contract_address):
    """
    Função para excluir dados da tabela 'dex' onde o 'base_asset_contract_address' corresponde ao 'contract_address'.
    :param contract_address: O endereço do contrato do ativo base a ser excluído
    """
    try:
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():

            cursor = connection.cursor()
    
            # Comando SQL para exclusão
            query = f"""
                DELETE FROM `{table_name_buy}`
                WHERE base_asset_contract_address = %s
            """
            
            # Executando o comando de exclusão
            cursor.execute(query, (contract_address,))

            # Confirmando a transação
            connection.commit()
            return True
        
    except mysql.connector.Error as err:
        print(f"Erro ao excluir dados: {err}")
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
            query = f"SELECT * FROM `{table_name_top10}`"
            cursor.execute(query)

            # Recuperando os resultados
            resultados = cursor.fetchall()

            existing_tokens = []
            for row in resultados:
                existing_tokens.append({
                    'base_asset_contract_address': row[0],
                    'name': row[1],
                    'price': row[2],
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
            delete_query = f"DELETE FROM `{table_name_top10}`"
            cursor.execute(delete_query)

            # Inserir os novos tokens no banco de dados
            for token in tokens:
                insert_query = f"""
                    INSERT INTO `{table_name_top10}` (base_asset_contract_address, name, price)
                    VALUES (%s, %s, %s)
                """
                data = (token['base_asset_contract_address'], token['name'], token['price'])
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




def update_buy(data, contract_address):
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
                UPDATE `{table_name_buy}`
                SET {set_clause_str}
                WHERE contract_address = %s
            """
            
            # Adiciona o contract_address no final dos valores
            values.append(contract_address)

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
