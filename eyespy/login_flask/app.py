from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL, MySQLdb
import bcrypt
import os
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key =  "supersecretkey"

# Update the configuration with the MySQL root user password
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'  # Ganti dengan kata sandi Anda yang sebenarnya
app.config['MYSQL_DB'] = 'flaskdb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

mysql = MySQL(app)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash("Please login to access this page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        curl = mysql.connection.cursor()
        curl.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = curl.fetchone()
        curl.close()

        if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
            session['name'] = user['name']
            session['email'] = user['email']
            return redirect(url_for('dashboard'))
        else:
            flash("Failed, Email and Password do not match.")
            return redirect(url_for('login'))
    else:
        return render_template("login.html")

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        hash_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hash_password))
        mysql.connection.commit()
        cur.close()

        session['name'] = name
        session['email'] = email
        return redirect(url_for('dashboard'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    classification = None
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            flash('File successfully uploaded')
            # Di sini Anda akan menambahkan logika klasifikasi yang sebenarnya
            # Sebagai demonstrasi, kami hanya menetapkan hasil klasifikasi dummy
            classification = 'Dummy classification result'
    return render_template('dashboard.html', classification=classification)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
