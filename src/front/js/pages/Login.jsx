import React, { useContext, useState } from "react";
import { Context } from "../store/appContext.js";
import { useNavigate } from "react-router-dom";
import { Container, Button, Form } from "react-bootstrap";
import { Helmet } from "react-helmet-async";

const PENDING_PRODUCT_CONFIG_STORAGE_KEY = "mw_pending_product_config";
const PENDING_PRODUCT_CONFIG_MAX_AGE_MS = 30 * 60 * 1000;

const getPendingProductReturnTo = () => {
  if (typeof window === "undefined") return null;

  const rawPendingConfig = window.sessionStorage.getItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
  if (!rawPendingConfig) return null;

  try {
    const pendingConfig = JSON.parse(rawPendingConfig);
    const savedAt = Number(pendingConfig?.saved_at);
    const isFresh = Number.isFinite(savedAt) && Date.now() - savedAt <= PENDING_PRODUCT_CONFIG_MAX_AGE_MS;
    const returnTo = pendingConfig?.return_to;

    if (!isFresh || typeof returnTo !== "string" || !returnTo.startsWith("/") || returnTo.startsWith("//")) {
      window.sessionStorage.removeItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
      return null;
    }

    return returnTo;
  } catch (error) {
    window.sessionStorage.removeItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
    return null;
  }
};

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
  const [hasPendingProductConfig] = useState(() => Boolean(getPendingProductReturnTo()));
  const navigate = useNavigate();

  const handleEmail = (event) => { setEmail(event.target.value); };
  const handlePassword = (event) => { setPassword(event.target.value); };
  const handleConfirmPassword = (event) => { setConfirmPassword(event.target.value); };
  const handleToken = (event) => { setToken(event.target.value); };

  const validatePassword = (rawPassword) => {
    const minLength = 6;
    const maxLength = 20;
    const hasLetter = /[a-zA-Z]/.test(rawPassword);

    if (rawPassword.length < minLength) {
      return "La contraseña debe tener al menos 6 caracteres.";
    }
    if (rawPassword.length > maxLength) {
      return "La contraseña no debe tener más de 20 caracteres.";
    }
    if (!hasLetter) {
      return "La contraseña debe contener al menos una letra.";
    }
    return "";
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
    let uri;

    if (isLogin) {
      uri = process.env.REACT_APP_BACKEND_URL + "/api/login";
    } else {
      if (password !== confirmPassword) {
        setErrorMessage("Las contraseñas no coinciden");
        return;
      }
      uri = process.env.REACT_APP_BACKEND_URL + "/api/signup";
    }

    const options = {
      method: "POST",
      body: JSON.stringify(dataToSend),
      headers: {
        "Content-Type": "application/json"
      }
    };

    try {
      const response = await fetch(uri, options);
      const data = await response.json();

      if (!response.ok) {
        console.error("Error: ", response.status, response.statusText);
        setErrorMessage(data.message || "Correo o contraseña incorrectos");
        return;
      }

      if (data.access_token && data.results) {
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.results));
        actions.setCurrentUser(data.results);
        actions.setIsLoged(true);
        const pendingProductReturnTo = getPendingProductReturnTo();

        if (data.results.is_admin) {
          navigate("/admin");
        } else if (pendingProductReturnTo) {
          navigate(pendingProductReturnTo);
        } else {
          navigate("/");
        }
      } else {
        setErrorMessage("Datos incompletos en la respuesta del servidor");
      }
    } catch (error) {
      console.error("Error en el manejo del inicio de sesión:", error);
      setErrorMessage("Error inesperado, intenta más tarde");
    }
  };

  const handleToggleForm = (event) => {
    event.preventDefault();
    setIsLogin(!isLogin);
    setErrorMessage("");
    setSuccessMessage("");
  };

  const handleForgotPassword = (event) => {
    event.preventDefault();
    setIsForgotPassword(true);
    setErrorMessage("");
    setSuccessMessage("");
  };

  const handleCancelForgotPassword = () => {
    setIsForgotPassword(false);
    setEmail("");
    setErrorMessage("");
    setSuccessMessage("");
  };

  const handleForgotPasswordSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (response.ok) {
        setSuccessMessage(data.message || "Revisa tu correo para continuar.");
        setIsResetPassword(true);
      } else {
        setErrorMessage(data.error || "Error al enviar el correo.");
      }
    } catch (error) {
      setErrorMessage("Error inesperado. Intenta nuevamente más tarde.");
    }
  };

  const handleResetPasswordSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    if (password !== confirmPassword) {
      setErrorMessage("Las contraseñas no coinciden");
      return;
    }

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });
      const data = await response.json();
      if (response.ok) {
        setSuccessMessage(data.message || "Contraseña restablecida con éxito.");
        setIsResetPassword(false);
        setIsLogin(true);
      } else {
        setErrorMessage(data.error || "Error al restablecer la contraseña.");
      }
    } catch (error) {
      setErrorMessage("Error inesperado. Intenta nuevamente más tarde.");
    }
  };

  const authTitle = isResetPassword
    ? "Restablece tu contraseña"
    : isForgotPassword
      ? "Recupera tu acceso"
      : isLogin
        ? "Accede a tu cuenta"
        : "Crea tu cuenta";

  const authSubtitle = isResetPassword
    ? "Introduce el código que has recibido y define una nueva contraseña para volver a entrar."
    : isForgotPassword
      ? "Te enviaremos un correo para que puedas recuperar el acceso de forma segura."
      : isLogin
        ? "Continúa con tu compra, recupera tu carrito y consulta tus pedidos."
        : "Crea tu cuenta para guardar tus pedidos y continuar con la compra.";

  return (
    <>
      <Helmet>
        <meta name="theme-color" content="#ff324d" />
      </Helmet>

      <Container fluid className="auth-page">
        <div
          className="auth-page-media"
          aria-hidden="true"
          style={{
            backgroundImage: "url(https://res.cloudinary.com/dewanllxn/image/upload/v1733817377/herrero-ciudad-real_ndf77e.jpg)",
          }}
        />
        <div className="auth-page-overlay" aria-hidden="true" />

        <div className="auth-page-content">
          <div className="auth-box login-card">
            <div className="login-card-header">
              <p className="login-card-eyebrow">Metal Wolft</p>
              <h1 className="login-card-title">{authTitle}</h1>
              <p className="login-card-subtitle">{authSubtitle}</p>
            </div>

            {isLogin && !isForgotPassword && !isResetPassword && hasPendingProductConfig && (
              <div className="auth-pending-return" role="status">
                <i className="fa-solid fa-bag-shopping" aria-hidden="true"></i>
                <span>Después de iniciar sesión volverás a tu reja configurada.</span>
              </div>
            )}

            {successMessage && <div className="auth-status auth-status--success">{successMessage}</div>}
            {errorMessage && <div className="auth-status auth-status--error">{errorMessage}</div>}

            <hr className="hr_login auth-divider" />

            {isForgotPassword ? (
              <>
                <p className="login-card-helper">Te enviaremos un correo electrónico para restablecer tu contraseña.</p>
                <Form onSubmit={handleForgotPasswordSubmit}>
                  <Form.Group className="auth-form-group">
                    <Form.Label className="auth-field-label">Email</Form.Label>
                    <Form.Control
                      className="auth-field-control"
                      type="email"
                      value={email}
                      onChange={handleEmail}
                      required
                    />
                  </Form.Group>
                  <div className="auth-form-actions auth-form-actions--split">
                    <Button className="auth-secondary-button" variant="secondary" type="button" onClick={handleCancelForgotPassword}>
                      Cancelar
                    </Button>
                    <Button className="btn btn-style-background-color auth-submit-button" variant="primary" type="submit">
                      Enviar
                    </Button>
                  </div>
                </Form>
              </>
            ) : isResetPassword ? (
              <Form onSubmit={handleResetPasswordSubmit}>
                <Form.Group className="auth-form-group">
                  <Form.Label className="auth-field-label">Código</Form.Label>
                  <Form.Control
                    className="auth-field-control"
                    type="text"
                    value={token}
                    onChange={handleToken}
                    required
                  />
                </Form.Group>
                <Form.Group className="auth-form-group">
                  <Form.Label className="auth-field-label">Nueva contraseña</Form.Label>
                  <Form.Control
                    className="auth-field-control"
                    type="password"
                    value={password}
                    onChange={handlePassword}
                    required
                  />
                </Form.Group>
                <Form.Group className="auth-form-group">
                  <Form.Label className="auth-field-label">Confirmar contraseña</Form.Label>
                  <Form.Control
                    className="auth-field-control"
                    type="password"
                    value={confirmPassword}
                    onChange={handleConfirmPassword}
                    required
                  />
                </Form.Group>
                <div className="auth-form-actions auth-form-actions--split">
                  <Button className="auth-secondary-button" variant="secondary" type="button" onClick={() => setIsResetPassword(false)}>
                    Cancelar
                  </Button>
                  <Button className="btn btn-style-background-color auth-submit-button" variant="primary" type="submit">
                    Restablecer
                  </Button>
                </div>
              </Form>
            ) : (
              <Form onSubmit={handleSubmit}>
                <Form.Group className="auth-form-group">
                  <Form.Label className="auth-field-label">Email</Form.Label>
                  <Form.Control
                    className="auth-field-control"
                    type="email"
                    value={email}
                    onChange={handleEmail}
                    required
                  />
                </Form.Group>
                <Form.Group className="auth-form-group">
                  <Form.Label className="auth-field-label">Contraseña</Form.Label>
                  <Form.Control
                    className="auth-field-control"
                    type="password"
                    value={password}
                    onChange={handlePassword}
                    required
                  />
                </Form.Group>
                {!isLogin && (
                  <Form.Group className="auth-form-group">
                    <Form.Label className="auth-field-label">Confirmar contraseña</Form.Label>
                    <Form.Control
                      className="auth-field-control"
                      type="password"
                      value={confirmPassword}
                      onChange={handleConfirmPassword}
                      required
                    />
                  </Form.Group>
                )}
                <div className="auth-form-actions">
                  <Button className="btn btn-style-background-color auth-submit-button" variant="primary" type="submit">
                    {isLogin ? "Iniciar sesión" : "Registrarse"}
                  </Button>
                </div>
              </Form>
            )}

            {!isForgotPassword && !isResetPassword && (
              <div className="auth-card-links">
                <p className="auth-link-row">
                  {isLogin ? "¿Nuevo usuario?" : "¿Ya tienes una cuenta?"}{" "}
                  <button type="button" onClick={handleToggleForm} className="auth-inline-link">
                    {isLogin ? "Crear cuenta" : "Ingresar"}
                  </button>
                </p>
                <button type="button" onClick={handleForgotPassword} className="auth-inline-link auth-inline-link--standalone">
                  ¿Olvidaste tu contraseña?
                </button>
              </div>
            )}
          </div>
        </div>
      </Container>
    </>
  );
};
