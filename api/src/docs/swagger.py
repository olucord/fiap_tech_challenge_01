from flasgger import Swagger

def configure_swagger(app):
    swagger_config = {
        "swagger": "2.0",
        "info": {
            "title": "API com Token Bearer",
            "description": "Exemplo de API com autenticação Bearer no Flasgger",
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