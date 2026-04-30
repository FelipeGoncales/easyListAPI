from flask import request, jsonify
from flask_bcrypt import check_password_hash
from main import app
from supabase_client import supabase
from components import generateToken

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    senha = data.get('senha')

    response = (
        supabase
        .table('USUARIOS')
        .select('SENHA,ID_USUARIO,CONFIRMADO')
        .eq('EMAIL',email)
        .execute()
    )

    if not response.data:
        return jsonify({
            'error': 'Usuário não encontrado'
        }), 404

    usuario = response.data[0]

    senha_hash = usuario['SENHA']
    id_usuario = usuario['ID_USUARIO']
    confirmado = usuario['CONFIRMADO']

    if not check_password_hash(senha_hash, senha):
        return jsonify({
            'error': 'Senha incorreta'
        }), 401

    if confirmado != 1:
        return jsonify({
            'error': 'Email não confirmado',
            'emailNotConfirmed': True
        }), 400

    token = generateToken(id_usuario, email)

    return jsonify({
        'success': 'Login realizado com sucesso!',
        'token': token
    }), 200

