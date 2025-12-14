from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sys

from database import (
    init_database, create_user, get_user_by_username, get_all_sweets,
    create_sweet, update_sweet, delete_sweet, search_sweets,
    purchase_sweet, restock_sweet, get_sweet_by_id
)
from models import (
    UserRegister, UserLogin, TokenResponse, SweetCreate, SweetUpdate,
    SweetResponse, PurchaseRequest, RestockRequest, SearchParams
)
from auth import (
    hash_password, create_access_token, verify_token, authenticate_user
)

# Initialize FastAPI app
app = FastAPI(title="Sweet Shop Management API", version="1.0.0")

# CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()

# Dependency to get current user from token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    username = payload.get("sub")
    user = get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return {
        "id": user["id"],
        "username": user["username"],
        "is_admin": bool(user["is_admin"])
    }

# Dependency to check if user is admin
def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Check if current user is admin"""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# ============ ROOT ENDPOINT ============

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Sweet Shop Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_base": "/api"
    }

@app.get("/api")
def api_info():
    """API information endpoint"""
    return {
        "message": "Sweet Shop Management API",
        "endpoints": {
            "auth": {
                "register": "POST /api/auth/register",
                "login": "POST /api/auth/login"
            },
            "sweets": {
                "list": "GET /api/sweets",
                "create": "POST /api/sweets",
                "search": "GET /api/sweets/search",
                "update": "PUT /api/sweets/{id}",
                "delete": "DELETE /api/sweets/{id} (Admin only)"
            },
            "inventory": {
                "purchase": "POST /api/sweets/{id}/purchase",
                "restock": "POST /api/sweets/{id}/restock (Admin only)"
            }
        }
    }

# ============ AUTH ENDPOINTS ============

@app.post("/api/auth/register", response_model=TokenResponse)
def register(user_data: UserRegister):
    """Register a new user"""
    # Check if username already exists
    if get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Determine admin status
    ADMIN_KEY = "aswd"
    conn = __import__('sqlite3').connect("sweet_shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()
    
    # First user is admin OR user provided correct admin key
    is_admin = (user_count == 0) or (user_data.admin_key == ADMIN_KEY)
    
    password_hash = hash_password(user_data.password)
    user_id = create_user(user_data.username, password_hash, is_admin)
    
    # Generate token
    access_token = create_access_token(data={"sub": user_data.username, "is_admin": is_admin})
    return TokenResponse(access_token=access_token)

@app.post("/api/auth/login", response_model=TokenResponse)
def login(user_data: UserLogin):
    """Login and get access token"""
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(
        data={"sub": user_data.username, "is_admin": user["is_admin"]}
    )
    return TokenResponse(access_token=access_token)

# ============ SWEETS ENDPOINTS ============

@app.post("/api/sweets", response_model=SweetResponse, status_code=status.HTTP_201_CREATED)
def add_sweet(sweet: SweetCreate, current_user: dict = Depends(get_current_user)):
    """Add a new sweet (Protected)"""
    sweet_id = create_sweet(sweet.name, sweet.category, sweet.price, sweet.quantity)
    created_sweet = get_sweet_by_id(sweet_id)
    return SweetResponse(**created_sweet)

@app.get("/api/sweets", response_model=list[SweetResponse])
def get_sweets(current_user: dict = Depends(get_current_user)):
    """Get all sweets (Protected)"""
    sweets = get_all_sweets()
    return [SweetResponse(**sweet) for sweet in sweets]

@app.get("/api/sweets/search", response_model=list[SweetResponse])
def search_sweets_endpoint(
    name: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    current_user: dict = Depends(get_current_user)
):
    """Search sweets by name, category, or price range (Protected)"""
    results = search_sweets(name, category, min_price, max_price)
    return [SweetResponse(**sweet) for sweet in results]

@app.put("/api/sweets/{sweet_id}", response_model=SweetResponse)
def update_sweet_endpoint(
    sweet_id: int,
    sweet_update: SweetUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a sweet's details (Protected)"""
    if not get_sweet_by_id(sweet_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sweet not found"
        )
    
    update_sweet(
        sweet_id,
        name=sweet_update.name,
        category=sweet_update.category,
        price=sweet_update.price,
        quantity=sweet_update.quantity
    )
    updated_sweet = get_sweet_by_id(sweet_id)
    return SweetResponse(**updated_sweet)

