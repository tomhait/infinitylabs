CREATE DATABASE hearts_game;
USE hearts_game;

# 1. Reference table for cards
CREATE TABLE cards (
	card_id INT PRIMARY KEY AUTO_INCREMENT,
	card_shape  ENUM('Clubs', 'Diamonds', 'Spades', 'Hearts') NOT NULL,
	card_rank ENUM('2', '3', '4', '5', '6', '7', '8', '9', '10',
	'J', 'Q', 'K', 'A') NOT NULL,
	penalty_value INT DEFAULT 0
);

ALTER TABLE cards ADD CONSTRAINT unique_card UNIQUE (card_shape, card_rank);

ALTER TABLE cards ADD CONSTRAINT check_penalty CHECK (
	(card_shape = 'Spades' AND card_rank = 'Q' AND penalty_value = 13)
	OR (card_shape = 'Hearts' AND penalty_value = 1) OR 
	(card_shape NOT IN ('Hearts' OR (card_shape = 'Spades' AND card_rank = 'Q') AND penalty_value = 0))
);

# 2. Games' Information
CREATE TABLE games (
	game_id INT PRIMARY KEY AUTO_INCREMENT,
	server_id INT NOT NULL,
	status ENUM('active', 'finished', 'terminated') DEFAULT 'active'
);

# 3. Players' Information
CREATE TABLE players (
	player_id INT PRIMARY KEY AUTO_INCREMENT,
	player_name VARCHAR(50) NOT NULL,
	game_id INT NOT NULL REFERENCES games(game_id),
	score INT DEFAULT 0
);

ALTER TABLE players ADD CONSTRAINT check_score CHECK (score BETWEEN 0 AND 100);

# 4. Initial cards each player has
CREATE TABLE init_cards (
	card_id INT NOT NULL,
	player_id INT NOT NULL,
	game_id INT NOT NULL,
	card_num INT NOT NULL,
	FOREIGN KEY (card_id) REFERENCES cards(card_id),
	FOREIGN KEY (player_id) REFERENCES players(player_id),
	FOREIGN KEY (game_id) REFERENCES games(game_id),
	CONSTRAINT player_card UNIQUE(game_id, player_id, card_id)
);

ALTER TABLE init_cards ADD CONSTRAINT check_num_cards CHECK (card_num BETWEEN 1 AND 13);

# 5. round tracking - a complete cycle of playing all 52 cards
CREATE TABLE rounds (
	round_id INT PRIMARY KEY AUTO_INCREMENT,
	round_num INT NOT NULL,
	game_id INT NOT NULL,
	FOREIGN KEY (game_id) REFERENCES games(game_id)
);

ALTER TABLE rounds 
ADD CONSTRAINT unique_round_pair UNIQUE (round_id, round_num);

# 6. Trick tracking - a single turn out of 13
CREATE TABLE tricks (
	trick_id INT PRIMARY KEY AUTO_INCREMENT,
	round_id INT NOT NULL,
	trick_num INT NOT NULL,
	first_player_id INT NOT NULL,
	winner_id INT NOT NULL,
	first_shape ENUM('Clubs', 'Diamonds', 'Spades', 'Hearts'),
	FOREIGN KEY (round_id) REFERENCES rounds(round_id),
	FOREIGN KEY (first_player_id) REFERENCES players(player_id),
	FOREIGN KEY (winner_id) REFERENCES players(player_id)
);

ALTER TABLE tricks ADD CONSTRAINT check_trick_num CHECK (
	trick_num BETWEEN 1 AND 13);

# 7. Played cards in a trick
CREATE TABLE plays (
	trick_id INT,
	player_id INT NOT NULL,
	card_id INT NOT NULL,
	play_order INT NOT NULL,
	CONSTRAINT trick_play_order UNIQUE(trick_id, play_order),
	CONSTRAINT trick_player UNIQUE(trick_id, player_id),
	CONSTRAINT trick_card UNIQUE(trick_id, card_id),
	FOREIGN KEY (trick_id) REFERENCES tricks(trick_id),
	FOREIGN KEY (player_id) REFERENCES players(player_id),
	FOREIGN KEY (card_id) REFERENCES cards(card_id)
);

ALTER TABLE plays ADD CONSTRAINT check_play_order CHECK (
	play_order BETWEEN 1 AND 4);
