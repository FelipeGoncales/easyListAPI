from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["*"])

SENHA_SECRETA = "easylist"
EMAIL_APP = "easylistbgi@gmail.com"
SENHA_APP = "epsjtikubllqfrxx"

from task_view import *
from login_view import *
from cadastro_view import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)