ALTER TABLE users
ADD frozen INT DEFAULT 0;

ALTER TABLE subscriptions
ADD freeze_invites INT DEFAULT 0;