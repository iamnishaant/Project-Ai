CREATE DATABASE ghost_game;
USE ghost_game;

CREATE TABLE user_stats (
    player_name VARCHAR(50) PRIMARY KEY,
    games_played INT DEFAULT 0,
    total_score INT DEFAULT 0,
    best_score INT DEFAULT 0,
    hearts_of_dead INT DEFAULT 0
);
