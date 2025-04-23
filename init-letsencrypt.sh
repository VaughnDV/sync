#!/bin/bash

domains=(rpi.vaughndv.com)
email="vaughndevilliers@gmail.com" # Adding a valid address is strongly recommended
staging=0 # Set to 1 if you're testing your setup to avoid hitting request limits

data_path="./ssl"
rsa_key_size=4096

if [ -d "$data_path" ]; then
  read -p "Existing data found for $domains. Continue and replace existing certificate? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

# Create necessary directories
mkdir -p "$data_path/conf/live/$domains"
mkdir -p "$data_path/conf/archive/$domains"
mkdir -p "$data_path/conf/renewal"
mkdir -p "./docker/nginx/letsencrypt"

if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  mkdir -p "$data_path/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo
fi

# Stop any running containers
echo "### Stopping any running containers ..."
docker-compose down
echo

# Start all services
echo "### Starting all services ..."
docker-compose up -d
echo

# Wait for services to start
echo "### Waiting for services to start ..."
sleep 10

# Test the challenge file
echo "### Testing challenge file ..."
mkdir -p ./docker/nginx/letsencrypt/.well-known/acme-challenge
echo "test" > ./docker/nginx/letsencrypt/.well-known/acme-challenge/test
curl -I http://rpi.vaughndv.com/.well-known/acme-challenge/test
rm -f ./docker/nginx/letsencrypt/.well-known/acme-challenge/test
echo

echo "### Requesting Let's Encrypt certificate for $domains ..."
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Select appropriate email arg
case "$email" in
  "") email_arg="--register-unsafely-without-email" ;;
  *) email_arg="--email $email" ;;
esac

# Enable staging mode if needed
if [ $staging != "0" ]; then staging_arg="--staging"; fi

# Request the certificate
docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $email_arg \
    $domain_args \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot
echo

# Stop all services
echo "### Stopping all services ..."
docker-compose down
echo

# Start all services with SSL configuration
echo "### Starting all services with SSL configuration ..."
docker-compose up -d
echo

echo "### Done! Your certificates should now be installed and nginx should be running with SSL."

echo "### Updating nginx configuration for SSL ..."
# Update nginx configuration to use SSL
cat > docker/nginx/nginx.conf << 'EOL'
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name rpi.vaughndv.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name rpi.vaughndv.com;

    ssl_certificate /etc/letsencrypt/live/rpi.vaughndv.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rpi.vaughndv.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

    location /static/ {
        alias /app/static/;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
EOL

echo "### Reloading nginx with SSL configuration ..."
docker-compose up --force-recreate -d nginx 