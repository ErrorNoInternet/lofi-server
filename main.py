import os
import pafy
import time
import asyncio
import requests
import threading
import websockets

played = {}
video = None
videoURL = "https://www.youtube.com/watch?v=jfKfPfyJRdk"

def update_video():
    global video
    while True:
        try:
            video = pafy.new(videoURL)
            time.sleep(3)
        except Exception as exception:
            print(exception)
            continue

async def handle_client(websocket, path):
    print("Handling new connection...")
    played[path] = []
    while True:
        while True:
            try:
                streamURL = video.streams[0].url
                playlistData = requests.get(streamURL).text.replace("\n", "")
                break
            except Exception as error:
                print(f"{error}\nFailed to fetch video, retrying...")
                time.sleep(1)
                continue
        playlists = playlistData.split("#EXTINF:5.0,")
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
            if id not in played[path]:
                played[path].append(id)
                streamData = requests.get(url).content
                print("Sending segment to client...")
                await websocket.send(streamData)
                await websocket.recv()
        time.sleep(1)

print("Starting server...")
threading.Thread(target=update_video).start()
server_thread = websockets.serve(handle_client, "0.0.0.0", os.getenv("PORT") if os.getenv("PORT") != None else 8080)
asyncio.get_event_loop().run_until_complete(server_thread)
asyncio.get_event_loop().run_forever()

