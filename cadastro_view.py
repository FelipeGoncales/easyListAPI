from flask import Flask, request, jsonify
import sqlite3
from main import app, connectDb, SENHA_SECRETA
import jwt
import re
from flask_bcrypt import check_password_hash, generate_password_hash
from login_view import generateToken
from components import remover_bearer, validar_user

def validarSenha(senha):
    if len(senha) < 8:
        return "A senha deve 8 caracateres ou mais."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
        return "A senha deve conter pelo menos um símbolo especial (!@#$%^&*...)."

    if not re.search(r"[A-Z]", senha):
        return "A senha deve conter pelo menos uma letra maiúscula."

    if not re.search(r"[0-9]", senha):
        return "A senha deve conter pelo menos um número."

    return True

@app.route('/cadastro', methods=['GET'])
def get_cadastro():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)

    try:
        payload = jwt.decode(token, SENHA_SECRETA, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
        email = payload['email']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    if not validar_user(id_usuario, email):
        return jsonify({
            'userExist': False
        }), 400

    con = connectDb()

    cursor = con.cursor()

    cursor.execute('''
        SELECT EMAIL, SENHA, NOME
        FROM USUARIOS
        WHERE ID_USUARIO = ?
    ''', (id_usuario,))

    data = cursor.fetchone()

    if not data:
        return jsonify({
            'error': 'Usuário não encontrado.'
        }), 400

    cursor.close()

    usuario = {
            'id_usuario': id_usuario,
            'email': data[0],
            'senha': data[1],
            'nome': data[2]
        }

    return jsonify({
        "usuario": usuario
    }), 200

@app.route('/cadastro', methods=['POST'])
def post_cadastro():
    data = request.get_json()

    # Obtém os dados
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    # Abre o cursor
    con = connectDb()
    cursor = con.cursor()

    cursor.execute('''
                SELECT 1
                FROM USUARIOS
                WHERE EMAIL = ?
            ''', (email,))

    if cursor.fetchone():
        cursor.close()
        return jsonify({
            'error': 'Email já cadastrado.'
        }), 400

    validacaoSenha = validarSenha(senha)

    if validacaoSenha is not True:
        return jsonify({
            "error": validacaoSenha
        }), 400

    senha_hash = generate_password_hash(senha).decode('utf-8')

    cursor.execute('''
        INSERT INTO USUARIOS (EMAIL, NOME, SENHA)
        VALUES (?, ?, ?)
        RETURNING ID_USUARIO
    ''', (email, nome, senha_hash))

    id_usuario = cursor.fetchone()[0]

    token = generateToken(id_usuario, email)

    con.commit()

    cursor.close()

    return jsonify({
        'success': 'Cadastro realizado com sucesso!',
        'token': token
    }), 200

@app.route('/cadastro', methods=['DELETE'])
def delete_cadastro():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)

    try:
        payload = jwt.decode(token, SENHA_SECRETA, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
        email = payload['email']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    if not validar_user(id_usuario, email):
        return jsonify({
            'userExist': False
        }), 400

    # Abre o cursor
    con = connectDb()
    cursor = con.cursor()

    cursor.execute('''
        DELETE FROM USUARIOS
        WHERE ID_USUARIO = ?
    ''', (id_usuario,))

    con.commit()

    cursor.close()

    return jsonify({
        'success': 'Usuário deletado com sucesso!'
    }), 200