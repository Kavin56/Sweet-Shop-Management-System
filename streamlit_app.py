import streamlit as st
import requests
from typing import Optional

# API base URL
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

def make_authenticated_request(method: str, endpoint: str, data: dict = None, params: dict = None):
    """Make an authenticated API request"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            return response.json(), None
        elif response.status_code == 204:
            return None, None
        else:
            return None, response.json().get("detail", "An error occurred")
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to API. Make sure the server is running!"
    except Exception as e:
        return None, str(e)

def login(username: str, password: str):
    """Login user"""
    try:
        # Clean and validate inputs
        username = str(username).strip()
        password = str(password).strip()
        
        if not username or not password:
            return False, "Username and password cannot be empty"
        
        payload = {"username": username, "password": password}
        
        response = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                st.session_state.token = data["access_token"]
                st.session_state.username = username
                # Decode token to get admin status
                import jwt
                try:
                    payload = jwt.decode(data["access_token"], "your-secret-key-change-in-production", algorithms=["HS256"])
                    st.session_state.is_admin = payload.get("is_admin", False)
                except Exception:
                    st.session_state.is_admin = False
                return True, "Login successful!"
            else:
                return False, "Invalid response from server: missing access_token"
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", f"Login failed with status {response.status_code}")
            except:
                error_msg = f"Login failed with status {response.status_code}"
            return False, error_msg
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to API. Make sure the server is running on http://localhost:8000"
    except KeyError as e:
        return False, f"Unexpected response format: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def register(username: str, password: str, admin_key: str = None):
    """Register new user"""
    try:
        # Clean and validate inputs
        username = str(username).strip()
        password = str(password).strip()
        admin_key = str(admin_key).strip() if admin_key else None
        
        if not username or not password:
            return False, "Username and password cannot be empty"
        
        payload = {"username": username, "password": password}
        if admin_key:
            payload["admin_key"] = admin_key
        
        response = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                st.session_state.token = data["access_token"]
                st.session_state.username = username
                # Decode token to get admin status
                import jwt
                try:
                    payload = jwt.decode(data["access_token"], "your-secret-key-change-in-production", algorithms=["HS256"])
                    st.session_state.is_admin = payload.get("is_admin", False)
                except Exception:
                    st.session_state.is_admin = False
                admin_msg = " You are now logged in as admin!" if st.session_state.is_admin else " You are now logged in!"
                return True, "Registration successful!" + admin_msg
            else:
                return False, "Invalid response from server: missing access_token"
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", f"Registration failed with status {response.status_code}")
            except:
                error_msg = f"Registration failed with status {response.status_code}"
            return False, error_msg
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to API. Make sure the server is running on http://localhost:8000"
    except KeyError as e:
        return False, f"Unexpected response format: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def logout():
    """Logout user"""
    st.session_state.token = None
    st.session_state.username = None
    st.session_state.is_admin = False

# Main app
st.set_page_config(page_title="Sweet Shop Management", layout="wide")

st.title("🍬 Sweet Shop Management System")

# Check API connection
try:
    response = requests.get(f"{API_BASE_URL}/docs", timeout=2)
    api_status = "🟢 API Connected"
except:
    api_status = "🔴 API Not Connected - Make sure to run 'python main.py' first!"

st.sidebar.markdown(f"**Status:** {api_status}")
if "Not Connected" in api_status:
    st.sidebar.warning("The API server must be running on http://localhost:8000 for this app to work.")

# Authentication section
if not st.session_state.token:
    st.header("Login / Register")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            login_submit = st.form_submit_button("Login")
            
            if login_submit:
                login_username = login_username.strip() if login_username else ""
                login_password = login_password.strip() if login_password else ""
                
                if login_username and login_password:
                    success, message = login(login_username, login_password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both username and password")
    
    with tab2:
        with st.form("register_form"):
            reg_username = st.text_input("Username", key="reg_username")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_admin_key = st.text_input("Admin Key (optional)", type="password", key="reg_admin_key", help="Enter 'aswd' to get admin privileges")
            reg_submit = st.form_submit_button("Register")
            
            if reg_submit:
                reg_username = reg_username.strip() if reg_username else ""
                reg_password = reg_password.strip() if reg_password else ""
                reg_admin_key = reg_admin_key.strip() if reg_admin_key else None
                
                if reg_username and reg_password:
                    success, message = register(reg_username, reg_password, reg_admin_key)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both username and password")

else:
    # User is logged in
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"Welcome, {st.session_state.username}!")
        if st.session_state.is_admin:
            st.info("👑 You have Admin privileges")
    with col2:
        if st.button("Logout"):
            logout()
            st.rerun()
    
    # Main functionality tabs
    tab1, tab2, tab3, tab4 = st.tabs(["View Sweets", "Add Sweet", "Search", "Inventory"])
    
    # Tab 1: View All Sweets
    with tab1:
        st.header("All Sweets")
        if st.button("Refresh List"):
            st.rerun()
        
        sweets, error = make_authenticated_request("GET", "/api/sweets")
        if error:
            st.error(f"Error: {error}")
        elif sweets:
            if len(sweets) == 0:
                st.info("No sweets available. Add some sweets using the 'Add Sweet' tab!")
            else:
                for sweet in sweets:
                    with st.expander(f"🍬 {sweet['name']} - ${sweet['price']:.2f}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Category:** {sweet['category']}")
                            st.write(f"**Price:** ${sweet['price']:.2f}")
                            st.write(f"**Quantity in Stock:** {sweet['quantity']}")
                        with col2:
                            st.write(f"**ID:** {sweet['id']}")
                            st.write(f"**Created:** {sweet['created_at'][:10]}")
                            
                            if st.session_state.is_admin:
                                if st.button(f"Delete", key=f"delete_{sweet['id']}"):
                                    _, error = make_authenticated_request("DELETE", f"/api/sweets/{sweet['id']}")
                                    if error:
                                        st.error(f"Error: {error}")
                                    else:
                                        st.success("Sweet deleted!")
                                        st.rerun()
    
    # Tab 2: Add Sweet
    with tab2:
        st.header("Add New Sweet")
        with st.form("add_sweet_form"):
            name = st.text_input("Sweet Name *")
            category = st.text_input("Category *")
            price = st.number_input("Price *", min_value=0.0, step=0.01, format="%.2f")
            quantity = st.number_input("Initial Quantity *", min_value=0, step=1)
            submit = st.form_submit_button("Add Sweet")
            
            if submit:
                if name and category and price >= 0 and quantity >= 0:
                    data = {"name": name, "category": category, "price": price, "quantity": quantity}
                    result, error = make_authenticated_request("POST", "/api/sweets", data=data)
                    if error:
                        st.error(f"Error: {error}")
                    else:
                        st.success(f"Sweet '{name}' added successfully!")
                        st.rerun()
                else:
                    st.error("Please fill all required fields with valid values")
    
    # Tab 3: Search Sweets
    with tab3:
        st.header("Search Sweets")
        with st.form("search_form"):
            search_name = st.text_input("Name (contains)")
            search_category = st.text_input("Category (exact)")
            col1, col2 = st.columns(2)
            with col1:
                min_price = st.number_input("Min Price", min_value=0.0, step=0.01, format="%.2f", value=0.0)
            with col2:
                max_price = st.number_input("Max Price", min_value=0.0, step=0.01, format="%.2f", value=0.0)
            
            search_submit = st.form_submit_button("Search")
            
            if search_submit:
                params = {}
                if search_name:
                    params["name"] = search_name
                if search_category:
                    params["category"] = search_category
                if min_price > 0:
                    params["min_price"] = min_price
                if max_price > 0:
                    params["max_price"] = max_price
                
                results, error = make_authenticated_request("GET", "/api/sweets/search", params=params)
                if error:
                    st.error(f"Error: {error}")
                elif results:
                    st.write(f"Found {len(results)} result(s):")
                    for sweet in results:
                        st.write(f"🍬 **{sweet['name']}** - {sweet['category']} - ${sweet['price']:.2f} (Stock: {sweet['quantity']})")
                else:
                    st.info("No results found")
    
    # Tab 4: Inventory Management
    with tab4:
        st.header("Inventory Management")
        
        # Get all sweets for selection
        sweets, error = make_authenticated_request("GET", "/api/sweets")
        if error:
            st.error(f"Error: {error}")
        elif sweets:
            if len(sweets) == 0:
                st.info("No sweets available. Add some sweets first!")
            else:
                sweet_options = {f"{s['name']} (ID: {s['id']}, Stock: {s['quantity']})": s['id'] for s in sweets}
                selected_sweet = st.selectbox("Select a Sweet", list(sweet_options.keys()))
                sweet_id = sweet_options[selected_sweet]
                
                col1, col2 = st.columns(2)
                
                # Purchase section
                with col1:
                    st.subheader("Purchase Sweet")
                    with st.form("purchase_form"):
                        purchase_qty = st.number_input("Quantity to Purchase", min_value=1, step=1, key="purchase_qty")
                        purchase_submit = st.form_submit_button("Purchase")
                        
                        if purchase_submit:
                            data = {"quantity": purchase_qty}
                            result, error = make_authenticated_request("POST", f"/api/sweets/{sweet_id}/purchase", data=data)
                            if error:
                                st.error(f"Error: {error}")
                            else:
                                st.success(f"Purchased {purchase_qty} unit(s)!")
                                st.rerun()
                
                # Restock section (Admin only)
                with col2:
                    st.subheader("Restock Sweet")
                    if st.session_state.is_admin:
                        with st.form("restock_form"):
                            restock_qty = st.number_input("Quantity to Restock", min_value=1, step=1, key="restock_qty")
                            restock_submit = st.form_submit_button("Restock")
                            
                            if restock_submit:
                                data = {"quantity": restock_qty}
                                result, error = make_authenticated_request("POST", f"/api/sweets/{sweet_id}/restock", data=data)
                                if error:
                                    st.error(f"Error: {error}")
                                else:
                                    st.success(f"Restocked {restock_qty} unit(s)!")
                                    st.rerun()
                    else:
                        st.info("🔒 Admin access required for restocking")
        else:
            st.info("No sweets available. Add some sweets first!")

