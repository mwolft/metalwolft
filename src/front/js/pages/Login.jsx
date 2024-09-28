import React, { useContext, useState } from "react";
import { Context } from '../store/appContext.js';
import { useNavigate } from "react-router-dom";
import { Row, Col, Container } from "react-bootstrap";

export const Login = () => {
  const { actions } = useContext(Context);
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const navigate = useNavigate();

  const handleEmail = (event) => { setEmail(event.target.value); };
  const handlePassword = (event) => { setPassword(event.target.value); };
  const handleConfirmPassword = (event) => { setConfirmPassword(event.target.value); };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const dataToSend = { email, password };
    let uri, options;

    if (isLogin) {
      // Configuración para iniciar sesión
      uri = process.env.BACKEND_URL + '/api/login';
    } else {
      // Verificación de contraseñas coincidentes para el registro
      if (password !== confirmPassword) {
        actions.setAlert({ visible: true, back: 'danger', text: 'Las contraseñas no coinciden' });
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
        actions.setAlert({ visible: true, back: 'danger', text: data.message || 'Error al procesar la solicitud' });
        return;
      }

      if (data.access_token && data.results) {
        // Guardar el token y el usuario en localStorage solo si se recibe la respuesta correcta
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.results));
        actions.setCurrentUser(data.results);
        actions.setIsLoged(true);
        actions.setAlert({ visible: true, back: 'info', text: data.message || 'Inicio de sesión exitoso' });

        // Redirigir dependiendo del rol
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
    <Container className="auth-container d-flex justify-content-center align-items-center" style={{ marginTop: '120px', marginBottom: '120px' }}>
      <div className="auth-box p-5">
        <Row className="text-center mb-5 d-flex justify-content-center">
          <Col className="d-flex justify-content-center align-items-center flex-row">
            <button className="loginbtn mx-1"> 
              <h2
                className={`auth-toggle ${isLogin ? 'active' : ''}`} onClick={() => setIsLogin(true)}>
                Entrar
              </h2>
            </button>
            <button className="loginbtn mx-1"> 
              <h2
                className={`auth-toggle ${!isLogin ? 'active' : ''}`} onClick={() => setIsLogin(false)}>
                Registrarse
              </h2>
            </button>
          </Col>
        </Row>
        <form onSubmit={handleSubmit}>
          <div className="form-group mt-3 h6">
            <label htmlFor="email" className="mb-1">Correo electrónico:</label>
            <input
              type="email"
              className="form-control"
              id="email"
              value={email}
              onChange={handleEmail}
              required
            />
          </div>
          <div className="form-group mt-3 h6">
            <label htmlFor="password" className="mb-1">Contraseña:</label>
            <input
              type="password"
              className="form-control"
              id="password"
              value={password}
              onChange={handlePassword}
              required
            />
          </div>
          {!isLogin && (
            <div className="form-group mt-3 h6">
              <label htmlFor="confirmPassword" className="mb-1">Confirmar Contraseña:</label>
              <input
                type="password"
                className="form-control"
                id="confirmPassword"
                value={confirmPassword}
                onChange={handleConfirmPassword}
                required
              />
            </div>
          )}
          <div className="container d-flex justify-content-center">
            <button className="stylebtn" variant="primary" type="submit">
              <i className="fa-solid fa-arrow-right"></i>
            </button>
          </div>
        </form>
      </div>
    </Container>
  );
};
