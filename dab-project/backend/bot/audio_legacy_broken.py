import discord
import queue

class BroadcastSink(discord.sinks.Sink):
    def __init__(self):
        super().__init__()
        self.subscribers = [] # List of queue.Queue

    def add_subscriber(self, q: queue.Queue):
        if q not in self.subscribers:
            self.subscribers.append(q)

    def remove_subscriber(self, q: queue.Queue):
        if q in self.subscribers:
            self.subscribers.remove(q)

    @discord.sinks.core.Filters.container
    def write(self, data, user):
        """Called by Pycord when audio data is received."""
        # Broadcast the PCM data to all subscribers
        for q in self.subscribers:
            try:
                # Using put_nowait to not block the receive loop
                q.put_nowait(data)
            except queue.Full:
                pass

    def cleanup(self):
        self.subscribers.clear()

class BroadcastSource(discord.AudioSource):
    def __init__(self, q: queue.Queue):
        self.q = q

    def read(self) -> bytes:
        """Called by Pycord's voice thread to send audio."""
        try:
            return self.q.get_nowait()
        except queue.Empty:
            # Return silence (20ms of 16-bit 48kHz stereo = 3840 bytes)
            return b'\x00' * 3840

    def is_opus(self) -> bool:
        return False
