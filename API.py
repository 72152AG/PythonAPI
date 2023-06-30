from flask import Flask, render_template, request, session, redirect
from flask_redis import FlaskRedis
from flask_session import Session
import nltk
import os
from nltk.corpus import wordnet
from nltk.corpus import util as nltk_util
from redis import Redis


app = Flask(__name__)
app.secret_key = "your_secret_key"


# store user information (flask_session), didnt work well
users = {}


app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)


# redis configure (change url if needed, base url used here)
app.config['REDIS_URL'] = 'redis://localhost:6379/0'
redis_store = FlaskRedis(app)
app.config['SESSION_REDIS'] = redis_store


def load_users():
    if os.path.exists('users.txt'):
        with open('users.txt', 'r') as file:
            for line in file:
                username, password = line.strip().split(':')
                users[username] = password


load_users()


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' in session:
        # user IS logged in 
        if request.method == 'POST':
            word = request.form['word']
            synonyms = get_synonyms(word)
            antonyms = get_antonyms(word)
            pos_tag = get_word_pos(word)
            session['history'].append(word)  # add word to history
            return render_template('index.html', synonyms=synonyms, antonyms=antonyms, pos_tag=pos_tag, history=session['history'])
        return render_template('index.html', history=session['history'])
    else:
        # user IS NOT logged in 
        if request.method == 'POST':
            word = request.form['word']
            synonyms = get_synonyms(word)
            antonyms = get_antonyms(word)
            pos_tag = get_word_pos(word)
            return render_template('index.html', synonyms=synonyms, antonyms=antonyms, pos_tag=pos_tag)
        return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return "Username already exists!"

        # write user info to .txt file (put database here for commercial use)
        with open('users.txt', 'a') as file:
            file.write(f"{username}:{password}\n")

        users[username] = password
        session['username'] = username
        session['history'] = []
        return redirect('/')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # username/password validation
        if username in users and users[username] == password:
            if 'history' not in session:
                session['history'] = []  # initialize history list for the user
            session['username'] = username
            return redirect('/')
        else:
            return render_template('login.html', error='Invalid username or password.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username')
    return redirect('/')

# show synonyms and example uses for them
def get_synonyms(word):
    synonyms = []
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.append({
                'name': lemma.name(),
                'examples': lemma.synset().examples()
            })
    return synonyms

# show anthonyms and example uses for them
def get_antonyms(word):
    antonyms = []
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            for antonym in lemma.antonyms():
                antonyms.append({
                    'name': antonym.name(),
                    'examples': antonym.synset().examples()
                })
    return antonyms

# show POS (part of speech) for the word
def get_word_pos(word):
    tagged_word = nltk.pos_tag([word])
    return tagged_word[0][1]


if __name__ == '__main__':
    app.run(ssl_context='adhoc')
