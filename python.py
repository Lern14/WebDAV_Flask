import os
import requests
from flask import Flask, render_template, send_from_directory, abort, request, Response, redirect, url_for, flash
from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from waitress import create_server
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Определение базовой директории вашего приложения
base_dir = os.path.dirname(os.path.abspath(__file__))

# Путь к папке `htdocs`
htdocs_path = os.path.join(base_dir, 'wsgidav', 'dir_browser', 'htdocs')

# ________Путь к целевой директории
target_directory = r"G:\Distr"

# _________Сетевой адрес сервера
server_ip = '192.168.100.000'  # измените на фактический IP-адрес вашего сервера

# _______Конфигурация WsgiDAV
dav_config = {
    "provider_mapping": {
        "/webdav": FilesystemProvider(target_directory)
    },
    "simple_dc": {
        "user_mapping": {"*": True},
    },
    "dir_browser": {
        "enable": True,
        "response_trailer": True,
        "davmount": True,
        "htdocs_path": htdocs_path  # Указываем путь к папке htdocs
    },
    "verbose": 2,
}

# Создание WsgiDAV приложения
dav_app = WsgiDAVApp(dav_config)

def basic_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == 'master' and auth.password == '1qazXSW@'):
            return Response(
                'Login required', 401,
                {'WWW-Authenticate': 'Basic realm="Login required"'})
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@app.route('/<path:subpath>')
@basic_auth_required
def index(subpath=''):
    directory_path = os.path.join(target_directory, subpath)
    return list_directory(directory_path)

@app.route('/download/<path:filename>', methods=['GET'])
@basic_auth_required
def download_file(filename):
    file_path = os.path.join(target_directory, filename.replace('/', os.path.sep))
    if os.path.exists(file_path):
        return send_from_directory(directory=os.path.dirname(file_path), path=os.path.basename(file_path), as_attachment=True)
    else:
        abort(404)

def list_directory(directory_path):
    try:
        files = []
        for f in os.listdir(directory_path):
            file_path = os.path.join(directory_path, f)
            file_info = {
                'name': f,
                'is_dir': os.path.isdir(file_path),
                'size': os.path.getsize(file_path) / (1024 * 1024) if not os.path.isdir(file_path) else '',
                'creation_time': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                'full_path': file_path.replace('\\', '/'),
                'network_path': fr"\\\\lan\\dfs\\Distr\\{os.path.relpath(file_path, target_directory).replace(os.sep, r'\\')}"
            }
            files.append(file_info)
        current_directory = os.path.relpath(directory_path, target_directory).replace('\\', '/')
        return render_template('index.html', files=files, current_directory=current_directory)
    except FileNotFoundError:
        abort(404)

@app.route('/search', methods=['GET', 'POST'])
@basic_auth_required
def search():
    if request.method == 'POST':
        query = request.form['query']
        result_files = []
        for root, dirs, files in os.walk(target_directory):
            for name in files:
                if query.lower() in name.lower():
                    file_path = os.path.join(root, name)
                    file_info = {
                        'name': name,
                        'size': os.path.getsize(file_path) / (1024 * 1024),  # размер в МБ
                        'creation_time': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                        'path': os.path.relpath(file_path, target_directory).replace('\\', '/'),
                        'network_path': fr"\\\\lan\\dfs\\Distr\\{os.path.relpath(file_path, target_directory).replace(os.sep, r'\\')}"
                    }
                    result_files.append(file_info)
        return render_template('search.html', query=query, result_files=result_files)
    return render_template('search.html')

@app.route('/download_url', methods=['GET', 'POST'])
@basic_auth_required
def download_url():
    if request.method == 'POST':
        url = request.form['url']
        current_directory = request.form['current_directory']
        download_path = os.path.join(target_directory, current_directory.replace('/', os.path.sep))

        try:
            local_filename = os.path.join(download_path, url.split('/')[-1])
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            flash(f'Файл {local_filename} успешно загружен!', 'success')
            return redirect(url_for('index', subpath=current_directory))
        except Exception as e:
            flash(f'Ошибка при загрузке файла: {str(e)}', 'danger')
            return redirect(url_for('index', subpath=current_directory))
    current_directory = request.args.get('current_directory', '')
    return render_template('download_url.html', current_directory=current_directory)

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/webdav': dav_app
})

if __name__ == '__main__':
    server = create_server(app, host='0.0.0.0', port=20555)
    print(f"Сервер запущен на порту {server.effective_port}")
    server.run()
