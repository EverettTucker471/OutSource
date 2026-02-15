# OutSource Backend - Docker Setup Instructions

This document explains how to run the OutSource Python backend API and MySQL database using Docker containers.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose installed (comes with Docker Desktop)

## Environment Setup

Before running the application, you need to set up your environment variables:

1. **Copy the environment template**:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your desired credentials:
   ```
   MYSQL_ROOT_PASSWORD=your_secure_root_password
   MYSQL_DATABASE=outsource_db
   MYSQL_USER=your_db_user
   MYSQL_PASSWORD=your_secure_password
   DATABASE_URL=mysql+pymysql://your_db_user:your_secure_password@db:3306/outsource_db
   API_PORT=8000
   MYSQL_PORT=3306

   # JWT Configuration
   JWT_SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_HOURS=24
   ```

   **Generate a secure JWT secret key**:
   ```bash
   openssl rand -hex 32
   ```

   **IMPORTANT**:
   - The `.env` file is git-ignored and will not be committed to version control
   - Never commit passwords or secrets to git
   - For production, use strong passwords and consider using a secrets manager
   - The default `.env` file created for you has basic development credentials

## Project Structure

```
backend/
├── app/
│   ├── controllers/      # API endpoint controllers
│   ├── services/         # Business logic layer
│   ├── repositories/     # Database access layer
│   ├── models/           # SQLAlchemy database models
│   ├── dtos/             # Data Transfer Objects (Pydantic models)
│   ├── dependencies/     # FastAPI dependencies (auth, etc.)
│   ├── utils/            # Utilities (JWT, helpers, etc.)
│   ├── testing/          # Test files
│   ├── config.py         # Application configuration
│   ├── database.py       # Database configuration
│   └── main.py           # FastAPI application entry point
├── .env                  # Environment variables (git-ignored)
├── .env.example          # Environment template
├── Dockerfile            # Docker image for Python app
├── docker-compose.yml    # Orchestration for app and MySQL
├── requirements.txt      # Python dependencies
└── instructions.md       # This file
```

## Running the Application

### Option 1: Using Docker Compose (Recommended)

This will start both the MySQL database and the Python API in separate containers.

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Build and start the containers:
   ```bash
   docker-compose up -d --build
   ```

3. Check that containers are running:
   ```bash
   docker-compose ps
   ```

4. View logs:
   ```bash
   docker-compose logs -f
   ```

5. Stop the containers:
   ```bash
   docker-compose down
   ```

6. Stop and remove volumes (deletes database data):
   ```bash
   docker-compose down -v
   ```

### Option 2: Running Containers Individually

#### Step 1: Run MySQL Container

```bash
docker run -d \
  --name outsource_mysql \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=outsource_db \
  -e MYSQL_USER=user \
  -e MYSQL_PASSWORD=password \
  -p 3306:3306 \
  mysql:8.0
```

#### Step 2: Build and Run the Python App Container

1. Build the Docker image:
   ```bash
   cd backend
   docker build -t outsource-api .
   ```

2. Run the container (using environment variables from your .env file):
   ```bash
   docker run -d \
     --name outsource_api \
     -p 8000:8000 \
     --env-file .env \
     --link outsource_mysql:db \
     outsource-api
   ```

## Accessing the Application

Once the containers are running:

- **API Base URL**: http://localhost:8000
- **API Documentation (Swagger UI)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **MySQL Database**: localhost:3306

## Authentication

The API uses JWT (JSON Web Token) authentication to secure endpoints.

### Authentication Flow

1. **Login** with username and password to receive a JWT token
2. **Include the token** in the `Authorization` header for all protected endpoints
3. **Logout** when done (client-side, just discard the token)

### JWT Token Details

- **Expiration**: 24 hours (configurable via `JWT_ACCESS_TOKEN_EXPIRE_HOURS`)
- **Algorithm**: HS256
- **Payload**: Contains user ID and expiration timestamp
- **Stateless**: No server-side session storage

### Token Structure

The JWT token payload contains:
```json
{
  "sub": "1",           // User ID
  "exp": 1739599200     // Expiration timestamp (Unix time)
}
```

### Protected vs Unprotected Endpoints

