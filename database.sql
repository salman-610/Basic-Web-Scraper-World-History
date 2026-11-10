CREATE DATABASE IF NOT EXISTS world_history_db;

USE world_history_db;

CREATE TABLE IF NOT EXISTS historical_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_title VARCHAR(500) NOT NULL,
    event_date VARCHAR(50) DEFAULT NULL,
    event_year INT DEFAULT NULL,
    category VARCHAR(100) DEFAULT NULL,
    description TEXT DEFAULT NULL,
    source_url VARCHAR(1000) DEFAULT NULL,
    source_name VARCHAR(255) DEFAULT NULL,
    scraped_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    review_reason TEXT DEFAULT NULL,

    UNIQUE KEY unique_event (event_title(250), event_year),
    INDEX idx_event_year (event_year),
    INDEX idx_event_category (category),
    INDEX idx_event_date (event_date)
);
