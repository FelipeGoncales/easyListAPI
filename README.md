# EasyList API

API REST desenvolvida com **Flask** para o gerenciamento de tarefas do EasyList. Responsável por autenticação de usuários, cadastro com verificação por e-mail e operações CRUD de tarefas.

🔗 **Deploy:** [Render](https://render.com) — `https://sua-api.onrender.com`

---

## Tecnologias

- **Python 3.13**
- **Flask** — framework web
- **Flask-CORS** — liberação de CORS para o frontend
- **Flask-Bcrypt** — hash de senhas
- **PyJWT** — autenticação via tokens JWT
- **Supabase (PostgreSQL)** — banco de dados
- **Gunicorn** — servidor WSGI para produção
- **smtplib** — envio de e-mails de verificação via Gmail SMTP

---

## Variáveis de Ambiente

Configure as seguintes variáveis no painel do Render (ou em um arquivo `.env` local):

| Variável | Descrição |
|---|---|
| `SUPABASE_URL` | URL do projeto no Supabase |
| `SUPABASE_KEY` | Chave anon/public do Supabase |

---

## Endpoints

### Autenticação

#### `POST /login`
Realiza o login do usuário.

**Body (JSON):**
```json
{
  "email": "usuario@email.com",
  "senha": "Senha123!"
}
```

**Respostas:**
- `200` — Login realizado, retorna o token JWT
- `401` — Senha incorreta
- `400` — E-mail não confirmado
- `404` — Usuário não encontrado

---

### Cadastro

#### `POST /cadastro`
Cria um novo usuário e envia o código de verificação por e-mail.

**Body (JSON):**
```json
{
  "nome": "Felipe",
  "email": "felipe@email.com",
  "senha": "Senha123!"
}
```

A senha deve ter: mínimo 8 caracteres, uma letra maiúscula, um número e um símbolo especial.

**Respostas:**
- `200` — Código enviado por e-mail
- `400` — Dados incompletos, e-mail já cadastrado ou senha inválida

---

#### `GET /cadastro`
Retorna os dados do usuário autenticado.

**Headers:** `Authorization: Bearer <token>`

**Respostas:**
- `200` — Retorna os dados do usuário
- `401` — Token ausente, expirado ou inválido
- `400` — E-mail não confirmado ou usuário não encontrado

---

#### `PUT /cadastro`
Atualiza os dados do usuário (nome, e-mail e/ou senha).

**Headers:** `Authorization: Bearer <token>`

**Body (JSON):**
```json
{
  "nome": "Felipe Gonçales",
  "email": "novoemail@email.com",
  "senhaAtual": "Senha123!",
  "senhaNova": "NovaSenha456@",
  "senhaNovaConfirm": "NovaSenha456@"
}
```

Se o e-mail for alterado, um novo código de verificação será enviado.

**Respostas:**
- `200` — Alterações salvas
- `400` — Senha atual incorreta, senhas divergentes ou dados inválidos
- `401` — Token ausente ou inválido

---

#### `DELETE /cadastro`
Remove permanentemente a conta do usuário autenticado.

**Headers:** `Authorization: Bearer <token>`

**Respostas:**
- `200` — Usuário deletado com sucesso
- `401` — Token ausente, expirado ou inválido

---

#### `POST /validar-cadastro`
Valida o código de verificação enviado por e-mail. O código expira em 20 minutos.

**Body (JSON):**
```json
{
  "email": "felipe@email.com",
  "codigo": "123456"
}
```

**Respostas:**
- `200` — Cadastro aprovado, retorna o token JWT
- `400` — Código incorreto, expirado ou e-mail não cadastrado

---

#### `GET /reenviar-codigo?email=<email>`
Reenvia o código de verificação para o e-mail informado.

**Query params:** `email`

**Respostas:**
- `200` — Código reenviado
- `400` — Usuário não encontrado

---

### Tarefas

Todos os endpoints de tarefa exigem o header `Authorization: Bearer <token>`.

#### `GET /task`
Lista todas as tarefas do usuário autenticado, ordenadas por data.

**Resposta `200`:**
```json
{
  "tasks": [
    {
      "id": 1,
      "titulo": "Estudar Flask",
      "descricao": "Revisar documentação",
      "isCompleted": false,
      "data": "2026-05-01"
    }
  ]
}
```

---

#### `GET /task/<id_task>`
Retorna uma tarefa específica pelo ID.

**Resposta `200`:**
```json
{
  "task": {
    "id": 1,
    "titulo": "Estudar Flask",
    "descricao": "Revisar documentação",
    "isCompleted": false,
    "data": "2026-05-01"
  }
}
```

- `404` — Tarefa não encontrada

---

#### `POST /task`
Cria uma nova tarefa.

**Body (JSON):**
```json
{
  "titulo": "Estudar Flask",
  "descricao": "Revisar documentação",
  "isCompleted": false,
  "data": "2026-05-01"
}
```

A data deve estar no formato `YYYY-MM-DD`.

**Resposta `200`:** Retorna os dados da tarefa criada incluindo o ID gerado.

---

#### `PUT /task`
Atualiza uma tarefa existente. Apenas os campos informados serão alterados.

**Body (JSON):**
```json
{
  "id_task": 1,
  "titulo": "Novo título",
  "isCompleted": true
}
```

**Respostas:**
- `200` — Tarefa atualizada
- `400` — ID não informado ou nenhum campo para atualizar

---

#### `DELETE /task`
Remove uma tarefa pelo ID.

**Body (JSON):**
```json
{
  "id_task": 1
}
```

**Respostas:**
- `200` — Tarefa deletada
- `404` — Tarefa não encontrada

---

## Autenticação

A API utiliza **JWT (JSON Web Token)**. Após o login ou validação do cadastro, o token é retornado e deve ser enviado no header de todas as requisições protegidas:

```
Authorization: Bearer <token>
```

---

## Rodando localmente

```bash
# Clone o repositório
git clone https://github.com/FelipeGoncales/easyListAPI.git
cd easyListAPI

# Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
# Crie um arquivo .env com SUPABASE_URL e SUPABASE_KEY

# Rode a aplicação
python main.py
```

A API estará disponível em `http://localhost:5000`.
