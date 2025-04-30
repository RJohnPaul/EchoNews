/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ["tailwindui.com","images.unsplash.com"], // Add allowed external image domains here
  },
  rewrites: async () => {
    return [
      {
        source: "/api/py/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "https://newsai-swc7.onrender.com/api/py/:path*"
            : "/api/",
      },
      {
        source: "/docs",
        destination:
          process.env.NODE_ENV === "development"
            ? "https://newsai-swc7.onrender.com/api/py/docs"
            : "/api/py/docs",
      },
      {
        source: "/openapi.json",
        destination:
          process.env.NODE_ENV === "development"
            ? "https://newsai-swc7.onrender.com/api/py/openapi.json"
            : "/api/py/openapi.json",
      },
    ];
  },
};

module.exports = nextConfig;
