# Base image with specified platform
FROM nielsborie/machine-learning-environments

# Install required packages as root
USER root
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential \
    g++ \
    cmake \
    curl

# Install Ollama and Llama 2
# RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python dependencies
RUN pip install \
    flask==2.3.2 \
    flask-cors==3.0.10 \
    groq \
    pymongo

# Set the working directory to /app
WORKDIR /app

# Copy the application code to the container
COPY /RAG_Back/input /app/

# Expose the Flask port
EXPOSE 8090

# Start the Flask server
CMD ["python", "app.py"]
