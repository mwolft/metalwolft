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
          localStorage.setItem('token', auth.access_token);
          localStorage.setItem('user', JSON.stringify(auth.results));
        });
    },
    logout: () => {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return Promise.resolve();
    },
    checkAuth: () => {
      return localStorage.getItem('token') ? Promise.resolve() : Promise.reject();
    },
    checkError: (error) => {
      const status = error.status;
      if (status === 401 || status === 403) {
        localStorage.removeItem('token');
        return Promise.reject();
      }
      return Promise.resolve();
    },
    getPermissions: () => Promise.resolve(),
  };
  