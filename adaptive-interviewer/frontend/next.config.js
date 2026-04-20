/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const backend = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8002";
    return [{ source: "/api/backend/:path*", destination: `${backend}/:path*` }];
  },
};
module.exports = nextConfig;
