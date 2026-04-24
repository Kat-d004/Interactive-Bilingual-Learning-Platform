-- IBLP Database Schema
-- Run this script to initialize the database

-- Parents table
CREATE TABLE IF NOT EXISTS parents (
    parent_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_email (email)
);

-- Children table
CREATE TABLE IF NOT EXISTS children (
    child_id INT PRIMARY KEY AUTO_INCREMENT,
    parent_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    age INT,
    profile_color VARCHAR(20),
    avatar_emoji VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (parent_id) REFERENCES parents(parent_id) ON DELETE CASCADE,
    INDEX idx_parent_id (parent_id)
);

-- Student progress table (replaces localStorage)
CREATE TABLE IF NOT EXISTS student_progress (
    progress_id INT PRIMARY KEY AUTO_INCREMENT,
    child_id INT NOT NULL,
    total_stars INT DEFAULT 0,
    colors_completed BOOLEAN DEFAULT FALSE,
    colors_attempts INT DEFAULT 0,
    numbers_completed BOOLEAN DEFAULT FALSE,
    numbers_attempts INT DEFAULT 0,
    animals_completed BOOLEAN DEFAULT FALSE,
    animals_attempts INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE,
    UNIQUE KEY unique_child (child_id),
    INDEX idx_child_id (child_id)
);

-- Quiz scores table
CREATE TABLE IF NOT EXISTS quiz_scores (
    score_id INT PRIMARY KEY AUTO_INCREMENT,
    child_id INT NOT NULL,
    quiz_category VARCHAR(50) NOT NULL,
    score INT NOT NULL,
    total_questions INT NOT NULL,
    percentage DECIMAL(5,2),
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE,
    INDEX idx_child_id (child_id),
    INDEX idx_category (quiz_category),
    INDEX idx_completed_at (completed_at)
);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id INT PRIMARY KEY AUTO_INCREMENT,
    child_id INT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    theme VARCHAR(50) DEFAULT 'light',
    sound_enabled BOOLEAN DEFAULT TRUE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE,
    UNIQUE KEY unique_child (child_id)
);

-- Session tokens table (for persistent login)
CREATE TABLE IF NOT EXISTS sessions (
    session_id INT PRIMARY KEY AUTO_INCREMENT,
    parent_id INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (parent_id) REFERENCES parents(parent_id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_parent_id (parent_id),
    INDEX idx_expires_at (expires_at)
);

-- Activity log table (for analytics)
CREATE TABLE IF NOT EXISTS activity_log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    child_id INT NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    module VARCHAR(50),
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE,
    INDEX idx_child_id (child_id),
    INDEX idx_activity_type (activity_type),
    INDEX idx_created_at (created_at)
);

-- Create indexes for common queries
CREATE INDEX idx_progress_updated ON student_progress(updated_at DESC);
CREATE INDEX idx_quiz_date_range ON quiz_scores(child_id, completed_at DESC);
