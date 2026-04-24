<?php
/**
 * Database Configuration and Helper Functions
 * IBLP - Interactive Bilingual Learning Project
 */

// ── Database credentials ────────────────────────────────────────────────────
define('DB_HOST', 'localhost');
define('DB_USER', 'root');           
define('DB_PASS', 'foodman');               
define('DB_NAME', 'iblp_database');
define('DB_PORT', 3306);
define('DB_TYPE', 'mysql');

// ── Get a PDO connection, auto-creating tables if needed ────────────────────
function getDBConnection() {
    if (!ob_get_level()) ob_start();
 
    try {
        $pdo = new PDO(
            'mysql:host=' . DB_HOST . ';port=' . DB_PORT . ';charset=utf8mb4',
            DB_USER,
            DB_PASS,
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
        );
        $pdo->exec(
            "CREATE DATABASE IF NOT EXISTS `" . DB_NAME . "`
             CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        );
        $pdo->exec("USE `" . DB_NAME . "`");
        $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        ensureSchema($pdo);
        return $pdo;
 
    } catch (PDOException $e) {
        ob_end_clean();
        error_log("Database connection error: " . $e->getMessage());
        $host = $_SERVER['HTTP_HOST'] ?? 'localhost';
        header('Content-Type: application/json; charset=utf-8');
        header('Access-Control-Allow-Origin: http://' . $host);
        header('Access-Control-Allow-Credentials: true');
        http_response_code(500);
        echo json_encode([
            'error'  => 'Database connection failed',
            'detail' => 'Could not connect to MySQL on ' . DB_HOST . ':' . DB_PORT . '. Make sure MySQL is running.',
            'hint'   => $e->getMessage()
        ]);
        exit;
    }
}
 
