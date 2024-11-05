from flask import jsonify, request
from app.models import Usuario, Comment, Category, Tag, Post, post_tag, db
from flask_jwt_extended import get_jwt_identity, create_access_token, jwt_required
from . import app


# Manejar manualmente los 404
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error='Recurso no encontrado.'), 404

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
        return jsonify({'error':'Usuario inexistente.'}), 404
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
                usuario.name = data.get('nombre',usuario.name)
                usuario.last_name = data.get('apellido',usuario.last_name)
                usuario.email = data.get('email',usuario.email)
                # Si el usuario desea cambiar la contraseña
                # debe ser el SOLAMENTE el que se logea y no
                # un admin.
                if usuario.id == usuario_login.id:
                    current_password = data.get('password_actual')
                    new_password = data.get('nueva_password')
                    # Se comprueba que haya algo escrito en
                    # ambas variables.
                    if current_password and new_password:
                        if Usuario.check_password(usuario.pass_hash,current_password):
                            usuario.pass_hash = Usuario.set_password_hash(new_password)
                        else:
                            return jsonify({'error':'La contraseña actual es incorrecta.'}), 401
                elif usuario_login.rol == "admin":
                    usuario.rol = data.get('rol',usuario.rol)
                db.session.commit()
                return jsonify({'message':f'Usuario {data["usuario"]} actualizado exitosamente.'}), 200
        return jsonify({'error':'Usuario inexistente.'}), 404
    except Exception as e:
        return jsonify({'error':f'El error es: {e}'})
    
@jwt_required()
def edit_profile_status(user_id):
    user_id_jwt = get_jwt_identity()
    usuario = Usuario.query.get_or_404(user_id)
    usuario_login = Usuario.query.filter_by(id=user_id_jwt).first()

    if usuario_login.rol != "admin":
        return jsonify({'error':'No tienes los permisos para la modificación del Rol.'}), 403
    
    data = request.get_json()
    usuario.status = data.get('status')

    if usuario.status == "activo":
        usuario.activate()
    elif usuario.status == "bloqueado":
        usuario.block()
    elif usuario.status == "inactivo":
        usuario.delete()
    else:
        return jsonify({'error':'Debe eligir 1 de los 3 estados.'}), 403
    
    return jsonify({'message':f'El estado del usuarios {data["usuario"]} ha sido actualizado correctamente.'}), 200

"""

                    CRUD de POSTEOS

"""

@jwt_required()
def get_all_post():
    posts = Post.query.all()
    posts_listado = [post.serialize() for post in posts]
    return jsonify((f'Todos los posts: {posts_listado}')), 200

@jwt_required()
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify({post.serialize()}), 200

@jwt_required()
def create_post():
    data = request.get_json()
    autor_id = get_jwt_identity()
    post = Post(
        titulo = data.get['titulo'],
        contenido = data.get('contenido'),
        autor_id = autor_id,
        categoria_id = data.get['categoria'],
    )
    tag_id = data.get('tags',[])
    tags = Tag.query.filter(Tag.id.in_(tag_id)).all()

    post.tags.extends(tags)

    db.session.add(post)
    db.session.commit()

    return jsonify({'message':f'Post {data['titulo']} creado con éxito.'}),200

@jwt_required()
def edit_post(post_id):
    user_iden = get_jwt_identity()
    post = Post.query.get_or_404(post_id)

    if post.autor_id == user_iden.id or user_iden.rol == "admin":
        data = request.get_json()
        post.title = data.get('titulo',post.title)
        post.content = data.get('contenido',post.content)
        post.category_id = data.get('categoria',post.category_id)
        post.status_post = data.get('status_post')
        if post.status_post == 'publicado':
            post.publish()
        elif post.status_post == 'borrador':
            post.draft()
        new_tags_id = data.get('tag',[])
        if new_tags_id:
            new_tags = Tag.query.filter(Tag.id.in_(new_tags_id)).all()
            post.tag_id = new_tags
        try:
            db.session.commit()
            return jsonify({'message':'Post editado correctamente.'}), 200
        except Exception as e:
            return jsonify({'error':f' {str(e)}'})
        
@jwt_required()
def delete_post(post_id):
    user_iden = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    if post.id == user_iden.id or user_iden.rol == "admin":
        post.delete()
        return jsonify({'message':f'El post {post['title']}, fue eliminado correctamente.'}), 200
    return jsonify({'error':'No posees los permisos suficientes para eliminar el post.'}), 403


"""

                    CRUD de CATEGORIAS

"""

