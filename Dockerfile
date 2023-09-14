FROM python:3.9

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y curl

COPY . .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Set the entrypoint script as the entrypoint for the container
ENTRYPOINT ["./entrypoint.sh"]
