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
from components import generateToken

def validarSenha(senha):
    if len(senha) < 8:
        return "A senha deve 8 caracateres ou mais"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
        return "A senha deve conter pelo menos um símbolo especial (!@#$%^&*...)"

    if not re.search(r"[A-Z]", senha):
        return "A senha deve conter pelo menos uma letra maiúscula"

    if not re.search(r"[0-9]", senha):
        return "A senha deve conter pelo menos um número"

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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def enviarEmail(email, codigo):
    remetente = EMAIL_APP
    senha = SENHA_APP
    destinatario = email

    # Criar a mensagem
    mensagem = MIMEMultipart()
    mensagem['From'] = remetente
    mensagem['To'] = destinatario
    mensagem['Subject'] = "Código de verificação EasyList"

    # Corpo HTML do email
    corpo_html = f"""
        <body style="margin:0; padding:25px; background-color:#e5e7eb; font-family: Helvetica, Arial, sans-serif;">
          <table width="100%" height="100%" bgcolor="#e5e7eb" align="center">
            <tr>
              <td align="center" valign="middle" bgcolor="#e5e7eb">
                <table width="350" bgcolor="#90a1b9" style="border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.1); padding:30px; text-align:center;">
                  <tr>
                    <td style="font-size:24px; font-weight:bold; color:#314158; padding-bottom:20px;">EasyList</td>
                  </tr>
                  <tr>
                    <td style="font-size:16px; color:#314158; padding-bottom:10px; font-weight:semibold;">Olá!</td>
                  </tr>
                  <tr>
                    <td style="font-size:14px; color:#314158; padding-bottom:20px;">Seu código de verificação é:</td>
                  </tr>
                  <tr>
                    <td style="background-color:#cad5e2; color:#314158; font-size:28px; font-weight:bold; padding:15px 0; border-radius:8px; letter-spacing:4px; margin-bottom:20px;">{codigo}</td>
                  </tr>
                  <tr>
                    <td style="font-size:14px; color:#314158; padding-bottom:20px; padding-top: 8px;">Insira este código no aplicativo para validar seu email.</td>
                  </tr>
                  <tr>
                    <td style="font-size:13px; color:#314158; line-height:1.5;">Atenciosamente,<br>Equipe EasyList</td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </body>
    """

    mensagem.attach(MIMEText(corpo_html, 'html'))

    # Enviar o email via SMTP
    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
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
            'error': 'Usuário não encontrado'
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
            'error': 'Email já cadastrado'
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
    email = request.args.get('email')

    con = connectDb()

    cursor = con.cursor()

    cursor.execute('''
        SELECT ID_USUARIO
        FROM USUARIOS
        WHERE EMAIl = ?
    ''', (email,))

    resposta = cursor.fetchone()

    if not resposta:
        return jsonify({
            'error': 'Usuário não encontrado'
        }), 400

    id_usuario = resposta[0]

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

@app.route('/validar-cadastro', methods=['POST'])
def validar_cadastro():

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

    if not resposta:
        return jsonify({
            'error': 'Email não cadastrado'
        }), 400

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

    cursor.execute('''
        SELECT ID_USUARIO
        FROM USUARIOS
        WHERE EMAIL = ?
    ''', (email,))

    id_usuario = cursor.fetchone()[0]

    con.close()

    token = generateToken(id_usuario, email)

    return jsonify({
        'success': 'Cadastro aprovado com sucesso!',
        'token': token
    }), 200

