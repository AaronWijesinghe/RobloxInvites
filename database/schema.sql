CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT NOT NULL,
    display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS presences (
    user_id BIGINT PRIMARY KEY,
    game_instance_id TEXT NOT NULL,
    place_id BIGINT NOT NULL,
    user_status INT NOT NULL
);

CREATE TABLE IF NOT EXISTS old_presences (
    user_id BIGINT PRIMARY KEY,
    game_instance_id TEXT NOT NULL,
    place_id BIGINT NOT NULL,
    user_status INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transfers (
    user_id BIGINT PRIMARY KEY,
    old_game_instance_id TEXT NOT NULL,
    old_place_id BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS place_id_cache (
    place_id BIGINT PRIMARY KEY,
    universe_id BIGINT DEFAULT 0,
    max_players INT DEFAULT 2
);

CREATE TABLE IF NOT EXISTS universe_id_cache (
    universe_id BIGINT PRIMARY KEY,
    root_place_id BIGINT DEFAULT 0,
    game_name TEXT DEFAULT 0,
    month_last_updated INT DEFAULT 1,
    day_last_updated INT DEFAULT 1,
    year_last_updated INT DEFAULT 1970
);

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY,
    announcement_channel BIGINT DEFAULT 0,
    invite_channel BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS subscriptions (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS custom_titles (
    guild_id BIGINT NOT NULL,
    universe_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    color TEXT NOT NULL,
    game_name TEXT NOT NULL,
    root_place_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id, universe_id)
);

CREATE TABLE IF NOT EXISTS blacklist (
    guild_id BIGINT NOT NULL,
    place_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id, place_id)
);