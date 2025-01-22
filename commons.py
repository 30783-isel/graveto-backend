# Função para garantir que o valor seja um número (float) ou 0.0 se não for válido
def to_float(value):
    if isinstance(value, tuple):  # Se o valor for uma tupla, pega o primeiro item
        value = value[0]
    try:
        # Tente converter para float
        return float(value)
    except (ValueError, TypeError):
        # Se não for possível, retorne 0.0 (valor padrão)
        return 0.0

def to_int(value):
    if isinstance(value, tuple):  # Se o valor for uma tupla, pega o primeiro item
        value = value[0]
    try:
        # Tente converter para inteiro
        return int(value)
    except (ValueError, TypeError):
        # Se não for possível, retorne 0 (valor padrão)
        return 0


# Função para garantir que o valor seja um número (float) ou 0.0 se não for válido
def convert_2_string(value):
    if isinstance(value, tuple):  # Se o valor for uma tupla, pega o primeiro item
        value = value[0]
    try:
        # Tente converter para float
        return str(value)
    except (ValueError, TypeError):
        # Se não for possível, retorne 0.0 (valor padrão)
        return 0.0