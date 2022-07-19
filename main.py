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
    global last_played, video_data
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
                if id not in video_data.keys():
                    size = 0
                    for video_data_id in video_data:
                        size += len(video_data[video_data_id])
                    print(f"Downloading {id} ({len(video_data)} segment{'s' if len(video_data) != 1 else ''} in memory, {round(size/1024/1024, 1)} MB)...")
                    stream_data = requests.get(url).content
                    video_data[id] = stream_data

            while len(video_data) > buffer_limit:
                old_id = min(video_data.keys())
                del video_data[old_id]
            new_last_played = dict(last_played)
            for path in last_played:
                if id - last_played[path] > buffer_limit:
                    print(f"Removing {old_id} (dead connection)...")
                    del new_last_played[path]
            last_played = new_last_played
            time.sleep(0.5)
        except Exception as exception:
            print(f"Failed to process stream: {exception}")
            continue

async def handle_client(websocket, path):
    print(f"Handling new connection from {path}...")

    global video_data
    last_played[path] = 0
    if not video_data:
        print(f"Waiting for buffer ({path})...")
        while not video_data:
            await asyncio.sleep(1)

    copy = dict(video_data)
    for id in copy:
        print(f"Sending {id} (buffer) to {path}...")
        last_played[path] = id
        try:
            await websocket.send(copy[id])
            await websocket.recv()
        except Exception as exception:
            print(f"Unable to communicate with {path}: {exception}")
            return
    while True:
        if max(video_data.keys()) > last_played[path]:
            id = last_played[path] + 1
            last_played[path] = id
            print(f"Sending {id} to {path}...")
            try:
                await websocket.send(video_data[id])
                await websocket.recv()
            except Exception as exception:
                print(f"Unable to communicate with {path}: {exception}")
                return
        else:
            await asyncio.sleep(0.5)

async def main():
    async with websockets.serve(handle_client, "0.0.0.0", os.getenv("PORT") if os.getenv("PORT") != None else 8080):
        await asyncio.Future()

print("Starting server...")
threading.Thread(target=update_video).start()
asyncio.run(main())

