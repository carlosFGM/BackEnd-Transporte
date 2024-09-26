from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from email_validator import validate_email, EmailNotValidError
from datetime import datetime
import os, secrets, pytz, json, bcrypt 
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/prueba'
db = SQLAlchemy(app)

cdmx_tz = pytz.timezone('America/Mexico_City')

#1
class Usuario(db.Model):
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(10), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(cdmx_tz))
    fecha_actualizacion = db.Column(db.DateTime, default=lambda: datetime.now(cdmx_tz))
    token = db.Column(db.String(50), nullable=False)

class Reporte(db.Model):
    id_reporte = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    fecha = db.Column(db.DateTime, default=lambda: datetime.now(cdmx_tz))
    id_ruta = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)

class Ruta(db.Model):
    id_ruta = db.Column(db.Integer, primary_key=True)
    numero_ruta = db.Column(db.String(50), unique=True, nullable=False)
    estatus = db.Column(db.String(50), nullable=False)

#2
with app.app_context():
    db.create_all()

#3
@app.route('/rutas', methods=['GET'])
def get_rutas():
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), './'))
        json_path = os.path.join(base_dir, 'rutas.json')
        
        with open(json_path) as f:
            data = json.load(f)  
        
        return jsonify(data), 200 
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#4
@app.route('/validarCorreo', methods=['POST'])
def validar_correo():
    try:
        data = request.json
        email = data['correo']
        
        valid = validate_email(email)
        return jsonify({"correo": valid.email, "estatus": "valido"})
    
    except EmailNotValidError as e:
        return jsonify({"error": str(e), "estatus": "invalido"}), 400

#5
@app.route('/insertarUsuario', methods=['POST'])
def insertar_usuario():
    data = request.json
    try:
        try:
            validate_email(data['correo']) 
        except EmailNotValidError as e:
            return jsonify({"error": str(e), "estatus": "invalido"}), 400
        
        usuario_existente = Usuario.query.filter_by(correo=data['correo']).first()
        if usuario_existente:
            return jsonify({"error": "El correo ya está registrado", "estatus": "correo_duplicado"}), 409
        
        token = secrets.token_hex(25)
        fecha_creacion = datetime.now(cdmx_tz)
        fecha_actualizacion = datetime.now(cdmx_tz)
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        nuevo_usuario = Usuario(
            nombres=data['nombres'],
            correo=data['correo'],
            password=hashed_password.decode('utf-8'),
            telefono=data['telefono'],
            token=token,
            fecha_creacion=fecha_creacion,
            fecha_actualizacion=fecha_actualizacion
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        return jsonify({"mensaje": "Usuario insertado correctamente", "id_usuario": nuevo_usuario.id_usuario}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

#6
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    try:
        correo = data['correo']
        password = data['password']
        
        usuario = Usuario.query.filter_by(correo=correo).first()
        
        if not usuario:  
            return jsonify({"mensaje": "Usuario no encontrado"}), 404
        
        if not bcrypt.checkpw(password.encode('utf-8'), usuario.password.encode('utf-8')):
            return jsonify({"mensaje": "Contraseña incorrecta"}), 401
        
        return jsonify({
            "mensaje": "Login exitoso",
            "token": usuario.token
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#6
@app.route('/insertarReporte', methods=['POST'])
def insertar_reporte():
    data = request.json
    try:
        nuevo_reporte = Reporte(
            id_usuario=data['id_usuario'],
            fecha=datetime.strptime(data['fecha'], '%Y-%m-%d %H:%M:%S'),
            id_ruta=data['id_ruta'],
            descripcion=data['descripción']
        )
        db.session.add(nuevo_reporte)
        db.session.commit()
        return jsonify({"mensaje": "Reporte insertado correctamente", "id_reporte": nuevo_reporte.id_reporte}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
      
#7
@app.route('/insertarRuta', methods=['POST'])
def insertar_ruta():
    data = request.json
    try:
        nueva_ruta = Ruta(
            numero_ruta=data['numero_ruta'],
            estatus=data['estatus']
        )
        db.session.add(nueva_ruta)
        db.session.commit()
        return jsonify({"mensaje": "Ruta insertada correctamente", "id_ruta": nueva_ruta.id_ruta}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)