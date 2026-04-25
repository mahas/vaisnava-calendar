#!/bin/bash

cd "$HOME/Documents/Proyectos Web/gcal-moderno/gaurabda-calendar"

lsof -ti :8047 | xargs kill -9 2>/dev/null
lsof -ti :3000 | xargs kill -9 2>/dev/null

python3 server/server.py > /tmp/vaishnava-backend.log 2>&1 &

sleep 3

cd web
python3 -m http.server 3000 > /tmp/vaishnava-frontend.log 2>&1 &

sleep 3

open "http://127.0.0.1:3000/index.html"