**Unprotected** (no authentication required):
- `POST /login` - Authenticate and get token
- `POST /logout` - Logout (client-side)
- `GET /health` - Health check
- `GET /` - Welcome message

**Protected** (requires JWT token):
- `POST /users` - Create new user
- `GET /users` - List all users
- `GET /users/{user_id}` - Get user by ID
- `GET /users/current` - Get current authenticated user

## API Endpoints

### Authentication Endpoints

#### Login
Get a JWT token by authenticating with username and password.

```bash
POST /login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "securepassword123"
}

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Logout
Logout endpoint (client should discard the token).

```bash
POST /logout

# Response:
{
  "message": "Successfully logged out"
}
```

### User Endpoints

All user endpoints require authentication via JWT token in the `Authorization` header.

#### Create User
```bash
POST /users
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "username": "johndoe",
  "password": "securepassword123",
  "name": "John Doe",
  "preferences": []
}

# Response (201 Created):
{
  "id": 1,
  "username": "johndoe",
  "name": "John Doe",
  "preferences": []
}
```

#### Get Current User
Get the currently authenticated user from the JWT token.

```bash
GET /users/current
Authorization: Bearer <your-jwt-token>

# Response (200 OK):
{
  "id": 1,
  "username": "johndoe",
  "name": "John Doe",
  "preferences": []
}
```

#### Get User by ID
```bash
GET /users/{user_id}
Authorization: Bearer <your-jwt-token>

# Response (200 OK):
{
  "id": 1,
  "username": "johndoe",
  "name": "John Doe",
  "preferences": []
}
```

#### Get All Users
```bash
GET /users
Authorization: Bearer <your-jwt-token>

# Response (200 OK):
[
  {
    "id": 1,
    "username": "johndoe",
    "name": "John Doe"
  },
  {
    "id": 2,
    "username": "janedoe",
    "name": "Jane Doe"
  }
]
```

## Testing the API

### Using curl

#### Complete Authentication Flow

1. **Login to get a JWT token**:
   ```bash
   curl -X POST http://localhost:8000/login \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "password": "testpass123"
     }'
   ```

   Save the `access_token` from the response:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzM5NTk5MjAwfQ...",
     "token_type": "bearer"
   }
   ```

2. **Store the token in a variable** (for convenience):
   ```bash
   TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```

3. **Create a user** (requires authentication):
   ```bash
   curl -X POST http://localhost:8000/users \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{
       "username": "newuser",
       "password": "newpass123",
       "name": "New User",
       "preferences": []
     }'
   ```

4. **Get current user**:
   ```bash
   curl http://localhost:8000/users/current \
     -H "Authorization: Bearer $TOKEN"
   ```

5. **Get all users**:
   ```bash
   curl http://localhost:8000/users \
     -H "Authorization: Bearer $TOKEN"
   ```

6. **Get user by ID**:
   ```bash
   curl http://localhost:8000/users/1 \
     -H "Authorization: Bearer $TOKEN"
   ```

7. **Logout**:
   ```bash
   curl -X POST http://localhost:8000/logout
   ```

#### Testing Without Authentication (Should Fail)

Try accessing a protected endpoint without a token:
```bash
curl http://localhost:8000/users
# Response: 401 Unauthorized
# {"detail": "Not authenticated"}
```

Try with an invalid token:
```bash
curl http://localhost:8000/users \
  -H "Authorization: Bearer invalid_token"
# Response: 401 Unauthorized
# {"detail": "Could not validate credentials"}
```

### Using the Swagger UI

The Swagger UI now includes authentication support.

1. Open http://localhost:8000/docs in your browser
2. **Authenticate first**:
   - Click the "Authorize" button (🔒) at the top right
   - First, login to get a token:
     - Expand the `POST /login` endpoint
     - Click "Try it out"
     - Enter your username and password
     - Click "Execute"
     - Copy the `access_token` from the response
   - Click "Authorize" again
   - Enter: `Bearer <your-token>` (replace `<your-token>` with the actual token)
   - Click "Authorize"
3. Now you can test protected endpoints:
   - Expand any endpoint you want to test
   - Click "Try it out"
   - Fill in the required parameters
   - Click "Execute"
4. The 🔒 icon next to endpoints indicates they require authentication

## Automated Testing

The backend includes comprehensive automated tests using pytest.

### Test Structure

