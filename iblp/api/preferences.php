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
    $postData = [];
    $child_id = $_GET['child_id'] ?? null;
}

if (!$child_id) { http_response_code(400); echo json_encode(['error' => 'child_id required']); exit; }

try {
    $db = getDBConnection();
    if (!verifyChildOwnership($db, $child_id, $parent_id)) { http_response_code(403); echo json_encode(['error' => 'Access denied']); exit; }

    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        $stmt = $db->prepare('SELECT * FROM user_preferences WHERE child_id = ?');
        $stmt->execute([$child_id]);
        $prefs = $stmt->fetch();

        if (!$prefs) {
            $db->prepare('INSERT INTO user_preferences (child_id, language) VALUES (?, ?)')->execute([$child_id, 'en']);
            $stmt->execute([$child_id]);
            $prefs = $stmt->fetch();
        }
        echo json_encode(['success' => true, 'preferences' => $prefs]);

    } elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $data = $postData;
        $stmt = $db->prepare('SELECT preference_id FROM user_preferences WHERE child_id = ?');
        $stmt->execute([$child_id]);
        if (!$stmt->fetch()) {
            $db->prepare('INSERT INTO user_preferences (child_id, language) VALUES (?, ?)')->execute([$child_id, 'en']);
        }

        $fields = []; $params = [];
        if (isset($data['language']))              { $fields[] = 'language = ?';              $params[] = $data['language']; }
        if (isset($data['theme']))                 { $fields[] = 'theme = ?';                 $params[] = $data['theme']; }
        if (isset($data['sound_enabled']))         { $fields[] = 'sound_enabled = ?';         $params[] = $data['sound_enabled'] ? 1 : 0; }
        if (isset($data['notifications_enabled'])) { $fields[] = 'notifications_enabled = ?'; $params[] = $data['notifications_enabled'] ? 1 : 0; }

        if (empty($fields)) { http_response_code(400); echo json_encode(['error' => 'No fields to update']); exit; }

        $fields[]  = 'updated_at = NOW()';
        $params[]  = $child_id;
        $db->prepare('UPDATE user_preferences SET ' . implode(', ', $fields) . ' WHERE child_id = ?')->execute($params);
        echo json_encode(['success' => true, 'message' => 'Preferences updated']);
    }

} catch (PDOException $e) {
    error_log("Preferences error: " . $e->getMessage());
    http_response_code(500); echo json_encode(['error' => 'Database error']);
}
?>
