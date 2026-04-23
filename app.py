from flask import Flask, render_template, request, jsonify, redirect, url_for
import database
import random
import os

app = Flask(__name__)

USER_ID = 1

with app.app_context():
    database.init_db()

def get_db_cursor():
    conn = database.get_db_connection()
    return conn, conn.cursor()

@app.route('/')
def index():
    conn, c = get_db_cursor()
    # Get all products
    c.execute('SELECT * FROM products')
    products = [dict(p) for p in c.fetchall()]
    
    # Get random "Trending" products for the homepage section
    c.execute('SELECT * FROM products ORDER BY RANDOM() LIMIT 4')
    trending = [dict(p) for p in c.fetchall()]
    
    conn.close()
    return render_template('index.html', products=products, trending=trending)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn, c = get_db_cursor()
    c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    prod = c.fetchone()
    
    if prod:
        # Track interaction viewing product page
        c.execute('INSERT INTO interactions (user_id, product_id) VALUES (?, ?)', (USER_ID, product_id))
        conn.commit()
        product = dict(prod)
        
        # Parse features string into a python list using "|" separator
        if product.get('features'):
            product['features_list'] = [f.strip() for f in product['features'].split('|') if f.strip()]
        else:
            product['features_list'] = []
            
        # Get similar products (same category, excluding current)
        c.execute('''
            SELECT * FROM products 
            WHERE category = ? AND id != ? 
            ORDER BY RANDOM() LIMIT 4
        ''', (product['category'], product_id))
        similar_products = [dict(row) for row in c.fetchall()]
    else:
        product = None
        similar_products = []

    conn.close()
    if not product:
        return "Product not found", 404
        
    return render_template('product.html', product=product, similar_products=similar_products)

@app.route('/track/<int:product_id>', methods=['POST'])
def track_click(product_id):
    conn, c = get_db_cursor()
    c.execute('SELECT id FROM products WHERE id = ?', (product_id,))
    if c.fetchone() is None:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
        
    c.execute('INSERT INTO interactions (user_id, product_id) VALUES (?, ?)', (USER_ID, product_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Interaction tracked'})

@app.route('/recommend', methods=['GET'])
def recommend():
    conn, c = get_db_cursor()
    c.execute('''
        SELECT p.category 
        FROM interactions i
        JOIN products p ON i.product_id = p.id
        WHERE i.user_id = ?
        ORDER BY i.timestamp DESC
        LIMIT 5
    ''', (USER_ID,))
    
    recent_categories = [row['category'] for row in c.fetchall()]
    
    if recent_categories:
        most_common_cat = max(set(recent_categories), key=recent_categories.count)
        
        c.execute('''
            SELECT * FROM products 
            WHERE category = ?
            ORDER BY RANDOM()
            LIMIT 4
        ''', (most_common_cat,))
        recommended_products = [dict(row) for row in c.fetchall()]
        
        if len(recommended_products) < 4:
            needed = 4 - len(recommended_products)
            c.execute('''
                SELECT * FROM products 
                WHERE category != ?
                ORDER BY RANDOM()
                LIMIT ?
            ''', (most_common_cat, needed))
            recommended_products.extend([dict(row) for row in c.fetchall()])
    else:
        c.execute('SELECT * FROM products ORDER BY RANDOM() LIMIT 4')
        recommended_products = [dict(row) for row in c.fetchall()]

    conn.close()
    return jsonify({'recommendations': recommended_products})

@app.route('/recent', methods=['GET'])
def recent():
    conn, c = get_db_cursor()
    c.execute('''
        SELECT p.*
        FROM interactions i
        JOIN products p ON i.product_id = p.id
        WHERE i.user_id = ?
        GROUP BY p.id
        ORDER BY MAX(i.timestamp) DESC
        LIMIT 4
    ''', (USER_ID,))
    
    recent_products = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'recent': recent_products})

@app.route('/search_suggest', methods=['GET'])
def search_suggest():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    conn, c = get_db_cursor()
    # Simple search for autocomplete
    c.execute('''
        SELECT id, name, category, image_url 
        FROM products 
        WHERE LOWER(name) LIKE ? OR LOWER(category) LIKE ?
        LIMIT 5
    ''', (f'%{query}%', f'%{query}%'))
    
    suggestions = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(suggestions)

# --- CART AND CHECKOUT ROUTES ---

@app.route('/cart', methods=['GET'])
def view_cart():
    conn, c = get_db_cursor()
    c.execute('''
        SELECT c.id as cart_id, p.*, c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (USER_ID,))
    cart_items = [dict(row) for row in c.fetchall()]
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    conn.close()
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    if quantity < 1:
        quantity = 1
        
    conn, c = get_db_cursor()
    c.execute('SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?', (USER_ID, product_id))
    item = c.fetchone()
    
    if item:
        c.execute('UPDATE cart SET quantity = quantity + ? WHERE id = ?', (quantity, item['id']))
    else:
        c.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)', (USER_ID, product_id, quantity))
        
    conn.commit()
    conn.close()
    
    # Check if redirect parameter exists (if called via AJAX or form from product page)
    # default redirect to cart
    return redirect(url_for('view_cart'))

@app.route('/cart/remove/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    conn, c = get_db_cursor()
    c.execute('DELETE FROM cart WHERE id = ? AND user_id = ?', (cart_id, USER_ID))
    conn.commit()
    conn.close()
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        address = request.form.get('address')
        city = request.form.get('city')
        zip_code = request.form.get('zipcode')
        full_address = f"{address}, {city}, {zip_code}"
        return redirect(url_for('payment', addr=full_address))
        
    conn, c = get_db_cursor()
    c.execute('SELECT p.price, c.quantity FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = ?', (USER_ID,))
    items = c.fetchall()
    total = sum(item['price'] * item['quantity'] for item in items)
    conn.close()
    
    if total == 0:
        return redirect(url_for('index'))
        
    return render_template('checkout.html', total=total)

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    address = request.args.get('addr', 'Unknown Address')
    conn, c = get_db_cursor()
    c.execute('SELECT p.price, c.quantity FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = ?', (USER_ID,))
    items = c.fetchall()
    total = sum(item['price'] * item['quantity'] for item in items)
    
    if request.method == 'POST':
        if total > 0:
            c.execute('INSERT INTO orders (user_id, address, total_price, status) VALUES (?, ?, ?, ?)', 
                      (USER_ID, address, total, 'Placed'))
            order_id = c.lastrowid
            c.execute('DELETE FROM cart WHERE user_id = ?', (USER_ID,))
            conn.commit()
            conn.close()
            return redirect(url_for('success', order_id=order_id))
            
    conn.close()
    return render_template('payment.html', total=total, address=address)

@app.route('/success/<int:order_id>')
def success(order_id):
    return render_template('success.html', order_id=order_id)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