@app.delete("/api/sweets/{sweet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sweet_endpoint(sweet_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete a sweet (Admin only)"""
    if not get_sweet_by_id(sweet_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sweet not found"
        )
    delete_sweet(sweet_id)
    return None

# ============ INVENTORY ENDPOINTS ============

@app.post("/api/sweets/{sweet_id}/purchase", response_model=SweetResponse)
def purchase_sweet_endpoint(
    sweet_id: int,
    purchase: PurchaseRequest,
    current_user: dict = Depends(get_current_user)
):
    """Purchase a sweet, decreasing its quantity (Protected)"""
    sweet = get_sweet_by_id(sweet_id)
    if not sweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sweet not found"
        )
    
    if not purchase_sweet(sweet_id, purchase.quantity):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient quantity in stock"
        )
    
    updated_sweet = get_sweet_by_id(sweet_id)
    return SweetResponse(**updated_sweet)

@app.post("/api/sweets/{sweet_id}/restock", response_model=SweetResponse)
def restock_sweet_endpoint(
    sweet_id: int,
    restock: RestockRequest,
    current_user: dict = Depends(get_admin_user)
):
    """Restock a sweet, increasing its quantity (Admin only)"""
    sweet = get_sweet_by_id(sweet_id)
    if not sweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sweet not found"
        )
    
    restock_sweet(sweet_id, restock.quantity)
    updated_sweet = get_sweet_by_id(sweet_id)
    return SweetResponse(**updated_sweet)

# ============ CLI INTERFACE ============

def display_sweets(sweets_list):
    """Display sweets in a formatted table"""
    if not sweets_list:
        print("\nNo sweets found.")
        return
    
    print("\n" + "="*80)
    print(f"{'ID':<5} {'Name':<25} {'Category':<15} {'Price':<10} {'Quantity':<10}")
    print("="*80)
    for sweet in sweets_list:
        print(f"{sweet['id']:<5} {sweet['name']:<25} {sweet['category']:<15} ${sweet['price']:<9.2f} {sweet['quantity']:<10}")
    print("="*80)

