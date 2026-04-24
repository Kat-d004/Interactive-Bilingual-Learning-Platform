<?php
ob_start();
require_once __DIR__ . '/../config/db.php';
setJsonHeader();

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit;
}

startSecureSession();

if (!isLoggedIn()) {
    http_response_code(401);
    echo json_encode(['authenticated' => false, 'redirect' => 'login.html']); exit;
}

$parent_id = getCurrentParentId();

try {
    $db = getDBConnection();

    $stmt = $db->prepare('SELECT parent_id, email, full_name FROM parents WHERE parent_id = ?');
    $stmt->execute([$parent_id]);
    $parent = $stmt->fetch();

    if (!$parent) {
        session_destroy();
        http_response_code(401);
        echo json_encode(['authenticated' => false, 'redirect' => 'login.html']); exit;
    }

    $stmt = $db->prepare('SELECT child_id, name, avatar_emoji FROM children WHERE parent_id = ? AND is_active = TRUE');
    $stmt->execute([$parent_id]);
    $children = $stmt->fetchAll();

    echo json_encode([
        'authenticated' => true,
        'parent_id'     => $parent['parent_id'],
        'parent_name'   => $parent['full_name'],
        'email'         => $parent['email'],
        'children'      => $children
    ]);

} catch (PDOException $e) {
    error_log("Auth check error: " . $e->getMessage());
    http_response_code(500); echo json_encode(['error' => 'Database error']);
}
?>
