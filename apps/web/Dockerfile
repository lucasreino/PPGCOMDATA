FROM node:18-alpine

WORKDIR /workspace

# Copy dependencies first for faster caching
COPY package.json ./
RUN npm install

# Copy application files
COPY . .

# Expose port 3000
EXPOSE 3000

# Start hot-reload server
CMD ["npm", "run", "dev"]
