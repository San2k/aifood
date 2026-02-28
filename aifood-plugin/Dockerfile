FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy built files
COPY dist/ ./dist/
COPY openclaw.plugin.json ./
COPY skills/ ./skills/

# Plugin will be loaded by OpenClaw
CMD ["node", "dist/index.js"]
