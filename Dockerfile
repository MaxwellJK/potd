FROM alpine
MAINTAINER marcofontana.ing@gmail.com

RUN mkdir /app
WORKDIR /app

# RUN apt-get update && apt-get -y install cron
# Install Python
RUN apk add python3 py-pip

# Copy potd-cron file to the cron.d directory
COPY potd-cron /etc/cron.d/potd-cron
 
# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/potd-cron

# Apply cron job
RUN crontab /etc/cron.d/potd-cron
 
# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Copy potd.py file to the app directory
COPY potd.py /app
COPY requirements.txt /app

RUN pip install -r /app/requirements.txt --break-system-packages

RUN mkdir image/

# Run the command on container startup
# CMD crond -b && tail -f /var/log/cron.log
CMD sleep infinity