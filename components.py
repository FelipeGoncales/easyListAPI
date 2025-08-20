from flask import jsonify, request
import jwt
from main import connectDb, SENHA_SECRETA

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

# Validar token
def validar_user(id_usuario, email):
    con = connectDb()

    cursor = con.cursor()

    cursor.execute('''
        SELECT 1 
        FROM USUARIOS
        WHERE ID_USUARIO = ? AND EMAIL = ? AND CONFIRMADO = 1
    ''', (id_usuario, email))

    if cursor.fetchone():
        return True

    return False