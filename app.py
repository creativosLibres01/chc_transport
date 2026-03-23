import os
import re
import json
import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cambiar-en-produccion-clave-secreta-32chars')
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

csrf = CSRFProtect(app)
def _limiter_key():
    return request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1').split(',')[0].strip()

limiter = Limiter(
    app=app,
    key_func=_limiter_key,
    default_limits=["200 per day", "50 per hour"]
)

# En Vercel solo /tmp es escribible; los datos no persisten entre deploys
DATA_DIR = Path('/tmp/chc_data') if os.environ.get('VERCEL') else Path('data')
DATA_DIR.mkdir(exist_ok=True)
RESERVAS_FILE = DATA_DIR / 'reservas.json'
CONTACTOS_FILE = DATA_DIR / 'contactos.json'

# Validación: longitud máxima de campos
MAX_LEN = {'nombre': 120, 'telefono': 20, 'origen': 100, 'destino': 100, 'correo': 120, 'mensaje': 1000, 'notas': 500}
TEL_REGEX = re.compile(r'^[\d\s\+\-\(\)]{7,20}$')
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def _validate_reserva(data):
    err = []
    if not (data.get('nombre') or '').strip():
        err.append('Nombre requerido')
    elif len(data.get('nombre', '')) > MAX_LEN['nombre']:
        err.append('Nombre demasiado largo')
    if not (data.get('telefono') or '').strip():
        err.append('Teléfono requerido')
    elif not TEL_REGEX.match((data.get('telefono') or '').replace(' ', '')):
        err.append('Teléfono inválido')
    if not (data.get('origen') or '').strip():
        err.append('Origen requerido')
    elif len(data.get('origen', '')) > MAX_LEN['origen']:
        err.append('Origen demasiado largo')
    if not (data.get('destino') or '').strip():
        err.append('Destino requerido')
    elif len(data.get('destino', '')) > MAX_LEN['destino']:
        err.append('Destino demasiado largo')
    fecha = data.get('fecha')
    if not fecha:
        err.append('Fecha requerida')
    else:
        try:
            dt = datetime.datetime.strptime(fecha, '%Y-%m-%d')
            if dt.date() < datetime.date.today():
                err.append('La fecha no puede ser pasada')
        except ValueError:
            err.append('Fecha inválida')
    if not data.get('hora'):
        err.append('Hora requerida')
    pax = data.get('pax')
    if pax is None or pax == '':
        err.append('Pasajeros requerido')
    else:
        try:
            n = int(pax)
            if n < 1 or n > 200:
                err.append('Pasajeros debe estar entre 1 y 200')
        except ValueError:
            err.append('Pasajeros inválido')
    if len(data.get('notas', '') or '') > MAX_LEN['notas']:
        err.append('Notas demasiado largas')
    return err

def _validate_contacto(data):
    err = []
    if not (data.get('nombre') or '').strip():
        err.append('Nombre requerido')
    elif len(data.get('nombre', '')) > MAX_LEN['nombre']:
        err.append('Nombre demasiado largo')
    if not (data.get('correo') or '').strip():
        err.append('Correo requerido')
    elif not EMAIL_REGEX.match((data.get('correo') or '').strip()):
        err.append('Correo inválido')
    elif len(data.get('correo', '')) > MAX_LEN['correo']:
        err.append('Correo demasiado largo')
    if not (data.get('telefono') or '').strip():
        err.append('Teléfono requerido')
    elif not TEL_REGEX.match((data.get('telefono') or '').replace(' ', '')):
        err.append('Teléfono inválido')
    if not (data.get('mensaje') or '').strip():
        err.append('Mensaje requerido')
    elif len(data.get('mensaje', '')) > MAX_LEN['mensaje']:
        err.append('Mensaje demasiado largo')
    return err

def _append_json(filepath, payload):
    if filepath.exists():
        try:
            data = json.loads(filepath.read_text(encoding='utf-8'))
            if not isinstance(data, list):
                data = []
        except Exception:
            data = []
    else:
        data = []
    data.append(payload)
    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def _sanitize(obj):
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, str):
        return obj.strip()[:500]
    return obj

@app.route('/')
def index():
    return render_template('index.html')

@app.post('/api/reservar')
@limiter.limit("5 per minute")
def reservar():
    payload = _sanitize(request.get_json(force=True, silent=True) or {})
    err = _validate_reserva(payload)
    if err:
        return jsonify(ok=False, message='Por favor corrige los datos.', errors=err), 400
    payload['created_at'] = datetime.datetime.now().isoformat(timespec='seconds')
    _append_json(RESERVAS_FILE, payload)
    return jsonify(ok=True, message='¡Reserva registrada! Pronto nos pondremos en contacto.'), 201

@app.post('/api/contacto')
@limiter.limit("5 per minute")
def contacto():
    payload = _sanitize(request.get_json(force=True, silent=True) or {})
    err = _validate_contacto(payload)
    if err:
        return jsonify(ok=False, message='Por favor corrige los datos.', errors=err), 400
    payload['created_at'] = datetime.datetime.now().isoformat(timespec='seconds')
    _append_json(CONTACTOS_FILE, payload)
    return jsonify(ok=True, message='Mensaje enviado. Gracias por escribirnos.'), 201

@app.get('/health')
def health():
    return {'status': 'ok'}

# Endpoint para obtener token CSRF (para APIs)
@app.get('/api/csrf-token')
def csrf_token():
    from flask_wtf.csrf import generate_csrf
    return jsonify(csrf_token=generate_csrf())

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=debug)
