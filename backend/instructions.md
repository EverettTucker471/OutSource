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

## API Endpoints

### User Endpoints

#### Create User
```bash
POST /users
Content-Type: application/json

{
  "username": "johndoe",
  "password": "securepassword123",
  "name": "John Doe",
  "friends": [1, 2, 3],
  "groups": [10, 20]
}
```

#### Get Current User
```bash
GET /users/current
X-User-Id: 1
```

#### Get User by ID
```bash
GET /users/{user_id}
```

## Testing the API

### Using curl

1. Create a user:
   ```bash
   curl -X POST http://localhost:8000/users \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "password": "testpass123",
       "name": "Test User",
       "friends": [],
       "groups": []
     }'
   ```

2. Get user by ID:
   ```bash
   curl http://localhost:8000/users/1
   ```

3. Get current user (requires X-User-Id header):
   ```bash
   curl http://localhost:8000/users/current \
     -H "X-User-Id: 1"
   ```

### Using the Swagger UI

1. Open http://localhost:8000/docs in your browser
2. Expand the endpoint you want to test
3. Click "Try it out"
4. Fill in the required parameters
5. Click "Execute"

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

### Configuration Files

- `.env` - Your actual environment variables (git-ignored, created from .env.example)
- `.env.example` - Template file with placeholder values (committed to git)
- When setting up a new environment, copy `.env.example` to `.env` and update the values

## Development

For local development with hot-reload, the app directory is mounted as a volume. Changes to Python files will automatically restart the server.

## Security Notes

- The default credentials in this setup are for development only
- Change all passwords and secrets before deploying to production
- Use environment variables or secrets management for production deployments
- Password hashing is implemented using bcrypt for user passwords
