"""
jwt.py

Configura o JWT (Json Web Token) para o aplicativo Flask por meio da biblioteca 
flask_jwt_extended.

É REDUNDANTE?
Funções: 
- configure_jwt(app): inicializa o JWTManager no arquivo principal da aplicação,
o app.py

"""
from flask_jwt_extended import JWTManager

def configure_jwt(app):
    """
    Inicializa o JWTManager com a aplicação Flask.
    ---
    Parameters:
        app: instância da aplicação Flask. 
    """
    JWTManager(app)

