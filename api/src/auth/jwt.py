"""
jwt.py

Inicializa o JWT (Json Web Token) na aplicação Flask

Functions:
    configure_jwt(app): inicializa o JWTManager na API.

        Params:
            app: instância da aplicação Flask.

        Returns:
            None
"""
from flask_jwt_extended import JWTManager

def configure_jwt(app) -> None:
    """
    Inicializa o JWTManager com a aplicação Flask.
    
    Params:
        app: instância da aplicação Flask.

    Returns:
        None
    """
    JWTManager(app)

