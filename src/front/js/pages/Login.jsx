import React, { useContext, useState } from "react";
import { Context } from '../store/appContext.js';
import { useNavigate } from "react-router-dom";
import { Row, Col, Container, Form, Button } from "react-bootstrap";

export const Login = () => {
  const { actions } = useContext(Context);
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const navigate = useNavigate();

  const handleEmail = (event) => setEmail(event.target.value);
  const handlePassword = (event) => setPassword(event.target.value);
  const handleConfirmPassword = (event) => setConfirmPassword(event.target.value);

  const handleSubmit = async (event) => {
    event.preventDefault();
  
    const dataToSend = { email, password };
    let uri, options;
  
    if (isLogin) {
      uri = process.env.BACKEND_URL + '/api/login';
    } else {
      if (password !== confirmPassword) {
        actions.setAlert({ visible: true, back: 'danger', text: 'Las contraseñas no coinciden' });
        return;
      }
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
        
        // Manejo específico de error 401
        if (response.status === 401 && isLogin) {
          actions.setAlert({ visible: true, back: 'danger', text: 'Usuario no encontrado. Regístrate para continuar.' });
          setIsLogin(false); // Cambia al modo de registro automáticamente
        } else {
          actions.setAlert({ visible: true, back: 'danger', text: data.message || 'Error al procesar la solicitud' });
        }
        return;
      }
  
      if (data.access_token && data.results) {
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.results));
        actions.setCurrentUser(data.results);
        actions.setIsLoged(true);
        actions.setAlert({ visible: true, back: 'info', text: data.message || 'Inicio de sesión exitoso' });
  
        if (data.results.is_admin) {
          navigate("/admin");
        } else {
          navigate("/");
        }
      } else {
        actions.setAlert({ visible: true, back: 'danger', text: 'Datos incompletos en la respuesta del servidor' });
      }
    } catch (error) {
      console.error('Error en el manejo del inicio de sesión:', error);
      actions.setAlert({ visible: true, back: 'danger', text: 'Error inesperado, intenta más tarde' });
    }
  };
  

  return (
    <Container className="d-flex justify-content-center align-items-center" style={{ marginTop: '120px', marginBottom: '120px' }}>
      <div className="p-4" style={{ maxWidth: '400px', width: '100%', backgroundColor: 'white', borderRadius: '10px', boxShadow: '0px 0px 10px rgba(0,0,0,0.1)' }}>
        <Row className="text-center mb-4">
          <Col>
            <Button variant="link" className={`auth-toggle ${isLogin ? 'active' : ''}`} onClick={() => setIsLogin(true)}>
              Iniciar sesión
            </Button>
            <Button variant="link" className={`auth-toggle ${!isLogin ? 'active' : ''}`} onClick={() => setIsLogin(false)}>
              Registrarse
            </Button>
          </Col>
        </Row>
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3" controlId="formBasicEmail">
            <Form.Label>Correo electrónico:</Form.Label>
            <Form.Control
              type="email"
              value={email}
              onChange={handleEmail}
              required
              placeholder="Ingresa tu correo"
            />
          </Form.Group>
          <Form.Group className="mb-3" controlId="formBasicPassword">
            <Form.Label>Contraseña:</Form.Label>
            <Form.Control
              type="password"
              value={password}
              onChange={handlePassword}
              required
              placeholder="Ingresa tu contraseña"
            />
          </Form.Group>
          {!isLogin && (
            <Form.Group className="mb-3" controlId="formConfirmPassword">
              <Form.Label>Confirmar contraseña:</Form.Label>
              <Form.Control
                type="password"
                value={confirmPassword}
                onChange={handleConfirmPassword}
                required
                placeholder="Confirma tu contraseña"
              />
            </Form.Group>
          )}
          <Button variant="primary" type="submit" className="w-100">
            {isLogin ? 'Iniciar sesión' : 'Registrarse'}
          </Button>
        </Form>
      </div>
    </Container>
  );
};
