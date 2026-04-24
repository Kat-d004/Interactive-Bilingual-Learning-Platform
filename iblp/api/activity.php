<?php
ob_start();
require_once __DIR__ . '/../config/db.php';
setJsonHeader();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit;
}

startSecureSession();
$parent_id = getCurrentParentId();
if (!$parent_id) { http_response_code(401); echo json_encode(['error' => 'Unauthorized']); exit; }

$data = json_decode(file_get_contents('php://input'), true);
if (empty($data['child_id']) || empty($data['activity_type'])) {
    http_response_code(400); echo json_encode(['error' => 'child_id and activity_type required']); exit;
}

try {
    $db = getDBConnection();
    if (!verifyChildOwnership($db, $data['child_id'], $parent_id)) { http_response_code(403); echo json_encode(['error' => 'Access denied']); exit; }

    $db->prepare('INSERT INTO activity_log (child_id, activity_type, module, details) VALUES (?, ?, ?, ?)')->execute([
        $data['child_id'],
        $data['activity_type'],
        $data['module'] ?? null,
        json_encode($data['details'] ?? [])
    ]);

    http_response_code(201);
    echo json_encode(['success' => true, 'message' => 'Activity logged']);

} catch (PDOException $e) {
    error_log("Activity log error: " . $e->getMessage());
    http_response_code(500); echo json_encode(['error' => 'Database error']);
}
?>
