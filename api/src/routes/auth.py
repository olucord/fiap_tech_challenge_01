"""
auth.py

Módulo responsável pela autenticação das rotas de raspagem via JWT com um banco
de dados de usuários

Endpoints:
    POST /register: endpoint para registrar um novo usuário com base nos 
    parâmetros passados na requisição HTTP (username e password).

        Params:
            username (str): nome do usuário a ser registrado.
            password (str): senha do usuário a ser registrado.	
        
        Returns:
            response: objeto JSON contendo a confirmação do usuário criado ou 
            uma mensagem de erro, se a solicitação falhar.

    POST /login: endpoint para autenticar um usuário, retornando um JWT em caso
    de uma autenticação bem-sucedida.

        Params:
            username (str): nome do usuário a ser logado.
            password (str): senha do usuário a ser logado.	
            
        Returns:
            response: objeto JSON contendo o token gerado para o usuário ou 
            uma mensagem de erro, se a solicitação falhar.
            
    DELETE /account: endpoint para deletar um usuário.

        Returns:
            response: objeto JSON contendo a confirmação que o usuário foi
            deletado ou uma mensagem de erro, se a solicitação falhar.
"""

from flask import Blueprint, jsonify, request, Response
from src.models import db, User
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity)
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register() -> Response:
    """
    Registra um novo usuário
    ---
    tags:
      - Auth    
    parameters:
      - in: query
        name: username
        type: string
        required: true
      - in: query
        name: password
        type: string
        required: true
    responses:
      201:
        description: Usuário criado com sucesso
      400:
        description: Faltando dados requeridos
      409:
        description: Usuário já existe
      500:
        description: Erro interno no servidor ao tentar registar um usuário
    """    
    # with app.app_context():  # Garante o contexto da aplicação
    data = request.args.to_dict()
    # Verifica se os campos necessários existem
    if 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing username or password"}), 400
    
    # Verifica se o usuário já existe
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "User already exists"}), 409
    
    # Cria o novo usuário
    new_user = User(
        username=data['username'],
        password=data['password']
    )
    
    db.session.add(new_user)
    try:
        db.session.commit()
        return jsonify({"msg": "User created"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login() -> Response:
    """
    Autentica um usuário e retorna um token JWT
    ---
    tags:
      - Auth
    parameters:
      - in: query
        name: username
        type: string
        required: true
      - in: query
        name: password
        type: string
        required: true
    responses:
      200:
        description: Token de acesso fornecido ao usuário
      400:
        description: Faltando dados requeridos
      401:
        description: Credenciais inválidas
    """
    data = request.args.to_dict()
    # Verifica se os campos necessários existem
    if 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing username or password"}), 400
    user = User.query.filter_by(username=data['username']).first()

    if str(user.username).strip() == str(data['username']).strip():
      if str(user.password).strip()==str(data['password']).strip():
        token = create_access_token(
            identity=user.username, expires_delta=timedelta(minutes=30)
            )
        
        return jsonify({"acess token":token}), 200
    else:
      return jsonify({"error":"Invalid credentials"}), 401
        
@auth_bp.route('/account', methods=['DELETE'])
@jwt_required()
def delete_account() -> Response:
    """
    Deleta a conta do usuário autenticado
    ---
    tags:
      - Auth
    security:
      - JWT: []
    responses:
      200:
        description: Usuário deletado com sucesso
      404:
        description: Usuário não encontrado
    """
    user_id = get_jwt_identity()

    user = User.query.get(user_id)
        
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({
            "msg":f"User '{user.username}' deleted sucessfully"
            }), 200
    
    return jsonify({"error":"User not found"}), 404    