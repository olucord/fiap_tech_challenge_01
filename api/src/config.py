"""
config.py

Este módulo define as configurações principais da aplicação Flask para diferen-
tes ambientes (desenvolvimento e produção), além de fornecer a ela um provedor 
JSON personalizado.

Classes:
    - ConfigDev: Configurações específicas para ambiente de desenvolvimento.
    - ConfigProd: Config urações específicas para ambiente de produção.
    - CustomJSONProvider: Provedor personalizado de serialização e desseriali-
    zação JSON no Flask com ajustes para compatibilidade com Unicode e controle 
    de ordenação de chaves.
"""

from flask.json.provider import DefaultJSONProvider
from typing import Any

class ConfigDev:
    """
    Configurações de desenvolvimento para a aplicação Flask.

    Atributos:
        DEBUG (bool): Ativa o modo de depuração.
        JWT_SECRET_KEY (str): Chave secreta usada para assinatura de tokens JWT.
        JSONIFY_PRETTYPRINT_REGULAR (bool): Ativa a identação na saída JSON.
        SWAGGER (dict): Configurações para a interface Swagger UI.
        CACHE_TYPE (str): Tipo de cache utilizado ('simple' usa cache em memória).
    """
    DEBUG = True
    JWT_SECRET_KEY = 'Nem_toda_senha_sera_segura'
    JSONIFY_PRETTYPRINT_REGULAR = True
    SWAGGER = {
    "title":"Embrapa's API",
    "uiversion":3
}
    CACHE_TYPE = 'simple'

class ConfigProd:
    """
    Configurações de produção para a aplicação Flask.

    Atributos:
        DEBUG (bool): Desativa o modo de depuração em produção.
    """
    DEBUG = False

class CustomJSONProvider(DefaultJSONProvider):
    """
    Provedor personalizado de JSON para a aplicação Flask.

    Sobrescreve os métodos padrão de serialização e desserialização JSON no 
    Flask para permitir melhor compatibilidade com caracteres especiais e ordem 
    de chaves.

    Métodos:
        dumps: serializa um objeto Python em uma string JSON.
        loads: desserializa uma string JSON em um objeto Python.
    """
  
    def dumps(self, obj, **kwargs) -> str:
        """
        Serializa um objeto Python em uma string JSON.

        Argumentos:
            obj: Objeto Python a ser serializado.
            **kwargs: Parâmetros adicionais para customizar a serialização.

        Returns:
            str: Representação JSON do objeto.
        """
        kwargs.setdefault('ensure_ascii', False)
        kwargs.setdefault('sort_keys', False)
        return super().dumps(obj, **kwargs)

    def loads(self, s, **kwargs) -> Any:
        """
        Desserializa uma string JSON em um objeto Python.

        Argumentos:
            s (str): String JSON a ser convertida.
            **kwargs: Parâmetros adicionais para customizar a desserialização.

        Returns:
            Any: Objeto Python resultante da conversão.
        """
        return super().loads(s, **kwargs)