<?php
ob_start();
require_once __DIR__ . '/../config/db.php';
setJsonHeader();

startSecureSession();
$parent_id = getCurrentParentId();
if (!$parent_id) { http_response_code(401); echo json_encode(['error' => 'Unauthorized']); exit; }

try {
    $db = getDBConnection();

    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        $child_id = $_GET['child_id'] ?? null;
        if (!$child_id) { http_response_code(400); echo json_encode(['error' => 'child_id required']); exit; }
        if (!verifyChildOwnership($db, $child_id, $parent_id)) { http_response_code(403); echo json_encode(['error' => 'Access denied']); exit; }

        $stmt = $db->prepare('SELECT * FROM quiz_scores WHERE child_id = ? ORDER BY completed_at DESC LIMIT 100');
        $stmt->execute([$child_id]);
        echo json_encode(['success' => true, 'scores' => $stmt->fetchAll()]);

    } elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $data = json_decode(file_get_contents('php://input'), true);
        if (empty($data['child_id']) || empty($data['quiz_category']) || $data['score'] === null) {
            http_response_code(400); echo json_encode(['error' => 'Missing required fields']); exit;
        }
        if (!verifyChildOwnership($db, $data['child_id'], $parent_id)) { http_response_code(403); echo json_encode(['error' => 'Access denied']); exit; }

        $total      = $data['total_questions'] ?? 10;
        $score      = $data['score'] ?? 0;
        $percentage = round(($score / $total) * 100, 2);

        $stmt = $db->prepare('INSERT INTO quiz_scores (child_id, quiz_category, score, total_questions, percentage) VALUES (?, ?, ?, ?, ?)');
        $stmt->execute([$data['child_id'], $data['quiz_category'], $score, $total, $percentage]);

        if ($percentage >= 70) {
            $stars = ceil($percentage / 20);
            $db->prepare('UPDATE student_progress SET total_stars = total_stars + ? WHERE child_id = ?')->execute([$stars, $data['child_id']]);
        }

        echo json_encode(['success' => true, 'message' => 'Score recorded', 'percentage' => $percentage]);
    }

} catch (PDOException $e) {
    error_log("Quiz error: " . $e->getMessage());
    http_response_code(500); echo json_encode(['error' => 'Database error']);
}
?>
