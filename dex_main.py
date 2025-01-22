import multiprocessing
from dex import app as app

def run_flask_app(object_property, shared_properties):
    """
    Inicia uma instância do Flask em um processo separado.
    O número da porta é incrementado com base no 'instance_id'.
    """
    # Atualiza o dicionário compartilhado com as propriedades
    shared_properties['object_property'] = object_property

    # Inicializa o app Flask e passa as propriedades via app.config
    with app.app_context():
        # Armazena as propriedades no config do Flask
        app.config['object_property'] = object_property
        
        # Calcula a porta com base no instance_id
        genPort = 5000 + object_property.get('instance_id', 0)
        
        # Inicia o Flask app
        app.run(host='0.0.0.0', port=genPort, debug=True, use_reloader=False)

def start_multiple_flask_instances():
    # Cria um dicionário compartilhado entre os processos
    with multiprocessing.Manager() as manager:
        shared_properties = manager.dict()

        properties_list = [
            {'instance_id': 1, 'other_property': 'value1'},
            {'instance_id': 2, 'other_property': 'value2'},
        ]

        processes = []
        for properties in properties_list:
            process = multiprocessing.Process(target=run_flask_app, args=(properties, shared_properties))
            processes.append(process)
            process.start()

        # Espera todos os processos terminarem
        for process in processes:
            process.join()

if __name__ == "__main__":
    start_multiple_flask_instances()