def sweet_management_menu(current_user):
    """Main menu for sweet management after login"""
    is_admin = current_user["is_admin"]
    
    while True:
        print("\n" + "="*50)
        print("Sweet Shop Management - Main Menu")
        print("="*50)
        print(f"Logged in as: {current_user['username']}")
        if is_admin:
            print("👑 Admin privileges active")
        print("\n1. View All Sweets")
        print("2. Add New Sweet")
        print("3. Search Sweets")
        print("4. Update Sweet")
        print("5. Delete Sweet" + (" (Admin)" if is_admin else " (Admin Only)"))
        print("6. Purchase Sweet")
        print("7. Restock Sweet" + (" (Admin)" if is_admin else " (Admin Only)"))
        print("8. Logout")
        print("9. Exit Application")
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == "1":
            # View all sweets
            print("\n--- All Sweets ---")
            sweets = get_all_sweets()
            display_sweets(sweets)
        
        elif choice == "2":
            # Add new sweet
            print("\n--- Add New Sweet ---")
            name = input("Enter sweet name: ").strip()
            category = input("Enter category: ").strip()
            try:
                price = float(input("Enter price: ").strip())
                quantity = int(input("Enter initial quantity: ").strip())
                
                if not name or not category:
                    print("Error: Name and category are required!")
                    continue
                
                if price < 0 or quantity < 0:
                    print("Error: Price and quantity must be non-negative!")
                    continue
                
                sweet_id = create_sweet(name, category, price, quantity)
                print(f"\n✓ Sweet '{name}' added successfully! (ID: {sweet_id})")
            except ValueError:
                print("Error: Invalid input! Price must be a number and quantity must be an integer.")
        
        elif choice == "3":
            # Search sweets
            print("\n--- Search Sweets ---")
            print("Leave fields empty to skip that filter")
            name = input("Enter name (or part of name): ").strip() or None
            category = input("Enter category (exact match): ").strip() or None
            
            min_price = None
            max_price = None
            min_price_str = input("Enter minimum price: ").strip()
            if min_price_str:
                try:
                    min_price = float(min_price_str)
                except ValueError:
                    print("Warning: Invalid minimum price, ignoring...")
            
            max_price_str = input("Enter maximum price: ").strip()
            if max_price_str:
                try:
                    max_price = float(max_price_str)
                except ValueError:
                    print("Warning: Invalid maximum price, ignoring...")
            
            results = search_sweets(name, category, min_price, max_price)
            print(f"\nFound {len(results)} result(s):")
            display_sweets(results)
        
        elif choice == "4":
            # Update sweet
            print("\n--- Update Sweet ---")
            try:
                sweet_id = int(input("Enter sweet ID to update: ").strip())
                sweet = get_sweet_by_id(sweet_id)
                if not sweet:
                    print(f"Error: Sweet with ID {sweet_id} not found!")
                    continue
                
                print(f"\nCurrent details:")
                print(f"  Name: {sweet['name']}")
                print(f"  Category: {sweet['category']}")
                print(f"  Price: ${sweet['price']:.2f}")
                print(f"  Quantity: {sweet['quantity']}")
                print("\nEnter new values (press Enter to keep current value):")
                
                new_name = input(f"Name [{sweet['name']}]: ").strip() or None
                new_category = input(f"Category [{sweet['category']}]: ").strip() or None
                
                new_price = None
                price_str = input(f"Price [${sweet['price']:.2f}]: ").strip()
                if price_str:
                    try:
                        new_price = float(price_str)
                    except ValueError:
                        print("Warning: Invalid price, keeping current value")
                
                new_quantity = None
                quantity_str = input(f"Quantity [{sweet['quantity']}]: ").strip()
                if quantity_str:
                    try:
                        new_quantity = int(quantity_str)
                    except ValueError:
                        print("Warning: Invalid quantity, keeping current value")
                
                if update_sweet(sweet_id, new_name, new_category, new_price, new_quantity):
                    print(f"\n✓ Sweet updated successfully!")
                else:
                    print("\nError: Failed to update sweet!")
            except ValueError:
                print("Error: Invalid sweet ID!")
        
        elif choice == "5":
            # Delete sweet (Admin only)
            if not is_admin:
                print("\n✗ Error: Admin privileges required to delete sweets!")
                continue
            
            print("\n--- Delete Sweet ---")
            try:
                sweet_id = int(input("Enter sweet ID to delete: ").strip())
                sweet = get_sweet_by_id(sweet_id)
                if not sweet:
                    print(f"Error: Sweet with ID {sweet_id} not found!")
                    continue
                
                print(f"\nSweet to delete:")
                print(f"  Name: {sweet['name']}")
                print(f"  Category: {sweet['category']}")
                print(f"  Price: ${sweet['price']:.2f}")
                print(f"  Quantity: {sweet['quantity']}")
                
                confirm = input("\nAre you sure you want to delete this sweet? (yes/no): ").strip().lower()
                if confirm == "yes":
                    if delete_sweet(sweet_id):
                        print(f"\n✓ Sweet '{sweet['name']}' deleted successfully!")
                    else:
                        print("\nError: Failed to delete sweet!")
                else:
                    print("Deletion cancelled.")
            except ValueError:
                print("Error: Invalid sweet ID!")
        
        elif choice == "6":
            # Purchase sweet
            print("\n--- Purchase Sweet ---")
            try:
                sweet_id = int(input("Enter sweet ID to purchase: ").strip())
                quantity = int(input("Enter quantity to purchase: ").strip())
                
                if quantity <= 0:
                    print("Error: Quantity must be positive!")
                    continue
                
                sweet = get_sweet_by_id(sweet_id)
                if not sweet:
                    print(f"Error: Sweet with ID {sweet_id} not found!")
                    continue
                
                if purchase_sweet(sweet_id, quantity):
                    updated = get_sweet_by_id(sweet_id)
                    print(f"\n✓ Purchased {quantity} unit(s) of '{sweet['name']}'!")
                    print(f"  Remaining stock: {updated['quantity']}")
                else:
                    print(f"\n✗ Error: Insufficient stock! Available: {sweet['quantity']}")
            except ValueError:
                print("Error: Invalid input! ID and quantity must be integers.")
        
        elif choice == "7":
            # Restock sweet (Admin only)
            if not is_admin:
                print("\n✗ Error: Admin privileges required to restock!")
                continue
            
            print("\n--- Restock Sweet ---")
            try:
                sweet_id = int(input("Enter sweet ID to restock: ").strip())
                quantity = int(input("Enter quantity to add: ").strip())
                
                if quantity <= 0:
                    print("Error: Quantity must be positive!")
                    continue
                
                sweet = get_sweet_by_id(sweet_id)
                if not sweet:
                    print(f"Error: Sweet with ID {sweet_id} not found!")
                    continue
                
                if restock_sweet(sweet_id, quantity):
                    updated = get_sweet_by_id(sweet_id)
                    print(f"\n✓ Restocked {quantity} unit(s) of '{sweet['name']}'!")
                    print(f"  New stock: {updated['quantity']}")
                else:
                    print("\n✗ Error: Failed to restock!")
            except ValueError:
                print("Error: Invalid input! ID and quantity must be integers.")
        
        elif choice == "8":
            # Logout
            print("\n✓ Logged out successfully!")
            return None
        
        elif choice == "9":
            # Exit application
            print("\nGoodbye!")
            sys.exit(0)
        
        else:
            print("\nInvalid choice! Please try again.")

