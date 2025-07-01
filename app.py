import os
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import requests
from bson.objectid import ObjectId

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

# MongoDB Config
mongo_uri = os.getenv("MONGO_URI")
app.config["MONGO_URI"] = mongo_uri

# --- ADD THIS PRINT STATEMENT ---
print(f"DEBUG: MONGO_URI from os.getenv() is: {mongo_uri}")
# --- END ADDITION ---

mongo = PyMongo(app)

db = None
users = None
learners = None

try:
    db = mongo.db
    users = db.users
    learners = db.learners
    print("MongoDB collections (users, learners) initialized successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB or accessing collections: {e}")
    print("Please ensure MONGO_URI is set correctly and MongoDB is accessible.")

# ... rest of your code
    # and routes will return a 500 error, indicating database unavailability.


@app.route('/')
def home():
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if the 'users' collection is available (i.e., DB connection was successful)
    if users is None:
        return "Database not available. Please check server logs for connection errors.", 500

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
    # Check if the 'users' collection is available
    if users is None:
        return "Database not available. Please check server logs for connection errors.", 500

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

    # Check if the 'learners' collection is available
    if learners is None:
        return "Database not available. Please check server logs for connection errors.", 500

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

    # Check if the 'learners' collection is available
    if learners is None:
        return "Database not available. Please check server logs for connection errors.", 500

    try:
        learners.delete_one({'_id': ObjectId(id)})
    except Exception as e:
        print(f"Error deleting course: {e}")
        return "Error deleting course. Please try again.", 500
    return redirect('/dashboard')


def get_youtube_playlist(course):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("YOUTUBE_API_KEY is not set in environment variables.")
        return None

    query = f"{course} full course playlist"
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&q={query}&type=playlist&key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        if 'items' in data and len(data['items']) > 0:
            playlist_id = data['items'][0]['id']['playlistId']
            return f"https://www.youtube.com/playlist?list={playlist_id}"
        print(f"No YouTube playlist found for query: {query}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching YouTube playlist: {e}")
        return None
    except ValueError as e: # For JSON decoding errors
        print(f"Error decoding YouTube API response: {e}")
        print(f"Response content: {response.text}")
        return None


if __name__ == '__main__':
    # Print the MONGO_URI to ensure it's being read during local testing
    # In production environments like Render, avoid printing sensitive information
    # print(f"MONGO_URI: {mongo_uri}")
    # print(f"SECRET_KEY: {'Set' if app.secret_key else 'Not Set'}")
    # print(f"YOUTUBE_API_KEY: {'Set' if os.getenv('YOUTUBE_API_KEY') else 'Not Set'}")

    app.run(host='0.0.0.0', port=5000, debug=True)
