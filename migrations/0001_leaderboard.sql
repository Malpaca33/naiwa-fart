CREATE TABLE IF NOT EXISTS leaderboard_runs (
  token TEXT PRIMARY KEY,
  started_at INTEGER NOT NULL,
  submitted_at INTEGER
);

CREATE TABLE IF NOT EXISTS leaderboard_scores (
  player_id TEXT PRIMARY KEY,
  score INTEGER NOT NULL CHECK (score >= 0),
  achieved_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS leaderboard_scores_rank
  ON leaderboard_scores (score DESC, achieved_at ASC);
