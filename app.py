import os
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import requests
from bson.objectid import ObjectId

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Set secret key strictly from environment variable (no fallback)
app.secret_key = os.getenv("SECRET_KEY")

# MongoDB Config
mongo_uri = os.getenv("MONGO_URI")
app.config["MONGO_URI"] = mongo_uri

# --- CRITICAL FIX: Explicitly set the MongoDB database name ---
# Even with readWriteAnyDatabase, Flask-PyMongo needs to know which DB
# to attach to mongo.db if not specified in the URI path.
app.config["MONGO_DBNAME"] = "learning_courses_db"  # You can choose any name you like here
# --- END CRITICAL FIX ---

# --- DEBUGGING AID: Print the MONGO_URI to confirm it's loaded ---
print(f"DEBUG: MONGO_URI from os.getenv() is: {mongo_uri}")
# --- END DEBUGGING AID ---

# Initialize PyMongo
mongo = PyMongo(app)

# Initialize db and collections to None initially
db = None
users = None
learners = None

# --- ENHANCED ERROR HANDLING FOR DATABASE CONNECTION ---
try:
    # Attempt to ping the database to confirm a successful underlying connection.
    # This will raise an exception if there's an issue with auth or network.
    mongo.cx.admin.command('ping')
    print("DEBUG: PyMongo client successfully pinged the MongoDB deployment!")

    # If ping succeeds, then it's safe to access .db and its collections.
    # With MONGO_DBNAME set, mongo.db should now correctly point to your chosen database.
    db = mongo.db
    users = db.users
    learners = db.learners
    print("MongoDB collections (users, learners) initialized successfully.")

except Exception as e:
    # This block will now catch more specific PyMongo errors if they occur during ping.
    print(f"ERROR: Failed to connect to MongoDB or access collections: {e}")
    print("Please ensure MONGO_URI is set correctly, MongoDB is accessible (IP whitelist/firewall), and credentials are valid.")
    # If connection fails, db, users, and learners will remain None,
    # and routes will return a 500 error, indicating database unavailability.
# --- END ENHANCED ERROR HANDLING ---


@app.route('/')
def home():
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if the 'users' collection is available before proceeding
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
    # Check if the 'users' collection is available before proceeding
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

    # Check if the 'learners' collection is available before proceeding
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

    # Check if the 'learners' collection is available before proceeding
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
