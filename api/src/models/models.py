"""
models.py

Este módulo define os modelos de dados da aplicação usando SQLAlchemy como ORM
(Object-Relational Mapping). Um ORM permite mapear tabelas do banco de dados 
como classes Python, facilitando o acesso e manipulação dos dados.

Classes:
    User: definição da tabela 'User' para autenticação e gerenciamento de
    usuários. 
"""

from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
import os

db = SQLAlchemy()

class User(db.Model):
    """
    Classe de usuários que representa a tabela de usuários no banco de dados

    Attrs:
        id (int): o identificador único do usuário na tabela.
        username (str): nome do usuário na tabela.
        password (str): senha do usuário na tabela.
    """
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
