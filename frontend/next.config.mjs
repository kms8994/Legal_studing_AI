/** @type {import('next').NextConfig} */
const backendOrigin = process.env.BACKEND_API_ORIGIN ?? "http://127.0.0.1:8000";

const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
