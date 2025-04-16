import unicodedata

def remove_acentos(texto):
    """Remove acentos e caracteres especiais de uma string"""
    if not isinstance(texto, str):
        texto = str(texto)
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join([c for c in texto if not unicodedata.combining(c)])
    return texto

def formatar_nome(nome: str) -> str:
    """
    Formata nomes de acordo com as regras especificadas:
    - Primeira letra de cada palavra maiúscula
    - Preposições (de, da, do, dos, das, e) mantidas em minúsculo
    - Trata casos especiais com apóstrofo (D'Avila, D'Almeida, etc.)

    Args:
        nome (str): Nome a ser formatado

    Returns:
        str: Nome formatado
    """
    preposicoes = {'de', 'da', 'do', 'dos', 'das', 'e'}

    # Remove espaços extras e divide em palavras
    palavras = nome.strip().split()

    if not palavras:
        return nome

    palavras_formatadas = []
    for i, palavra in enumerate(palavras):
        # Caso especial para nomes com apóstrofo (D'Avila, D'Almeida, etc.)
        if "'" in palavra:
            partes = palavra.split("'", 1)
            # Formata a parte antes do apóstrofo (D')
            parte1 = partes[0].lower().capitalize()
            # Formata a parte depois do apóstrofo (Avila)
            parte2 = partes[1].lower().capitalize() if partes[1] else ''
            palavra = f"{parte1}'{parte2}"
        # Caso para preposições (exceto no início)
        elif i > 0 and palavra.lower() in preposicoes:
            palavra = palavra.lower()
        # Caso padrão - capitaliza a primeira letra
        else:
            palavra = palavra.lower().capitalize()

        palavras_formatadas.append(palavra)

    return ' '.join(palavras_formatadas)