// ── Auto-create all tables if they don't exist ──────────────────────────────
function ensureSchema(PDO $db) {
    $db->exec("
        CREATE TABLE IF NOT EXISTS parents (
            parent_id     INT          PRIMARY KEY AUTO_INCREMENT,
            email         VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name     VARCHAR(255) NOT NULL,
            phone         VARCHAR(20),
            created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
            updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_active     BOOLEAN      DEFAULT TRUE,
            INDEX idx_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ");
    $db->exec("
        CREATE TABLE IF NOT EXISTS children (
            child_id      INT          PRIMARY KEY AUTO_INCREMENT,
            parent_id     INT          NOT NULL,
            name          VARCHAR(255) NOT NULL,
            age           INT,
            profile_color VARCHAR(20),
            avatar_emoji  VARCHAR(10),
            created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
            updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_active     BOOLEAN      DEFAULT TRUE,
            FOREIGN KEY (parent_id) REFERENCES parents(parent_id) ON DELETE CASCADE,
            INDEX idx_parent_id (parent_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ");
    $db->exec("
        CREATE TABLE IF NOT EXISTS student_progress (
            progress_id       INT     PRIMARY KEY AUTO_INCREMENT,
            child_id          INT     NOT NULL,
            total_stars       INT     DEFAULT 0,
            colors_completed  BOOLEAN DEFAULT FALSE,
            colors_attempts   INT     DEFAULT 0,
            numbers_completed BOOLEAN DEFAULT FALSE,
            numbers_attempts  INT     DEFAULT 0,
            animals_completed BOOLEAN DEFAULT FALSE,
            animals_attempts  INT     DEFAULT 0,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE,
            UNIQUE KEY unique_child (child_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ");
    $db->exec("
        CREATE TABLE IF NOT EXISTS quiz_scores (
            score_id        INT          PRIMARY KEY AUTO_INCREMENT,
            child_id        INT          NOT NULL,
            quiz_category   VARCHAR(50)  NOT NULL,
            score           INT          NOT NULL,
            total_questions INT          NOT NULL,
            percentage      DECIMAL(5,2),
            completed_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE,
            INDEX idx_child_id  (child_id),
            INDEX idx_category  (quiz_category)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ");
    $db->exec("
        CREATE TABLE IF NOT EXISTS user_preferences (
            preference_id         INT         PRIMARY KEY AUTO_INCREMENT,
            child_id              INT         NOT NULL,
            language              VARCHAR(10) DEFAULT 'en',
            theme                 VARCHAR(50) DEFAULT 'light',
            sound_enabled         BOOLEAN     DEFAULT TRUE,
            notifications_enabled BOOLEAN     DEFAULT TRUE,
            created_at            TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
            updated_at            TIMESTAMP   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE,
            UNIQUE KEY unique_child (child_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ");
    $db->exec("
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INT          PRIMARY KEY AUTO_INCREMENT,
            parent_id  INT          NOT NULL,
            token      VARCHAR(255) UNIQUE NOT NULL,
            ip_address VARCHAR(45),
            user_agent VARCHAR(255),
            created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP    NULL DEFAULT NULL,
            FOREIGN KEY (parent_id) REFERENCES parents(parent_id) ON DELETE CASCADE,
            INDEX idx_token     (token),
            INDEX idx_parent_id (parent_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ");
    $db->exec("
        CREATE TABLE IF NOT EXISTS activity_log (
            log_id        INT          PRIMARY KEY AUTO_INCREMENT,
            child_id      INT          NOT NULL,
            activity_type VARCHAR(100) NOT NULL,
            module        VARCHAR(50),
            details       JSON,
            created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE,
            INDEX idx_child_id   (child_id),
            INDEX idx_activity   (activity_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ");
}
 
// ── Password helpers ─────────────────────────────────────────────────────────
function hashPassword($password) {
    return password_hash($password, PASSWORD_BCRYPT, ['cost' => 11]);
}
function verifyPassword($password, $hash) {
    return password_verify($password, $hash);
}
 
// ── Token generation ─────────────────────────────────────────────────────────
function generateToken() {
    return bin2hex(random_bytes(32));
}
 
// ── Secure session start ─────────────────────────────────────────────────────
function startSecureSession() {
    if (session_status() === PHP_SESSION_NONE) {
        $host        = $_SERVER['HTTP_HOST'] ?? 'localhost';
        $isLocalhost = in_array($host, ['localhost', '127.0.0.1'], true)
                       || strpos($host, 'localhost:') === 0;
        $isHttps     = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
 
        session_set_cookie_params([
            'lifetime' => 86400 * 30,
            'path'     => '/',
            'domain'   => $isLocalhost ? '' : $host,
            'secure'   => $isHttps,
            'httponly' => true,
            'samesite' => 'Lax',
        ]);
        session_start();
    }
}
 
// ── Auth helpers ─────────────────────────────────────────────────────────────
function isLoggedIn() {
    startSecureSession();
    return isset($_SESSION['parent_id']) && !empty($_SESSION['parent_id']);
}
 
function getCurrentParentId() {
    startSecureSession();
    return $_SESSION['parent_id'] ?? null;
}
 
// ── CORS + JSON headers ───────────────────────────────────────────────────────
function setJsonHeader() {
    if (ob_get_level()) ob_clean();
    header('Content-Type: application/json; charset=utf-8');
 
    $host   = $_SERVER['HTTP_HOST'] ?? 'localhost';
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
 
    $allowedOrigins = [
        'http://'  . $host, 'https://' . $host,
        'http://localhost', 'https://localhost',
        'http://127.0.0.1', 'https://127.0.0.1',
    ];
 
    if (!empty($origin) && in_array($origin, $allowedOrigins, true)) {
        header('Access-Control-Allow-Origin: ' . $origin);
    } else {
        header('Access-Control-Allow-Origin: http://' . $host);
    }
    header('Access-Control-Allow-Credentials: true');
    header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Authorization');
}
 
// ── Child ownership verification ─────────────────────────────────────────────
function verifyChildOwnership(PDO $db, $child_id, $parent_id) {
    $stmt = $db->prepare(
        'SELECT child_id FROM children WHERE child_id = ? AND parent_id = ? AND is_active = TRUE'
    );
    $stmt->execute([$child_id, $parent_id]);
    return $stmt->fetch() !== false;
}
 
// ── Email validation ──────────────────────────────────────────────────────────
function validateEmail($email) {
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        return ['valid' => false, 'message' => 'Invalid email format.'];
    }
    $domain  = strtolower(substr(strrchr($email, '@'), 1));
    $blocked = [
        'mailinator.com','guerrillamail.com','trashmail.com','yopmail.com',
        'tempmail.com','temp-mail.org','throwaway.email','maildrop.cc',
    ];
    if (in_array($domain, $blocked, true)) {
        return ['valid' => false, 'message' => 'Disposable email addresses are not allowed.'];
    }
    return ['valid' => true, 'message' => ''];
}
 
// ── CORS preflight ────────────────────────────────────────────────────────────
if (isset($_SERVER['REQUEST_METHOD']) && $_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    setJsonHeader();
    http_response_code(200);
    exit;
}
 

