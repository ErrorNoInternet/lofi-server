import os
import asyncio
import websockets

async def handleClient(websocket, path):
    await websocket.send("Hello World from Heroku!")

port = 8080
environmentPort = os.getenv("PORT")
if environmentPort != None:
    port = int(environmentPort)

serverThread = websockets.serve(handleClient, "0.0.0.0", port)
asyncio.get_event_loop().run_until_complete(serverThread)
print("Starting server..."); asyncio.get_event_loop().run_forever()

