# Use an existing image as a base
FROM node:latest

# coping the required application files
COPY . /react_app
WORKDIR /react_app/react_app

# Install the dependencies
RUN npm install

# Expose the port that the app listens on
EXPOSE 9000

# running the spring boot app
CMD ["npm", "run", "dev"]
