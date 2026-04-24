<?php
ob_start();
require_once __DIR__ . '/../config/db.php';
setJsonHeader();
startSecureSession();
session_destroy();
echo json_encode(['success' => true, 'message' => 'Logged out successfully', 'redirect' => 'login.html']);
?>
