"""Event emitter for streaming events"""
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Callable
from collections import defaultdict
import json


class EventEmitter:
    """Event emitter for real-time event streaming"""
    
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = defaultdict(list)
        self.event_queue: asyncio.Queue = asyncio.Queue()
    
    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit an event"""
        event = {
            "type": event_type,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data
        }
        
        # Put in queue
        await self.event_queue.put(event)
        
        # Notify listeners
        for listener in self.listeners[event_type]:
            try:
                await listener(event)
            except Exception as e:
                print(f"Error in listener: {e}")
    
    async def stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream events"""
        while True:
            event = await self.event_queue.get()
            yield event
            
            # Stop on end event
            if event.get("type") in ["RUN_END", "RUN_ERROR"]:
                break
    
    def on(self, event_type: str, handler: Callable):
        """Register event listener"""
        self.listeners[event_type].append(handler)
    
    def off(self, event_type: str, handler: Callable):
        """Remove event listener"""
        if handler in self.listeners[event_type]:
            self.listeners[event_type].remove(handler)
    
    async def close(self):
        """Close event emitter"""
        await self.event_queue.put(None)  # Sentinel to stop streaming
