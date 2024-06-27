class SensorClass:
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.value = None
        self.timestamp = None

    def update(self, value, timestamp):
        self.value = value
        self.timestamp = timestamp
        
    def get_position(self):
        return self.x, self.y

    def get_value(self):
        return self.value

    def get_timestamp(self):
        return self.timestamp

    def __str__(self):
        return f"Sensor ({self.x}, {self.y}) :\n - Value {self.value}\n - Last update : {self.timestamp}"