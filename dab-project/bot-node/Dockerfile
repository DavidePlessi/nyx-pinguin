FROM node:20-alpine

# Installa build tools necessari per node-gyp (sodium-native, davey)
RUN apk add --no-cache python3 make g++ ffmpeg libc6-compat

WORKDIR /app

# Copia e installa dipendenze
COPY package*.json ./
RUN npm ci

# Copia sorgenti
COPY index.js cookies.tx[t] ./

# Il bot non espone porte web
CMD ["npm", "start"]
