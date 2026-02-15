-- Insert sample users
INSERT INTO users (username, password, name, preferences) VALUES
('sunny_dev', 'password1', 'Sunny Singh', '["hiking", "outdoor activities", "sunny weather"]'),
('weather_wiz', 'password2', 'Wendy Wizard', '["cycling", "photography", "clear skies"]'),
('cloud_runner', 'password3', 'Chris Cloud', '["running", "nature walks", "morning activities"]');

-- Insert sample circles (Sunny owns circle 1, Wendy owns circle 2)
INSERT INTO circles (name, public, owner) VALUES
('Saturday Hikers', TRUE, 1),  -- Sunny's public circle
('Photography Club', FALSE, 2); -- Wendy's private circle

-- Insert sample events
INSERT INTO events (name, description, start_at, end_at, state) VALUES
('Morning Hike', 'Early morning hike at the local trail', '2026-02-20 07:00:00', '2026-02-20 10:00:00', 'upcoming'),
('Photography Meetup', 'Photography session at the park', '2026-02-22 14:00:00', '2026-02-22 17:00:00', 'upcoming'),
('Weekend Run', 'Group run through the city', '2026-02-15 08:00:00', '2026-02-15 09:30:00', 'passed');

-- Add circle memberships
INSERT INTO circle_membership (user_id, circle_id) VALUES
(1, 1), -- Sunny in their own circle
(2, 1), -- Wendy in Sunny's circle
(2, 2), -- Wendy in their own circle
(3, 1); -- Chris in Sunny's circle

-- Add event ownership
INSERT INTO event_ownership (user_id, event_id) VALUES
(1, 1), -- Sunny owns Morning Hike
(2, 2), -- Wendy owns Photography Meetup
(3, 3), -- Chris owns Weekend Run
(1, 3); -- Sunny co-owns Weekend Run

-- Insert friend requests
INSERT INTO friend_requests (outgoing_user_id, incoming_user_id, status) VALUES
(1, 2, 'pending'), -- Sunny to Wendy
(3, 1, 'pending'); -- Chris to Sunny

-- test accept friend request
-- -- Start a transaction to accept a friend request
-- START TRANSACTION;

-- 1. Update the request status
-- UPDATE friend_requests
-- SET status = 'accepted'
-- WHERE id = 1;

-- -- 2. Insert into the friends table (Sunny and Wendy are now friends)
-- INSERT INTO friends (user1_id, user2_id)
-- VALUES (1, 2);

-- Commit the changes to the database
-- COMMIT;

-- Sample queries to verify the data (commented out)
-- SELECT * FROM users;
-- SELECT * FROM circles;
-- SELECT * FROM events;
-- SELECT * FROM friends;
-- SELECT * FROM circle_membership;
-- SELECT * FROM friend_requests;
-- SELECT * FROM event_ownership;
