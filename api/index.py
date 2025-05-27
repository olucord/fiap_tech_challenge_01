"""
app.py

Módulo principal da API. Inicializa a aplicação Flask importando as 
configurações e utilitários da API. 

Também é responsável por executar a aplicação no servidor.

Rotas:
- / : rota principal da API flask.
"""

from flask import Flask
from src.config import ConfigDev, CustomJSONProvider
# from src.models import db
from src.routes import scraping_bp
# from src.auth import configure_jwt
# from src.routes import auth_bp
from src.docs import configure_swagger

app = Flask(__name__)
app.config.from_object(ConfigDev)
# db.init_app(app)
# configure_jwt(app)
app.json = CustomJSONProvider(app)
app.register_blueprint(scraping_bp)
# app.register_blueprint(auth_bp)
configure_swagger(app)

@app.route('/')
def home() -> str:
    """
    Rota principal da aplicação, faz uma saudação, apresenta a API e exibe um 
    link de ajuda para usar a aplicação.

    Returns:
        str: informações sobre a API.
    """
    return (
        "Welcome to Embrapa's API! To get started, "
        "visit http://127.0.0.1:5000/scrape/content/help "
        "for instructions on how to use the API."
    )

if __name__ == '__main__':
    app.run(debug=True)