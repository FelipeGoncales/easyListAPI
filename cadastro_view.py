import datetime
from flask import Flask, request, jsonify
import sqlite3
from main import app, connectDb, SENHA_SECRETA, EMAIL_APP, SENHA_APP
import jwt
import re
from flask_bcrypt import generate_password_hash
from components import remover_bearer, validar_user
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading

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

def gerarCodigo(id_usuario):
    codigo = ""

    for i in range(6):
        num = random.choice([0,1,2,3,4,5,6,7,8,9])
        codigo = codigo + str(num)

    criado_em = datetime.datetime.now()

    con = connectDb()

    cursor = con.cursor()

    cursor.execute('''
        UPDATE USUARIOS
        SET CODIGO= ?, CODIGO_CRIADO_EM= ?
        WHERE ID_USUARIO = ?
    ''', (codigo, criado_em, id_usuario))

    con.commit()
    con.close()
    return codigo

def enviarEmail(email, codigo):
    # 1️⃣ Configurações do remetente e destinatário
    remetente = EMAIL_APP
    senha = SENHA_APP
    destinatario = email

    # 2️⃣ Criar a mensagem
    mensagem = MIMEMultipart()
    mensagem['From'] = remetente
    mensagem['To'] = destinatario
    mensagem['Subject'] = "Código de verificação"

    # 3️⃣ Corpo do email (pode ser texto simples ou HTML)
    corpo = f"Olá!\n\nSeu código é: {codigo}\n\nAtt, EasyList"
    mensagem.attach(MIMEText(corpo, 'plain'))

    # 4️⃣ Conectar no servidor SMTP e enviar
    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)  # Gmail SMTP
        servidor.starttls()  # Conexão segura
        servidor.login(remetente, senha)
        servidor.send_message(mensagem)
        servidor.quit()
        print("Email enviado com sucesso!")
    except Exception as e:
        print("Erro ao enviar email:", e)

def enviarEmailAsync(email, codigo):
    # Função que será executada em outra thread
    enviarEmail(email, codigo)

def enviarEmailEmThread(email, codigo):
    thread = threading.Thread(target=enviarEmailAsync, args=(email, codigo))
    thread.start()

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
        SELECT EMAIL, SENHA, NOME, CONFIRMADO
        FROM USUARIOS
        WHERE ID_USUARIO = ?
    ''', (id_usuario,))

    data = cursor.fetchone()

    if not data:
        return jsonify({
            'error': 'Usuário não encontrado.'
        }), 400

    con.close()

    confirmado = data[3]

    if confirmado != 1:
        return jsonify({
            'error': 'Email não confirmado',
            'emailNotConfirmed': True
        }), 400

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

    if nome is None or email is None or senha is None:
        return jsonify({
            'error': 'Dados incompletos'
        }), 400

    # Abre o cursor
    con = connectDb()
    cursor = con.cursor()

    cursor.execute('''
                SELECT 1
                FROM USUARIOS
                WHERE EMAIL = ?
            ''', (email,))

    if cursor.fetchone():
        con.close()
        return jsonify({
            'error': 'Email já cadastrado.'
        }), 400

    validacaoSenha = validarSenha(senha)

    if validacaoSenha is not True:
        con.close()
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

    con.commit()
    con.close()

    codigoGerado = gerarCodigo(id_usuario)

    if not codigoGerado:
        return jsonify({
            "error": "Erro ao gerar código de verificação"
        }), 400

    # Envia o email
    enviarEmailEmThread(email, codigoGerado)

    return jsonify({
        'success': 'Código de verificação enviado por email'
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

    con.close()

    return jsonify({
        'success': 'Usuário deletado com sucesso!'
    }), 200

@app.route('/reenviar-codigo', methods=['GET'])
def reenviar_codigo():
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

    try:
        codigoGerado = gerarCodigo(id_usuario)

        enviarEmailEmThread(email, codigoGerado)

        return jsonify({
            'success': f'Código reenviado!'
        }), 200
    except Exception as e:
        return jsonify({
            'error': e
        }), 400

@app.route('/validar-codigo', methods=['POST'])
def validar_codigo():

    data = request.get_json()
    email = data.get('email')
    codigo = data.get('codigo')

    if not codigo or not email:
        return jsonify({
            'error': 'Dados incompletos'
        }), 401

    con = connectDb()
    cursor = con.cursor()

    cursor.execute('''
        SELECT CODIGO, CODIGO_CRIADO_EM 
        FROM USUARIOS
        WHERE EMAIl = ?
    ''', (email,))

    resposta = cursor.fetchone()

    codigoBanco = resposta[0]
    criadoEm = datetime.datetime.strptime(resposta[1], "%Y-%m-%d %H:%M:%S.%f")

    if str(codigo) != str(codigoBanco):
        con.close()
        return jsonify({
            'error': 'Código incorreto'
        }), 400

    currentTime = datetime.datetime.now()

    diferenca = currentTime - criadoEm

    if diferenca.total_seconds() > 20 * 60:
        con.close()
        return jsonify({
            'error': 'Código expirado, solicite um novo'
        }), 400

    cursor.execute('''
        UPDATE USUARIOS
        SET CODIGO= NULL, CODIGO_CRIADO_EM= NULL, CONFIRMADO = True
        WHERE email = ?
    ''', (email,))

    con.commit()
    con.close()

    return jsonify({
        'success': 'Cadastro aprovado com sucesso!'
    }), 200