```
backend/app/testing/
├── auth_api_testing.py      # Authentication endpoint tests
└── user_api_testing.py      # User endpoint tests
```

### Running Tests

#### 1. Install Test Dependencies

Make sure all dependencies are installed:
```bash
cd backend
pip install -r requirements.txt
```

The test dependencies included are:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- SQLite - In-memory test database

#### 2. Run All Tests

Run all tests:
```bash
cd backend
python3 -m pytest app/testing/ -v
```

Run specific test file:
```bash
python3 -m pytest app/testing/auth_api_testing.py -v
python3 -m pytest app/testing/user_api_testing.py -v
```

Run a specific test:
```bash
python3 -m pytest app/testing/auth_api_testing.py::TestAuthAPI::test_login_with_valid_credentials_returns_200_and_token -v
```

#### 3. Test Output

Successful test output:
```
============================= test session starts ==============================
collected 17 items

app/testing/auth_api_testing.py::TestAuthAPI::test_login_with_valid_credentials_returns_200_and_token PASSED [ 5%]
app/testing/auth_api_testing.py::TestAuthAPI::test_login_with_invalid_password_returns_401 PASSED [ 11%]
...
app/testing/user_api_testing.py::TestUsersAPI::test_get_all_users PASSED [100%]

======================= 17 passed in 5.53s =========================
```

### Test Coverage

#### Authentication Tests (`auth_api_testing.py`)

1. **Login Tests**:
   - `test_login_with_valid_credentials_returns_200_and_token` - Successful login
   - `test_login_with_invalid_username_returns_401` - Non-existent username
   - `test_login_with_invalid_password_returns_401` - Wrong password

2. **Logout Tests**:
   - `test_logout_returns_200` - Logout endpoint

3. **Protected Endpoint Tests**:
   - `test_protected_endpoint_without_token_returns_401` - No token provided
   - `test_protected_endpoint_with_valid_token_returns_200` - Valid token
   - `test_protected_endpoint_with_invalid_token_returns_401` - Malformed token

4. **User Context Tests**:
   - `test_get_current_user_returns_authenticated_user` - JWT-based current user
   - `test_create_user_requires_authentication` - User creation requires auth
   - `test_create_user_with_valid_token_succeeds` - Authenticated user creation

#### User Endpoint Tests (`user_api_testing.py`)

1. **User Creation Tests**:
   - `test_create_user_returns_201` - Successful user creation with auth
   - `test_create_user_without_auth_returns_401` - User creation requires auth

2. **User Retrieval Tests**:
   - `test_get_user_by_id` - Get user by ID with auth
   - `test_get_current_user_returns_authenticated_user` - Get current user from JWT
   - `test_get_current_user_without_token_returns_401` - Current user requires auth
   - `test_get_all_users` - List all users with auth
   - `test_get_all_users_without_auth_returns_401` - List users requires auth

### Test Database

Tests use an **in-memory SQLite database** that is:
- Created fresh for each test
- Isolated from your development/production MySQL database
- Automatically cleaned up after tests complete
- Fast (no disk I/O)

Each test follows this pattern:
1. **Setup**: Create tables, create test admin user, login to get JWT token
2. **Execute**: Run the test with authentication
3. **Teardown**: Drop tables, close database connection

### Writing New Tests

Example test structure:
```python
def test_my_new_feature(self):
    """Test description."""
    # Use the pre-authenticated token
    res = self.client.post(
        "/some/endpoint",
        headers=self.get_auth_headers(),
        json={"data": "value"}
    )

    # Assert response
    self.assertEqual(res.status_code, 200)
    self.assertIn("expected_key", res.json())
```

### Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipelines (GitHub Actions, etc.)
- Before deploying to production

### Test Helpers

Both test classes include helpful utilities:

**Authentication Helpers**:
- `setup_auth_user()` - Creates test admin user and gets JWT token
- `get_auth_headers()` - Returns `Authorization: Bearer <token>` headers
- `create_user_direct(username, password, name)` - Create user bypassing API

**Available in Tests**:
- `self.client` - FastAPI TestClient for making requests
- `self.auth_token` - JWT token for authenticated requests
- `self.db` - Database session for direct database operations

## Database Access

### Connect to MySQL Container

