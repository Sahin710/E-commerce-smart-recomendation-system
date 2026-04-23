import sqlite3
import os
import random

DB_PATH = os.path.join(os.path.dirname(__file__), 'ecommerce.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            image_url TEXT NOT NULL,
            description TEXT,
            rating REAL,
            stock INTEGER,
            discount INTEGER,
            features TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            address TEXT NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'Placed',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Seed User
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (name) VALUES (?)", ("John Doe",))

    # Seed 50 Products
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        base_products = [
            # Shoes
            ("Nike Air Max 270", "Shoes", 150.00, "https://images.unsplash.com/photo-1542291026-7eec264c27ff"),
            ("Adidas Ultraboost 22", "Shoes", 190.00, "https://images.unsplash.com/photo-1587563871167-1ee9c731aefb"),
            ("Puma Suede Classic", "Shoes", 70.00, "https://images.unsplash.com/photo-1608231387042-66d1773070a5"),
            ("Reebok Club C 85", "Shoes", 75.00, "https://images.unsplash.com/photo-1514989940723-e8e51635b782"),
            ("Vans Old Skool", "Shoes", 65.00, "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77"),
            ("Converse Chuck Taylor All Star", "Shoes", 60.00, "https://images.unsplash.com/photo-1491553895911-0055eca6402d"),
            ("New Balance 990v5", "Shoes", 185.00, "https://images.unsplash.com/photo-1539185441755-769473a23570"),
            ("Asics Gel-Kayano 28", "Shoes", 160.00, "https://images.unsplash.com/photo-1520316587275-5e4f06f68971"),
            ("Timberland Premium 6-Inch Boot", "Shoes", 198.00, "https://images.unsplash.com/photo-1520639888713-7851133b1ed0"),
            ("Dr. Martens 1460 8-Eye Boot", "Shoes", 150.00, "https://images.unsplash.com/photo-1508215885820-4585e5610ec0"),
            # Sunglasses
            ("Ray-Ban Aviator Classic", "Sunglasses", 161.00, "https://images.unsplash.com/photo-1511499767150-a48a237f0083"),
            ("Oakley Holbrook", "Sunglasses", 146.00, "https://images.unsplash.com/photo-1572635196237-14b3f281501f"),
            ("Gucci GG0061S", "Sunglasses", 350.00, "https://images.unsplash.com/photo-1508296695146-257a814070b4"),
            ("Prada Linea Rossa", "Sunglasses", 270.00, "https://images.unsplash.com/photo-1511499767150-a48a237f0083"),
            ("Tom Ford Henry Square", "Sunglasses", 395.00, "https://images.unsplash.com/photo-1572635196237-14b3f281501f"),
            ("Persol PO3048S", "Sunglasses", 260.00, "https://images.unsplash.com/photo-1508296695146-257a814070b4"),
            ("Maui Jim Peahi Polarized", "Sunglasses", 250.00, "https://images.unsplash.com/photo-1511499767150-a48a237f0083"),
            ("Costa Del Mar Fantail", "Sunglasses", 199.00, "https://images.unsplash.com/photo-1572635196237-14b3f281501f"),
            ("Warby Parker Haskell", "Sunglasses", 95.00, "https://images.unsplash.com/photo-1508296695146-257a814070b4"),
            ("Quay Australia High Key", "Sunglasses", 65.00, "https://images.unsplash.com/photo-1511499767150-a48a237f0083"),
            # Electronics
            ("Apple iPhone 14 Pro", "Electronics", 999.00, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9"),
            ("Samsung Galaxy S23 Ultra", "Electronics", 1199.00, "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c"),
            ("Sony WH-1000XM5", "Electronics", 398.00, "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb"),
            ("Apple MacBook Pro 14", "Electronics", 1999.00, "https://images.unsplash.com/photo-1517336714731-489689fd1ca8"),
            ("Dell XPS 13 Plus", "Electronics", 1399.00, "https://images.unsplash.com/photo-1593642632823-8f785ba67e45"),
            ("Nintendo Switch OLED", "Electronics", 349.99, "https://images.unsplash.com/photo-1578303512597-81e6cc155b3e"),
            ("Sony PlayStation 5", "Electronics", 499.99, "https://images.unsplash.com/photo-1606813907291-d86efa9b94db"),
            ("Microsoft Xbox Series X", "Electronics", 499.99, "https://images.unsplash.com/photo-1605901309584-818e25960b8f"),
            ("GoPro HERO11 Black", "Electronics", 399.00, "https://images.unsplash.com/photo-1526644253653-ce9fbb00d07a"),
            ("DJI Mini 3 Pro Drone", "Electronics", 759.00, "https://images.unsplash.com/photo-1524143986875-3b098d78b363"),
            # Clothing
            ("Levi's 501 Original Jeans", "Clothing", 79.50, "https://images.unsplash.com/photo-1542272604-787c3835535d"),
            ("Patagonia Better Sweater", "Clothing", 139.00, "https://images.unsplash.com/photo-1556821840-3a63f95609a7"),
            ("The North Face Nuptse", "Clothing", 280.00, "https://images.unsplash.com/photo-1551028719-00167b16eac5"),
            ("Carhartt WIP Chase", "Clothing", 85.00, "https://images.unsplash.com/photo-1556821840-3a63f95609a7"),
            ("Champion Reverse Weave", "Clothing", 65.00, "https://images.unsplash.com/photo-1551028719-00167b16eac5"),
            ("Nike Sportswear Club", "Clothing", 55.00, "https://images.unsplash.com/photo-1556821840-3a63f95609a7"),
            ("Adidas Originals Firebird", "Clothing", 80.00, "https://images.unsplash.com/photo-1551028719-00167b16eac5"),
            ("Ralph Lauren Classic Polo", "Clothing", 95.00, "https://images.unsplash.com/photo-1556821840-3a63f95609a7"),
            ("Tommy Hilfiger Essential", "Clothing", 35.00, "https://images.unsplash.com/photo-1551028719-00167b16eac5"),
            ("Calvin Klein Trunks", "Clothing", 45.00, "https://images.unsplash.com/photo-1542272604-787c3835535d"),
            # Accessories
            ("Apple Watch Series 8", "Accessories", 399.00, "https://images.unsplash.com/photo-1546868871-7041f2a55e12"),
            ("Garmin Fenix 7 Solar", "Accessories", 899.99, "https://images.unsplash.com/photo-1523275335684-37898b6baf30"),
            ("Samsung Galaxy Watch 5", "Accessories", 449.99, "https://images.unsplash.com/photo-1579586337278-3befd40fd17a"),
            ("Casio G-Shock DW5600E", "Accessories", 74.95, "https://images.unsplash.com/photo-1523275335684-37898b6baf30"),
            ("Rolex Submariner Date", "Accessories", 10250.00, "https://images.unsplash.com/photo-1523275335684-37898b6baf30"),
            ("Bellroy Note Sleeve", "Accessories", 89.00, "https://images.unsplash.com/photo-1627123424574-724758594e93"),
            ("Secrid Twinwallet", "Accessories", 115.00, "https://images.unsplash.com/photo-1627123424574-724758594e93"),
            ("Herschel Supply Co. Bag", "Accessories", 109.99, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62"),
            ("Fjallraven Kanken Classic", "Accessories", 80.00, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62"),
            ("Patagonia Atom Sling 8L", "Accessories", 65.00, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62")
        ]
        
        products = []
        for name, cat, price, url in base_products:
            image_url = f"{url}?auto=format&fit=crop&w=400&q=80"
            description = f"Experience premium quality with the {name} from our latest {cat} collection. Crafted with precision for everyday use ensuring supreme durability and modern aesthetic."
            
            # Additional UI enhancements
            rating = round(random.uniform(3.5, 5.0), 1)
            stock = random.choice([0, random.randint(5, 50)]) # Sometimes 0 for Out of Stock Demo
            discount = random.choice([0, 0, 0, 10, 15, 20, 25]) # Frequently 0, occasionally discounted
            
            features = "Premium Build Quality|Long-lasting durability|Eco-friendly packaging|1 Year Manufacturer Warranty|Sleek Modern Design"
            
            products.append((name, cat, price, image_url, description, rating, stock, discount, features))

        c.executemany('''
            INSERT INTO products 
            (name, category, price, image_url, description, rating, stock, discount, features) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', products)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
