from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.responses import HTMLResponse
from project1.api.websockets.manager import manager
import aio_pika
from aio_pika.abc import AbstractMessage 
from project1.dependencies.dependencies import get_channel
from aio_pika import Message, DeliveryMode
import sys

router = APIRouter(
    responses={404: {"detail": "Not found"}},
)

@router.post("/currency")
async def currency(message: str, channel: aio_pika.Channel = Depends(get_channel) ):
    
    #await manager.broadcast(f"1$ is currently:{message}")
    exchange = await channel.get_exchange(name = "currency", ensure = False)
    message_body = message.encode()
    message = Message(
            message_body,
            delivery_mode=DeliveryMode.PERSISTENT,
        ) 
    await exchange.publish(message,routing_key="*")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"You wrote: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client left the chat")
    