```bash
docker exec -it outsource_mysql mysql -u user -ppassword outsource_db
```

### View Users Table

```sql
SELECT * FROM users;
```

### Exit MySQL

```sql
exit;
```

### Connect Using Database GUI Tools (DBeaver, MySQL Workbench, etc.)

You can use GUI database tools to visually explore and manage your MySQL database.

#### DBeaver Setup

1. **Download and Install DBeaver**
   - Download from: https://dbeaver.io/download/
   - Install the Community Edition (free)

2. **Create a New Connection**
   - Open DBeaver
   - Click "New Database Connection" (or Database → New Database Connection)
   - Select "MySQL" from the list
   - Click "Next"

3. **Configure Connection Settings**
   - **Server Host**: `localhost`
   - **Port**: `3306`
   - **Database**: `outsource_db`
   - **Username**: `user`
   - **Password**: `password`
   - **Authentication**: Database Native

4. **Test and Connect**
   - Click "Test Connection" to verify settings
   - If prompted to download MySQL drivers, click "Download"
   - Click "Finish" to save the connection
   - Double-click the connection to connect

5. **Browse the Database**
   - Expand the `outsource_db` database in the left sidebar
   - Navigate to Tables → users
   - Right-click on `users` table and select "View Data" to see all records

#### MySQL Workbench Setup

1. **Download and Install MySQL Workbench**
   - Download from: https://dev.mysql.com/downloads/workbench/

2. **Create Connection**
   - Open MySQL Workbench
   - Click the "+" icon next to "MySQL Connections"
   - Configure:
     - **Connection Name**: OutSource Local
     - **Hostname**: `127.0.0.1`
     - **Port**: `3306`
     - **Username**: `user`
     - **Password**: Click "Store in Keychain" and enter `password`
   - Click "Test Connection"
   - Click "OK"

3. **Connect and Browse**
   - Click on the connection to open it
   - In the left sidebar, expand "Schemas"
   - Select `outsource_db`
   - Browse tables and data

#### TablePlus Setup

1. **Download TablePlus**
   - Download from: https://tableplus.com/

2. **Create Connection**
   - Click "Create a new connection"
   - Select "MySQL"
   - Configure:
     - **Name**: OutSource
     - **Host**: `localhost`
     - **Port**: `3306`
     - **User**: `user`
     - **Password**: `password`
     - **Database**: `outsource_db`
   - Click "Test" then "Connect"

#### Connection Parameters Summary

Use these credentials for any MySQL client (values from your `.env` file):

| Parameter | Value | .env Variable |
|-----------|-------|---------------|
| Host | `localhost` or `127.0.0.1` | N/A |
| Port | `3306` (default) | `MYSQL_PORT` |
| Database | `outsource_db` (default) | `MYSQL_DATABASE` |
| Username | Value from .env | `MYSQL_USER` |
| Password | Value from .env | `MYSQL_PASSWORD` |
| Root Username | `root` | N/A |
| Root Password | Value from .env | `MYSQL_ROOT_PASSWORD` |

**Note**: The actual values depend on your `.env` file configuration. The default development setup uses:
- Username: `user`
- Password: `password`
- Root Password: `rootpassword`

#### Common GUI Operations

**View All Users**
- Navigate to the `users` table
- Open/View data to see all records

**Run Custom Queries**
- Open a SQL console/editor
- Example queries:
  ```sql
  -- Get all users
  SELECT * FROM users;

  -- Get user by username
  SELECT * FROM users WHERE username = 'testuser';

  -- Count total users
  SELECT COUNT(*) FROM users;

  -- Get users with friends
  SELECT * FROM users WHERE JSON_LENGTH(friends) > 0;
  ```

**Export Data**
- Right-click on the `users` table
- Select "Export Data"
- Choose format (CSV, JSON, SQL, etc.)

**Import Data**
- Right-click on the `users` table
- Select "Import Data"
- Follow the wizard to import records

#### Troubleshooting GUI Connections

**Connection Refused**
- Ensure Docker containers are running: `docker-compose ps`
- Verify MySQL is listening on port 3306: `docker port outsource_mysql`

**Authentication Failed**
- Double-check username and password
- Try connecting with root user: username `root`, password `rootpassword`

**Can't Download Drivers (DBeaver)**
- Download drivers manually from MySQL website
- Add driver JAR file in DBeaver's Driver Manager

