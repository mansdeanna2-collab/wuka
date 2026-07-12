# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# npm registry (can be overridden, e.g. https://registry.npmmirror.com for
# hosts with poor connectivity to registry.npmjs.org)
ARG NPM_REGISTRY=https://registry.npmjs.org

# Copy package files
COPY package*.json ./

# Configure npm registry and make network fetches more resilient
RUN npm config set registry "$NPM_REGISTRY" \
    && npm config set fetch-retries 5 \
    && npm config set fetch-retry-mintimeout 20000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && npm config set fetch-timeout 600000

# Install dependencies (include devDependencies so the build tools like vite
# are available even when NODE_ENV=production is set in the build environment).
# Verify vite is actually installed afterwards: on network timeouts npm can
# crash with "Exit handler never called!" but still exit 0, leaving an
# incomplete node_modules that Docker would cache as a "successful" layer.
RUN npm ci --include=dev && node_modules/.bin/vite --version

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80 || exit 1
