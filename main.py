from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, g
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from forms import BlogRegister, CreatePostForm, BlogLogin, CommentForm
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from wtforms import StringField, validators, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
import email_validator
from flask_gravatar import Gravatar
from flask import abort
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

messages = ''
##CONFIGURE TABLES
login_manager = LoginManager()
login_manager.init_app(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False,
                    base_url=None)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    posts = relationship("BlogPost", back_populates="author")
    comments = db.relationship("Comment", back_populates='comment_author')


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    # author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates='parent_post')


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment_author = relationship('User', back_populates='comments')
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    parent_post = relationship("BlogPost", back_populates='comments')


db.create_all()


@app.route('/')
def do_it():
    return redirect(url_for('login'))


@app.route('/all-posts')
# @login_required
def get_all_posts():
    # print(current_user.id)
    posts = BlogPost.query.all()
    x = current_user.is_authenticated
    return render_template("index.html", logged_in=x, all_posts=posts)


@app.route('/register', methods=["GET", 'POST'])
def register():
    global messages
    user_register_form = BlogRegister()
    if request.method == 'POST':
        if user_register_form.validate_on_submit():
            user_db = User.query.filter_by(email=user_register_form.email.data).first()
            if user_db:
                messages = 'E-Mail is already registered.'
                return redirect(url_for('login', message=messages))
            user = User(name=user_register_form.name.data, email=user_register_form.email.data,
                        password=generate_password_hash(user_register_form.password.data, method='pbkdf2:sha256',
                                                        salt_length=8))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=user_register_form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    global messages
    user_login_form = BlogLogin()
    if request.method == 'POST':
        if user_login_form.validate_on_submit():
            try:
                user = User.query.filter_by(email=user_login_form.email.data).first()
                if check_password_hash(user.password, user_login_form.password.data):
                    login_user(user)
                    return redirect(url_for('get_all_posts'))
                else:
                    messages = "Invalid Credentials.\nKindly check your id or password again."
            except:
                messages = "Invalid Credentials.\nKindly check your email-id again."

    return render_template("login.html", message=messages, logged_in=False, form=user_login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    x = current_user.is_authenticated
    commentForm = CommentForm(text='')
    if commentForm.validate_on_submit():
        x = current_user.is_authenticated
        if x:
            check_comment = Comment.query.filter_by(author_id=current_user.id).all()
            flag = 0
            if len(check_comment) > 5 and current_user.id != 1:
                flag = 1
            for c in check_comment:
                if c.text == commentForm.commentSection.data:
                    flag += 1
            if flag == 0:
                cmnt = Comment(
                    text=commentForm.commentSection.data,
                    author_id=current_user.id,
                    post_id=post_id
                )
                db.session.add(cmnt)
                db.session.commit()
        else:
            global messages
            messages = 'You need to login or register to comment.'
            return redirect(url_for('login'))
    all_comments = Comment.query.filter_by(post_id=post_id).all()
    # print(all_comments)
    return render_template("post.html", post=requested_post, comment_form=commentForm, comments=all_comments,
                           logged_in=x)


@app.route("/about")
# @login_required
def about():
    x = current_user.is_authenticated
    return render_template("about.html", logged_in=x)


@app.route("/contact")
# @login_required
def contact():
    x = current_user.is_authenticated
    return render_template("contact.html", logged_in=x)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    x = current_user.is_authenticated
    # print(f"Hello: {x}")
    return render_template("make-post.html", logged_in=x, form=form)


@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=current_user,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        # post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    x = current_user.is_authenticated
    return render_template("make-post.html", logged_in=x, is_edit=True, form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
