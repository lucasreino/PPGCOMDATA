/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  transpilePackages: ["@splinetool/react-spline", "@splinetool/runtime"],
};

module.exports = nextConfig;
