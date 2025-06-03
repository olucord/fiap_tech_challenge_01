"""
swagger.py

Este módulo inicializa e configura o Swagger na aplicação Flask, permitindo a 
documentação e o teste dos endpoints através da interface Swagger UI, com 
suporte à autenticação via JWT.

Functions:
    configure_swagger(app): Configura e inicializa o Swagger na API.

        Params:
            app: instância da aplicação Flask.

        Returns:
            None
"""

from flasgger import Swagger

def configure_swagger(app) -> None:
    """
    Inicializa e configura o Swagger com a aplicação Flask.

    Contém as configurações do Swagger que serão aplicadas na API.

        Params:
            app: instância da aplicação Flask.

        Returns:
            None
    """
    swagger_config = {
        "swagger": "2.0",
        "info": {
            "title": "Embrapa's API",
            "description": "API para raspagem de dados do site da Embrapa com autenticação via JWT",
            "version": "1.0"
        },
        "securityDefinitions": {
            'JWT': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Insira o token JWT no formato: `Bearer <token>`. Exemplo: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`'
            }
        }
    }

    Swagger(app, template=swagger_config)