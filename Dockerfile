FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates

# Download and run the UV installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Install Node.js 22.x from NodeSource and globally install Prettier
RUN curl -sL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh && \
    bash nodesource_setup.sh && \
    apt-get install -y nodejs && \
    rm nodesource_setup.sh && \
    node -v && \
    npm -v && \
    npm install -g prettier@3.4.2

# Ensure Node.js binaries are in the PATH
ENV PATH="/usr/local/bin:/root/.local/bin:$PATH"

WORKDIR /app

COPY app.py /app
COPY re.txt /app

# Pre-install uv and requests to satisfy dependencies
RUN pip install --no-cache-dir --break-system-packages uv requests numpy scikit-learn pandas

# Install additional dependencies listed in re.txt, if any
RUN pip install --no-cache-dir --break-system-packages -r re.txt

RUN mkdir -p /data

# Start the application using uv
CMD ["uv", "run", "app.py"]
