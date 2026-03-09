from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret"

def get_db_connection():
    conn = sqlite3.connect("ecommerce.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect("ecommerce.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        password TEXT
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM shop")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO shop (name, image, price)
            VALUES (?, ?, ?)
            """, [
                ('Camel Noir', 'img1.jpg', 1200),
                ('Charcoal Cream', 'img2.jpg', 999),
                ('Solid Black', 'img3.jpg', 1100),
                ('Charcoal gray', 'img4.jpg', 1500),
                ('Triple-Tone Pullover', 'img5.jpg', 1250),
                ('Dark Gray', 'img6.jpg', 1700),
                ('Black-Gray', 'img7.jpg', 1100),
                ('Black', 'img8.jpg', 1200),
                ('Aqua White', 'img9.jpg', 1900),
                ('Bro-White special', 'img10.jpg', 2599)
            ])

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS heart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_address (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        name TEXT,
        phone TEXT,
        address TEXT,
        pincode TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        method TEXT,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/home')
def about():
    return render_template('index1.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        name = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO app (name, password) VALUES (?, ?)",
            (name, password)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('reg.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        name = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM app WHERE name=? AND password=?",
            (name, password)
        ).fetchone()
        conn.close()

        if user:
            session['name'] = name
            return redirect(url_for('welcome'))
        else:
            return "Invalid username or password"

    return render_template('login.html')

@app.route('/welcome')
def welcome():
    if 'name' in session:
        return render_template('index1.html')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/shop')
def shop_page():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM shop").fetchall()
    conn.close()

    return render_template('shop.html', products=products)


@app.route('/search')
def search():
    query = request.args.get('q', '')

    conn = get_db_connection()

    if query:
        products = conn.execute(
            "SELECT * FROM shop WHERE name LIKE ?",
            ('%' + query + '%',)
        ).fetchall()
    else:
        products = []

    conn.close()

    return render_template('search.html', products=products, query=query)


@app.route('/add_to_heart', methods=['POST'])
def add_to_heart():
    product_id = request.form.get('product_id')

    conn = get_db_connection()

    existing = conn.execute(
        "SELECT id FROM heart WHERE product_id=?",
        (product_id,)
    ).fetchone()

    if not existing:
        conn.execute(
            "INSERT INTO heart (product_id, quantity) VALUES (?, ?)",
            (product_id, 1)
        )

    conn.commit()
    conn.close()

    return redirect(url_for('shop_page'))



@app.route('/wishlist')
def wishlist():
    conn = get_db_connection()

    heart_items = conn.execute("""
        SELECT h.id AS heart_id,
               h.product_id,
               s.name,
               s.price,
               s.image
        FROM heart h
        JOIN shop s ON h.product_id = s.id
        ORDER BY h.id DESC
    """).fetchall()

    conn.close()

    return render_template('heart.html', heart_items=heart_items)



@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):

    conn = get_db_connection()

    existing = conn.execute(
        "SELECT id, quantity FROM cart WHERE product_id=?",
        (product_id,)
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE cart SET quantity=? WHERE id=?",
            (existing['quantity'] + 1, existing['id'])
        )
    else:
        conn.execute(
            "INSERT INTO cart (product_id, quantity) VALUES (?, ?)",
            (product_id, 1)
        )

    conn.commit()
    conn.close()

    return redirect(url_for('shop_page'))


@app.route('/cart')
def cart():

    conn = get_db_connection()

    cart_items = conn.execute("""
        SELECT c.id AS cart_id,
               c.product_id,
               c.quantity,
               s.name,
               s.price,
               s.image
        FROM cart c
        JOIN shop s ON c.product_id = s.id
    """).fetchall()

    conn.close()

    return render_template('cart.html', cart_items=cart_items)


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():

    cart_id = request.form.get('cart_id')

    conn = get_db_connection()
    conn.execute("DELETE FROM cart WHERE id=?", (cart_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('cart'))


@app.route('/buy_now', methods=['GET', 'POST'])
def buy_now():

    if request.method == 'POST':

        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        pincode = request.form.get('pincode')

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO orders (product_id, quantity, status) VALUES (?, ?, ?)",
            (1, 1, 'Address Provided')
        )

        order_id = cursor.lastrowid

        conn.execute(
            """INSERT INTO customer_address 
               (order_id, name, phone, address, pincode)
               VALUES (?, ?, ?, ?, ?)""",
            (order_id, name, phone, address, pincode)
        )

        conn.commit()
        conn.close()

        return redirect(url_for('payment', order_id=order_id))

    return render_template('address.html')



@app.route('/payment/<int:order_id>', methods=['GET', 'POST'])
def payment(order_id):

    if request.method == 'POST':

        method = request.form.get('payment_method')

        conn = get_db_connection()

        conn.execute(
            "INSERT INTO payments (order_id, method, status) VALUES (?, ?, ?)",
            (order_id, method, 'Pending')
        )

        conn.commit()
        conn.close()

        return render_template('order_success.html', method=method)

    return render_template('payment.html', order_id=order_id)



@app.route('/contact', methods=['GET', 'POST'])
def contact():

    if request.method == 'POST':

        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        conn = get_db_connection()

        conn.execute(
            "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
            (name, email, message)
        )

        conn.commit()
        conn.close()

        return render_template('contact_success.html', name=name)

    return render_template('contact.html')


if __name__ == "__main__":
    init_db()
    app.run(debug=True)