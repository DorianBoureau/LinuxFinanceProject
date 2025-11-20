#!/bin/bash

while true; do
  if ! pgrep -f "streamlit" > /dev/null
  then
    echo "Restarting Streamlit..."
    streamlit run app/main.py --server.port 8501
  fi
  sleep 10
done
