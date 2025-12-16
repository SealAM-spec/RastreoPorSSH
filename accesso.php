<?php
session_start();

// Datos de conexión
$servername = "localhost"; // o "db" si usas docker-compose
$username = "root";       // tu usuario de la BD
$password = "root";       // tu contraseña de la BD
$dbname = "UsersDB";      // nombre de la BD de usuarios

// Crear conexión
$conn = new mysqli($servername, $username, $password, $dbname);

// Verificar conexión
if ($conn->connect_error) {
    die("Conexión fallida: " . $conn->connect_error);
}

// Recibir datos del formulario
$user = $_POST['username'];
$pass = $_POST['password'];

// Preparar consulta segura
$stmt = $conn->prepare("SELECT password FROM usuarios WHERE username = ?");
$stmt->bind_param("s", $user);
$stmt->execute();
$stmt->store_result();

if ($stmt->num_rows > 0) {
    $stmt->bind_result($hashed_password);
    $stmt->fetch();

    // Verificar contraseña
    if (password_verify($pass, $hashed_password)) {
        $_SESSION['usuario'] = $user;
        echo "Login exitoso. Bienvenido, " . $user;
        // Aquí puedes redirigir a otra página:
        // header("Location: dashboard.php");
    } else {
        echo "Contraseña incorrecta.";
    }
} else {
    echo "Usuario no encontrado.";
}

$stmt->close();
$conn->close();
?>
