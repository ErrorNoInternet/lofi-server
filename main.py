import os
import pafy
import time
import asyncio
import requests
import websockets

played = {}; port = 8080; video = None
environmentPort = os.getenv("PORT")
if environmentPort != None:
    port = int(environmentPort)
videoURL = "https://www.youtube.com/watch?v=5qap5aO4i9A"

def updateVideo():
    while True:
        video = pafy.new(videoURL); time.sleep(2)

async def handleClient(websocket, path):
    print("Handling new connection..."); played[path] = []
    while True:
        while True:
            try:
                streamURL = video.streams[0].url
                playlistData = requests.get(streamURL).text.replace("\n", "")
                break
            except:
                print("Failed to fetch video, retrying...")
                continue
        playlists = playlistData.split("#EXTINF:5.0,"); playlists = playlists[1:]
        for url in playlists:
            index = 64
            while True:
                id = url.split("/")[index]
                try:
                    id = int(id); break
                except:
                    index += 1; continue
            if id not in played[path]:
                played[path].append(id)
                streamData = requests.get(url).content
                print("Sending segment to client...")
                await websocket.send(streamData); await websocket.recv()
        time.sleep(1)

serverThread = websockets.serve(handleClient, "0.0.0.0", port)
asyncio.get_event_loop().run_until_complete(serverThread)
print("Starting server..."); asyncio.get_event_loop().run_forever()

