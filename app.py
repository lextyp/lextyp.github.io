from flask import Flask
from flask import url_for, render_template, request, redirect
import sqlite3
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hebrew_database_2.db'
db = SQLAlchemy(app)


class Metaphors(db.Model):
    __tablename__ = 'metaphors'  # имя таблицы
    id = db.Column(db.Integer, primary_key=True) # имя колонки = специальный тип (тип данных, первичный ключ)
    metaphor = db.Column(db.Text)
    example = db.Column(db.Integer)


class Meaning(db.Model):
    __tablename__ = 'meaning'
    id = db.Column(db.Integer, primary_key=True)
    frame = db.Column(db.Text)
    meaning = db.Column(db.Text)
    int = db.Column(db.Integer)


class Grammar(db.Model):
    __tablename__ = 'grammar'
    id = db.Column(db.Integer, primary_key=True)
    grammar = db.Column(db.Text)
    example = db.Column(db.Integer)


class Verbforms(db.Model):
    __tablename__ = 'verbforms'
    id = db.Column(db.Integer, primary_key=True)
    verbform = db.Column(db.Text)
    example = db.Column(db.Integer)


class Examples(db.Model):
    __tablename__ = 'examples'
    id = db.Column(db.Integer, primary_key=True)
    id_text = db.Column(db.Integer)
    russian = db.Column(db.Text)
    hebrew = db.Column(db.Text)
    source = db.Column(db.Text)
    governing = db.Column(db.Text)


class Database():
    def __init__(self, db):
        self.data = db

    def search_by(self, word, feature):
        res = None
        if feature == 'metaphors':
            res = self.data.session.query(Metaphors.example).filter(Metaphors.metaphor == word).all()
        elif feature == 'meaning':
            res = self.data.session.query(Meaning.int).filter(Meaning.meaning == word).all()
        elif feature == 'verbforms':
            res = self.data.session.query(Verbforms.example).filter(Verbforms.verbform == word).all()
        elif feature == 'frames':
            res = self.data.session.query(Meaning.int).filter(Meaning.frame == word).all()
        return [int(i[0]) for i in res]

    def search_sent(self, string, sent):
        res = []
        for i in sent:
            if string in self.data.session.query(Grammar.grammar).filter(Grammar.id == i).one().split():
                res.append(i)
        return res

    def grammar_search(self, string):
        values = string.split(',')
        sent = []
        sentences = self.data.session.query(Grammar.grammar).all()
        for num, i in enumerate(sentences):
            if values[0] in str(i[0]).split():
                    sent.append(self.data.session.query(Grammar.example).filter(Grammar.id == num).one())
        if len(values) > 1:
            for i in range(1, len(values)):
                sent = self.search_sent(values[i], sent)
        return [int(i[0]) for i in sent]

    def search(self, metaphor, verbform, grammar, meaning, frames):
        results = []
        if metaphor != '':
            results.append(self.search_by(metaphor, 'metaphors'))
        if verbform != '':
            results.append(self.search_by(verbform, 'verbforms'))
        if grammar != '':
            results.append(self.grammar_search(grammar))
        if meaning != '':
            results.append(self.search_by(meaning, 'meaning'))
        if frames != '':
            results.append(self.search_by(frames, 'frames'))
        if results != []:
            results = set.intersection(*list(map(set, results)))
        else:
            redirect(url_for('error'))
        return results


@app.route('/')
def index():
    frames = set(db.session.query(Meaning.frame).all())
    metaphors = set(db.session.query(Metaphors.metaphor).all())
    meanings = set(db.session.query(Meaning.meaning).all())
    verbforms = set(db.session.query(Verbforms.verbform).all())
    return render_template('hebrew.html', frames=frames, metaphors=metaphors, meanings=meanings, verbforms=verbforms)


@app.route('/process_data', methods=['get'])
def process_data():
    if not request.args:
        return redirect(url_for('index'))
    meaning = request.args.get('meaning')
    metaphor = request.args.get('metaphor')
    verbform = request.args.get('verbform')
    grammar = request.args.get('grammar')
    frames = request.args.get('frame')
    s = Database(db)
    answers = s.search(metaphor, verbform, grammar, meaning, frames)
    if None not in answers:
        results = db.session.query(Examples.source, Examples.hebrew, Examples.russian).filter(
            Examples.id_text.in_(answers)).all()
        return render_template('search.html', results=results)
    else:
        return redirect(url_for('error'))


@app.route('/error')
def error():
    return '<html><body>Произошла какая-то ошибка. Попробуйте еще раз.</body></html>'


if __name__ == '__main__':
    app.run()
