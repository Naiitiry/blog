from sqlalchemy import Enum, func
from werkzeug.security import check_password_hash, generate_password_hash
from . import db


# Tabla intermedia para muchos-a-muchos entre Post y Tag
post_tag = db.Table(
    'post_tag',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Usuario(db.Model):
    __tablename__ = "usuario"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    last_name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(150),nullable=False,unique=True)
    username = db.Column(db.String(100),nullable=False,unique=True)
    pass_hash = db.Column(db.String(400),nullable=False)
    rol = db.Column(Enum('admin','usuario',name='rol'),default='usuario',nullable=False)
    status = db.Column(Enum('activo','inactivo','bloqueado',name='status'),default='activo',nullable=True)
    date_register = db.Column(db.DateTime,default=func.now(),nullable=True)

    # Relación usuario - post
    posts = db.relationship('Post',backref='autor',lazy=True)
    # Relación usuario - comentario
    comments = db.relationship('Comment',backref='autor',lazy=True)

    def set_password_hash(self,password):
        self.pass_hash=generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.pass_hash,password)
    
    def delete(self):
        self.status = 'inactivo'

    def activate(self):
        self.status = 'activo'

    def block(self):
        self.status = 'bloqueado'

    def serialize_public(self):
        post_totales = Post.query.filter_by(autor_id=self.id).count()
        return{
            'id':self.id,
            'Usuario':self.username,
            'status':self.status,
            'cantidad de posteos':post_totales
        }
    
    def serialize_private(self):
        post_totales = Post.query.filter_by(autor_id=self.id).count()
        return{
            'id':self.id,
            'Usuario':self.username,
            'email':self.email,
            'nombre':self.name,
            'apellido':self.last_name,
            'rol':self.rol,
            'status':self.status,
            'fecha de creación':self.date_register,
            'cantidad de posteos':post_totales
        }

class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100),nullable=False)
    content = db.Column(db.Text,nullable=False)
    creation_date = db.Column(db.DateTime,default=func.now())
    update_date = db.Column(db.DateTime,default=func.now(),onupdate=func.now())
    autor_id = db.Column(db.Integer,db.ForeignKey('usuario.id'),nullable=False)
    category_id = db.Column(db.Integer,db.ForeignKey('categoria.id'),nullable=False)
    tag_id = db.Column(db.Integer,db.ForeignKey('tag.id'),nullable=False)
    status_post = db.Column(Enum('borrador','publicado','eliminado',name='status_post'),default='borrador',nullable=True)

    # Relaciones
    tags = db.relationship('Tag', secondary=post_tag, back_populates='posts', lazy=True)
    comments = db.relationship('Comment', backref='post', lazy=True)

    def delete(self):
        self.status_post = 'eliminado'
    
    def draft(self):
        self.status_post = 'borrador'

    def publish(self):
        self.status_post = 'publicado'

    def serialize(self):
        return{
            'id':self.id,
            'titulo':self.title,
            'contenido':self.content,
            'fecha de creación':self.creation_date,
            'creador':self.autor.username,
            'comentarios totales':len(self.comments),
            'tags':[tag.name for tag in self.tags],
        }
    
class Comment(db.Model):
    __tablename__ = 'comentario'
    id = db.Column(db.Integer,primary_key=True)
    content = db.Column(db.Text,nullable=False)
    creation_date = db.Column(db.DateTime,default=func.now())
    post_id = db.Column(db.Integer,db.ForeignKey('post.id'),nullable=False)
    autor_id = db.Column(db.Integer,db.ForeignKey('usuario.id'),nullable=False)
    status_comment = db.Column(Enum('borrador','publicado',name='status_comment'),default='borrador',nullable=True)

    def publish_comment(self):
        self.status_comment = 'publicado'
    
    def draft_comment(self):
        self.status_comment = 'borrador'

    def serialize(self):
        return{
            'contenido':self.content,
            'fecha de creación':self.creation_date,
            'autor':self.autor.username
        }
    
class Category(db.Model):
    __tablename__ = "categoria"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False,unique=True)

    # Relación con Post y poder medir las categorias
    posts = db.relationship('Post', backref='categoria', lazy=True)

    def serialize(self):
        return{
            'id':self.id,
            'categoría':self.name,
            'total de categorias por post':len(self.posts)
        }
    
    def get_total_categories(self):
        return {
            'total de categorias':len(self.posts)
        }

class Tag(db.Model):
    __tablename__ = "tag"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False,unique=True)

    # Relación muchos-a-muchos con Post
    posts = db.relationship('Post', secondary=post_tag, back_populates='tags', lazy=True)

    def serialize(self):
        return{
            'id':self.id,
            'tag':self.name,
        }
    
    def total_tag(self):
        return{
            'total de tags': len(self.name)
        }