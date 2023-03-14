FROM node:18-alpine
WORKDIR /project1
COPY . .
RUN yarn install --production
CMD ["node", "src/index.js"]
EXPOSE 3000