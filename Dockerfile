FROM python:slim

# Install system dependencies for Rust and UV
RUN apt update && apt install -y \
    curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Rust and Cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

# Install UV
RUN pip install uv

WORKDIR /app

# Copy necessary project metadata files first
COPY pyproject.toml requirements.lock README.md ./

# Install dependencies
RUN uv pip install --no-cache --system -r requirements.lock

# Copy the source code after dependencies
COPY src ./src

CMD ["python", "src/code2prompt_mcp/main.py"]
