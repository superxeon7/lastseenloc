<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$data = $_POST;
$data['ip'] = $_SERVER['REMOTE_ADDR'];
$data['timestamp'] = date('Y-m-d H:i:s');
$data['user_agent'] = $_SERVER['HTTP_USER_AGENT'];

$logFile = '../logs/info.txt';
file_put_contents($logFile, json_encode($data) . "\n", FILE_APPEND);

echo json_encode(['status' => 'success']);
?>