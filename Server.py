import concurrent.futures
import json
import threading
import time
import socket
import string


class TextColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


cache: dict = {}
cache_lock = threading.Lock()
IS_SERVER_RUNNING = False
PORT = 12345


def receive_message(sock: socket.socket) -> string:
    # get a byte from buffer until \n
    data: bytes = b""
    recv: bytes = sock.recv(1)
    while recv != b'\n':
        data += recv
        recv = sock.recv(1)
    return data.decode()


def search_domain(domain: string) -> string:
    # search the domain in the dict
    return cache.get(domain)


def add_domain(domain: string) -> string:
    # lookup the domain and add to dict
    ip = socket.gethostbyname(domain)

    # lock the adding of the dict
    with cache_lock:
        cache[domain] = ip

    return ip


def handle_client(client_sock: socket.socket):
    # processing client request and answering
    wanted_domain = receive_message(client_sock)

    ip = search_domain(wanted_domain)
    time.sleep(5)  # artificial waiting

    if not ip:
        # not in cache
        ip = add_domain(wanted_domain)

    # responding to user
    client_sock.send((ip + '\n').encode())


def save_cache():
    # saving cache as json
    json.dump(cache, open("cache.txt", 'w'))


def load_cache():
    # loading cache as json
    global cache
    cache = json.load(open("cache.txt", "r"))


def run_server():
    # open server socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.settimeout(1)
    server_sock.bind(("", PORT))
    server_sock.listen(10)

    global IS_SERVER_RUNNING

    # threading the calls
    with concurrent.futures.ThreadPoolExecutor() as executor:
        while IS_SERVER_RUNNING:
            try:
                # open a client handler with a new thread
                client_sock, address = server_sock.accept()
                executor.submit(handle_client, client_sock)
            except socket.timeout:
                pass
            except Exception as e:
                raise e

    # the executor wait here for all to finish


def start_server():
    # loading cache
    with cache_lock:
        load_cache()

    # starting server in new thread
    global IS_SERVER_RUNNING
    IS_SERVER_RUNNING = True
    server_thread = threading.Thread(target=run_server, name="server_thread")
    server_thread.start()
    print(f"{TextColors.OKGREEN}server started{TextColors.ENDC}")
    return server_thread


def close_server(server_thread: threading.Thread):
    # saving cache
    with cache_lock:
        save_cache()

    global IS_SERVER_RUNNING

    # if server is not running do nothing
    if not IS_SERVER_RUNNING:
        return

    IS_SERVER_RUNNING = False
    server_thread.join()
    print(f"{TextColors.OKGREEN}server closed{TextColors.ENDC}")


def check_input(message: string):
    # check if user input is correct

    choice = input(message)
    if not choice.isdigit():
        return None

    return int(choice)


def lunch_menu():
    menu_text: string = f"""{TextColors.HEADER}Server menu:{TextColors.ENDC}
    0. print menu again
    1. start server
    2. close server
    3. exit"""

    server_thread: threading.Thread = None

    print(menu_text)
    while True:
        choice = check_input("enter your choice: ")
        match choice:
            case 0:
                print(menu_text)

            case 1:
                server_thread = start_server()

            case 2:
                close_server(server_thread)

            case 3:
                if not IS_SERVER_RUNNING:
                    break
                print(f"{TextColors.WARNING}close server first (press 2){TextColors.ENDC}")

            case _:
                print(f"{TextColors.WARNING}enter a valid input{TextColors.ENDC}")


if __name__ == '__main__':
    lunch_menu()
