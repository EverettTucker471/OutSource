-- 1. Users Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    preferences JSON
);

-- 2. Events Table
CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(1000),
    start_at DATETIME NOT NULL,
    end_at DATETIME NOT NULL,
    state ENUM('upcoming', 'passed') NOT NULL DEFAULT 'upcoming'
);

-- 3. Circles Table
CREATE TABLE circles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    public BOOLEAN NOT NULL DEFAULT FALSE,
    owner INT NOT NULL,
    FOREIGN KEY (owner) REFERENCES users(id)
);

-- 4. Friends Table (Junction with Unique Pair)
CREATE TABLE friends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user1_id INT NOT NULL,
    user2_id INT NOT NULL,
    FOREIGN KEY (user1_id) REFERENCES users(id),
    FOREIGN KEY (user2_id) REFERENCES users(id),
    CONSTRAINT unique_friendship UNIQUE (user1_id, user2_id)
);

-- 5. Circle Membership Table (Junction with Unique User/Circle)
CREATE TABLE circle_membership (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    circle_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (circle_id) REFERENCES circles(id),
    CONSTRAINT unique_membership UNIQUE (user_id, circle_id)
);

-- 6. Friend Requests Table
CREATE TABLE friend_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outgoing_user_id INT NOT NULL,
    incoming_user_id INT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    FOREIGN KEY (outgoing_user_id) REFERENCES users(id),
    FOREIGN KEY (incoming_user_id) REFERENCES users(id),
    CONSTRAINT unique_friend_request UNIQUE (outgoing_user_id, incoming_user_id)
);

-- 7. Event Ownership Table (Junction with Unique User/Event)
CREATE TABLE event_ownership (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (event_id) REFERENCES events(id),
    CONSTRAINT unique_event_ownership UNIQUE (user_id, event_id)
);
