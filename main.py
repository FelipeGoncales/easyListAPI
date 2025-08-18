from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["*"])

def connectDb():
    return sqlite3.connect('banco.db')

SENHA_SECRETA = "easylist"

from task_view import *
from login_view import *
from cadastro_view import *

if __name__ == '__main__':
    app.run(debug=True)