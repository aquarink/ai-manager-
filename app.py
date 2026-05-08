from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import os
import datetime
import requests
import urllib.parse

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

app.config['SECRET_KEY'] = 'super-secret-key-itcha'
password = urllib.parse.quote_plus('VeryStronGPassWord@9290')
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postdefault:{password}@localhost/ai_manager_db'
app.config['UPLOAD_FOLDER'] = '/var/www/ai-manager/uploads'

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS ---
class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    price = db.Column(db.Float)
    max_agents = db.Column(db.Integer)
    max_file_size_mb = db.Column(db.Integer)
    quota = db.Column(db.Integer, default=0)

class Client(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    api_key = db.Column(db.String(100), unique=True)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'))
    is_admin = db.Column(db.Boolean, default=False)
    usage_count = db.Column(db.Integer, default=0)

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    name = db.Column(db.String(50))
    system_prompt = db.Column(db.Text)
    model_name = db.Column(db.String(50), default='llama3.1:8b')
    files = db.relationship('AgentFile', backref='agent', lazy=True, cascade="all, delete-orphan")

class AgentFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    filename = db.Column(db.String(100))
    file_path = db.Column(db.String(255))
    file_size_bytes = db.Column(db.BigInteger, default=0)

class ApiLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer)
    agent_id = db.Column(db.Integer)
    prompt = db.Column(db.Text)
    response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return Client.query.get(int(user_id))

# --- HELPERS ---
def get_client_storage_usage(client_id):
    total_size = db.session.query(db.func.sum(AgentFile.file_size_bytes)).join(Agent).filter(Agent.client_id == client_id).scalar()
    return total_size or 0

# --- ROUTES ---
@app.route('/')
def index():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Client.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        clients = Client.query.all()
        packages = Package.query.all()
        logs = ApiLog.query.order_by(ApiLog.timestamp.desc()).limit(10).all()
        return render_template('admin_dashboard.html', clients=clients, packages=packages, logs=logs)
    else:
        agents = Agent.query.filter_by(client_id=current_user.id).all()
        client_pkg = Package.query.get(current_user.package_id)
        storage_usage = get_client_storage_usage(current_user.id)
        return render_template('client_dashboard.html', agents=agents, package=client_pkg, storage_usage=storage_usage)

@app.route('/logout')
def logout():
    logout_user(); return redirect(url_for('login'))

# --- ADMIN CRUD ---
@app.route('/admin/package/add', methods=['POST'])
@login_required
def add_package():
    if not current_user.is_admin: return redirect(url_for('dashboard'))
    new_pkg = Package(name=request.form['name'], price=request.form['price'], max_agents=request.form['max_agents'], max_file_size_mb=request.form['max_file_size_mb'], quota=request.form['quota'])
    db.session.add(new_pkg); db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/admin/package/edit/<int:id>', methods=['POST'])
@login_required
def edit_package(id):
    if not current_user.is_admin: return redirect(url_for('dashboard'))
    pkg = Package.query.get_or_404(id)
    pkg.name = request.form['name']; pkg.price = request.form['price']; pkg.max_agents = request.form['max_agents']; pkg.quota = request.form['quota']; pkg.max_file_size_mb = request.form['max_file_size_mb']
    db.session.commit(); return redirect(url_for('dashboard'))

@app.route('/admin/package/delete/<int:id>')
@login_required
def delete_package(id):
    if not current_user.is_admin: return redirect(url_for('dashboard'))
    db.session.delete(Package.query.get_or_404(id)); db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/admin/client/add', methods=['POST'])
@login_required
def add_client():
    if not current_user.is_admin: return redirect(url_for('dashboard'))
    import uuid
    new_client = Client(username=request.form['username'], password=request.form['password'], package_id=request.form['package_id'], api_key=str(uuid.uuid4()))
    db.session.add(new_client); db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/admin/client/edit/<int:id>', methods=['POST'])
