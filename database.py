import sqlite3
from datetime import datetime
from typing import Optional

# Database file name
DB_FILE = "sweet_shop.db"

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    
    # Sweets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(username: str, password_hash: str, is_admin: bool = False) -> int:
    """Create a new user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, password_hash, is_admin, created_at)
        VALUES (?, ?, ?, ?)
    """, (username, password_hash, 1 if is_admin else 0, datetime.now().isoformat()))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_sweet_by_id(sweet_id: int) -> Optional[dict]:
    """Get sweet by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sweets WHERE id = ?", (sweet_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_sweets() -> list:
    """Get all sweets"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sweets ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def create_sweet(name: str, category: str, price: float, quantity: int) -> int:
    """Create a new sweet"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sweets (name, category, price, quantity, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (name, category, price, quantity, datetime.now().isoformat()))
    sweet_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sweet_id

def update_sweet(sweet_id: int, name: str = None, category: str = None, 
                 price: float = None, quantity: int = None) -> bool:
    """Update a sweet's details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if category is not None:
        updates.append("category = ?")
        values.append(category)
    if price is not None:
        updates.append("price = ?")
        values.append(price)
    if quantity is not None:
        updates.append("quantity = ?")
        values.append(quantity)
    
    if not updates:
        conn.close()
        return False
    
    values.append(sweet_id)
    query = f"UPDATE sweets SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def delete_sweet(sweet_id: int) -> bool:
    """Delete a sweet"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sweets WHERE id = ?", (sweet_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def search_sweets(name: str = None, category: str = None, 
                  min_price: float = None, max_price: float = None) -> list:
    """Search sweets by name, category, or price range"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM sweets WHERE 1=1"
    params = []
    
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    if category:
        query += " AND category = ?"
        params.append(category)
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    
    query += " ORDER BY id"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def purchase_sweet(sweet_id: int, quantity: int) -> bool:
    """Purchase a sweet (decrease quantity)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantity FROM sweets WHERE id = ?", (sweet_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    
    current_quantity = row[0]
    if current_quantity < quantity:
        conn.close()
        return False
    
    new_quantity = current_quantity - quantity
    cursor.execute("UPDATE sweets SET quantity = ? WHERE id = ?", (new_quantity, sweet_id))
    conn.commit()
    conn.close()
    return True

def restock_sweet(sweet_id: int, quantity: int) -> bool:
    """Restock a sweet (increase quantity)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantity FROM sweets WHERE id = ?", (sweet_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    
    current_quantity = row[0]
    new_quantity = current_quantity + quantity
    cursor.execute("UPDATE sweets SET quantity = ? WHERE id = ?", (new_quantity, sweet_id))
    conn.commit()
    conn.close()
    return True

