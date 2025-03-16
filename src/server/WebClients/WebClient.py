class WebClient:
    def __init__(self, websocket, ip, hostname):
        self.websocket = websocket
        self.ip = ip
        self.hostname = hostname

    def __str__(self):
        return f"Client {self.hostname} ({self.ip})"

    