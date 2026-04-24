<?php
ob_start();
require_once __DIR__ . '/../config/db.php';
setJsonHeader();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit;
}

$data = json_decode(file_get_contents('php://input'), true);
if (empty($data['email']) || empty($data['password'])) {
    http_response_code(400); echo json_encode(['error' => 'Email and password required']); exit;
}

try {
    $db = getDBConnection();

    $stmt = $db->prepare('SELECT parent_id, password_hash, full_name FROM parents WHERE email = ? AND is_active = TRUE');
    $stmt->execute([$data['email']]);
    $parent = $stmt->fetch();

    if (!$parent || !verifyPassword($data['password'], $parent['password_hash'])) {
        http_response_code(401); echo json_encode(['error' => 'Invalid credentials']); exit;
    }

    startSecureSession();
    $_SESSION['parent_id']   = $parent['parent_id'];
    $_SESSION['parent_name'] = $parent['full_name'];
    $_SESSION['login_time']  = time();

    $stmt = $db->prepare('SELECT child_id, name, avatar_emoji FROM children WHERE parent_id = ? AND is_active = TRUE');
    $stmt->execute([$parent['parent_id']]);
    $children = $stmt->fetchAll();

    http_response_code(200);
    echo json_encode([
        'success'     => true,
        'message'     => 'Login successful',
        'parent_id'   => $parent['parent_id'],
        'parent_name' => $parent['full_name'],
        'children'    => $children
    ]);

} catch (PDOException $e) {
    error_log("Login error: " . $e->getMessage());
    http_response_code(500); echo json_encode(['error' => 'Database error']);
}
?>
