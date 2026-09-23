"""SSE Manager for real-time event streaming"""
import asyncio
from typing import Dict, Set
from collections import defaultdict
import json

from app.services.sse_protocol import TERMINAL_EVENTS


class SSEManager:
    """Server-Sent Events manager"""
    
    def __init__(self):
        # run_id -> set of queues
        self.clients: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()
    
    async def connect(self, run_id: str) -> asyncio.Queue:
        """Create SSE connection and return message queue"""
        queue = asyncio.Queue()
        
        async with self._lock:
            self.clients[run_id].add(queue)
        
        return queue
    
    async def disconnect(self, run_id: str, queue: asyncio.Queue):
        """Disconnect SSE client"""
        async with self._lock:
            self.clients[run_id].discard(queue)
            
            # Clean up if no clients left
            if not self.clients[run_id]:
                del self.clients[run_id]
    
    async def broadcast(self, run_id: str, event: dict):
        """Broadcast event to all clients subscribed to this run"""
        async with self._lock:
            queues = self.clients.get(run_id, set()).copy()
        
        # asyncio.Queue.put_nowait 是同步方法，不能 await
        for queue in queues:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Queue full, drop old message
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except Exception:
                    pass
    
    async def stream_response(self, run_id: str, queue: asyncio.Queue):
        """Generate SSE stream response"""
        try:
            while True:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    queue.get(),
                    timeout=300.0  # 5 minutes timeout
                )
                
                # Format as SSE
                yield f"data: {json.dumps(event)}\n\n"
                
                # Close connection on terminal event
                if event.get("type") in TERMINAL_EVENTS:
                    break
                    
        except asyncio.TimeoutError:
            # Send heartbeat on timeout
            yield f": heartbeat\n\n"
        except Exception as e:
            error_event = {
                "type": "SSE_ERROR",
                "content": {"error": str(e)}
            }
            yield f"data: {json.dumps(error_event)}\n\n"
        finally:
            await self.disconnect(run_id, queue)
