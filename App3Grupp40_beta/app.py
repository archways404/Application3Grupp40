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
    
@app.route('/admin_add_product', methods=['GET', 'POST'])
def admin_add_product():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT DISTINCT(supplier_name), supplier_id FROM suppliers')
    supplier_list = cursor.fetchall()

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT products.product_id, products.product_name, products.base_price, suppliers.supplier_name FROM products INNER JOIN suppliers ON products.supplier_id = suppliers.supplier_id;')
    data = cursor.fetchall()


    if 'loggedin' in session:
            if session['is_admin'] == True:

                if request.method == 'POST' and 'product_name' in request.form and 'base_price' in request.form and 'quantity' in request.form:
                    product_name = request.form['product_name']
                    base_price = request.form['base_price']
                    quantity = request.form['quantity']
                    supplier_id = request.form['supplier_id']

                    if not product_name or not base_price or not quantity:
                        flash('Please fill out the form!')

                    else:

                        loop = 1

                        while (loop <= int(quantity)):

                            cursor.execute("INSERT INTO products (product_name, base_price, supplier_id) VALUES (%s,%s, %s)" , (product_name, base_price, supplier_id))                        
                            conn.commit()
                            loop = loop + 1

                        else:
                            print("Finally finished!") 
                            flash('You have successfully added the product, please refresh the page in order to see the updated list!')
                            
                return render_template('admin_add_product.html', data=data, supplier_list=supplier_list)
            
            else:

                return render_template('profile.html')
            
    return redirect(url_for('login'))

#SQL STATEMENT COLLECTION BELOW

@app.route('/admin_add_edit_product', methods=['GET', 'POST'])
def admin_add_edit_product():

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("select distinct(product_name), base_price, supplier_name, count(product_name) as amount from products join suppliers on suppliers.supplier_id=products.supplier_id group by base_price, product_name, supplier_name")
    info = cursor.fetchall()

    cursor.execute('SELECT DISTINCT(supplier_name), supplier_id FROM suppliers')
    supplier_list = cursor.fetchall()
    
    cursor.execute('SELECT DISTINCT(supplier_name), supplier_id FROM suppliers') 
    data = cursor.fetchall()

    cursor.execute('select distinct(product_name) from products') 
    data_product = cursor.fetchall()
    if 'loggedin' in session:
        if session['is_admin'] == True:
            if request.method == 'POST' and 'supplier_id' in request.form and 'product_name' in request.form and 'quantity' in request.form and 'choice' in request.form:
                supplier_id = request.form.get('supplier_id')
                product_name = request.form.get('product_name')
                quantity = request.form.get('quantity')
                choice = request.form.get('choice')
                if not supplier_id or not product_name or not quantity or not choice:
                        flash('Please fill out the form!')
                else:
                    if choice == 'Add':

                        loop = 1
                        while (loop <= int(quantity)):
                            cursor.execute('SELECT product_name, base_price, supplier_id FROM products WHERE product_name =  %s' , (product_name,))
                            add_product_list = cursor.fetchall()
                            add_product = add_product_list[0]
                            add_product_product_name = add_product[0]
                            add_product_base_price = add_product[1]
                            add_product_supplier_id = add_product[2]
                            cursor.execute("INSERT INTO products (product_name, base_price, supplier_id) VALUES (%s,%s, %s)" , (add_product_product_name, add_product_base_price, add_product_supplier_id))                        
                            conn.commit()
                            loop = loop + 1
                        else:
                            flash('You have successfully added the product!')
                            cursor.execute("select distinct(product_name), base_price, supplier_name, count(product_name) as amount from products join suppliers on suppliers.supplier_id=products.supplier_id group by base_price, product_name, supplier_name")
                            info = cursor.fetchall()
                    elif choice == 'Delete':
                        loop = 1

                        while (loop <= int(quantity)):

                            cursor.execute('SELECT product_id FROM products WHERE product_name = %s' , (product_name,))
                            delete_product_list = cursor.fetchall()
                            delete_product = delete_product_list[0]
                            delete_product_id = delete_product[0]
                            print(delete_product_id)

                            cursor.execute('DELETE FROM products WHERE product_id =  %s' , (delete_product_id,))                    

                            loop = loop + 1
                        else:
                            flash('You have successfully removed the product or products!')
                            cursor.execute("select distinct(product_name), base_price, supplier_name, count(product_name) as amount from products join suppliers on suppliers.supplier_id=products.supplier_id group by base_price, product_name, supplier_name")
                            info = cursor.fetchall()
                    else:
                        flash("Please select option as either ADD or DELETE!")
          
            return render_template('admin_add_edit_product.html', supplier_list=supplier_list, data=data, data_product=data_product, info=info)
               
        else:

            return render_template('profile.html')
        
    return redirect(url_for('login'))

