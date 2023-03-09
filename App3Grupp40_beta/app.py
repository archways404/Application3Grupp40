#Beta v2.0 *(9/3)

from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2 #pip install psycopg2 
import psycopg2.extras
import re 
from werkzeug.security import generate_password_hash, check_password_hash
 
app = Flask(__name__)
app.secret_key = 'grupp40'
 
DB_HOST = "pgserver.mau.se"
DB_NAME = "ak8893_test"
DB_USER = "ak8893"
DB_PASS = "xrbz4n8h"
 
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
 
@app.route('/')
def home():
    if 'loggedin' in session:
        if session['is_admin'] == True:
            return render_template('home_admin.html', email=session['email'], is_admin=session['is_admin'] )
        else:
            return render_template('home_user.html', email=session['email'])
    return render_template('home.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        print(password)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            password_rs = account['password']
            print(password_rs)
            if check_password_hash(password_rs, password):
                session['loggedin'] = True
                session['id'] = account['id']
                session['email'] = account['email']
                session['is_admin'] = account['is_admin']
                #session['city'] = account['city']
                #session['country'] = account['country']
                #session['phone'] = account['phone']
                #session['adress'] = account['adress']
                return redirect(url_for('home'))
            else:
                flash('Incorrect username/password')
        else:
            flash('Incorrect username/password')
    return render_template('login.html')
  
@app.route('/register', methods=['GET', 'POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        email = request.form['email']
        #city = request.form['city']
        #country = request.form['country']
        #phone = request.form['phone']
        #address = request.form['address']
        is_admin = False
    
        _hashed_password = generate_password_hash(password)
 
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        print(account)
        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not password or not email:
            flash('Please fill out the form!')
        else:
            cursor.execute("INSERT INTO users (first_name, last_name, password, email, is_admin) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (first_name, last_name, _hashed_password, email, is_admin, city, country, address, phone))
            conn.commit()
            flash('You have successfully registered!')
    elif request.method == 'POST':
        flash('Please fill out the form!')
    return render_template('register.html')
   
   
@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('email', None)
   session.pop('is_admin', None)
   return redirect(url_for('home'))
  
@app.route('/profile')
def profile(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        return render_template('profile.html', account=account)
    return redirect(url_for('login'))
 
if __name__ == "__main__":
    app.run(debug=True)