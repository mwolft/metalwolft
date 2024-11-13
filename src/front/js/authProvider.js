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
        console.log("Login successful.");
        localStorage.setItem('token', auth.access_token);
        localStorage.setItem('user', JSON.stringify(auth.results));
      })
      .catch(error => {
        console.error("Login error:", error);
        throw error;
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

    if (token && user && user.is_admin) {
      console.log("User authenticated.");
      return Promise.resolve();
    } else {
      console.warn("User not authenticated or unauthorized.");
      return Promise.reject({ redirectTo: '/login' });
    }
  },
  checkError: (error) => {
    const status = error.status;
    if (status === 401 || status === 403) {
      console.warn("Unauthorized access detected. Logging out.");
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return Promise.reject({ redirectTo: '/login' });
    }
    return Promise.resolve();
  },
  getPermissions: () => {
    const user = JSON.parse(localStorage.getItem('user') || "{}");
    return user.is_admin ? Promise.resolve("admin") : Promise.resolve();
  },
  getIdentity: () => {
    try {
      const user = JSON.parse(localStorage.getItem('user'));
      if (!user || !user.firstname || !user.lastname) {
        throw new Error("User data is incomplete.");
      }
      return Promise.resolve({
        id: user.user_id,
        fullName: `${user.firstname} ${user.lastname}`,
      });
    } catch (error) {
      console.error("Error getting user identity:", error);
      return Promise.reject(error);
    }
  }
};
