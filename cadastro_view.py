import datetime
from flask import Flask, request, jsonify
from main import app, SENHA_SECRETA, EMAIL_APP, SENHA_APP
import jwt
import re
from flask_bcrypt import generate_password_hash, check_password_hash
from components import remover_bearer, validar_user
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from components import generateToken
from supabase_client import supabase

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

    criado_em = datetime.datetime.now().isoformat()

    try:
        response = (
            supabase
            .table('USUARIOS')
            .update({'CODIGO': int(codigo), "CODIGO_CRIADO_EM": criado_em, "CONFIRMADO": False})
            .eq('ID_USUARIO', id_usuario)
            .execute()
        )

        return codigo

    except Exception as e:
        return str(e)



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

    response = (
        supabase
        .table('USUARIOS')
        .select('EMAIL, SENHA, NOME, CONFIRMADO')
        .eq('ID_USUARIO', id_usuario)
        .execute()
    )

    if not response.data:
        return jsonify({
            'error': 'Usuário não encontrado'
        }), 400

    data = response.data[0]

    confirmado = data['CONFIRMADO']

    if confirmado != 1:
        return jsonify({
            'error': 'Email não confirmado',
            'emailNotConfirmed': True
        }), 400

    usuario = {
            'id_usuario': id_usuario,
            'email': data["EMAIL"],
            'senha': data["SENHA"],
            'nome': data["NOME"]
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

    # Faz a busca
    response = (
        supabase
        .table('USUARIOS')
        .select('EMAIL')
        .eq('EMAIL', email)
        .execute()
    )

    if response.data:
        return jsonify({
            'error': 'Email já cadastrado'
        }), 400

    validacaoSenha = validarSenha(senha)

    if validacaoSenha is not True:
        return jsonify({
            "error": validacaoSenha
        }), 400

    senha_hash = generate_password_hash(senha).decode('utf-8')

    response = (
        supabase
        .table('USUARIOS')
        .insert({'EMAIL': email, 'NOME': nome, 'SENHA': senha_hash})
        .execute()
    )

    if not response.data:
        return jsonify({
            'error': 'Erro ao cadastrar usuário.'
        }), 400

    id_usuario = response.data[0]['ID_USUARIO']


    codigoGerado = gerarCodigo(id_usuario)

    if not codigoGerado:
        return jsonify({
            "error": "Erro ao gerar código de verificação"
        }), 400

    print(codigoGerado)

    # Envia o email
    enviarEmailEmThread(email, codigoGerado)

    return jsonify({
        'success': 'Código de verificação enviado por email'
    }), 200



@app.route('/cadastro', methods=['PUT'])
def put_cadastro():
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

    data = request.get_json()

    # Obtém os dados
    nome = data.get('nome')
    email = data.get('email')
    senhaAtual = data.get('senhaAtual')
    senhaNova = data.get('senhaNova')
    senhaNovaConfirm = data.get('senhaNovaConfirm')

    if nome is None or email is None:
        return jsonify({
            'error': 'Dados incompletos'
        }), 400

    if senhaNova or senhaNovaConfirm:

        if senhaNova and senhaNovaConfirm and senhaNova != senhaNovaConfirm:
            return jsonify({
                "error": "Senhas diferem"
            })

        if senhaAtual is None:
            return jsonify({
                "error": "Informe a senha atual"
            }), 401

    if senhaAtual:
        if senhaAtual is None or senhaNova is None or senhaNovaConfirm is None:
            return jsonify({
                'error': 'Dados incompletos'
            }), 400

        response = (
            supabase
            .table('USUARIOS')
            .select('SENHA')
            .eq('ID_USUARIO', id_usuario)
            .execute()
        )

        senha_hash = response.data[0]['SENHA']

        checkPassword = check_password_hash(senha_hash, senhaAtual)

        if not checkPassword:
            return jsonify({
                "error": "Senha atual incorreta"
            }), 400

        if senhaAtual == senhaNova:
            return jsonify({
                "error": "A nova senha não pode ser igual a atual"
            }), 400

        validacaoSenha = validarSenha(senhaNova)

        if validacaoSenha is not True:
            return jsonify({
                "error": validacaoSenha
            }), 400

    response = (
        supabase
        .table('USUARIOS')
        .select('EMAIL', 'NOME')
        .eq('ID_USUARIO', id_usuario)
        .execute()
    )

    row = response.data

    if not row:
        return jsonify({
            'error': 'Usuário não encontrado'
        }), 404

    emailBanco = row[0]['EMAIL']
    nomeBanco = row[0]['NOME']

    if emailBanco == email and nomeBanco == nome and senhaAtual is None:
        return jsonify({
            "success": "Nenhuma alteração necessária"
        }), 200

    query = {}

    if email is not None and email != emailBanco:
        query['EMAIL'] = email
    if nome is not None and nome != nomeBanco:
        query['NOME'] = nome
    if senhaNova is not None:
        nova_senha_hash = generate_password_hash(senhaNova).decode('utf-8')
        query['SENHA'] = nova_senha_hash

    response = (
        supabase
        .table('USUARIOS')
        .update(query)
        .eq('ID_USUARIO', id_usuario)
        .execute()
    )

    if email != emailBanco:
        codigoGerado = gerarCodigo(id_usuario)

        if not codigoGerado:
            return jsonify({
                "error": "Erro ao gerar código de verificação"
            }), 400

        # Envia o email
        enviarEmailEmThread(email, codigoGerado)

        return jsonify({
            'success': 'Código de verificação enviado por email',
            'codigoEnviado': True
        }), 200

    return jsonify({
        'success': 'Alterações salvas com sucesso!'
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

    response = (
        supabase
        .table('USUARIOS')
        .delete()
        .eq('ID_USUARIO', id_usuario)
        .execute()
    )

    return jsonify({
        'success': 'Usuário deletado com sucesso!'
    }), 200

@app.route('/reenviar-codigo', methods=['GET'])
def reenviar_codigo():
    email = request.args.get('email')

    response = (
        supabase
        .table('USUARIOS')
        .select('ID_USUARIO')
        .eq('EMAIL', email)
        .execute()
    )

    resposta = response.data

    if not resposta:
        return jsonify({
            'error': 'Usuário não encontrado'
        }), 400

    id_usuario = resposta[0]['ID_USUARIO']

    try:
        codigoGerado = gerarCodigo(id_usuario)

        enviarEmailEmThread(email, codigoGerado)

        return jsonify({
            'success': f'Código reenviado!'
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e)
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

    response = (
        supabase
        .table('USUARIOS')
        .select('CODIGO, CODIGO_CRIADO_EM')
        .eq('EMAIL', email)
        .execute()
    )

    resposta = response.data

    if not resposta:
        return jsonify({
            'error': 'Email não cadastrado'
        }), 400

    codigoBanco = resposta[0]['CODIGO']
    criadoEm = datetime.datetime.strptime(resposta[0]['CODIGO_CRIADO_EM'], "%Y-%m-%dT%H:%M:%S.%f")

    if str(codigo) != str(codigoBanco):
        return jsonify({
            'error': 'Código incorreto'
        }), 400

    currentTime = datetime.datetime.now()

    diferenca = currentTime - criadoEm

    if diferenca.total_seconds() > 20 * 60:
        return jsonify({
            'error': 'Código expirado, solicite um novo'
        }), 400

    response = (
        supabase
        .table('USUARIOS')
        .update({'CODIGO': None, 'CODIGO_CRIADO_EM': None, 'CONFIRMADO': True})
        .eq('EMAIL', email)
        .execute()
    )

    response = (
        supabase
        .table('USUARIOS')
        .select('ID_USUARIO')
        .eq('EMAIL', email)
        .execute()
    )

    id_usuario = response.data[0]['ID_USUARIO']

    token = generateToken(id_usuario, email)

    return jsonify({
        'success': 'Cadastro aprovado com sucesso!',
        'token': token
    }), 200
