FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --include=dev
COPY . .
RUN npm run prisma:generate && npm run build
EXPOSE 8080
CMD ["npm", "run", "start"]
