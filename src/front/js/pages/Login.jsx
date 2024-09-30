import React, { useContext, useState } from "react";
import { Context } from '../store/appContext.js';
import { useNavigate } from "react-router-dom";
import { Row, Col, Container, Button, Form } from "react-bootstrap";

export const Login = () => {
  const { actions } = useContext(Context);
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState(""); // Estado para manejar los errores debajo de la contraseña
  const navigate = useNavigate();

  const handleEmail = (event) => { setEmail(event.target.value); };
  const handlePassword = (event) => { setPassword(event.target.value); };
  const handleConfirmPassword = (event) => { setConfirmPassword(event.target.value); };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage(""); // Reiniciar el mensaje de error al intentar nuevamente

    const dataToSend = { email, password };
    let uri, options;

    if (isLogin) {
      // Configuración para iniciar sesión
      uri = process.env.BACKEND_URL + '/api/login';
    } else {
      // Verificación de contraseñas coincidentes para el registro
      if (password !== confirmPassword) {
        setErrorMessage('Las contraseñas no coinciden');
        return;
      }
      // Configuración para registrarse
      uri = process.env.BACKEND_URL + '/api/signup';
    }

    options = {
      method: 'POST',
      body: JSON.stringify(dataToSend),
      headers: {
        'Content-Type': 'application/json'
      }
    };

    try {
      const response = await fetch(uri, options);
      const data = await response.json();

      if (!response.ok) {
        console.error('Error: ', response.status, response.statusText);
        setErrorMessage(data.message || 'Correo o contraseña incorrectos');
        return;
      }

      if (data.access_token && data.results) {
        // Guardar el token y el usuario en localStorage solo si se recibe la respuesta correcta
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.results));
        actions.setCurrentUser(data.results);
        actions.setIsLoged(true);

        // Redirigir dependiendo del rol
        if (data.results.is_admin) {
          navigate("/admin");
        } else {
          navigate("/");
        }
      } else {
        setErrorMessage('Datos incompletos en la respuesta del servidor');
      }
    } catch (error) {
      console.error('Error en el manejo del inicio de sesión:', error);
      setErrorMessage('Error inesperado, intenta más tarde');
    }
  };

  const handleToggleForm = (event) => {
    event.preventDefault(); // Esto evitará cualquier acción predeterminada del navegador
    setIsLogin(!isLogin);
    setErrorMessage(""); // Reiniciar el mensaje de error al cambiar entre login y registro
  };

  return (
    <Container className="auth-container d-flex justify-content-center align-items-center" style={{ marginTop: '120px', marginBottom: '120px' }}>
      <div className="auth-box p-3">
        <Row className="text-center mb-3 d-flex justify-content-center">
          <Col>
            <h4>{isLogin ? "INICIAR SESIÓN" : "REGÍSTRATE"}</h4>
          </Col>
        </Row>
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mt-2">
            <Form.Label>Email:</Form.Label>
            <Form.Control
              type="email"
              value={email}
              onChange={handleEmail}
              required
            />
          </Form.Group>
          <Form.Group className="mt-2">
            <Form.Label>Contraseña:</Form.Label>
            <Form.Control
              type="password"
              value={password}
              onChange={handlePassword}
              required
            />
            {errorMessage && (
              <Form.Text className="text-danger">{errorMessage}</Form.Text>
            )}
          </Form.Group>
          {!isLogin && (
            <Form.Group className="mt-2">
              <Form.Label>Confirmar Contraseña:</Form.Label>
              <Form.Control
                type="password"
                value={confirmPassword}
                onChange={handleConfirmPassword}
                required
              />
            </Form.Group>
          )}
          <div className="container d-flex justify-content-center mt-3">
            <Button className="stylebtn" variant="primary" type="submit">
              {isLogin ? "Iniciar sesión" : "Registrarse"}
            </Button>
          </div>
        </Form>
        <Row className="mt-4 text-center">
          <Col>
            <span>
              {isLogin ? "¿Nuevo Usuario? " : "¿Ya dispone de una cuenta? "}
              <a href="#" onClick={handleToggleForm} className="text-primary text-decoration-underline">
                {isLogin ? "Crear cuenta" : "Ingresar"}
              </a>
            </span>
          </Col>
        </Row>
      </div>
    </Container>
  );
};
