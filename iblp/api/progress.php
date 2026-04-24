<?php
ob_start();
require_once __DIR__ . '/../config/db.php';
setJsonHeader();

startSecureSession();
$parent_id = getCurrentParentId();
if (!$parent_id) { http_response_code(401); echo json_encode(['error' => 'Unauthorized']); exit; }

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $postData = json_decode(file_get_contents('php://input'), true) ?? [];
    $child_id = $postData['child_id'] ?? $_GET['child_id'] ?? null;
} else {
    $child_id = $_GET['child_id'] ?? null;
    $postData = [];
}

if (!$child_id) { http_response_code(400); echo json_encode(['error' => 'child_id required']); exit; }

try {
    error_log("Progress.php: Starting operation for child_id: $child_id");
    $db = getDBConnection();
    if (!verifyChildOwnership($db, $child_id, $parent_id)) {
        http_response_code(403); echo json_encode(['error' => 'Access denied']); exit;
    }

    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        $stmt = $db->prepare('SELECT * FROM student_progress WHERE child_id = ?');
        $stmt->execute([$child_id]);
        $progress = $stmt->fetch();

        if (!$progress) {
            $db->prepare('INSERT INTO student_progress (child_id, total_stars) VALUES (?, 0)')->execute([$child_id]);
            $stmt->execute([$child_id]);
            $progress = $stmt->fetch();
        }

        $stmt = $db->prepare('SELECT quiz_category, score, total_questions, percentage, completed_at FROM quiz_scores WHERE child_id = ? ORDER BY completed_at DESC LIMIT 50');
        $stmt->execute([$child_id]);
        $scores = $stmt->fetchAll();

        echo json_encode(['success' => true, 'progress' => $progress, 'quiz_scores' => $scores]);

    } elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $data = $postData;

        // Helper closures: only bind a value when the key was actually present
        // in the payload.  JS false -> JSON false -> PHP (bool)false which is
        // NOT null, so COALESCE(false, col) would try to store '' in a tinyint
        // column and crash.  We convert booleans to 0/1 and absent keys to null.
        $maybeInt  = fn($key) => array_key_exists($key, $data) ? (int)$data[$key]      : null;
        $maybeBool = fn($key) => array_key_exists($key, $data) ? ($data[$key] ? 1 : 0) : null;

        $stmt = $db->prepare('
            UPDATE student_progress SET
                total_stars       = COALESCE(?, total_stars),
                colors_completed  = COALESCE(?, colors_completed),
                colors_attempts   = COALESCE(?, colors_attempts),
                numbers_completed = COALESCE(?, numbers_completed),
                numbers_attempts  = COALESCE(?, numbers_attempts),
                animals_completed = COALESCE(?, animals_completed),
                animals_attempts  = COALESCE(?, animals_attempts),
                updated_at        = NOW()
            WHERE child_id = ?
        ');
        $stmt->execute([
            $maybeInt ('total_stars'),
            $maybeBool('colors_completed'),
            $maybeInt ('colors_attempts'),
            $maybeBool('numbers_completed'),
            $maybeInt ('numbers_attempts'),
            $maybeBool('animals_completed'),
            $maybeInt ('animals_attempts'),
            $child_id
        ]);
        echo json_encode(['success' => true, 'message' => 'Progress updated']);
    }

} catch (PDOException $e) {
    error_log("Progress error: " . $e->getMessage());
    error_log("Stack trace: " . $e->getTraceAsString());
    http_response_code(500);
    echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
}
?>
