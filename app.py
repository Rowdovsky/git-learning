import socket

hostname = socket.gethostname()
print(f"Hostname: {hostname}")

IPadd = socket.gethostbyname(hostname)
print(f"IP Address: {IPadd}")

for i in range(0,10)
    print(i