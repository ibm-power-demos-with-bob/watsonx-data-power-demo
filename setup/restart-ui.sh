#!/bin/bash
fuser -k 3000/tcp 2>/dev/null
sleep 2
cd /home/U8GO7IL/watsonx-data-power-demo/demo-ui
setsid sh -c 'PORT=3000 npm start >> /tmp/demo-ui.log 2>&1' </dev/null &
sleep 6
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://129.40.125.69:3000/
