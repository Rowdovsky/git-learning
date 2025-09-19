import socket

hostname = socket.gethostname()
print(f"Hostname: {hostname}")

IPadd = socket.gethostbyname(hostname)
print(f"IP Address: {IPadd}")