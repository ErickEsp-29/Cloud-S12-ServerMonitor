FROM node:18-alpine

LABEL maintainer="erickespinoza <erick-jem@hotmail.com>"
LABEL description="Servicio A - Frontend/Gateway | Monitor de Servidores | S12"

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]