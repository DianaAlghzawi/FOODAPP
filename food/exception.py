class ModelNotFoundException(Exception):
    def __init__(self, name: str, key: str, value: any):
        self.content = f'Model: {name} with {key}:{value} not found'
