<?php
// Get all inputs
$message = $_POST['message'];
$fontFamily = $_POST['fontFamily'];
$fontStyle = $_POST['fontStyle'];
$color = $_POST['color'];
$size = $_POST['size']; 
$resetTime = $_POST['resetTime']; 

// Open file

$handle = fopen("data.txt", 'r');
$line = fgets($handle);
fclose($handle);

// Clear file
$handle = fopen("data.txt", "w");
fwrite($handle, trim($line). "\n");
fwrite($handle, "empty \n");
fwrite($handle, $message. "\n");
fwrite($handle, $fontFamily. "\n");
fwrite($handle, $size. "\n");
fwrite($handle, $color. "\n");
fwrite($handle, $fontStyle. "\n");
fwrite($handle, $resetTime);
fclose($handle);
header("location: message.html");
?>