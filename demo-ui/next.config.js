/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow Carbon styles to be transpiled
  transpilePackages: ['@carbon/react', '@carbon/ibm-products', '@carbon/icons-react'],
}

module.exports = nextConfig
