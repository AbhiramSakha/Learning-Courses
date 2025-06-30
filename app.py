import os
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import requests
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# MongoDB Config
from flask import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)

# Use the fixed URI
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# Access database (important: replace 'mydatabase' if you named it something else)
db = mongo.db
users = db.users
mongo = PyMongo(app)

# Fix collection naming issue (MongoDB is case-sensitive)
db = mongo.db
users = db.users
learners = db.learners  # Collection to store course searches


@app.route('/')
def home():
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = users.find_one({'username': username})
        if existing_user:
            return render_template('register.html', error="Username already exists.")
        users.insert_one({'username': username, 'password': password})
        return redirect('/login')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({'username': username, 'password': password})
        if user:
            session['username'] = username
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        course = request.form['course']
        playlist_url = get_youtube_playlist(course)

        if playlist_url:
            learners.insert_one({"course": course, "link": playlist_url})
            return jsonify({'playlist_url': playlist_url})
        else:
            return jsonify({'error': 'No playlist found'}), 404

    all_learners = list(learners.find())
    return render_template('dashboard.html', learners=all_learners)


@app.route('/delete/<id>')
def delete_course(id):
    if 'username' not in session:
        return redirect('/login')
    learners.delete_one({'_id': ObjectId(id)})
    return redirect('/dashboard')


def get_youtube_playlist(course):
    api_key = os.getenv("YOUTUBE_API_KEY")
    query = f"{course} full course playlist"
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&q={query}&type=playlist&key={api_key}"

    response = requests.get(url)
    data = response.json()

    if 'items' in data and len(data['items']) > 0:
        playlist_id = data['items'][0]['id']['playlistId']
        return f"https://www.youtube.com/playlist?list={playlist_id}"
    return None
app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    app.run(debug=True)
