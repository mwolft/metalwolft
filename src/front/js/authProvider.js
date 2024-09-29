export const authProvider = {
  login: ({ email, password }) => {
    const request = new Request(process.env.REACT_APP_BACKEND_URL + "/api/login", {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      headers: new Headers({ 'Content-Type': 'application/json' }),
    });
    return fetch(request)
      .then(response => {
        if (response.status < 200 || response.status >= 300) {
          throw new Error(response.statusText);
        }
        return response.json();
      })
      .then(auth => {
        console.log("Login successful:", auth);
        localStorage.setItem('token', auth.access_token);
        localStorage.setItem('user', JSON.stringify(auth.results));
      });
  },
  logout: () => {
    console.log("Logging out...");
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return Promise.resolve();
  },
  checkAuth: () => {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || "{}");
    console.log("checkAuth executed. Token:", token);
    console.log("checkAuth executed. User:", user);

    if (token && user && user.is_admin) {
      console.log("User is authenticated and authorized.");
      return Promise.resolve();
    } else {
      console.warn("User is not authenticated or not authorized.");
      return Promise.reject({ redirectTo: '/login' });  // Aseguramos que la redirección sea clara
    }
  },
  checkError: (error) => {
    const status = error.status;
    console.log("checkError executed. Status:", status);
    if (status === 401 || status === 403) {
      localStorage.removeItem('token');
      return Promise.reject({ redirectTo: '/login' });
    }
    return Promise.resolve();
  },
  getPermissions: () => {
    const user = JSON.parse(localStorage.getItem('user') || "{}");
    console.log("getPermissions executed. User:", user);
    if (user.is_admin) {
      return Promise.resolve("admin");
    } else {
      return Promise.resolve();
    }
  },
};
