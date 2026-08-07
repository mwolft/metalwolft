const ADMIN_TOKEN_STORAGE_KEY = 'mw_admin_token';
const ADMIN_USER_STORAGE_KEY = 'mw_admin_user';

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
        if (!auth?.access_token || !auth?.results?.is_admin) {
          localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
          localStorage.removeItem(ADMIN_USER_STORAGE_KEY);
          throw new Error("Usuario no autorizado para el panel de administracion.");
        }

        localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, auth.access_token);
        localStorage.setItem(ADMIN_USER_STORAGE_KEY, JSON.stringify(auth.results));
      })
      .catch(error => {
        console.error("Login error:", error);
        throw error;
      });
  },
  logout: () => {
    localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
    localStorage.removeItem(ADMIN_USER_STORAGE_KEY);
    return Promise.resolve();
  },
  checkAuth: () => {
    const token = localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY);
    const user = JSON.parse(localStorage.getItem(ADMIN_USER_STORAGE_KEY) || "{}");

    if (token && user && user.is_admin) {
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
      localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
      localStorage.removeItem(ADMIN_USER_STORAGE_KEY);
      return Promise.reject({ redirectTo: '/login' });
    }
    return Promise.resolve();
  },
  getPermissions: () => {
    const user = JSON.parse(localStorage.getItem(ADMIN_USER_STORAGE_KEY) || "{}");
    return user.is_admin ? Promise.resolve("admin") : Promise.resolve();
  },
  getIdentity: () => {
    try {
      const user = JSON.parse(localStorage.getItem(ADMIN_USER_STORAGE_KEY));
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
