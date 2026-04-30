from flask import request, jsonify
from main import app, SENHA_SECRETA
import jwt
from components import remover_bearer, validar_user
from datetime import datetime
from supabase_client import supabase


def validarData(data):
    try:
        datetime.strptime(data, "%Y-%m-%d")
        return True
    except:
        return False

def formatarData(data):
    return datetime.strptime(data,"%Y-%m-%d").isoformat()

def formatarDataBanco(data):
    # Banco já retorna '2026-04-29', só pega os primeiros 10 caracteres
    return data[:10]

@app.route('/task', methods=['GET'])
def get_tasks():
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
        .table('TASK')
        .select('ID_TASK, TITULO, DESCRICAO, ISCOMPLETED, DATA')
        .eq('ID_USUARIO', id_usuario)
        .order('DATA')
        .execute()
    )

    tasks = response.data

    if not tasks:
        return jsonify({
            "tasks": []
        }), 200

    data = []

    for task in tasks:
        data.append({
            "id": task['ID_TASK'],
            "titulo": task['TITULO'],
            "descricao": task['DESCRICAO'],
            "isCompleted": task['ISCOMPLETED'],
            "data": formatarDataBanco(task['DATA'])
        })

    return jsonify({
        "tasks": data
    }), 200

@app.route('/task/<string:id_task>', methods=['GET'])
def get_unique_task(id_task):
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
        .table('TASK')
        .select('ID_TASK, TITULO, DESCRICAO, ISCOMPLETED, DATA')
        .eq('ID_USUARIO', id_usuario)
        .eq('ID_TASK', id_task)
        .execute()
    )

    data = response.data

    if not data:
        return jsonify({
            'error': 'Tarefa não encontrada'
        }), 404

    task = {
        "id": data[0]['ID_TASK'],
        "titulo": data[0]['TITULO'],
        "descricao": data[0]['DESCRICAO'],
        "isCompleted": data[0]['ISCOMPLETED'],
        "data": formatarDataBanco(data[0]['DATA'])
    }

    return jsonify({
        "task": task
    }), 200


@app.route('/task', methods=['POST'])
def create_tasks():
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

    titulo = data.get('titulo')
    descricao = data.get('descricao')
    isCompleted = data.get('isCompleted')
    data = data.get('data')

    if not titulo or not descricao or not data or isCompleted not in [False, True]:
        return jsonify({
            'error': 'Dados incompletos ou inválidos'
        }), 400

    dataValida = validarData(data)

    if not dataValida:
        return jsonify({
            'error': 'Data inválida'
        }), 400

    dataFormatada = formatarData(data)

    query = {
        'TITULO': titulo,
        'DESCRICAO': descricao,
        'ISCOMPLETED': isCompleted,
        'DATA': dataFormatada,
        'ID_USUARIO': id_usuario
    }

    response = (
        supabase
        .table('TASK')
        .insert(query)
        .execute()
    )

    res = response.data

    if not res:
        return jsonify({
            'error': 'Erro ao cadastrar a tarefa.'
        }), 400

    id_task = res[0]['ID_TASK']

    return jsonify({
        "success": "Tarefa adicionada com sucesso!",
        "newTask": {
            "titulo": titulo,
            "descricao": descricao,
            "id": id_task,
            "data": data,
            "isCompleted": isCompleted
        }
    }), 200

@app.route('/task', methods=['PUT'])
def update_tasks():
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

    id_task = data.get('id_task')
    titulo = data.get('titulo')
    descricao = data.get('descricao')
    isCompleted = data.get('isCompleted')
    dataTask = data.get('data')

    if not id_task:
        return jsonify({
            'error': 'É necessário informar o ID da tarefa'
        }), 400

    if titulo is not None or descricao is not None or isCompleted is not None or dataTask is not None:

        query = {}

        if titulo is not None:
            query['TITULO'] = titulo
        if descricao is not None:
            query['DESCRICAO'] = descricao
        if isCompleted is not None:
            query['ISCOMPLETED'] = isCompleted
        if dataTask is not None:
            dataValida = validarData(dataTask)

            if not dataValida:
                return jsonify({
                    'error': 'Data inválida'
                }), 400

            dataFormatada = formatarData(dataTask)

            query['DATA'] = dataFormatada

        response = (
            supabase
            .table('TASK')
            .update(query)
            .eq('ID_TASK', id_task)
            .eq('ID_USUARIO', id_usuario)
            .execute()
        )

        if not response.data:
            return jsonify({
                'error': 'Erro ao editar a tarefa'
            }), 400

        return jsonify({
            "success": "Tarefa atualizada com sucesso!"
        }), 200

    else:
        return jsonify({
            'error': 'É necessário informar ao menos um parâmetro para atualizar a tarefa'
        }), 400


@app.route('/task', methods=['DELETE'])
def remove_tasks():
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

    id_task = data.get('id_task')

    if not id_task:
        return jsonify({
            'error': 'Dados incompletos'
        }), 400

    response = (
        supabase
        .table('TASK')
        .select('ID_TASK')
        .eq('ID_TASK', id_task)
        .eq('ID_USUARIO', id_usuario)
        .limit(1)
        .execute()
    )

    row = response.data

    if not row:
        return jsonify({
            'error': 'Tarefa não encontrada'
        }), 404

    response = (
        supabase
        .table('TASK')
        .delete()
        .eq('ID_TASK', id_task)
        .eq('ID_USUARIO', id_usuario)
        .execute()
    )

    if not response.data:
        return jsonify({
            'error': 'Erro ao excluir a tarefa'
        }), 400

    return jsonify({
        "success": "Tarefa deletada com sucesso!"
    }), 200