def cli_interface():
    """Command-line interface for user registration and login"""
    while True:
        print("\n" + "="*50)
        print("Sweet Shop Management System - CLI")
        print("="*50)
        print("\n1. Register (Create Account)")
        print("2. Login")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1/2/3): ").strip()
        
        if choice == "1":
            print("\n--- Register New User ---")
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            admin_key = input("Enter admin key (optional, press Enter to skip): ").strip()
            
            if not username or not password:
                print("Error: Username and password are required!")
                continue
            
            # Check if user exists
            if get_user_by_username(username):
                print(f"Error: Username '{username}' already exists!")
                continue
            
            # Determine admin status
            ADMIN_KEY = "aswd"
            conn = __import__('sqlite3').connect("sweet_shop.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            conn.close()
            
            # First user is admin OR user provided correct admin key
            is_admin = (user_count == 0) or (admin_key == ADMIN_KEY)
            
            password_hash = hash_password(password)
            user_id = create_user(username, password_hash, is_admin)
            
            print(f"\n✓ User '{username}' registered successfully!")
            if is_admin:
                if user_count == 0:
                    print("✓ You are the first user - you have admin privileges!")
                else:
                    print("✓ Admin key verified - you have admin privileges!")
        
        elif choice == "2":
            print("\n--- Login ---")
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            
            user = authenticate_user(username, password)
            if user:
                print(f"\n✓ Login successful! Welcome, {username}!")
                if user["is_admin"]:
                    print("✓ You have admin privileges!")
                
                # Enter sweet management menu
                result = sweet_management_menu(user)
                # If user logged out, continue to main menu
            else:
                print("\n✗ Invalid username or password!")
        
        elif choice == "3":
            print("\nGoodbye!")
            sys.exit(0)
        
        else:
            print("\nInvalid choice! Please try again.")

if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Start the server in a separate thread so it runs in the background
    import threading
    import uvicorn
    
    def run_server():
        """Run the FastAPI server"""
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give server a moment to start
    import time
    time.sleep(1)
    
    print("\n" + "="*50)
    print("FastAPI Server Started!")
    print("="*50)
    print("API is available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("API info at: http://localhost:8000/api")
    print("\nThe server is running in the background.")
    print("You can use the CLI below AND access the web API simultaneously!")
    print("="*50)
    
    # Show CLI interface (this will run in the foreground)
    try:
        cli_interface()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        sys.exit(0)

