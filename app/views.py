from flask import jsonify, request
from app.models import Usuario, Comment, Category, Tag, Post, post_tag, db
from flask_jwt_extended import get_jwt_identity, create_access_token, jwt_required

def index():
    return jsonify({
        'message':'Bienvenido a la BLOG-API, que simulará un blog con usuarios, posts, comentarios, tags y categorías.'
    }), 200

"""

                    Funciones de registro, logeo y profile(que dará detalles del usuario)

"""
def register():
    data = request.get_json()
    try:
        usuario = Usuario(
            name = data['nombre'],
            last_name = data['apellido'],
            email = data['email'],
            username = data['usuario'],
            pass_hash = data['password'],
            rol = 'usuario',
            status = 'activo',
            data_register = data.get('fecha de registro')
        )
        usuario.set_password_hash(data['password'])
        db.session.add(usuario)
        db.session.commit()
        return jsonify({'message':f'El usuario {data["usuario"]} fue registrado con éxito!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error':f'Error al registrar: {e}'}),403

def login():
    data = request.get_json()
    usuario_login = Usuario.query.filter_by(usuario=data['usuario']).first_or_404()
    if usuario_login and usuario_login.check_password(data['password']):
        access_token = create_access_token(identity=usuario_login.id)
        return jsonify(access_token=access_token), 200
    return jsonify({'error':'Inicio de sesión inválido.'}), 401

@jwt_required()
def profile_public(user_id):
    usuario = Usuario.query.get_or_404(user_id)
    if not usuario:
        return jsonify({'error':'Usuario inexistent.'}), 404
    return jsonify(usuario.serialize_public()), 200

"""

                    CRUD de USUARIOS

"""

@jwt_required()
def profile_private(user_id):
    user_id_jwt = get_jwt_identity()
    usuario = Usuario.query.get_or_404(user_id)
    usuario_login = Usuario.query.filter_by(id=user_id_jwt).first_or_404()

    if not usuario:
        return jsonify({'error':'Usuario inexistent.'}), 404
    
    if usuario_login.id == usuario.id or usuario_login.rol == 'admin':
        return jsonify(usuario.serialize_private()), 200
    

@jwt_required()
def edit_profile(user_id):
    user_id_jwt = get_jwt_identity()
    usuario = Usuario.query.get_or_404(user_id)
    usuario_login = Usuario.query.filter_by(id=user_id_jwt).first()
    try:
        if usuario:
            if usuario.id == usuario_login.id or usuario_login.rol == 'admin':
                data = request.get_json()
            return jsonify({'error':'Usuario inexistent.'}), 404
    except Exception as e:
        return jsonify({'error':f'El error es: {e}'})