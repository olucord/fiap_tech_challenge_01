"""
config.py

Este módulo define as configurações da aplicação Flask para diferentes ambientes
(desenvolvimento e produção), além de lhe fornecer um provedor JSON 
personalizado.

Aqui também será carregada a string de conexão do PostgreSQL da variável de 
ambiente POSTGRES_URL e ajustado o prefixo "postgres://" para compatibilidade 
com bibliotecas como SQLAlchemy.

Classes:
    ConfigDev: Configurações específicas para ambiente de desenvolvimento.
    ConfigProd: Configurações específicas para ambiente de produção.
    CustomJSONProvider: Provedor personalizado de serialização e desserialização
    JSON no Flask com ajustes para compatibilidade com Unicode e controle de 
    ordenação de chaves.
"""

from flask.json.provider import DefaultJSONProvider
from typing import Any
import os

CONNECTION_STRING = os.environ.get('POSTGRES_URL')
if CONNECTION_STRING and CONNECTION_STRING.startswith("postgres://"):
    CONNECTION_STRING = CONNECTION_STRING.replace("postgres://", "postgresql://", 1)

class ConfigDev:
    """
    Configurações de desenvolvimento para a aplicação Flask.
    
    Attrs:
        DEBUG (bool): Ativa o modo de depuração.
        JWT_SECRET_KEY (str): Chave secreta usada para assinatura de tokens JWT.
        JSONIFY_PRETTYPRINT_REGULAR (bool): Ativa a identação na saída JSON.
        SQLALCHEMY_DATABASE_URI (str): String de conexão com o banco de dados
        PostgreSQL.
    """
    DEBUG = True
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JSONIFY_PRETTYPRINT_REGULAR = True
    SQLALCHEMY_DATABASE_URI = CONNECTION_STRING

class ConfigProd:
    """
    Configurações de produção para a aplicação Flask.
    
    Attrs:
        DEBUG (bool): Desativa o modo de depuração.
        JWT_SECRET_KEY (str): Chave secreta usada para assinatura de tokens JWT.
        JSONIFY_PRETTYPRINT_REGULAR (bool): Ativa a identação na saída JSON.
        SQLALCHEMY_DATABASE_URI (str): String de conexão com o banco de dados
        PostgreSQL.
    """
    DEBUG = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JSONIFY_PRETTYPRINT_REGULAR = True
    SQLALCHEMY_DATABASE_URI = CONNECTION_STRING

class CustomJSONProvider(DefaultJSONProvider):
    """
    Provedor personalizado de JSON para a aplicação Flask.

    Sobrescreve os métodos padrão de serialização e desserialização JSON no 
    Flask para permitir melhor compatibilidade com caracteres especiais e ordem 
    de chaves.
    
    Methods:
        dumps: serializa um objeto Python em uma string JSON.
        loads: desserializa uma string JSON em um objeto Python.
    """
  
    def dumps(self, obj, **kwargs) -> str:
        """
        Serializa um objeto Python em uma string JSON.

        Definimos os argumentos "ensure_ascii" e "sort_keys" como False, já que
        por padrão são True. O primeiro permite preservar caracteres unicode 
        além de apenas ASCII, enquanto o segundo mantém a ordem original das 
        chaves do dicionário, sem ordená-las.
        
        Args:
            obj (Any): Objeto Python a ser serializado.
            kwargs: Parâmetros adicionais para customizar a serialização.
        
        Returns:
            str: Representação JSON do objeto.
        """
        kwargs.setdefault('ensure_ascii', False)
        kwargs.setdefault('sort_keys', False)

        return super().dumps(obj, **kwargs)

    def loads(self, s, **kwargs) -> Any:
        """
        Desserializa uma string JSON em um objeto Python.
        
        Args:
            s (str): String JSON a ser convertida.
            kwargs: Parâmetros adicionais para customizar a desserialização.
        
        Returns:
            obj (Any): Objeto Python resultante da conversão.
        """
        return super().loads(s, **kwargs)