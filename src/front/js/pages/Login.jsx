import React, { useContext, useState } from "react";
import { Context } from '../store/appContext.js';
import { useNavigate } from "react-router-dom";
import { Row, Col, Container } from "react-bootstrap";

export const Login = () => {
  const { store, actions } = useContext(Context);
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
    if (isLogin) {
      const dataToSend = { email, password };
      const uri = process.env.BACKEND_URL + '/api/login';
      const options = {
        method: 'POST',
        body: JSON.stringify(dataToSend),
        headers: {
          'Content-Type': 'application/json'
        }
      };
      const response = await fetch(uri, options);
      if (!response.ok) {
        console.log('Error: ', response.status, response.statusText);
        if (response.status === 401) {
          const data = await response.json();
          let alert = {
            visible: true,
            back: 'danger',
            text: 'Usuario no encontrado'
          };
          actions.setAlert(alert);
        }
        return;
      }
      const data = await response.json();
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.results));
      actions.setCurrentUser(data.results);
      actions.setIsLoged(true);
      actions.setAlert({ visible: true, back: 'info', text: data.message });
      navigate('/'); 
    } else {
      if (password !== confirmPassword) {
        actions.setAlert({ visible: true, back: 'danger', text: 'Las contraseñas no coinciden' });
        return;
      }
      const dataToSend = { email, password };
      const uri = process.env.BACKEND_URL + '/api/signup';
      const options = {
        method: 'POST',
        body: JSON.stringify(dataToSend),
        headers: {
          'Content-Type': 'application/json'
        }
      };
      const response = await fetch(uri, options);
      if (!response.ok) {
        console.log('Error: ', response.status, response.statusText);
        const data = await response.json();
        actions.setAlert({ visible: true, back: 'danger', text: data.message });
        return;
      }
      const data = await response.json();
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.results));
      actions.setCurrentUser(data.results);
      actions.setIsLoged(true);
      actions.setAlert({ visible: true, back: 'info', text: data.message });
      navigate('/'); 
    }
  };

  return (
    <Container className="auth-container d-flex justify-content-center align-items-center">
      <div className="auth-box p-5">
        <Row className="text-center mb-3">
          <Col>
            <button className="loginbtn">
              <h2
                className={`auth-toggle ${isLogin ? 'active' : ''}`} onClick={() => setIsLogin(true)}>
                LOGIN
              </h2>
            </button>
          </Col>
          <Col>
            <button className="loginbtn">
              <h2
                className={`auth-toggle ${!isLogin ? 'active' : ''}`} onClick={() => setIsLogin(false)}>
                SIGNUP
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


// import React, { useContext, useState } from "react";
// import { Context } from '../store/appContext.js';
// import { useNavigate } from "react-router-dom";
// import { Row, Col, Container } from "react-bootstrap";


// export const Login = () => {
//   const { store, actions } = useContext(Context)
//   const [email, setEmail] = useState("");
//   const [password, setPassword] = useState("");
//   const navigate = useNavigate()
//   const handleEmail = (event) => { setEmail(event.target.value); };
//   const handlePassword = (event) => { setPassword(event.target.value); };
//   const handleSubmit = async (event) => {
//     event.preventDefault();
//     const dataToSend = { email, password };
//     const uri = process.env.BACKEND_URL + '/api/login'
//     const options = {
//       method: 'POST',
//       body: JSON.stringify(dataToSend),
//       headers: {
//         'Content-Type': 'application/json'
//       }
//     }
//     const response = await fetch(uri, options)
//     if (!response.ok) {
//       // Tratamos el error
//       console.log('Error: ', response.status, response.statusText);
//       if (response.status == 401) {
//         const data = await response.json()
//         let alert = {
//           visible: true,
//           back: 'danger',
//           text: ('Usuario no encontrado')
//         }
//         actions.setAlert(alert)
//       }
//       return
//     };
//     const data = await response.json()
//     // Almaceno los datos en localStorage y en flux (store)
//     localStorage.setItem("token", data.access_token);
//     localStorage.setItem("user", JSON.stringify(data.results));
//     actions.setCurrentUser(data.results);
//     actions.setIsLoged(true)
//     actions.setAlert({ visible: true, back: 'info', text: data.message })
//   }
//   return (
//     <Container className="auth-container d-flex justify-content-center align-items-center">
//       <div className="auth-box p-5">
//         <Row className="text-center mb-3">
//           <Col>
//           <button className="loginbtn"> 
//             <h2
//               className={`auth-toggle ${store.isLogin ? 'active' : ''}`}
//               onClick={() => actions.setIsLoged(true)}
//             >
//               LOGIN
//             </h2>
//           </button>
//           </Col>
//           <Col>
//           <button className="loginbtn">
//             <h2
//               className={`auth-toggle ${!store.isLogin ? 'active' : ''}`}
//               onClick={() => actions.setIsLoged(false)}
//             >
//               SIGNUP
//             </h2>
//           </button>
//           </Col>
//         </Row>
//         <form onSubmit={handleSubmit}>
//           <div className="form-group mt-3 h6">
//             <label htmlFor="email" className="mb-1">Correo electrónico:</label>
//             <input type="email" className="form-control" id="email"
//               value={email} onChange={handleEmail} required />
//           </div>
//           <div className="form-group mt-3 h6">
//             <label htmlFor="password" className="mb-1">Contraseña:</label>
//             <input type="password" className="form-control" id="password"
//               value={password} onChange={handlePassword} required />
//           </div>
//           <div className="container d-flex justify-content-center">
//                 <button className="stylebtn" variant="primary" type="submit" onClick={handleSubmit}><i class="fa-solid fa-arrow-right"></i></button>               
//           </div>
//         </form>
//       </div>
//     </Container>
//   );
// };


// import React, { useContext, useState } from "react";
// import { Container, Row, Col, Button, Form } from 'react-bootstrap';
// import { Context } from '../store/appContext.js'
// import { useNavigate } from "react-router-dom";

// export const Login = () => {
//   const [isLogin, setIsLogin] = useState(true);
//   const { actions } = useContext(Context);
//   const [email, setEmail] = useState("");
//   const [password, setPassword] = useState("");
//   const navigate = useNavigate();

//   const handleEmailChange = (e) => {
//     setEmail(e.target.value);
//   };

//   const handlePasswordChange = (e) => {
//     setPassword(e.target.value);
//   };

//   const handleSubmit = async (event) => {
//     event.preventDefault();
//     console.log("form sing enviado");
    
//     const dataToSend = { email, password };
//     const uri = isLogin ? process.env.BACKEND_URL + '/api/login' : process.env.BACKEND_URL + '/api/signup';
//     const options = {
//       method: 'POST',
//       body: JSON.stringify(dataToSend),
//       headers: {
//         'Content-Type': 'application/json'
//       }
//     };
//     const response = await fetch(uri, options);
//     if (!response.ok) {
//       console.log('Error: ', response.status, response.statusText);
//       return
//     }
//     const data = await response.json()
//     // Almaceno los datos en localStorage y en flux (store)
//     localStorage.setItem("token", data.access_token);
//     localStorage.setItem("user", JSON.stringify(data.results));
//     actions.setCurrentUser(data.results);
//     actions.setIsLoged(true)
//     actions.setAlert({visible: true, back: 'info', text: data.message})
//     // Me voy al dashboard
//     navigate('/profile')
//     console.log(data);
//     if (isLogin) {
//       localStorage.setItem('token', data.access_token)
//       localStorage.setItem('user', JSON.stringify(data.results))
//       actions.setIsLoged(true);
//       actions.setCurrentUser(data.results);
//       actions.setAlert({visible: true, back: 'info', text: data.message})
//       navigate('/dashboard')
//     } else {
//     }
//   };

//   return (
//     <Container className="d-flex justify-content-center">
//       <Row>
//         <Col xs={12} md={12} lg={12} className="mx-auto">
//           <div className="square-box">
//             <div className="container d-flex justify-content-center">
//               <p className="btn me-2" variant="primary" onClick={() => setIsLogin(true)}>Login</p>
//               <p className="btn" variant="secondary" onClick={() => setIsLogin(false)}>Signup</p>
//             </div>
//             <Form onSubmit={handleSubmit}>
//               <Form.Group controlId="email">
//                 <Form.Label>Email</Form.Label>
//                 <Form.Control type="email" value={email} onChange={handleEmailChange} />
//               </Form.Group>
//               <Form.Group controlId="password">
//                 <Form.Label>Password</Form.Label>
//                 <Form.Control type="password" value={password} onChange={handlePasswordChange} />
//               </Form.Group>
//               <div className="container d-flex justify-content-center">
//                 <button className="stylebtn" variant="primary" type="submit" onClick={handleSubmit}><i class="fa-solid fa-arrow-right"></i></button> 
//               </div>
//             </Form>
//           </div>
//         </Col>
//       </Row>
//     </Container>
//   );
// };

