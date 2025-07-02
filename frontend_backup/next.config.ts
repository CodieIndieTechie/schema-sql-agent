import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    PORT: "3001",
    API_BASE_URL: "http://localhost:8001"
  }
};

export default nextConfig;
