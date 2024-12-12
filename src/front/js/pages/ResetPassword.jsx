import React, { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Container, Row, Col, Form, Button } from "react-bootstrap";

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (password !== confirmPassword) {
      setMessage("Las contraseñas no coinciden");
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
        setMessage("¡Contraseña restablecida con éxito!");
      } else {
        setMessage(data.error || "Error al restablecer la contraseña");
      }
    } catch (error) {
      setMessage("Error inesperado. Intenta nuevamente más tarde.");
    }
  };

  return (
    <Container className="auth-container d-flex justify-content-center align-items-center" style={{ marginTop: '120px', marginBottom: '120px' }}>
      <div className="auth-box p-3">
        <Row className="text-center mb-3 d-flex justify-content-center">
          <Col>
            <h4>Restablecer Contraseña</h4>
            <hr className="hr_login" />
          </Col>
        </Row>
        {message && <p className={`text-${message.includes("éxito") ? "success" : "danger"} text-center`}>{message}</p>}
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mt-2">
            <Form.Label><b>Nueva Contraseña:</b></Form.Label>
            <Form.Control
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </Form.Group>
          <Form.Group className="mt-2">
            <Form.Label><b>Confirmar Contraseña:</b></Form.Label>
            <Form.Control
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </Form.Group>
          <div className="container d-flex justify-content-center mt-3">
            <Button className="stylebtn" variant="primary" type="submit">
              Restablecer 
            </Button>
          </div>
        </Form>
      </div>
    </Container>
  );
};

export default ResetPassword;
