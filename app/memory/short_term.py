from .base import MemoryBase, MemoryRecord
from collections import deque

class ShortTermMemory(MemoryBase): 
    def __init__(self, context_window: int = 10): 
        self._context_window = context_window
        self._memory = list[str]

    def is_full(self):
        return len(self._memory) == self._context_window
    
    def add(self, record: MemoryRecord): 
        # check if memory is full 
        if self.is_full(): 
            self.trim_memory()
        self._memory.append(record)

    def trim_memory(self):
        current_len = len(self._memory)
        self._memory = self._memory[-current_len: ]
    
    def get_context_str(self):
        return "\n".join(
            record for record in self._memory
        )
    
    def clear(self): 
        self._memory = []
    
    def get_history(self) -> list[str]: 
        return self._memory