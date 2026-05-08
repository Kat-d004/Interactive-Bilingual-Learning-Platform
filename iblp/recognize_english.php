<?php
/**
 * recognize_english.php
 * Receives raw WAV audio via POST, runs Whisper ASR, returns JSON.
 * POST param ?topic=colours|numbers|animals
 */

header('Content-Type: application/json');

$topic = isset($_GET['topic']) ? preg_replace('/[^a-z]/', '', $_GET['topic']) : 'colours';

// Save raw POST body as a temp WAV
$tmpDir  = __DIR__ . '/tmp';
if (!is_dir($tmpDir)) mkdir($tmpDir, 0755, true);

$tmpFile = $tmpDir . '/eng_' . uniqid() . '.wav';
$raw     = file_get_contents('php://input');

if (!$raw || strlen($raw) < 100) {
    echo json_encode(['error' => 'No audio received']);
    exit;
}

file_put_contents($tmpFile, $raw);

$script  = escapeshellarg(__DIR__ . '/asr_predict_english.py');
$wav     = escapeshellarg($tmpFile);
$topicEsc = escapeshellarg($topic);

$output  = shell_exec("/opt/iblp/ml_env/bin/python3.12 $script $wav $topicEsc 2>/dev/null");

@unlink($tmpFile);

if (!$output) {
    echo json_encode(['error' => 'ASR script returned no output']);
    exit;
}

echo trim($output);
