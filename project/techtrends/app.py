import sqlite3
import sys
import logging
from datetime import datetime
from flask import Flask, json, render_template, request, url_for, redirect, flash

connection_count = 0
posts_count = 0
# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global connection_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    connection_count += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to get the current date and time
def getNow():
    date = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    return date

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    global posts_count
    posts_count = len(posts)
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info("[%s] - Article non existing", getNow())
      return render_template('404.html'), 404
    else:
      title = post[2]
      app.logger.info("[%s] - Article %s retrieved!", getNow(), title)
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info("[%s] - About paged accessed", getNow())
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info("[%s] - Article %s successfully created", getNow(), title)
            return redirect(url_for('index'))

    return render_template('create.html')

# Returns the health of the application
@app.route("/healthz")
def healthcheck():
    health = {
        "result": "OK - healthy"
    }
    response = app.response_class(
        response=json.dumps(health),
        status=200,
        mimetype='application/json'
    )
    app.logger.info("[%s] - Status request successful", getNow())
    return response

# Returns some metrics for amount of current posts and amount of db calls
@app.route("/metrics")
def metrics():
    global posts_count
    data = {
        "db_connection_count": connection_count,
        "post_count": posts_count,
    }
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    app.logger.info("[%s] - Metrics request successful", getNow())
    return response

# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(filename='app.log', level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
    app.run(host='0.0.0.0', port='3111')
