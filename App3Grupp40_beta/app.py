#Beta v2.0 *(9/3)

from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2 #pip install psycopg2 
import psycopg2.extras
import re 
from werkzeug.security import generate_password_hash, check_password_hash
 
app = Flask(__name__)
app.secret_key = 'grupp40'
 
DB_HOST = "pgserver.mau.se"
DB_NAME = "grupp40"
DB_USER = "an4231"
DB_PASS = "6umx36wl"
 
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
 
@app.route('/')
def home():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("select distinct(product_name), base_price, supplier_name, count(product_name) as amount from products join suppliers on suppliers.supplier_id=products.supplier_id group by base_price, product_name, supplier_name")
    data = cursor.fetchall()


    if 'loggedin' in session:
        if session['is_admin'] == True:
            return render_template('home_admin.html', email=session['email'], is_admin=session['is_admin'], data=data )
        else:
            return render_template('home_user.html', email=session['email'], data=data)
    return render_template('home.html', data=data)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        print(password)
        cursor.execute('SELECT * FROM customers WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            password_rs = account['password']
            print(password_rs)
            if check_password_hash(password_rs, password):
                session['loggedin'] = True
                session['customer_id'] = account['customer_id']
                session['email'] = account['email']
                session['is_admin'] = account['is_admin']
                session['city'] = account['city']
                session['country'] = account['country']
                session['phone'] = account['phone']
                session['address'] = account['address']
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
        city = request.form['city']
        country = request.form['country']
        phone = request.form['phone']
        address = request.form['address']
        is_admin = False
        _hashed_password = generate_password_hash(password)
        cursor.execute('SELECT * FROM customers WHERE email = %s', (email,))
        account = cursor.fetchone()
        print(account)
        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not password or not email or not phone or not address or not country or not city or not first_name or not last_name:
            flash('Please fill out the form!')
        else:
            cursor.execute("INSERT INTO customers (first_name, last_name, password, email, is_admin, city, country, address, phone) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (first_name, last_name, _hashed_password, email, is_admin, city, country, address, phone))
            conn.commit()
            flash('You have successfully registered!')
    elif request.method == 'POST':
        flash('Please fill out the form!')
    return render_template('register.html')
   
   
@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('customer_id', None)
   session.pop('email', None)
   session.pop('is_admin', None)
   return redirect(url_for('home'))
  
@app.route('/profile')
def profile(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
            if session['is_admin'] == True:
                cursor.execute('SELECT * FROM customers WHERE customer_id = %s', [session['customer_id']])
                account = cursor.fetchone()
                return render_template('profile_admin.html', account=account )
            else:
                cursor.execute('SELECT * FROM customers WHERE customer_id = %s', [session['customer_id']])
                account = cursor.fetchone()
                return render_template('profile.html', account=account)
    return redirect(url_for('login'))

@app.route('/admin_add_supplier', methods=['GET', 'POST'])
def admin_add_supplier():
    if 'loggedin' in session:
            if session['is_admin'] == True:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute("SELECT * FROM suppliers")
                data = cursor.fetchall()
                if request.method == 'POST' and 'supplier_name' in request.form and 'supplier_phone' in request.form and 'supplier_adress' in request.form:
                    supplier_name = request.form['supplier_name']
                    supplier_phone = request.form['supplier_phone']
                    supplier_adress = request.form['supplier_adress']
                    cursor.execute('SELECT * FROM suppliers WHERE supplier_name = %s', (supplier_name,))
                    doubleentry = cursor.fetchone()
                    print(doubleentry)
                    if doubleentry:
                        flash('supplier already exists!')
                    elif not supplier_name or not supplier_phone or not supplier_adress:
                        flash('Please fill out the form!')
                    else:
                        cursor.execute("INSERT INTO suppliers (supplier_name, supplier_phone, supplier_adress) VALUES (%s,%s,%s)", (supplier_name, supplier_phone, supplier_adress))
                        conn.commit()
                        flash('You have successfully added the supplier, please refresh the page in order to see the updated list!')
                return render_template('admin_add_supplier.html', data=data)
            else:
                return render_template('profile.html')
    return redirect(url_for('login'))
    

#SQL STATEMENT COLLECTION BELOW

    
if __name__ == "__main__":
    app.run(debug=True)