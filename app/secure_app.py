from flask import Flask, request, render_template_string, session, redirect, url_for, flash, abort
import sqlite3
import os
import hashlib
import secrets
import logging
from datetime import timedelta
from functools import wraps
import re

# ===== CONFIGURACIÓN DE LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== INICIALIZACIÓN DE LA APP =====
app = Flask(__name__)

# ===== CONFIGURACIÓN DE SEGURIDAD =====
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(minutes=30)

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# ===== FUNCIONES DE BASE DE DATOS =====
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ===== DECORADORES DE SEGURIDAD =====
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"Intento de acceso no autenticado desde {request.remote_addr}")
            flash('Por favor inicia sesión primero')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            logger.warning(f"Intento de acceso admin no autorizado desde {request.remote_addr}")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# ===== FUNCIONES DE SANITIZACIÓN =====
def sanitize_input(text):
    if text is None:
        return ""
    sanitized = re.sub(r'[<>"\'%;()&+]', '', text)
    return sanitized[:200]

# ===== RUTAS DE LA APLICACIÓN =====
@app.route('/')
def index():
    logger.info(f"Acceso a página principal desde {request.remote_addr}")
    return 'Welcome to the Secure Task Manager Application!'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            logger.warning(f"Intento de login con campos vacíos desde {request.remote_addr}")
            return 'Username y password son requeridos'

        if len(username) > 50 or len(password) > 50:
            logger.warning(f"Intento de login con datos muy largos desde {request.remote_addr}")
            return 'Datos inválidos'

        conn = get_db_connection()
        try:
            # ✅ CONSULTA PARAMETRIZADA - SQL INJECTION PREVENIDO
            query = "SELECT * FROM users WHERE username = ? AND password = ?"
            hashed_password = hash_password(password)
            user = conn.execute(query, (username, hashed_password)).fetchone()

            logger.info(f"Intento de login para usuario: {username} desde {request.remote_addr}")

            if user:
                session.permanent = True
                session['user_id'] = user['id']
                session['role'] = user['role']
                logger.info(f"Login exitoso: {username} (ID: {user['id']}, Rol: {user['role']})")
                return redirect(url_for('dashboard'))
            else:
                logger.warning(f"Login fallido para usuario: {username} desde {request.remote_addr}")
                return 'Credenciales inválidas!'
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            return 'Error interno del servidor'
        finally:
            conn.close()

    return '''
        <form method="post">
            Username: <input type="text" name="username" required><br>
            Password: <input type="password" name="password" required><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db_connection()

    try:
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ?", (user_id,)
        ).fetchall()

        user = conn.execute(
            "SELECT username, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        username = user['username'] if user else "Usuario"
        role = user['role'] if user else "user"
    except Exception as e:
        logger.error(f"Error en dashboard para user {user_id}: {str(e)}")
        tasks = []
        username = "Usuario"
        role = "user"
    finally:
        conn.close()

    return render_template_string('''
        <h1>Welcome, {{ username }}!</h1>
        <p>Role: {{ role }}</p>
        <form action="/add_task" method="post">
            <input type="text" name="task" placeholder="New task" maxlength="200" required><br>
            <input type="submit" value="Add Task">
        </form>
        <h2>Your Tasks</h2>
        <ul>
        {% for task in tasks %}
            <li>{{ task['task'] }} <a href="/delete_task/{{ task['id'] }}">Delete</a></li>
        {% endfor %}
        </ul>
        <a href="/logout">Logout</a>
    ''', username=username, role=role, tasks=tasks)

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    task = request.form.get('task', '').strip()

    if not task:
        flash('La tarea no puede estar vacía')
        return redirect(url_for('dashboard'))

    task = sanitize_input(task)

    if len(task) < 1:
        flash('Tarea inválida')
        return redirect(url_for('dashboard'))

    user_id = session['user_id']

    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO tasks (user_id, task) VALUES (?, ?)", (user_id, task)
        )
        conn.commit()
        logger.info(f"Tarea agregada: usuario {user_id} - {task[:50]}")
    except Exception as e:
        logger.error(f"Error al agregar tarea para user {user_id}: {str(e)}")
        flash('Error al agregar la tarea')
    finally:
        conn.close()

    return redirect(url_for('dashboard'))

@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        task = conn.execute(
            "SELECT user_id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()

        if not task:
            logger.warning(f"Intento de eliminar tarea inexistente ID:{task_id}")
            flash('Tarea no encontrada')
            return redirect(url_for('dashboard'))

        if task['user_id'] != user_id:
            logger.warning(f"Intento de eliminar tarea de otro usuario ID:{task_id} - User:{user_id}")
            flash('No tienes permiso para eliminar esta tarea')
            return redirect(url_for('dashboard'))

        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        logger.info(f"Tarea {task_id} eliminada por usuario {user_id}")
    except Exception as e:
        logger.error(f"Error al eliminar tarea: {str(e)}")
        flash('Error al eliminar la tarea')
    finally:
        conn.close()

    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
@admin_required
def admin():
    conn = get_db_connection()
    try:
        users = conn.execute("SELECT id, username, role FROM users").fetchall()
        total_tasks = conn.execute("SELECT COUNT(*) as count FROM tasks").fetchone()['count']
    except Exception as e:
        logger.error(f"Error en admin panel: {str(e)}")
        users = []
        total_tasks = 0
    finally:
        conn.close()

    return render_template_string('''
        <h1>Admin Panel</h1>
        <h2>Users</h2>
        <ul>
        {% for user in users %}
            <li>{{ user['username'] }} ({{ user['role'] }})</li>
        {% endfor %}
        </ul>
        <p>Total Tasks: {{ total_tasks }}</p>
        <a href="/dashboard">Back to Dashboard</a>
        <a href="/logout">Logout</a>
    ''', users=users, total_tasks=total_tasks)

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    logger.info(f"Logout usuario {user_id}")
    session.clear()
    return redirect(url_for('login'))

# ===== INICIO DE LA APLICACIÓN =====
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))

    logger.info(f"Iniciando aplicación en {host}:{port} (debug={debug_mode})")
    app.run(host=host, port=port, debug=debug_mode)
