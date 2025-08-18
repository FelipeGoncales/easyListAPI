from flask import Flask, request, jsonify
import sqlite3
from main import app, connectDb, SENHA_SECRETA
import jwt

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

@app.route('/task', methods=['GET'])
def get_tasks():
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

    cursor.execute("SELECT * FROM TASK WHERE ID_USUARIO = ?", (id_usuario,))

    tasks = cursor.fetchall()

    cursor.close()

    data = []

    if len(tasks) > 0:
        for task in tasks:
            data.append({
                "id": task[0],
                "titulo": task[1],
                "descricao": task[2],
                "isCompleted": task[3]
            })

    return jsonify({
        "tasks": data
    }), 200


@app.route('/task/<int:id_task>', methods=['GET'])
def get_unique_task(id_task):
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

    cursor.execute("SELECT * FROM TASK WHERE ID_TASK = ? AND ID_USUARIO = ?", (id_task, id_usuario))

    data = cursor.fetchone()

    if not data:
        return jsonify({
            'error': 'Tarefa não encontrada.'
        }), 404

    cursor.close()

    task = {
        "id": data[0],
        "titulo": data[1],
        "descricao": data[2],
        "isCompleted": data[3]
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
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    data = request.get_json()

    titulo = data.get('titulo')
    descricao = data.get('descricao')
    isCompleted = data.get('isCompleted')

    if not titulo or not descricao or isCompleted not in [False, True]:
        return jsonify({
            'error': 'Dados incompletos ou inválidos.'
        }), 400

    con = connectDb()

    cursor = con.cursor()

    cursor.execute('''
        INSERT INTO TASK (titulo, descricao, isCompleted, id_usuario)
        VALUES (?, ?, ?, ?)
        RETURNING ID_TASK
    ''', (titulo, descricao, isCompleted, id_usuario))

    id_task = cursor.fetchone()[0]

    con.commit()

    cursor.close()

    return jsonify({
        "success": "Tarefa adicionada com sucesso!",
        "newTask": {
            "titulo": titulo,
            "descricao": descricao,
            "id": id_task,
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
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    data = request.get_json()

    id_task = data.get('id_task')
    titulo = data.get('titulo')
    descricao = data.get('descricao')
    isCompleted = data.get('isCompleted')

    if not id_task:
        return jsonify({
            'error': 'É necessário informar o ID da tarefa.'
        }), 400

    if titulo is not None or descricao is not None or isCompleted is not None:

        con = connectDb()

        cursor = con.cursor()

        query = []
        params = []

        if titulo is not None:
            query.append("titulo = ?")
            params.append(titulo)
        if descricao is not None:
            query.append("descricao = ?")
            params.append(descricao)
        if isCompleted is not None:
            query.append("isCompleted = ?")
            params.append(isCompleted)

        if query:
            query = ", ".join(query)
            params.append(id_task)
            params.append(id_usuario)

        cursor.execute(f'''
            UPDATE TASK
            SET {query}
            WHERE id_task = ? AND id_usuario = ?
        ''', (tuple(params)))

        con.commit()

        cursor.close()

        return jsonify({
            "success": "Tarefa atualizada com sucesso!"
        }), 200

    else:
        return jsonify({
            'error': 'É necessário informar ao menos um parâmetro para atualizar a tarefa.'
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
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    data = request.get_json()

    id_task = data.get('id_task')

    if not id_task:
        return jsonify({
            'error': 'Dados incompletos.'
        }), 400

    con = connectDb()

    cursor = con.cursor()

    cursor.execute('''
        SELECT 1
        FROM TASK
        WHERE id_task = ? AND ID_USUARIO = ?
    ''', (id_task, id_usuario))

    row = cursor.fetchone()

    if not row:
        cursor.close()

        return jsonify({
            'error': 'Tarefa não encontrada.'
        }), 404

    cursor.execute('''
        DELETE FROM TASK
        WHERE id_task = ?
        AND id_usuario = ?
    ''', (id_task, id_usuario))

    con.commit()

    cursor.close()

    return jsonify({
        "success": "Tarefa deletada com sucesso!"
    }), 200