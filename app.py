from flask import Flask, render_template, request, redirect, url_for
import os
from forms import AddForm, DelForm
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
import requests
import validators
import config

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRETKEY

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'rss.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

bootstrap = Bootstrap(app)

db = SQLAlchemy(app)
Migrate(app, db)


class Page(db.Model):

    __tablename__ = 'pages'
    page = db.Column(db.Text, primary_key=True)

    def __init__(self, page):
        self.page = page

    def __repr__(self):
        return f"{self.page}"


@app.route('/', methods=['GET', 'POST'])
def index():
   pages = Page.query.all()
   form = AddForm()
   if form.validate_on_submit():
        page = form.page.data

        if validators.url(page):
           if requests.get(page).status_code == 200:
            new_page = Page(page)
            db.session.add(new_page)
            db.session.commit()
        
        return redirect(url_for('index'))

   return render_template('index.html', pages = pages, form = form)


@app.route('/del/<page>', methods=['GET', 'POST'])
def remove(page):
   del_page = Page.query.get(page)
   db.session.delete(del_page)
   db.session.commit()
   return redirect(url_for('index'))


def run_flask():
   app.run(host=config.FLASKHOST, port=config.FLASKPORT, debug=False)


if __name__ == '__main__':
   app.run(host=config.FLASKHOST, port=config.FLASKPORT)
