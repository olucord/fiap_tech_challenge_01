"""
index.py

Módulo principal da API. Inicializa a aplicação Flask importando as 
configurações e utilitários da API. 

Também é responsável por executar a aplicação no servidor.

Rotas:
- / : rota principal da API flask.
"""

from flask import Flask
from src.config import ConfigProd, CustomJSONProvider
from src.models import db
from src.routes import scraping_bp
from src.auth import configure_jwt
from src.routes import auth_bp
from src.docs import configure_swagger
import os

app = Flask(__name__)
app.config.from_object(ConfigProd)
CONNECTION_STRING = os.environ.get('POSTGRES_URL')
if CONNECTION_STRING and CONNECTION_STRING.startswith("postgres://"):
    CONNECTION_STRING = CONNECTION_STRING.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = CONNECTION_STRING
# app.config['SQLALCHEMY_ECHO'] = True # Debug de teste do banco de dado
db.init_app(app)
configure_swagger(app)
configure_jwt(app)
app.json = CustomJSONProvider(app)
app.register_blueprint(scraping_bp)
app.register_blueprint(auth_bp)

@app.route('/')
def home() -> str:
    """
    Rota principal da aplicação, faz uma saudação, apresenta a API e exibe um 
    link de ajuda para usar a aplicação.

    Returns:
        str: informações sobre a API.
    """
    return (
        "Welcome to Embrapa's API! To get started, visit https://tech-challenge"
        "-01-tariks-projects-66df066e.vercel.app/apidocs for a user-friendly "
        "interface using Swagger UI to test the API, or check out "
        "https://tech-challenge-01-tariks-projects-66df066e.vercel.app/scrape/"
        "content/help for technical usage instructions about each valid "
        "parameter and examples of how to use the API."
    )

if __name__ == '__main__':
    app.run(debug=True)