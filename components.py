import jwt
from main import SENHA_SECRETA
from supabase_client import supabase

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

# Validar token
def validar_user(id_usuario, email):

    response = (
        supabase
        .table('USUARIOS')
        .select()
        .limit(1)
        .eq('ID_USUARIO', id_usuario)
        .eq('EMAIL', email)
        .eq('CONFIRMADO', 1)
        .single()
        .execute()
    )

    if response.data:
        return True

    return False

def generateToken(idUsuario, email):
    payload = {
        'id_usuario': idUsuario,
        'email': email
    }

    token = jwt.encode(payload, SENHA_SECRETA, algorithm='HS256')

    return token