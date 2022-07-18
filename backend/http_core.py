
import re
import socket
import traceback


class Task:

    def __init__(self, test, action):
        self.test = test
        self.action = action

    # def test(self, req_path):
    #     return False
    #
    # def action(self):
    #     pass


class MyServer:

    def __init__(self, port):
        self.socket_1 = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.socket_1.bind(('localhost', port))
        self.socket_1.listen(10)

        self.tasks = []

    # def register(self, condition, action):
    #     self.tasks.append({
    #         'condition': condition,
    #         'action': action,
    #     })

    # def register(self, task):
    #     self.tasks.append(task)

    def register(self, test, action):
        self.tasks.append(Task(test, action))

    def run(self):
        while True:
            try:
                conn, addr = self.socket_1.accept()

                # req = conn.recv(1024).decode()

                # req = ''.encode()
                # while True:
                #     buffer = conn.recv(1024)
                #     if len(buffer) == 0: break
                #     req += buffer
                # req = req.decode()

                # req_parts = req.split('\r\n\r\n')
                # req_HTTP_head = req_parts[0]
                # req_HTTP_payload = req_parts[1] if len(req_parts) >= 2 else ''

                req_b = conn.recv(1024)
                req_b_HTTP_head_len = req_b.find(b'\r\n\r\n')
                req_HTTP_head = req_b[:req_b_HTTP_head_len].decode()
                req_b_content_length_matched = re.match('.*Content-Length: (\\d*)\r\n.*', req_HTTP_head, flags=re.DOTALL)
                if req_b_content_length_matched is not None:
                    req_b_HTTP_payload_len = int(req_b_content_length_matched.group(1))
                    # if (req_b_HTTP_head_len + req_b_HTTP_payload_len + 4 - 1024) > 0:
                    #     req_b += conn.recv(req_b_HTTP_head_len + req_b_HTTP_payload_len + 4 - 1024)
                    # req_b += conn.recv(req_b_HTTP_head_len + req_b_HTTP_payload_len + 4 + 10000)
                    while len(req_b) < (req_b_HTTP_head_len + req_b_HTTP_payload_len + 4):
                        req_b += conn.recv(req_b_HTTP_head_len + req_b_HTTP_payload_len + 4 - len(req_b))
                    req_HTTP_payload = req_b[req_b_HTTP_head_len+4:].decode()
                else:
                    req_b_HTTP_payload_len = 0
                    req_HTTP_payload = ''

                # print('req_b_HTTP_head_len={} , req_b_HTTP_payload_len={} , len(req_b)={}'.format(req_b_HTTP_head_len, req_b_HTTP_payload_len, len(req_b)))
                # print('\033[1;32m{}\033[0m'.format(req_HTTP_head))
                # print('\033[1;34m{}\033[0m'.format(req_HTTP_payload[-10:]))

                req_HTTP_head_lines = req_HTTP_head.split('\r\n')
                req_HTTP_first_line = req_HTTP_head_lines[0]
                print('\nNew request: [' + req_HTTP_first_line + ']')
                if len(req_HTTP_first_line.split(' ')) == 3:
                    req_path = req_HTTP_first_line.split(' ')[1]
                else:
                    # print('Strange first line of request: "{}".'.format(req_HTTP_first_line))
                    # break
                    conn.close()
                    continue

                if req_path == '/shutdown':
                    conn.send(bytes('HTTP/1.0 200 OK\r\n\r\nYou shut down the server.\r\n', 'UTF-8'))
                    conn.close()

                    print('Shut down.')
                    break

                replied = False
                for task in self.tasks:
                    if task.test(req_path, req_HTTP_payload):
                        # print('\033[1;32m{}\033[0m'.format(req))
                        mime, rsp = task.action(req_path, req_HTTP_payload)
                        # print('\033[1;32m{}\033[0m'.format(rsp))
                        conn.send(bytes('HTTP/1.0 200 OK\r\ncontent-type: {};charset=utf-8\r\n\r\n{}'.format(mime, rsp), 'UTF-8'))
                        replied = True
                        break
                if not replied:
                    conn.send(bytes('HTTP/1.0 404 NOT FOUND\r\n\r\n<html><body>Location <span style="color: red">{}</span> not exists!</body></html>\r\n'.format(req_path[1:]), 'UTF-8'))
                    print('\033[1;31m(404!)\033[0m')

                conn.close()
            except:
                traceback.print_exc()
                pass


def load_file(filepath):
    f = open(filepath, 'rb')
    file_bytes = f.read()
    f.close()
    return str(file_bytes, encoding='utf8')


if __name__ == '__main__':
    server_1 = MyServer(10007)

    def test_1(req_path, req_HTTP_payload):
        return req_path == '/'

    def action_1(req_path, req_HTTP_payload):
        return 'text/html', 'hello'

    server_1.register(test_1, action_1)

    server_1.run()  # blocked until shutdown





