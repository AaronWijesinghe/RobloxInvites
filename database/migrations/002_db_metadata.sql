CREATE TABLE IF NOT EXISTS metadata (
    id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    current_version TEXT DEFAULT '0.0.0'
);