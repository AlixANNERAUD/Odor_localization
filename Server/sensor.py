class SensorClass:
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def update(self, value):
        self.value = value
        
    def get_position(self):
        return self.x, self.y

    def get_value(self):
        return self.value