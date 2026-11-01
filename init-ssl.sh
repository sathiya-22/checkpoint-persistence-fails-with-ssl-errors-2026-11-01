#!/bin/bash
set -e

# Create certs directory if it doesn't exist
mkdir -p /certs
chmod 700 /certs

# Generate self-signed certificates
openssl genrsa -out /certs/root.key 2048
openssl req -new -x509 -days 3650 -key /certs/root.key -out /certs/root.crt -subj "/CN=root_ca"

openssl genrsa -out /certs/server.key 2048
openssl req -new -key /certs/server.key -out /certs/server.csr -subj "/CN=localhost"
openssl x509 -req -days 3650 -in /certs/server.csr -CA /certs/root.crt -CAkey /certs/root.key -CAcreateserial -out /certs/server.crt

openssl genrsa -out /certs/client.key 2048
openssl req -new -key /certs/client.key -out /certs/client.csr -subj "/CN=client"
openssl x509 -req -days 3650 -in /certs/client.csr -CA /certs/root.crt -CAkey /certs/root.key -CAcreateserial -out /certs/client.crt

chmod 600 /certs/server.key
chmod 600 /certs/client.key

# Configure pg_hba.conf to require SSL and client certificates
cat <<EOF > /certs/pg_hba.conf
hostssl all all 0.0.0.0/0 cert
EOF

# Copy the generated client certs to the host for the Python client
cp /certs/root.crt /certs/client.crt /certs/client.key /certs/server.crt /certs/server.key /certs/server.csr /certs/root.key /certs/root_ca.srl /host_certs/ || true # Copy to host_certs if mounted

echo "SSL certificates generated and pg_hba.conf configured."
# The actual database command in docker-compose.yml will pick up these files.
