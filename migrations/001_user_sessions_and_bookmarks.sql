CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS ix_user_sessions_expires_at ON user_sessions(expires_at);

CREATE TABLE IF NOT EXISTS user_bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_type VARCHAR(20) NOT NULL,
    item_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_bookmark_item
    ON user_bookmarks(user_id, item_type, item_id);

CREATE INDEX IF NOT EXISTS ix_user_bookmarks_user_id ON user_bookmarks(user_id);
