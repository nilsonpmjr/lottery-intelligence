import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["loter-ia.tail1cf76f.ts.net"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
