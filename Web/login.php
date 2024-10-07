<?php
// Iniciar sesión
session_start();

// Datos de conexión a la base de datos
$servername = "sql204.infinityfree.com";  // Servidor MySQL
$username = "if0_37418264";  // Usuario MySQL
$password = "fn41yj5tbkRFOP9";  // Contraseña MySQL
$dbname = "if0_37418264_usuarios";  // Nombre de la base de datos

// Crear la conexión
$conn = new mysqli($servername, $username, $password, $dbname);

// Verificar si la conexión es exitosa
if ($conn->connect_error) {
    die("Error de conexión: " . $conn->connect_error);
}

// Verificar si el formulario fue enviado
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Obtener los valores del formulario
    $email = $_POST['email'];
    $password = $_POST['password'];

    // Prevenir inyecciones SQL (usamos prepared statements)
    $stmt = $conn->prepare("SELECT * FROM datos WHERE `E-mail` = ?");
    $stmt->bind_param("s", $email);  // Vincular el correo electrónico como parámetro
    $stmt->execute();
    $result = $stmt->get_result();

    // Verificar si se encontró un usuario con ese correo
    if ($result->num_rows > 0) {
        // Obtener los datos del usuario
        $row = $result->fetch_assoc();
        
        // Verificar si la contraseña ingresada coincide
        if ($password == $row['Contrasenna']) {
            // Si el login es exitoso
            echo "Ingreso exitoso. Bienvenido " . $row['E-mail'];
        } else {
            echo "Contraseña incorrecta.";
        }
    } else {
        echo "No se encontró una cuenta con este correo.";
    }

    // Cerrar el statement
    $stmt->close();
}

// Cerrar la conexión
$conn->close();
?>