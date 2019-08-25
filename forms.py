from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, validators


class AddForm(FlaskForm):

    page = StringField('New Page:', [validators.required()])
    submit = SubmitField('Add Page')


class DelForm(FlaskForm):

    page = IntegerField('Page url:')
    submit = SubmitField('Remove Page')
