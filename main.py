from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/task', methods=['GET'])
def get_tasks():
    con = sqlite3.connect('banco.db')

    cursor = con.cursor()

    cursor.execute("SELECT * FROM TASK")

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


@app.route('/task', methods=['POST'])
def create_tasks():

    data = request.get_json()

    titulo = data.get('titulo')
    descricao = data.get('descricao')
    isCompleted = data.get('isCompleted')

    if not titulo or not descricao or isCompleted not in [False, True]:
        return jsonify({
            'error': 'Dados incompletos.'
        }), 400

    con = sqlite3.connect('banco.db')

    cursor = con.cursor()

    cursor.execute('''
        INSERT INTO TASK (titulo, descricao, isCompleted)
        VALUES (?, ?, ?)
    ''', (titulo, descricao, isCompleted))

    con.commit()

    cursor.close()

    return jsonify({
        "success": "Tarefa adicionada com sucesso!"
    }), 200

@app.route('/task', methods=['PUT'])
def update_tasks():

    data = request.get_json()

    id_task = data.get('id_task')
    titulo = data.get('titulo')
    descricao = data.get('descricao')
    isCompleted = data.get('isCompleted')

    if not id_task or not titulo or not descricao or isCompleted not in [False, True]:
        return jsonify({
            'error': 'Dados incompletos.'
        }), 400

    con = sqlite3.connect('banco.db')

    cursor = con.cursor()

    cursor.execute('''
        UPDATE TASK
        SET titulo = ?, descricao = ?, isCompleted = ?
        WHERE id_task = ?
    ''', (titulo, descricao, isCompleted, id_task))

    con.commit()

    cursor.close()

    return jsonify({
        "success": "Tarefa atualizada com sucesso!"
    }), 200


@app.route('/task', methods=['DELETE'])
def remove_tasks():

    data = request.get_json()

    id_task = data.get('id_task')

    if not id_task:
        return jsonify({
            'error': 'Dados incompletos.'
        }), 400

    con = sqlite3.connect('banco.db')

    cursor = con.cursor()

    cursor.execute('''
        SELECT 1
        FROM TASK
        WHERE id_task = ?
    ''', (id_task,))

    row = cursor.fetchone()

    if not row:
        cursor.close()

        return jsonify({
            'error': 'Tarefa não encontrada.'
        }), 404

    cursor.execute('''
        DELETE FROM TASK
        WHERE id_task = ?
    ''', (id_task,))

    con.commit()

    cursor.close()

    return jsonify({
        "success": "Tarefa deletada com sucesso!"
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)