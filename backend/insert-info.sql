INSERT INTO users (username, accessToken, name) VALUES 
('sunny_dev', 'token_abc_123', 'Sunny Singh'),
('weather_wiz', 'token_xyz_789', 'Wendy Wizard'),
('cloud_runner', 'token_qrs_456', 'Chris Cloud');

INSERT INTO friendRequests (outgoingUsr_id, incomingUsr_id, status) VALUES 
(1, 2, 'pending'), -- Sunny to Wendy
(3, 1, 'pending'); -- Chris to Sunny

-- Create the group
INSERT INTO circles (name) VALUES ('Saturday Hikers');

-- Add Sunny (userId: 1) and Wendy (userId: 2) to the circle (groupId: 1)
INSERT INTO circleMembership (userId, circleId) VALUES 
(1, 1),
(2, 1);

-- Start a transaction
START TRANSACTION;

-- 1. Update the request status
UPDATE friendRequests 
SET status = 'accepted' 
WHERE requestId = 1;

-- 2. Insert into the friends table 
-- (Assuming we know Sunny is 1 and Wendy is 2 from the request)
INSERT INTO friends (user1_id, user2_id) 
VALUES (1, 2);

-- Commit the changes to the database
COMMIT;

-- SELECT * FROM friends;
