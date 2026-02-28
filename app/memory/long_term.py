from .base import MemoryBase, MemoryRecord 
import json 
from pathlib import Path

class LongTermMemory(MemoryBase): 
    def __init__(self, save_path: str): 
        self.save_path = save_path
        self._memory: list[MemoryRecord] = []
        
        with open(save_path, "r") as f: 
            current_state = f.read()
            self._memory.append(current_state)

    def save(self): 
        Path(self.save_path).parent.mkdir(parents=True, exist_ok=True)
        records = [
            {
                "id": record.id, 
                "content": record.content
            } for record in self._memory
        ]
        with open(self.save_path, 'a') as f:
            f.write(json.dumps(records))
    
    def add(self, record: MemoryRecord): 
        self._memory.append(record)

    def clear(self):
        self._memory = []
        self.save()
        
    def get_context_str(self): 
        return "\n".join(
            record.content for record in self._memory
        )
        
    def trim_memory(self):
        current_length = len(self._memory)
        self._memory = self._memory[-current_length: ]
        self.save()
        
    def get_history(self) -> list[str]:
        return [record.content for record in self._memory]