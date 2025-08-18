from http.client import responses

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

