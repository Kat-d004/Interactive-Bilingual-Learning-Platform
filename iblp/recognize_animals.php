<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { echo json_encode(['error' => 'POST required']); exit; }

define('PYTHON_BIN',    '/home/kopano/ml_env/bin/python3.12');
define('PYTHON_SCRIPT', '/var/www/html/iblp/asr_predict_animals.py');
define('TMP_DIR',       '/var/www/html/iblp/tmp');
define('MAX_BYTES',     5 * 1024 * 1024);

if (!is_dir(TMP_DIR)) mkdir(TMP_DIR, 0755, true);

$rawInput = file_get_contents('php://input');
if (empty($rawInput)) {
    if (!empty($_FILES['audio']['tmp_name'])) {
        $rawInput = file_get_contents($_FILES['audio']['tmp_name']);
    } else {
        echo json_encode(['error' => 'No audio data received']); exit;
    }
}
if (strlen($rawInput) > MAX_BYTES) { echo json_encode(['error' => 'Audio too large']); exit; }

$tmpWav  = TMP_DIR . '/rec_ani_' . uniqid('', true) . '.wav';
file_put_contents($tmpWav, $rawInput);

$script  = escapeshellarg(PYTHON_SCRIPT);
$wavFile = escapeshellarg($tmpWav);
$cmd     = 'MPLCONFIGDIR=' . TMP_DIR . ' NUMBA_CACHE_DIR=' . TMP_DIR . ' HOME=' . TMP_DIR . ' '
         . PYTHON_BIN . ' ' . $script . ' ' . $wavFile . ' 2>/dev/null';

$output = shell_exec($cmd);
@unlink($tmpWav);

$json = null;
foreach (explode("\n", trim($output)) as $line) {
    $line = trim($line);
    if (strlen($line) > 0 && $line[0] === '{') { $json = $line; break; }
}

if (!$json) { echo json_encode(['error' => 'No output from Python', 'detail' => trim($output)]); exit; }

$result = json_decode($json, true);
if (json_last_error() !== JSON_ERROR_NONE) { echo json_encode(['error' => 'Invalid JSON from Python', 'detail' => $json]); exit; }

echo json_encode($result);
