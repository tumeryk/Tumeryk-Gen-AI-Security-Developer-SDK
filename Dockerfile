FROM python:3.12

# Set the working directory inside the container
WORKDIR /src

# Copy the current directory contents into the container at /src
COPY . /src

# Expose the port that the app runs on
EXPOSE 8000

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Set environment variables
ENV JWT_SECRET_KEY=abc1234
ENV URL=http://localhost:8000
ENV LOG_DIRECTORY="/src/logs"

# Create the log directory
RUN mkdir -p /src/logs

# Command to run your application
CMD ["python", "main.py"]
