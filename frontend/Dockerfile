# Dev image for the Vite dev server (hot reload). The browser (on the host)
# talks to the api-gateway directly at VITE_API_BASE; this container only
# serves the app on 5173 — the CORS origin the gateway allows.
FROM node:22-slim
WORKDIR /app
COPY package.json ./
# No lockfile is committed yet; `npm install` resolves the ranges in package.json.
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
