from flask import Flask, request, jsonify
import sqlite3
from flask_bcrypt import check_password_hash
from main import app, connectDb, SENHA_SECRETA
import jwt

def generateToken(idUsuario, email):
    payload = {
        'id_usuario': idUsuario,
        'email': email
    }

    token = jwt.encode(payload, SENHA_SECRETA, algorithm='HS256')

    return token

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

@app.route('/login', methods=['GET'])
def get_login():
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({'error': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)

    try:
        payload = jwt.decode(token, SENHA_SECRETA, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    con = connectDb()

    cursor = con.cursor()

    cursor.execute('''
        SELECT 1 
        FROM USUARIOS
        WHERE ID_USUARIO = ?    
    ''', (id_usuario,))

    if cursor.fetchone():
        return jsonify({
            'userExist': True
        }), 200

    return jsonify({
        'userExist': False
    }), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    senha = data.get('senha')

    con = connectDb()

    cursor = con.cursor()

    cursor.execute('''
        SELECT SENHA, ID_USUARIO
        FROM USUARIOS
        WHERE EMAIL = ?
    ''', (email,))

    resposta = cursor.fetchone()

    if not resposta:
        return jsonify({
            'error': 'Usuário não encontrado.'
        }), 404

    senha_hash = resposta[0]
    id_usuario = resposta[1]

    if not check_password_hash(senha_hash, senha):
        return jsonify({
            'error': 'Senha incorreta.'
        }), 401

    token = generateToken(id_usuario, email)

    return jsonify({
        'success': 'Login realizado com sucesso!',
        'token': token
    }), 200