@app.route('/admin_edit_discounts', methods=['GET', 'POST'])
def admin_edit_discounts():
    if 'loggedin' in session:
        if session['is_admin'] == True:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT discount_name, discount_change, start_date, end_date FROM discounts")
            data = cursor.fetchall()
            if request.method == 'POST' and 'discount_name' in request.form and 'discount_change' in request.form:           
                discount_name = request.form['discount_name']
                discount_change = request.form['discount_change']
                discount_changed = int(discount_change)
                base_change = 100
                base_changed = int(base_change)
                discount_change_to_dec = base_changed - discount_changed
                discount_change_in_dec = discount_change_to_dec / base_changed
                cursor.execute('SELECT * FROM discounts WHERE discount_name = %s', (discount_name,))
                doubleentry = cursor.fetchone()
                if doubleentry:
                    flash('Name already exists!')
                elif not discount_name or not discount_change:
                    flash('Please fill out the form!')
                else:
                    cursor.execute("INSERT INTO discounts (discount_name, discount_change) VALUES (%s,%s)", (discount_name, discount_change_in_dec))
                    conn.commit()
                    flash('You have successfully created the discount!')
                    cursor.execute("SELECT discount_name, discount_change, start_date, end_date FROM discounts")
                    data = cursor.fetchall()
            return render_template('admin_edit_discounts.html', data=data)
        else:
            return render_template('profile.html')
    return redirect(url_for('login'))

@app.route('/admin_apply_discounts', methods=['GET', 'POST'])
def admin_apply_discounts():
    if 'loggedin' in session:
        if session['is_admin'] == True:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT * FROM discounts")
            data = cursor.fetchall()

            cursor.execute('select distinct(discount_name) from discounts')
            discount_list = cursor.fetchall()

            cursor.execute('select distinct(product_name) from products')
            product_data = cursor.fetchall()

            if request.method == 'POST' and 'discount_name' in request.form and 'product_name' in request.form and 'choice' in request.form and 'start_date' in request.form and 'end_date' in request.form:           
                discount_name = request.form.get('discount_name')
                d_products = request.form.get('product_name')
                choice = request.form.get('choice')
                start_date = request.form['start_date']
                end_date = request.form['end_date']


                if choice == 'Apply':
                    cursor.execute('select discount_change from discounts where discount_name = %s', (discount_name,))
                    discount_change_list = cursor.fetchall()
                    discount_change_list_2 = discount_change_list[0]
                    discount_change = discount_change_list_2[0]
                    cursor.execute('INSERT INTO discounts (discount_name, discount_change, start_date, end_date, d_products) VALUES (%s,%s,%s,%s,%s)', (discount_name, discount_change, start_date, end_date, d_products,))
                    conn.commit()
                    flash('You have successfully created the discount!')
                    cursor.execute("SELECT * FROM discounts")
                    data = cursor.fetchall()

                if choice == 'Remove':
                    cursor.execute('select discount_change from discounts where discount_name = %s', (discount_name,))
                    discount_change_list = cursor.fetchall()
                    discount_change_list_2 = discount_change_list[0]
                    discount_change = discount_change_list_2[0]

                    cursor.execute('SELECT discount_id, discount_name, discount_change, start_date, end_date, d_products FROM discounts WHERE discount_name = %s and discount_change = %s and start_date = %s and end_date = %s and d_products = %s', (discount_name, discount_change, start_date, end_date, d_products,))
                    #cursor.execute('SELECT discount_name, discount_change, start_date, end_date, d_products FROM discounts WHERE discount_name = %s and discount_change = %s and start_date = %s and end_date = %s and d_products = %s', (discount_name, discount_change, start_date, end_date, d_products,))
                    not_in_table = cursor.fetchone()
                    print(not_in_table)

                    if not_in_table == None:
                        flash("Entry not in table, please fill out the form again!")
                        cursor.execute("SELECT * FROM discounts")
                        data = cursor.fetchall()

                    else:
                        cursor.execute('DELETE FROM discounts WHERE discount_name = %s and discount_change = %s and start_date = %s and end_date = %s and d_products = %s', (discount_name, discount_change, start_date, end_date, d_products,))
                        conn.commit()
                        flash("Discount removed from the database!")
                        cursor.execute("SELECT * FROM discounts")
                        data = cursor.fetchall()

                if choice == 'Select':  
                    flash('Please fill out the form!')
                    cursor.execute("SELECT * FROM discounts")
                    data = cursor.fetchall()

            return render_template('admin_apply_discounts.html', data=data, product_data=product_data, discount_list=discount_list)
        else:
            return render_template('profile.html')
    return redirect(url_for('login'))

    
if __name__ == "__main__":
    app.run(debug=True)