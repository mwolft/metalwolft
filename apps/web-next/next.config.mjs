/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "res.cloudinary.com"
      }
    ]
  },
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
