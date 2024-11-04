import asyncio
import websockets
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay

class CallWebRTC:
    def __init__(self):
        self.relay = MediaRelay()
        self.rooms = {}  # Dictionary to store rooms and their users

    async def start_socket(self):
        async with websockets.serve(self.handle_requests, 'localhost', 5000):
            print("WebSocket server listening on ws://localhost:5000")
            await asyncio.Future()

    async def handle_requests(self, websocket, path):
        # Extract room_id and user_id from the path
        _, room_id, user_id = path.strip("/").split("/")
        
        # Create a new room if it doesn't exist
        if room_id not in self.rooms:
            self.rooms[room_id] = {}

        # Initialize PeerConnection for the user and add to the room
        pc = RTCPeerConnection()
        self.rooms[room_id][user_id] = {'websocket': websocket, 'pc': pc}

        # Set up event handlers for the peer connection
        pc.on("connectionstatechange", self.on_connection_state_change(pc, room_id, user_id))
        pc.on("icecandidate", self.on_ice_candidate(pc, websocket))
        pc.on("track", self.on_track(pc))

        try:
            async for message in websocket:
                data = json.loads(message)
                await self.handle_message(data, room_id, user_id, websocket, pc)
        finally:
            await self.cleanup(room_id, user_id)

    def on_connection_state_change(self, pc, room_id, user_id):
        async def handler():
            print(f"Connection state for {user_id} in room {room_id}: {pc.connectionState}")
            if pc.connectionState in ["failed", "closed"]:
                await self.cleanup(room_id, user_id)
        return handler

    def on_ice_candidate(self, pc, websocket):
        async def handler(candidate):
            if candidate:  # Only send valid ICE candidates
                await websocket.send(json.dumps({
                    'type': 'candidate',
                    'candidate': candidate
                }))
        return handler

    def on_track(self, pc):
        async def handler(track):
            print(f"Track received: {track.kind}")
            if track.kind == "video":
                local_video = self.relay.subscribe(track)
                pc.addTrack(local_video)
            elif track.kind == 'audio':
                local_audio=self.relay.subscribe(track=track)
                pc.addTrack(local_audio)
        return handler

    async def handle_offer(self, data, pc, websocket):
        offer_sdp = RTCSessionDescription(sdp=data['sdp'], type=data['type'])
        await pc.setRemoteDescription(offer_sdp)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        await websocket.send(json.dumps({
            'type': 'answer',
            'sdp': pc.localDescription.sdp
        }))

    async def handle_answer(self, data, pc):
        answer_sdp = RTCSessionDescription(sdp=data['sdp'], type=data['type'])
        await pc.setRemoteDescription(answer_sdp)

    async def handle_candidate(self, data, pc):
        candidate = data['candidate']
        await pc.addIceCandidate(candidate)

    async def handle_message(self, data, room_id, user_id, websocket, pc):
        if data['type'] == 'offer':
            await self.handle_offer(data, pc, websocket)
        elif data['type'] == 'answer':
            await self.handle_answer(data, pc)
        elif data['type'] == 'candidate':
            await self.handle_candidate(data, pc)
        elif data['type'] == 'message':
            text_message = data['message']
            await self.broadcast_message(room_id, user_id, text_message)

    async def broadcast_message(self, room_id, user_id, message):
        # Send message to all users in the same room, except the sender
        for other_user_id, info in self.rooms[room_id].items():
            if other_user_id != user_id:  
                await info['websocket'].send(json.dumps({
                    'type': 'text',
                    'user_id': user_id,
                    'message': message
                }))

    async def cleanup(self, room_id, user_id):
        # Remove user from the room and close their PeerConnection
        if room_id in self.rooms and user_id in self.rooms[room_id]:
            pc = self.rooms[room_id][user_id]['pc']
            await pc.close()
            del self.rooms[room_id][user_id]

            # Remove the room if it’s empty
            if not self.rooms[room_id]:
                del self.rooms[room_id]

async def main():
    call = CallWebRTC()
    await call.start_socket()

if __name__ == "__main__":
    asyncio.run(main())
