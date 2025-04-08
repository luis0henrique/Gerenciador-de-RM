import unicodedata

def remove_acentos(texto):
    """Remove acentos e caracteres especiais de uma string"""
    if not isinstance(texto, str):
        texto = str(texto)
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join([c for c in texto if not unicodedata.combining(c)])
    return texto
