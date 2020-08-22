"""

--- Exercise statement: N°20 - Lock/RLock (multiprocessing)

Escriba un servidor tcp que atienda un puerto pasado por argumento (-p en getopt), y
reciba los siguientes comandos: ABRIR, CERRAR, AGREGAR, y LEER, por parte de los clientes.

Si el cliente envía un comando ABRIR, el servidor deberá solicitarle un nombre de archivo.
Si el cliente envía un comando "AGREGAR" el servidor deberá solicitarle una cadena de texto
para agregar al final del archivo.
Si el cliente envía un comando "LEER" el servidor le deberá enviar al cliente el
contenido del archivo.
Si el cliente envía un comando "CERRAR" el servidor deberá cerrar el archivo y cerrar
la comunicación con el cliente.
El servidor deberá poder mantener conexiones en simultáneo con varios clientes mediante
un sistema multiproceso.
Deberá controlar el acceso concurrente en la escritura al archivo, de modo que no se
sobreescriban las escrituras de dos clientes en el mismo instante de tiempo.

tag: sock_lock

"""

import multiprocessing
import getopt
import sys
import socket
from ctypes import c_char_p


def send_message(client_sock, message):
    client_sock.send(message.encode())


def telnet_shell(client_sock, address, l):
    manager = multiprocessing.Manager()

    print(f"\nGot a connection from {str(address)}.")

    file_route = manager.Value(c_char_p, "/tmp/file.txt")

    while True:
        send_message(client_sock, "\nComands:\n - OPEN\n - ADD\n - READ\n - CLOSE\n\nOption: ")

        response = client_sock.recv(1024)

        if response.decode() == "OPEN\r\n":
            send_message(client_sock, "\nEnter file source: ")
            reply = client_sock.recv(1024)
            file_route.value = reply.decode()
            l.acquire()
            with open(file_route.value, "w") as file:
                file.writelines("")
                file.close()
            l.release()

        elif response.decode() == "ADD\r\n":
            send_message(client_sock, "\nEnter string to append: ")
            reply = client_sock.recv(1024)
            l.acquire()
            with open(file_route.value, "a") as file:
                file.write(reply.decode())
                file.close()
            l.release()

        elif response.decode() == "READ\r\n":
            l.acquire()
            with open(file_route.value, "r") as file:
                lines = file.readlines()
                file.close()
            l.release()
            message = "\nFile content: \n"
            for line in lines:
                message = message + line
            send_message(client_sock, message)
        elif response.decode() == "CLOSE\r\n":
            send_message(client_sock, "Closing file...")
            l.acquire()
            file = open(file_route.value, "r")
            file.close()
            l.release()
            break
        else:
            message = "\nNot a valid command. Exiting..."
            client_sock.send(message.encode())
            break
    sys.exit(0)



def start_stream_socket(server_port):
    host = ""

    lock = multiprocessing.Lock()

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print("Failed to create socket")
        sys.exit()

    server.bind((host, int(server_port)))
    server.listen(5)

    while True:
        client, addr = server.accept()
        client_shell = multiprocessing.Process(target=shell, args=(client, addr, lock))
        client_shell.start()
        client_shell.join()
        client.close()


if __name__ == '__main__':
    port = 0

    if len(sys.argv[1:]) <= 1:
        print("Usage:\n server -> python ex20.py -p <port> \n client -> telnet 0.0.0.0 <port>")
    else:
        option, value = getopt.getopt(sys.argv[1:], "p:")
        for opt, val in option:
            if opt == "-p":
                port = val

        start_stream_socket(port)
