from flask import Blueprint, jsonify, request
from src.models import db, User
from flask_jwt_extended import (
    create_access_token, jwt_required,
    get_jwt_identity)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register_user():
    """
    Registra um novo usuário
    ---
    tags:
      - Auth
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              username:
                type: string
              password:
                type: string
            required:
              - username
              - password
    responses:
      201:
        description: Usuário criado com sucesso
      409:
        description: Usuário já existe
    """

    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error":"User already exists"}), 409
    new_user = User(
        username=data['username'], 
        password=data['password']
    )

    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg":"User created"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Autentica um usuário e retorna um token JWT
    ---
    tags:
      - Auth
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              username:
                type: string
              password:
                type: string
            required:
              - username
              - password
    responses:
      200:
        description: Token de acesso fornecido ao usuário
      401:
        description: Credenciais inválidas
    """

    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and user.password==data['password']:
        token = create_access_token(identity=str(user.id))
        return jsonify({"acess token":token}), 200
    return jsonify({"error":"Invalid credentials"}), 401

@auth_bp.route('/account', methods=['DELETE'])
@jwt_required()
def delete_account():

    """
    Deleta a conta do usuário autenticado
    ---
    tags:
      - Auth
    security:
      - BearerAuth: []
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
        return jsonify({"msg":f"User '{user.username}' deleted sucessfully"}), 
    200
    
    return jsonify({"error":"User not found"}), 404    
