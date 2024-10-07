<?php
// Datos de conexión a la base de datos
$servername = "sql204.infinityfree.com";  // Servidor MySQL 
$username = "if0_37418264";  // Usuario de MySQL
$password = "fn41yj5tbkRFOP9";  // Contraseña de MySQL
$dbname = "if0_37418264_usuarios";  // Nombre de la base de datos

// Crear conexión
$conn = new mysqli($servername, $username, $password, $dbname);

// Verificar la conexión
if ($conn->connect_error) {
    die("Conexión fallida: " . $conn->connect_error);
}

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Recoger los datos del formulario
    $username = $_POST['username'];
    $email = $_POST['email'];
    $confirmEmail = $_POST['confirmEmail'];
    $age = $_POST['age'];
    $password = $_POST['password'];
    $confirmPassword = $_POST['confirmPassword'];

    // Validar que los correos coincidan
    if ($email !== $confirmEmail) {
        die("Los correos no coinciden.");
    }

    // Validar que las contraseñas coincidan
    if ($password !== $confirmPassword) {
        die("Las contraseñas no coinciden.");
    }

    // Validar que la contraseña tenga al menos 8 caracteres y 1 número
    if (!preg_match("/^(?=.*\d)[a-zA-Z\d]{8,}$/", $password)) {
        die("La contraseña debe tener al menos 8 caracteres y contener al menos un número.");
    }

    // Preparar e insertar los datos en la base de datos sin encriptar la contraseña
    $stmt = $conn->prepare("INSERT INTO datos (Nombre, `E-mail`, Contrasenna, fecha_reg) VALUES (?, ?, ?, NOW())");
    $stmt->bind_param("sss", $username, $email, $password); // No ciframos la contraseña aquí

    if ($stmt->execute()) {
        // Redirige automáticamente a la página de inicio
        header("Location: index.html");
        exit(); // Es buena práctica usar exit() después de header para detener el script
    } else {
        echo "Error: " . $stmt->error;
    }

    // Cerrar el statement
    $stmt->close();
}

// Cerrar la conexión
$conn->close();
?>