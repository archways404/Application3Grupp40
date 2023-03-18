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

@app.route('/admin_show_discount_history', methods=['GET', 'POST'])
def admin_show_discount_history():
    if 'loggedin' in session:
        if session['is_admin'] == True:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT DISTINCT(p.product_name), d.discount_name, d.discount_change, d.start_date, d.end_date, (p.base_price * d.discount_change) AS updated_price FROM products p INNER JOIN discounts d ON p.product_name = d.d_products ORDER BY  d.discount_name, d.discount_change, d.start_date, d.end_date")
            data = cursor.fetchall()
            return render_template('admin_show_discount_history.html', data=data)
        else:
            return render_template('profile.html')
    return redirect(url_for('login'))

@app.route('/admin_view_cart', methods=['GET', 'POST'])
def admin_view_cart():
    if 'loggedin' in session:
        if session['is_admin'] == True:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT * from orders")
            data = cursor.fetchall()

            cursor.execute("SELECT order_id from orders WHERE is_paid = False")
            unconfirmed_order = cursor.fetchall()

            if request.method == 'POST' and 'choice' in request.form:           
                choice = request.form.get('choice')
                order_id_select = request.form.get('order_id_select')

                if choice == 'APPLY':

                    cursor.execute('UPDATE orders SET is_paid = True WHERE order_id = %s', (order_id_select,))
                    conn.commit()
                    flash("yeah baby, order confirmed!")
                    cursor.execute("SELECT * from orders")
                    data = cursor.fetchall()

                if choice == 'REMOVE':

                    cursor.execute("SELECT product_name FROM orders WHERE order_id = %s", (order_id_select,))
                    p_name = cursor.fetchall()
                    p_name_1 = p_name[0]
                    p_name_list = p_name_1[0]
                    
                    cursor.execute("SELECT is_paid FROM orders WHERE order_id = %s", (order_id_select,))
                    status_list2 = cursor.fetchall()
                    status_list1 = status_list2[0]
                    status = status_list1[0]

                    if status == True:
                        flash("Error. You can't change orders that have been paid!")
                    if status == False:
                        cursor.execute('UPDATE orders SET is_paid = Null WHERE order_id = %s', (order_id_select,))

                        for i in range(len(p_name_list)):
                            cursor.execute("INSERT into products (product_name, base_price, supplier_id) SELECT DISTINCT(product_name), base_price, supplier_id FROM products WHERE product_name = %s", (p_name_list[i],))
                            conn.commit()
                            print(p_name_list[i])
                        flash('You have successfully removed the product from users cart! AND I AM ON FUCKING FIREEEEEEEE')
                        cursor.execute("SELECT * from orders")
                        data = cursor.fetchall()

                if choice == 'SELECT':
                    flash('Please select an option!')
                
                if choice == 'UNCONFIRM':
                    cursor.execute('UPDATE orders SET is_paid = False WHERE order_id = %s', (order_id_select,))
                    conn.commit()

                    flash("THIS WILL BE REMOVED BEFORE DEADLINE!!")

                
            return render_template('admin_view_cart.html', data=data, unconfirmed_order=unconfirmed_order)
        else:
            return render_template('profile.html')
    return redirect(url_for('login'))


@app.route('/user_view_cart', methods=['GET', 'POST'])
def user_view_cart():
    if 'loggedin' in session:
        if session['is_admin'] == False:

            active_user = session['email']
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            cursor.execute("SELECT DISTINCT(order_id) FROM orders WHERE is_paid=false AND email = %s", (active_user,))
            unconfirmed_order = cursor.fetchall()
            #unconfirmed_order_list2 = cursor.fetchall()
            #unconfirmed_order_list1 = unconfirmed_order_list2[0]
            #unconfirmed_order = unconfirmed_order_list1[0]
            print(unconfirmed_order)


            cursor.execute("SELECT product, COUNT(product) as Quantity, ord_id FROM cart WHERE account = %s GROUP BY product, ord_id", (active_user,))
            data = cursor.fetchall()

            if request.method == 'POST' and 'choice' in request.form:           
                choice = request.form.get('choice')
                order_id_from_orders = request.form.get('order_id_select')
                print(order_id_from_orders)

                cursor.execute("SELECT is_paid FROM orders WHERE order_id = %s", (order_id_from_orders,))
                status_list2 = cursor.fetchall()
                status_list1 = status_list2[0]
                status = status_list1[0]
                print(status)

                if choice == 'PAY':
                        if status == True:
                            flash("Error. You can't change orders that have been purchased!")

                        if status == False:
                            #cursor.execute("UPDATE orders SET is_paid = true WHERE email=%s", (active_user,))
                            flash("You have purchased the item or items from the cart!")

                if choice == 'REMOVE':
                    if status == True:
                        flash("Error. You can't change orders that have been purchased!")

                    if status == False:
                        flash("You have removed the item or items from the cart!")

                if choice == 'SELECT':
                    flash('Please select an option!')
            return render_template('user_view_cart.html', data=data, active_user=active_user, unconfirmed_order=unconfirmed_order)
        else:
            return render_template('profile.html')
    return redirect(url_for('login'))

