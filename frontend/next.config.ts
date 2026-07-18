import type { NextConfig } from "next";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Pin the tracing root to this app so a stray parent lockfile doesn't
  // confuse Next's workspace-root inference.
  outputFileTracingRoot: __dirname,
  images: {
    // Allow serving item images straight from the backend's /uploads mount.
    remotePatterns: [
      {
        protocol: "http",
        hostname: "127.0.0.1",
      },
      {
        protocol: "http",
        hostname: "localhost",
      },
    ],
  },
  async rewrites() {
    // Proxy API + uploaded images through Next in dev so the browser hits a
    // single origin (avoids CORS friction). Overridable via NEXT_PUBLIC_API_URL.
    return [
      { source: "/api/:path*", destination: `${apiUrl}/api/:path*` },
      { source: "/uploads/:path*", destination: `${apiUrl}/uploads/:path*` },
    ];
  },
};

export default nextConfig;
