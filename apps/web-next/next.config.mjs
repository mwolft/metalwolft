/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      {
        source: "/politica-devoluciones",
        destination: "/politica-devolucion",
        permanent: true
      },
      {
        source: "/politica-cambios",
        destination: "/cambios-politica-cookies",
        permanent: true
      },
      {
        source: "/licencia",
        destination: "/license",
        permanent: true
      }
    ];
  }
};

export default nextConfig;
