<img width="1896" height="855" alt="image" src="https://github.com/user-attachments/assets/2f330cfa-801d-4db9-873f-47516cab771d" /># Sweet Shop Management System

A full-stack Sweet Shop Management System built with FastAPI (Python) and Streamlit, featuring user authentication, CRUD operations for sweets, inventory management, and search functionality.

## Features

- **User Authentication**: Register and login with JWT token-based authentication
- **Sweet Management**: Add, view, update, and delete sweets (admin only for delete)
- **Search**: Search sweets by name, category, or price range
- **Inventory Management**: Purchase sweets (decrease stock) and restock (admin only)
- **Admin Privileges**: First registered user automatically becomes admin, or use admin key during registration

## Project Structure

```
.
├── main.py              # FastAPI backend with CLI interface
├── streamlit_app.py     # Streamlit frontend
├── database.py          # Database models and operations
├── models.py            # Pydantic models for validation
├── auth.py              # Authentication utilities (JWT, password hashing)
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

The database will be automatically created when you first run `main.py`. A SQLite database file `sweet_shop.db` will be created in the project directory.

### 3. Run the Application

#### Option A: FastAPI Backend with CLI

Run the main.py file to access the CLI interface for user registration/login:

```bash
python main.py
```

This will:
1. Initialize the database
2. Show a CLI menu to register or login
3. Optionally start the FastAPI server

The API will be available at:
- API: http://localhost:8000
<img width="862" height="77" alt="image" src="https://github.com/user-attachments/assets/84b86742-124f-4648-984b-1eabbfd3e35e" />
- API Documentation: http://localhost:8000/docs
<img width="1896" height="855" alt="image" src="https://github.com/user-attachments/assets/6306c03f-efa8-40c4-951d-3d2a55d21dbc" />

#### Option B: Streamlit Frontend

In a separate terminal, run:

```bash
streamlit run streamlit_app.py
```

The Streamlit app will open in your browser (usually at http://localhost:8501).
<img width="1896" height="855" alt="image" src="https://github.com/user-attachments/assets/e72eaa0d-77ef-4a36-a03f-287404c3a29c" />

**Note**: Make sure the FastAPI server is running (from Option A) before using the Streamlit frontend, as it connects to the API.

## Usage

### First Time Setup

1. Run `python main.py`
2. Choose option 1 to register a new user
3. The first user registered will automatically have admin privileges
4. **Admin Key**: To grant admin privileges to additional users, enter the admin key `aswd` during registration (optional field)
5. Choose 'y' when asked if you want to start the API server
6. In another terminal, run `streamlit run streamlit_app.py` to access the web interface

### Admin Key

- **Admin Key**: `aswd`
- During registration, you can optionally provide this key to grant admin privileges
- The first user registered automatically gets admin privileges (no key needed)
- Admin privileges allow you to:
  - Delete sweets
  - Restock inventory
  - Access all protected endpoints

### API Endpoints

#### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get JWT token
<img width="497" height="169" alt="{40BFE147-E92D-4957-8EFA-7809ADE72A55}" src="https://github.com/user-attachments/assets/1797b578-5669-4e4d-b039-bd252d4f6c7b" />

#### Sweets (Protected - requires authentication)
- `POST /api/sweets` - Add a new sweet
- `GET /api/sweets` - Get all sweets
- `GET /api/sweets/search` - Search sweets (query params: name, category, min_price, max_price)
- `PUT /api/sweets/{id}` - Update a sweet
- `DELETE /api/sweets/{id}` - Delete a sweet (Admin only)
<img width="312" height="259" alt="{2E9E9894-6303-4105-AA64-2F3A0D866CB6}" src="https://github.com/user-attachments/assets/f7c92e9c-e67f-41c7-96f0-9be61aa313d5" />

#### Inventory (Protected - requires authentication)
- `POST /api/sweets/{id}/purchase` - Purchase a sweet (decreases quantity)
- `POST /api/sweets/{id}/restock` - Restock a sweet (increases quantity, Admin only)
<img width="479" height="328" alt="image" src="https://github.com/user-attachments/assets/e43e80b9-89fb-41c0-87d6-f9b074f7089c" />

### Using the Streamlit Interface

1. **Login/Register**: Use the login or register tabs to create an account or sign in
2. **View Sweets**: See all available sweets with their details
3. **Add Sweet**: Create new sweets with name, category, price, and initial quantity
4. **Search**: Search for sweets by various criteria
5. **Inventory**: Purchase sweets or restock them (restock requires admin privileges)

### Admin Features

- Delete sweets
- Restock inventory
- First registered user automatically becomes admin
- Additional users can get admin privileges by providing admin key `aswd` during registration

## Database

The application uses SQLite (`sweet_shop.db`) which is automatically created in the project directory. The database contains two tables:

- **users**: Stores user accounts with username, password hash, and admin status
- **sweets**: Stores sweet information with name, category, price, and quantity

## Security Notes

- Passwords are hashed using SHA256
- JWT tokens are used for authentication
- Admin-only endpoints are protected
- Admin key (`aswd`) is required for granting admin privileges during registration
- **Important**: Change the `SECRET_KEY` in `auth.py` and the `ADMIN_KEY` in `main.py` for production use!

## Testing

You can test the API using:
- The interactive API documentation at http://localhost:8000/docs
- The Streamlit frontend
- Any HTTP client (Postman, curl, etc.)

## Example API Usage

### Register a user
```bash
# Regular user registration
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "password123"}'
<img width="1042" height="131" alt="image" src="https://github.com/user-attachments/assets/817ad7fc-17fc-491c-a00b-c7ac06c17ef4" />

# Register with admin privileges (using admin key)
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123", "admin_key": "aswd"}'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Add a sweet (with token)
```bash
curl -X POST "http://localhost:8000/api/sweets" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name": "Chocolate Bar", "category": "Chocolate", "price": 2.50, "quantity": 100}'
```

## Troubleshooting

- **Connection Error in Streamlit**: Make sure the FastAPI server is running on port 8000
- **Database Errors**: Delete `sweet_shop.db` and restart to recreate the database
- **Port Already in Use**: Change the port in `main.py` (uvicorn.run) or stop the process using port 8000

## My AI Usage

During the development of this Sweet Shop Management System, I utilized AI tools to assist with specific aspects of the project:

### AI Tools Used

- **ChatGPT**: Used for brainstorming and code assistance

### How I Used AI

1. **Streamlit Frontend Development**: I used ChatGPT to help create the Streamlit application (`streamlit_app.py`). The AI assisted with:
   - Structuring the user interface components
   - Implementing the authentication flow in Streamlit
   - Creating the form layouts and tab navigation
   - Handling API requests and error management in the Streamlit context

2. **API Endpoint Design**: I used ChatGPT to brainstorm and refine the RESTful API endpoint structures. The AI helped with:
   - Planning the endpoint organization and naming conventions
   - Designing the request/response models
   - Structuring the authentication flow and protected routes
   - Planning the inventory management endpoints

### What I Built Myself

The core application logic, database design, authentication system, CLI interface, and overall architecture were developed independently. The AI was used primarily as a development tool to accelerate specific tasks and provide guidance on best practices.
