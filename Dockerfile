FROM python:3.9

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Set the entrypoint script as the entrypoint for the container
ENTRYPOINT ["./entrypoint.sh"]
