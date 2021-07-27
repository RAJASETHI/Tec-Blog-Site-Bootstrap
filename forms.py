from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, validators
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField
import email_validator


##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class CommentForm(FlaskForm):
    commentSection = StringField("Comment", validators=[DataRequired()], default='')
    submit = SubmitField("Submit Comment")


class BlogRegister(FlaskForm):
    email = StringField('Email: ', validators=[DataRequired(), validators.Email(), Email(granular_message=True)])
    password = PasswordField('Password: ', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField("SIGN ME UP!")


class BlogLogin(FlaskForm):
    email = StringField('Email: ', validators=[DataRequired(), validators.Email(), Email(granular_message=True)])
    password = PasswordField('Password: ', validators=[DataRequired()])
    submit = SubmitField("LOG IN")
