import os
import time
import asyncio
import requests
import threading
import websockets
try:
    import pafy
except:
    os.system("pip install git+https://github.com/Cupcakus/pafy")
    import pafy

video_url = "https://www.youtube.com/watch?v=jfKfPfyJRdk"
buffer_limit = 100
last_played = {}
video_data = {}

def update_video():
    global video_data
    while True:
        try:
            while True:
                try:
                    video = pafy.new(video_url)
                    stream_url = video.streams[1].url
                    playlist_data = requests.get(stream_url).text.replace("\n", "")
                    break
                except Exception as exception:
                    print(f"Failed to fetch video: {exception}")
                    time.sleep(1)
                    continue
            playlists = playlist_data.split("#EXTINF:5.0,")
            playlists = playlists[1:]
            for url in playlists:
                index = 64
                while True:
                    id = url.split("/")[index]
                    try:
                        id = int(id)
                        break
                    except:
                        index += 1
                        continue
                if len(video_data) > buffer_limit:
                    id = min(video_data.keys())
                    print(f"Removing {id}...")
                    del video_data[id]
                if id not in video_data.keys():
                    print(f"Adding {id}...")
                    stream_data = requests.get(url).content
                    video_data[id] = stream_data
        except Exception as exception:
            print(f"Failed to fetch video: {exception}")
            continue

async def handle_client(websocket, path):
    print(f"Handling new connection from {path}...")

    global video_data
    last_played[path] = 0
    if not video_data:
        print(f"Waiting for buffer ({path})...")
        while not video_data:
            time.sleep(1)

    copy = dict(video_data)
    for id in copy:
        last_played[path] = id
        await websocket.send(copy[id])
        await websocket.recv()
    while True:
        if max(video_data.keys()) > last_played[path]:
            id = max(video_data.keys())
            last_played[path] = id
            print(f"Sending {id} to {path}...")
            await websocket.send(video_data[id])

async def main():
    async with websockets.serve(handle_client, "0.0.0.0", os.getenv("PORT") if os.getenv("PORT") != None else 8080):
        await asyncio.Future()

print("Starting server...")
threading.Thread(target=update_video).start()
asyncio.run(main())

