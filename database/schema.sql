CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    discord_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    display_name TEXT NOT NULL,
    erased INT DEFAULT 0,
    joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS presences (
    user_id BIGINT PRIMARY KEY,
    game_instance_id TEXT,
    place_id BIGINT,
    user_status INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS old_presences (
    user_id BIGINT PRIMARY KEY,
    game_instance_id TEXT,
    place_id BIGINT,
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
    game_name TEXT NOT NULL,
    PRIMARY KEY (guild_id, place_id)
);

CREATE TABLE IF NOT EXISTS currently_playing (
    user_id BIGINT PRIMARY KEY,
    place_id BIGINT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS total_playtimes (
    user_id BIGINT PRIMARY KEY,
    total_playtime BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS game_playtimes (
    user_id BIGINT NOT NULL,
    place_id BIGINT NOT NULL,
    playtime BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, place_id)
);

CREATE TABLE IF NOT EXISTS snapshot_metadata (
    snapshot_id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS total_playtime_snapshots (
    snapshot_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    total_playtime BIGINT NOT NULL,
    
    PRIMARY KEY (snapshot_id, user_id),
    FOREIGN KEY (snapshot_id)
        REFERENCES snapshot_metadata(snapshot_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS game_playtime_snapshots (
    snapshot_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    place_id BIGINT NOT NULL,
    playtime BIGINT NOT NULL,
    
    PRIMARY KEY (snapshot_id, user_id, place_id),
    FOREIGN KEY (snapshot_id)
        REFERENCES snapshot_metadata(snapshot_id)
        ON DELETE CASCADE
);