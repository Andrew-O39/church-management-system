FROM node:20-alpine

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json /app/package.json
RUN npm install

COPY . /app

EXPOSE 3000

CMD ["npm", "run", "dev"]