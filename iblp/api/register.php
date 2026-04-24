<?php
ob_start();
require_once __DIR__ . '/../config/db.php';
setJsonHeader();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit;
}

$data   = json_decode(file_get_contents('php://input'), true);
$errors = [];

if (empty($data['email']))            $errors[] = 'Email required';
if (empty($data['full_name']))        $errors[] = 'Full name required';
if (empty($data['password']))         $errors[] = 'Password required';
if (empty($data['password_confirm'])) $errors[] = 'Password confirmation required';
if (empty($data['child_name']))       $errors[] = 'Child name required';

if (!empty($data['email'])) {
    $emailCheck = validateEmail($data['email']);
    if (!$emailCheck['valid']) $errors[] = $emailCheck['message'];
}
if (!empty($data['password']) && strlen($data['password']) < 8)
    $errors[] = 'Password must be at least 8 characters';
if (!empty($data['password']) && $data['password'] !== $data['password_confirm'])
    $errors[] = 'Passwords do not match';

if (!empty($errors)) {
    http_response_code(400); echo json_encode(['errors' => $errors]); exit;
}

try {
    $db = getDBConnection();

    $stmt = $db->prepare('SELECT parent_id FROM parents WHERE email = ?');
    $stmt->execute([$data['email']]);
    if ($stmt->fetch()) {
        http_response_code(400); echo json_encode(['error' => 'Email already registered']); exit;
    }

    $stmt = $db->prepare('INSERT INTO parents (email, password_hash, full_name, phone) VALUES (?, ?, ?, ?)');
    $stmt->execute([$data['email'], hashPassword($data['password']), $data['full_name'], $data['phone'] ?? null]);
    $parent_id = $db->lastInsertId();

    $stmt = $db->prepare('INSERT INTO children (parent_id, name, age, avatar_emoji) VALUES (?, ?, ?, ?)');
    $stmt->execute([$parent_id, $data['child_name'], $data['child_age'] ?? null, $data['avatar_emoji'] ?? '👧']);
    $child_id = $db->lastInsertId();

    $db->prepare('INSERT INTO student_progress (child_id, total_stars) VALUES (?, 0)')->execute([$child_id]);
    $db->prepare('INSERT INTO user_preferences (child_id, language) VALUES (?, ?)')->execute([$child_id, 'en']);
    $db->prepare('INSERT INTO activity_log (child_id, activity_type, details) VALUES (?, ?, ?)')->execute([
        $child_id, 'account_created', json_encode(['parent_email' => $data['email']])
    ]);

    startSecureSession();
    $_SESSION['parent_id']   = $parent_id;
    $_SESSION['parent_name'] = $data['full_name'];
    $_SESSION['login_time']  = time();

    http_response_code(201);
    echo json_encode([
        'success'   => true,
        'message'   => 'Registration successful',
        'parent_id' => $parent_id,
        'child_id'  => $child_id,
        'redirect'  => 'index.html?child_id=' . $child_id
    ]);

} catch (PDOException $e) {
    error_log("Registration error: " . $e->getMessage());
    http_response_code(500); echo json_encode(['error' => 'Registration failed']);
}
?>
