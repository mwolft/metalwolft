import jsonServerProvider from 'ra-data-json-server';
import { fetchUtils } from 'ra-core';

const httpClient = (url, options = {}) => {
  if (!options.headers) {
    options.headers = new Headers({ Accept: 'application/json' });
  }
  const token = localStorage.getItem('token');
  if (token) {
    options.headers.set('Authorization', `Bearer ${token}`);
  }
  return fetchUtils.fetchJson(url, options);
};

const baseDataProvider = jsonServerProvider(`${process.env.REACT_APP_BACKEND_URL}/api`, httpClient);

const dataProvider = {
  ...baseDataProvider,
  create: (resource, params) => {
    if (resource === 'invoices') {
      // Sobrescribir la ruta para crear facturas manuales
      return httpClient(`${process.env.REACT_APP_BACKEND_URL}/api/manual-invoice`, {
        method: 'POST',
        body: JSON.stringify(params.data),
      }).then(({ json }) => {
        // React Admin espera { data: { id: ... } }
        return { data: json.data };
      });
    }
    return baseDataProvider.create(resource, params);
  },
};

export default dataProvider;
