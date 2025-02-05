# Start the bot service in the background
python3 bot.py &

# Start the API service in the foreground
uvicorn api:app --host 0.0.0.0 --port 10000