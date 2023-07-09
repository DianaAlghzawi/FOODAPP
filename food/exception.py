from uuid import UUID


class ModelNotFoundException(Exception):
    def __init__(self, name: str, key: str, value: UUID):
        self.content = f'Model: {name} with {key}:{value} not found'
