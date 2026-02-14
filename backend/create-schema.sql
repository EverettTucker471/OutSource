-- 1. Users Table
CREATE TABLE users (
    userId INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    accessToken VARCHAR(255),
    name VARCHAR(100) NOT NULL
);

-- 2. Events Table
CREATE TABLE events (
    eventId INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    time TIME NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT -- 'desc' is a reserved keyword in SQL, using 'description'
);

-- 3. circles Table
CREATE TABLE circles (
    circleId INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- 4. Friends Table (Junction with Unique Pair)
CREATE TABLE friends (
    friendshipId INT AUTO_INCREMENT PRIMARY KEY,
    user1_id INT NOT NULL,
    user2_id INT NOT NULL,
    FOREIGN KEY (user1_id) REFERENCES users(userId),
    FOREIGN KEY (user2_id) REFERENCES users(userId),
    -- This ensures that a pair (User A, User B) can only exist once
    CONSTRAINT unique_friendship UNIQUE (user1_id, user2_id)
);

-- 5. circle Membership Table (Junction with Unique User/circle)
CREATE TABLE circleMembership (
    membershipId INT AUTO_INCREMENT PRIMARY KEY,
    userId INT NOT NULL,
    circleId INT NOT NULL,
    FOREIGN KEY (userId) REFERENCES users(userId),
    FOREIGN KEY (circleId) REFERENCES circles(circleId),
    -- This ensures a user can only be added to a specific circle once
    CONSTRAINT unique_circle_member UNIQUE (userId, circleId)
);

-- 6. Friend Requests Table
CREATE TABLE friendRequests (
    requestId INT AUTO_INCREMENT PRIMARY KEY,
    outgoingUsr_id INT NOT NULL,
    incomingUsr_id INT NOT NULL,
    status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',
    FOREIGN KEY (outgoingUsr_id) REFERENCES users(userId),
    FOREIGN KEY (incomingUsr_id) REFERENCES users(userId),
    -- Prevents sending the same request twice
    CONSTRAINT unique_request UNIQUE (outgoingUsr_id, incomingUsr_id)
);