**Port Already in Use**
- Check if another MySQL instance is running on port 3306
- Change the port mapping in docker-compose.yml if needed

## Troubleshooting

### Container Logs

View application logs:
```bash
docker-compose logs app
```

View database logs:
```bash
docker-compose logs db
```

### Restart Containers

```bash
docker-compose restart
```

### Rebuild After Code Changes

```bash
docker-compose up -d --build
```

### Check Container Status

```bash
docker-compose ps
```

### Remove Everything and Start Fresh

```bash
docker-compose down -v
docker-compose up -d --build
```

## Environment Variables

All environment variables are configured in the `.env` file (which is git-ignored for security).

### Available Variables

#### MySQL Container
- `MYSQL_ROOT_PASSWORD`: Root user password (change for production!)
- `MYSQL_DATABASE`: Database name (default: outsource_db)
- `MYSQL_USER`: Application database user
- `MYSQL_PASSWORD`: Application user password (change for production!)

#### Python App Container
- `DATABASE_URL`: SQLAlchemy connection string (must match MySQL credentials)
- `API_PORT`: Port for the FastAPI application (default: 8000)
- `MYSQL_PORT`: Port for MySQL database (default: 3306)

#### JWT Authentication
- `JWT_SECRET_KEY`: Secret key for signing JWT tokens (generate with `openssl rand -hex 32`)
- `JWT_ALGORITHM`: Algorithm for JWT signing (default: HS256)
- `JWT_ACCESS_TOKEN_EXPIRE_HOURS`: Token expiration time in hours (default: 24)

**IMPORTANT**:
- Generate a strong, unique JWT secret key for each environment
- Never use the same secret key across development, staging, and production
- Never commit your actual JWT secret key to version control
- Rotate JWT secret keys periodically for enhanced security

### Configuration Files

- `.env` - Your actual environment variables (git-ignored, created from .env.example)
- `.env.example` - Template file with placeholder values (committed to git)
- When setting up a new environment, copy `.env.example` to `.env` and update the values

## Development

For local development with hot-reload, the app directory is mounted as a volume. Changes to Python files will automatically restart the server.

## Security Notes

### General Security

- The default credentials in this setup are for development only
- Change all passwords and secrets before deploying to production
- Use environment variables or secrets management for production deployments
- Password hashing is implemented using bcrypt for user passwords
- Never commit `.env` files or secrets to version control

### JWT Security Best Practices

1. **Secret Key Management**:
   - Generate strong secret keys: `openssl rand -hex 32`
   - Use different keys for dev/staging/production
   - Store keys in secure secret managers (AWS Secrets Manager, HashiCorp Vault, etc.)
   - Rotate keys periodically (implement key versioning)

2. **Token Handling**:
   - Tokens expire after 24 hours (configurable)
   - Stateless design - no server-side session storage
   - Tokens only contain user ID and expiration
   - Client must include `Authorization: Bearer <token>` header

3. **SSL/TLS**:
   - Use HTTPS in production (JWT tokens should never be sent over HTTP)
   - Configure proper SSL certificates
   - Enable HSTS (HTTP Strict Transport Security)

4. **Additional Recommendations**:
   - Implement rate limiting on `/login` endpoint to prevent brute force attacks
   - Log failed authentication attempts
   - Consider implementing refresh tokens for longer sessions
   - Implement CORS properly (don't use wildcard `*` in production)
   - Validate and sanitize all user inputs
   - Keep dependencies updated (check for security vulnerabilities)

### What's Protected

- **All `/users/*` endpoints** require JWT authentication
- `/login`, `/logout`, `/health`, and `/` are unprotected
- Invalid or expired tokens return 401 Unauthorized
- Missing tokens return 401 Unauthorized

### Authentication Flow Security

1. User submits credentials to `/login`
2. Server verifies password with bcrypt
3. Server generates JWT with user ID
4. Client stores token (localStorage, sessionStorage, or memory)
5. Client includes token in `Authorization` header for all requests
6. Server validates token and extracts user ID
7. Server fetches user from database on each request

This ensures:
- Passwords are never sent except during login
- Tokens can be validated without database lookup
- User data is always fresh (queried on each request)
- No server-side session state needed
