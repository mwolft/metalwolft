/** @type {import('next').NextConfig} */
function getCspApiOrigin() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (!apiUrl) {
    return "http://127.0.0.1:3001";
  }

  try {
    return new URL(apiUrl).origin;
  } catch {
    return "http://127.0.0.1:3001";
  }
}

function buildContentSecurityPolicy() {
  const apiOrigin = getCspApiOrigin();
  const directives = [
    "default-src 'self'",
    "base-uri 'self'",
    "object-src 'none'",
    "form-action 'self'",
    "frame-ancestors 'self'",
    "script-src 'self' 'unsafe-inline' https://js.stripe.com https://*.js.stripe.com https://maps.googleapis.com https://*.paypal.com https://*.paypalobjects.com https://*.venmo.com",
    "style-src 'self' 'unsafe-inline' https://*.paypal.com https://*.paypalobjects.com https://*.venmo.com",
    "img-src 'self' data: blob: https://res.cloudinary.com https://*.stripe.com https://*.paypal.com https://*.paypalobjects.com https://*.venmo.com",
    "font-src 'self' data:",
    `connect-src 'self' ${apiOrigin} https://api.stripe.com https://maps.googleapis.com https://res.cloudinary.com https://*.paypal.com https://*.paypalobjects.com https://*.venmo.com`,
    "frame-src 'self' https://js.stripe.com https://*.js.stripe.com https://hooks.stripe.com https://*.paypal.com https://*.paypalobjects.com https://*.venmo.com",
    "child-src 'self' https://*.paypal.com https://*.paypalobjects.com https://*.venmo.com",
    "media-src 'self' blob: https://res.cloudinary.com"
  ];

  if (process.env.NODE_ENV !== "production") {
    directives[5] += " 'unsafe-eval'";
  }

  return directives.join("; ");
}

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
        source: "/favicon.ico",
        destination: "/icon.png",
        permanent: false
      },
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
  },
  async headers() {
    const headers = [
      {
        key: "Content-Security-Policy",
        value: buildContentSecurityPolicy()
      },
      {
        key: "X-Frame-Options",
        value: "SAMEORIGIN"
      },
      {
        key: "Cross-Origin-Opener-Policy",
        value: "same-origin-allow-popups"
      }
    ];

    if (process.env.NODE_ENV === "production") {
      headers.push({
        key: "Strict-Transport-Security",
        value: "max-age=31536000"
      });
    }

    return [
      {
        source: "/:path*",
        headers
      }
    ];
  }
};

export default nextConfig;
