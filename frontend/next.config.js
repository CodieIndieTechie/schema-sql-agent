/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    PORT: "3001",
    API_BASE_URL: "http://localhost:8001"
  }
};

module.exports = nextConfig;