@login_required
def edit_client(id):
    if not current_user.is_admin: return redirect(url_for('dashboard'))
    c = Client.query.get_or_404(id)
    c.username = request.form['username']; c.package_id = request.form['package_id']
    if request.form['password']: c.password = request.form['password']
    db.session.commit(); return redirect(url_for('dashboard'))

@app.route('/admin/client/delete/<int:id>')
@login_required
def delete_client(id):
    if not current_user.is_admin: return redirect(url_for('dashboard'))
    db.session.delete(Client.query.get_or_404(id)); db.session.commit()
    return redirect(url_for('dashboard'))

# --- CLIENT CRUD ---
@app.route('/agent/add', methods=['POST'])
@login_required
def add_agent():
    pkg = Package.query.get(current_user.package_id)
    if pkg.max_agents > 0 and Agent.query.filter_by(client_id=current_user.id).count() >= pkg.max_agents:
        flash('Agent limit reached'); return redirect(url_for('dashboard'))
    new_agent = Agent(client_id=current_user.id, name=request.form['name'], system_prompt=request.form['system_prompt'])
    db.session.add(new_agent); db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/agent/edit/<int:id>', methods=['POST'])
@login_required
def edit_agent(id):
    a = Agent.query.get_or_404(id)
    if a.client_id != current_user.id: return "Forbidden", 403
    a.name = request.form['name']; a.system_prompt = request.form['system_prompt']
    db.session.commit(); return redirect(url_for('dashboard'))

@app.route('/agent/delete/<int:id>')
@login_required
def delete_agent(id):
    a = Agent.query.get_or_404(id)
    if a.client_id != current_user.id: return "Forbidden", 403
    db.session.delete(a); db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/agent/upload/<int:agent_id>', methods=['POST'])
@login_required
def upload_file(agent_id):
    a = Agent.query.get_or_404(agent_id)
    if a.client_id != current_user.id: return "Forbidden", 403
    pkg = Package.query.get(current_user.package_id)
    
    files = request.files.getlist('file')
    for file in files:
        if file:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], f"{agent_id}_{filename}")
            file.save(path)
            size = os.path.getsize(path)
            
            # Check Storage Limit
            current_usage = get_client_storage_usage(current_user.id)
            if pkg.max_file_size_mb > 0 and (current_usage + size) > (pkg.max_file_size_mb * 1024 * 1024):
                os.remove(path)
                flash(f"Storage limit exceeded! ({pkg.max_file_size_mb} MB max)")
                return redirect(url_for('dashboard'))
            
            db.session.add(AgentFile(agent_id=agent_id, filename=filename, file_path=path, file_size_bytes=size))
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/agent/file/delete/<int:id>')
@login_required
def delete_file(id):
    f = AgentFile.query.get_or_404(id)
    a = Agent.query.get(f.agent_id)
    if a.client_id != current_user.id: return "Forbidden", 403
    if os.path.exists(f.file_path): os.remove(f.file_path)
    db.session.delete(f); db.session.commit()
    return redirect(url_for('dashboard'))

# --- API GATEWAY ---
@app.route('/api/chat', methods=['POST'])
def api_chat():
    key = request.headers.get('X-API-KEY')
    c = Client.query.filter_by(api_key=key).first()
    if not c: return jsonify({"error": "Invalid API Key"}), 401
    pkg = Package.query.get(c.package_id)
    if pkg.quota > 0 and c.usage_count >= pkg.quota: return jsonify({"error": "Quota exceeded"}), 403
    data = request.json
    a = Agent.query.get(data.get('agent_id'))
    if not a or a.client_id != c.id: return jsonify({"error": "Agent not found"}), 404
    try:
        resp = requests.post("http://localhost:11434/v1/chat/completions", json={"model": a.model_name, "messages": [{"role": "system", "content": a.system_prompt}, {"role": "user", "content": data.get('message')}]})
        ai_resp = resp.json()['choices'][0]['message']['content']
        c.usage_count += 1
        db.session.add(ApiLog(client_id=c.id, agent_id=a.id, prompt=data.get('message'), response=ai_resp))
        db.session.commit()
        return jsonify({"response": ai_resp})
    except Exception as e: return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=5001)
