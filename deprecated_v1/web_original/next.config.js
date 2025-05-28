/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'development' 
          ? 'http://localhost:8080/api/:path*'
          : '/api/:path*',  // In production, Vercel routes handle this
      },
    ]
  },
}

module.exports = nextConfig