from flask import Blueprint, jsonify, request
from src.models import db, User
from flask_jwt_extended import (
    create_access_token, jwt_required,
    get_jwt_identity, decode_token)
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)


####
# Testar nova funcao pra validar um token
####
# def valida_token(token):
#     tk_decodificado = decode_token(token)
#     print(tk_decodificado)
#     return tk_decodificado



@auth_bp.route('/register', methods=['GET'])  # Ajuste o método e endpoint conforme necessário
def register():
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
        required: false

    responses:
      201:
        description: Usuário criado com sucesso
      409:
        description: Usuário já existe
    """    
    # with app.app_context():  # Garante o contexto da aplicação
    data = request.args.to_dict()
    # Verifique se os campos necessários existem
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
def login():
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
        required: false

    responses:
      200:
        description: Token de acesso fornecido ao usuário
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
        token = create_access_token(identity=user.username, expires_delta=timedelta(minutes=30))
        
        return jsonify({"acess token":token}), 200
    else:
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
        return jsonify({"msg":f"User '{user.username}' deleted sucessfully"}), 
    200
    
    return jsonify({"error":"User not found"}), 404    
