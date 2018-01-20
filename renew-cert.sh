#!/bin/bash
set -e

EXPIRY_PATH="/home/ec2-user/.cert_expiry"
RENEW=0
FLAGS="--debug"
ONE_DAY_S=86400 # 1 day in seconds.
CERT_LIFESPAN_S=7776000 # 90 days in seconds.
NOW=$(date +%s) # Current time as seconds since epoch.

if [ -e "$EXPIRY_PATH" ]; then
  EXPIRY=$(cat "$EXPIRY_PATH")
  TIME_LEFT_S=$(($EXPIRY - $NOW))
  TIME_LEFT_D=$(echo "scale=2; $TIME_LEFT_S/$ONE_DAY_S" | bc -l)
  if [ "$TIME_LEFT_S" -lt "$ONE_DAY_S" ]; then
    echo "Less than a day ($TIME_LEFT_D) left before expiration. Renewing."
    RENEW=1
  else
    echo "Plenty of time left before expiration ($TIME_LEFT_D days). Not renewing."
  fi
else
  echo "Cert expiration unknown. Attempting forced renewal."
  RENEW=1
  FLAGS="$FLAGS --force-renewal"
fi


if [ "$RENEW" -eq "1" ]; then
  echo "Stopping server ..."
  docker stop nginx
  echo "Renewing certificate ..."
  sudo /home/ec2-user/certbot-auto $FLAGS renew
  echo "Restarting server ..."
  docker start nginx
  echo "Recording cert expiration date ..."
  echo "$(($NOW + $CERT_LIFESPAN_S))" > "$EXPIRY_PATH"
  echo "Done!"
fi