@app.route('/user_products_order', methods=['GET', 'POST'])
def user_products_order():
    if 'loggedin' in session:
        if session['is_admin'] == False:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            #cursor.execute("select distinct(products.product_name), products.base_price, count(products.product_name) as amount_in_stock from products left join discounts on discounts.d_products=products.product_name group by product_name, base_price")
            #backup tag
            
            cursor.execute("SELECT DISTINCT(products.product_name), products.base_price, count(products.product_name) as amount_in_stock, discounts.discount_change, discounts.start_date, discounts.end_date, discounts.discount_name, (products.base_price * discounts.discount_change) AS discounted_price FROM products left join discounts on discounts.d_products=products.product_name group by product_name, base_price, discounts.discount_change, discounts.start_date, discounts.end_date, discounts.discount_name order by base_price DESC")
            data = cursor.fetchall()

            cursor.execute('select distinct(product_name) from products') 
            data_product = cursor.fetchall()
            active_user = session['email']

            if request.method == 'POST' and 'quantity' in request.form:
                    quantity_from_form = request.form.get('quantity')
                    product_name = request.form.get('product_name')
                    cursor.execute("SELECT DISTINCT COUNT(product_name) FROM products WHERE product_name = %s", (product_name,))
                    item_list = cursor.fetchall()
                    item_shorter_list = item_list[0]
                    item = item_shorter_list[0]

                    quantity_from_form = request.form.get('quantity')
                    product_name = request.form.get('product_name')
                    quantity = int(quantity_from_form)

                    if (item <= quantity):
                        flash('ERROR: Quantity of product is less than what you wish to order!')

                    cursor.execute("SELECT order_id FROM orders WHERE datetime = CURRENT_DATE AND email= %s AND is_paid=false", (active_user,))
                    user_active_cart = cursor.fetchone()
                    print(user_active_cart)

                    if user_active_cart ==  None:
                        print("no active cart")
                        print("creating one...")
                        cursor.execute("INSERT INTO orders(datetime, is_paid, email) VALUES (CURRENT_DATE ,false ,%s)", (active_user,))
                        #cursor.execute("UPDATE orders SET datetime = CURRENT_DATE, is_paid = false, email = %s WHERE order_id=4", (active_user,))
                        conn.commit()
                        ######## REMOVE COMMENTED PART TOMORROW #####

                        cursor.execute("SELECT order_id FROM orders WHERE is_paid=false AND email = %s AND datetime = CURRENT_DATE", (active_user,))
                        order_id_for_user_list2 = cursor.fetchall()
                        order_id_for_user_list1 = order_id_for_user_list2[0]
                        order_id_for_user = order_id_for_user_list1[0]
                        print(order_id_for_user)

                        for i in range(quantity):
                            print(i)
                            cursor.execute('INSERT INTO cart(account, product, ord_id) VALUES (%s,%s,%s)', (active_user, product_name, order_id_for_user))
                            conn.commit()

                            cursor.execute('SELECT product_id FROM products WHERE product_name = %s' , (product_name,))
                            delete_product_list = cursor.fetchall()
                            delete_product = delete_product_list[0]
                            delete_product_id = delete_product[0]

                            cursor.execute('DELETE FROM products WHERE product_id =  %s', (delete_product_id,))
                            conn.commit()                    

                        flash('You have successfully added the product to your cart!')
                        cursor.execute("SELECT DISTINCT(products.product_name), products.base_price, count(products.product_name) as amount_in_stock, discounts.discount_change, discounts.start_date, discounts.end_date, discounts.discount_name, (products.base_price * discounts.discount_change) AS discounted_price FROM products left join discounts on discounts.d_products=products.product_name group by product_name, base_price, discounts.discount_change, discounts.start_date, discounts.end_date, discounts.discount_name order by base_price DESC")
                        data = cursor.fetchall()

                    else:
                        print("active cart")
                        cursor.execute("SELECT order_id FROM orders WHERE is_paid=false AND email = %s AND datetime = CURRENT_DATE", (active_user,))
                        order_id_for_user_list2 = cursor.fetchall()
                        order_id_for_user_list1 = order_id_for_user_list2[0]
                        order_id_for_user = order_id_for_user_list1[0]
                        print(order_id_for_user)

                        for i in range(quantity):
                            print(i)
                            cursor.execute('INSERT INTO cart(account, product, ord_id) VALUES (%s,%s,%s)', (active_user, product_name, order_id_for_user))
                            conn.commit()

                            cursor.execute('SELECT product_id FROM products WHERE product_name = %s' , (product_name,))
                            delete_product_list = cursor.fetchall()
                            delete_product = delete_product_list[0]
                            delete_product_id = delete_product[0]

                            cursor.execute('DELETE FROM products WHERE product_id =  %s', (delete_product_id,))
                            conn.commit()                    

                        flash('You have successfully added the product to your cart!')
                        cursor.execute("SELECT DISTINCT(products.product_name), products.base_price, count(products.product_name) as amount_in_stock, discounts.discount_change, discounts.start_date, discounts.end_date, discounts.discount_name, (products.base_price * discounts.discount_change) AS discounted_price FROM products left join discounts on discounts.d_products=products.product_name group by product_name, base_price, discounts.discount_change, discounts.start_date, discounts.end_date, discounts.discount_name order by base_price DESC")
                        data = cursor.fetchall()

            return render_template('user_products_order.html', data=data, active_user=active_user, data_product=data_product)
        else:
            return render_template('profile.html')
    return redirect(url_for('login'))






#cursor.execute("select distinct(product_name), base_price, supplier_name, count(product_name) as amount from products join suppliers on suppliers.supplier_id=products.supplier_id group by base_price, product_name, supplier_name")
#OLD shows everything but not updated price
    
if __name__ == "__main__":
    app.run(debug=True)

#note we need to add username to Orders

#note product name in order can be a bit of an issue since we have to store multiple product names in it, so ex:
# if you order 2 iMac, then the value will be {iMac, iMac} - this actually works better for us lol - either way / remove "quantity" and add their username to that row instead!
# we need their username in order to be able to create their carts