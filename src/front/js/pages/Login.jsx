import React, { useContext, useState } from "react";
import { Context } from '../store/appContext.js';
import { useNavigate } from "react-router-dom";
import { Row, Col, Container, Button, Form } from "react-bootstrap";

export const Login = () => {
  const { actions } = useContext(Context);
  const [isLogin, setIsLogin] = useState(true);
  const [isForgotPassword, setIsForgotPassword] = useState(false);
  const [isResetPassword, setIsResetPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [token, setToken] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const navigate = useNavigate();

  const handleEmail = (event) => { setEmail(event.target.value); };
  const handlePassword = (event) => { setPassword(event.target.value); };
  const handleConfirmPassword = (event) => { setConfirmPassword(event.target.value); };
  const handleToken = (event) => { setToken(event.target.value); };

  const validatePassword = (password) => {
    const minLength = 6;
    const maxLength = 20;
    const hasLetter = /[a-zA-Z]/.test(password);

    if (password.length < minLength) {
      return 'La contraseña debe tener al menos 6 caracteres.';
    }
    if (password.length > maxLength) {
      return 'La contraseña no debe tener más de 20 caracteres.';
    }
    if (!hasLetter) {
      return 'La contraseña debe contener al menos una letra.';
    }
    return '';
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage("");

    if (!isLogin) {
      const passwordError = validatePassword(password);
      if (passwordError) {
        setErrorMessage(passwordError);
        return;
      }
    }

    const dataToSend = { email, password };
    let uri, options;

    if (isLogin) {
      uri = process.env.REACT_APP_BACKEND_URL + '/api/login';
    } else {
      if (password !== confirmPassword) {
        setErrorMessage('Las contraseñas no coinciden');
        return;
      }
      uri = process.env.REACT_APP_BACKEND_URL + '/api/signup';
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
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.results));
        actions.setCurrentUser(data.results);
        actions.setIsLoged(true);

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
    event.preventDefault();
    setIsLogin(!isLogin);
    setErrorMessage("");
  };

  const handleForgotPassword = (event) => {
    event.preventDefault();
    setIsForgotPassword(true);
    setErrorMessage("");
  };

  const handleCancelForgotPassword = () => {
    setIsForgotPassword(false);
    setEmail("");
    setErrorMessage("");
  };

  const handleForgotPasswordSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (response.ok) {
        setSuccessMessage(data.message || 'Revisa tu correo para continuar.');
        setIsResetPassword(true); // Mostrar enlace para ingresar código
      } else {
        setErrorMessage(data.error || 'Error al enviar el correo.');
      }
    } catch (error) {
      setErrorMessage('Error inesperado. Intenta nuevamente más tarde.');
    }
  };

  const handleResetPasswordSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    if (password !== confirmPassword) {
      setErrorMessage('Las contraseñas no coinciden');
      return;
    }

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password }),
      });
      const data = await response.json();
      if (response.ok) {
        setSuccessMessage(data.message || 'Contraseña restablecida con éxito.');
        setIsResetPassword(false);
        setIsLogin(true);
      } else {
        setErrorMessage(data.error || 'Error al restablecer la contraseña.');
      }
    } catch (error) {
      setErrorMessage('Error inesperado. Intenta nuevamente más tarde.');
    }
  };

  return (
    <Container className="auth-container d-flex justify-content-center align-items-center" style={{ marginTop: '120px', marginBottom: '120px' }}>
      <div className="auth-box p-3">
        <Row className="text-center mb-3 d-flex justify-content-center">
          <Col>
            <h4>{isResetPassword ? "Restablecer Contraseña" : isForgotPassword ? "Recuperar Contraseña" : isLogin ? "INGRESAR" : "CREAR CUENTA"}</h4>
            <hr className="hr_login" />
          </Col>
        </Row>
        {successMessage && <p className="text-success text-center">{successMessage}</p>}
        {errorMessage && <p className="text-danger text-center">{errorMessage}</p>}
        {isForgotPassword ? (
          <>
            <p className="text-center">Te enviaremos un correo electrónico para restablecer tu contraseña.</p>
            <Form onSubmit={handleForgotPasswordSubmit}>
              <Form.Group className="mt-2">
                <Form.Label><b>Email:</b></Form.Label>
                <Form.Control
                  type="email"
                  value={email}
                  onChange={handleEmail}
                  required
                />
                {errorMessage && <Form.Text className="text-danger">{errorMessage}</Form.Text>}
              </Form.Group>
              <div className="container d-flex justify-content-center mt-3">
                <Button className="me-2" variant="secondary" onClick={handleCancelForgotPassword}>
                  Cancelar
                </Button>
                <Button variant="primary" type="submit">
                  Enviar
                </Button>
              </div>
            </Form>
          </>
        ) : isResetPassword ? (
          <Form onSubmit={handleResetPasswordSubmit}>
            <Form.Group className="mt-2">
              <Form.Label><b>Código:</b></Form.Label>
              <Form.Control
                type="text"
                value={token}
                onChange={handleToken}
                required
              />
            </Form.Group>
            <Form.Group className="mt-2">
              <Form.Label><b>Nueva Contraseña:</b></Form.Label>
              <Form.Control
                type="password"
                value={password}
                onChange={handlePassword}
                required
              />
            </Form.Group>
            <Form.Group className="mt-2">
              <Form.Label><b>Confirmar Contraseña:</b></Form.Label>
              <Form.Control
                type="password"
                value={confirmPassword}
                onChange={handleConfirmPassword}
                required
              />
            </Form.Group>
            <div className="container d-flex justify-content-center mt-3">
              <Button className="me-2" variant="secondary" onClick={() => setIsResetPassword(false)}>
                Cancelar
              </Button>
              <Button variant="primary" type="submit">
                Restablecer
              </Button>
            </div>
          </Form>
        ) : (
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mt-2">
              <Form.Label><b>Email:</b></Form.Label>
              <Form.Control
                type="email"
                value={email}
                onChange={handleEmail}
                required
              />
            </Form.Group>
            <Form.Group className="mt-2">
              <Form.Label><b>Contraseña:</b></Form.Label>
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
                <Form.Label><b>Confirmar Contraseña:</b></Form.Label>
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
        )}
        {!isForgotPassword && !isResetPassword && (
          <>
            <Row className="mt-4 text-center">
              <Col>
                <span>
                  {isLogin ? "¿Nuevo Usuario? " : "¿Ya tienes una cuenta? "}
                  <a href="#" onClick={handleToggleForm} className="text-decoration-underline" style={{ color: '#ff324d' }}>
                    {isLogin ? "Crear cuenta" : "Ingresar"}
                  </a>
                </span>
              </Col>
            </Row>
            <Row className="mt-2 text-center">
              <Col>
                <a href="#" onClick={handleForgotPassword} className="text-decoration-underline" style={{ color: '#ff324d' }}>
                  ¿Olvidaste tu contraseña?
                </a>
              </Col>
            </Row>
          </>
        )}
      </div>
    </Container>
  );
};
