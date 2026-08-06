ALTER TABLE users
ADD frozen INT DEFAULT 0;

ALTER TABLE subscriptions
ADD send_invites INT DEFAULT 1;