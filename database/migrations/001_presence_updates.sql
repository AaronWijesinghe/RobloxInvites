ALTER TABLE presences
ADD last_location TEXT,
ADD root_place_id BIGINT DEFAULT 0;