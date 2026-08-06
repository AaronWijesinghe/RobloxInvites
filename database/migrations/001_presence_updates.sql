ALTER TABLE presences
ADD IF NOT EXISTS last_location TEXT,
ADD IF NOT EXISTS root_place_id BIGINT DEFAULT 0;

ALTER TABLE old_presences
ADD IF NOT EXISTS last_location TEXT,
ADD IF NOT EXISTS root_place_id BIGINT DEFAULT 0;