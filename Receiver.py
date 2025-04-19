import socket
import random

class Receiver:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)  # 最大连接数为1
        self.client_sock = None
        self.client_addr = None
        self.expected_checksum = 0
        self.number = -1
        self.frame_text = ''

    def start(self):
        print(f"接收方正在监听 {self.host}:{self.port}...")
        self.client_sock, self.client_addr = self.sock.accept()  # 等待客户端连接
        print(f"与客户端 {self.client_addr} 建立连接。")

        while True:
            data = self.client_sock.recv(1024)  # 接收数据帧
            if not data:
                print("传输结束")
                break  # 如果没有数据，退出循环

            frame = self.parse_frame(data.decode())
            if frame:
                print(f"--当前待接收的帧序号为: {(self.number+1)%8} ")
                is_end = self.receive_frame(frame)
                if is_end == 1:
                    print("传输结束")
                    break

    def parse_frame(self, data):
        """解析数据帧"""
        try:
            num, data, checksum = data.split("|")
            num = int(num)
            checksum = int(checksum)
            return {"num": num, "data": data, "checksum": checksum}
        except ValueError:
            print("数据帧格式错误!")
            return None

    def receive_frame(self, frame):
        """接收数据帧并处理"""
        print(f"\t接收到帧:序号 = {frame['num']} 数据 = {frame['data']}, 校验和 = {frame['checksum']}")
        is_end = 0
        # 校验数据帧的校验和是否正确
        if frame["num"]==(self.number + 1) % 8: #判断序号
            if self.check_checksum(frame): #判断校验和
                print(f"\t帧校验通过，准备发送ACK: frame {frame['num']}")
                self.send_ack(frame)
                self.upload_data(frame["data"])
                self.number = (self.number + 1)%8
                if frame["data"]!="--end/":
                    self.frame_text += frame["data"]
                else:
                    is_end = 1
            else:
                print(f"\t帧损坏，丢弃! 校验和错误: {frame['checksum']} != {sum(ord(c) for c in frame['data']) % 256}")
        else:
            print(f"\t帧次序错误，丢弃! 该帧不是frame{self.number+1}")
        return is_end

    def check_checksum(self, frame):
        """校验数据帧的校验和是否与期望值一致"""
        return frame["checksum"] == sum(ord(c) for c in frame["data"]) % 256

    def send_ack(self, frame):
        """发送ACK确认接收到的数据帧"""
        print(f"\t发送ACK: {frame['num']}")
        loss = random.random()
        if loss >= 0.1:
            self.client_sock.sendall(f"{frame['num']}".encode())
        elif frame["data"] == "--end/":
            self.client_sock.sendall(f"{frame['num']}".encode())

    def upload_data(self, data):
        """上报接收到的数据到上层应用"""
        print(f"\t上传数据到上层: {data}")

    def frame_text_output(self):
        print("----接收所有帧的解析信息：" + self.frame_text)

if __name__ == "__main__":
    receiver = Receiver(host="127.0.0.1", port=12345)
    receiver.start()
    receiver.frame_text_output()