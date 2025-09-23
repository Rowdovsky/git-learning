import socket

hostname = socket.gethostname()
print(f"Hostname: {hostname}")

IPadd = socket.gethostbyname(hostname)
print(f"IP Address: {IPadd}")

for i in range(0,10):
    print(f"Count: {i}")

numero_a = int(input("Dame el primer número -> "))
numero_b = int(input("Dame el segundo número -> "))
print(f"La suma del número a más el número b es: {numero_a + numero_b} y la resta de los números es: {numero_a - numero_b}")

print(numero_a * numero_b)