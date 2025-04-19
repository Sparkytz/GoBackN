import socket
import time
import random
import threading

class Frame:
    """帧的数据结构"""
    def __init__(self,num,data,checksum):
        self.num = num #帧的序号
        self.data = data #帧的数据
        self.checksum = checksum #帧的校验和，这里没用书上的算法就用了个简单的表示，可见下面的函数

class Sender:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip #发送方ip
        self.server_port = server_port #发送方端口
        self.buffer = [] #缓冲流，可理解为发送窗口的缓存内容
        self.sent_frames = {}  #发送方已发送的帧，可理解为待处理
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #套接字
        self.sock.connect((self.server_ip, self.server_port)) #同上
        self.N = 8 #2^m
        self.Sw = 7 #控制发送窗口大小
        self.Sf = 0
        self.Sn = 0
        self.num = 0 #类中的帧序号
        self.timer = [None] * self.N #计时器列表，存放所有帧的计时器
        self.lock = threading.Lock()
        self.send_event = threading.Event() #控制start_sender()中的start_send()的暂停和重启

    def data_in_buffer(self, num, data):
        """将数据封装成帧并放入缓存"""
        frame = self.frame_data(num, data) #实例化帧

        if len(self.buffer) >= self.N and 0<=num<=7: #窗口缓冲流循环表示
            self.buffer[num] = frame

        if len(self.buffer) < self.N: #第一轮里将帧逐个放入窗口
            self.buffer.append(frame)

    def send_data(self,num):
        """向接收方发送数据"""
        if (num - self.Sf)%self.N <= (self.Sn-self.Sf)%self.N:
            self.send_frame(num)
        self.Sn = (self.Sn+1)%self.N

    def frame_data(self, num, data):
        """将数据包装成带有校验和的帧"""
        checksum = self.checksum(data)
        frame = Frame(num, data, checksum)
        return frame

    def checksum(self, data):
        """简单的校验和算法：计算字符串中字符的ASCII值之和的模256"""
        return sum(ord(c) for c in data) % 256

    def send_frame(self, num, token=0):
        """发送一帧数据"""
        window = [f"Frame:{(i+self.Sf)%self.N};{self.buffer[(i+self.Sf)%self.N].data}" for i in range(self.Sw)]
        #print(f"当前窗口：Sf={self.Sf}, Sn={self.Sn} ",window) # 可用于显示当前窗口
        if not self.buffer:
            return
        loss = random.random() #丢包率
        err = random.random() #误码率
        frame = self.buffer[num] #取出序号为num的帧
        self.sent_frames[frame.num] = time.time()  # 记录发送时间戳
        print(f"发送帧:序号 = {frame.num}, 数据 = {frame.data}, 校验和 = {frame.checksum}")
        if loss >= 0.2:
            if err >= 0.1:
                self.sock.sendall(f"{frame.num}|{frame.data}|{frame.checksum}".encode())  # 发送正常数据帧
            else:
                self.sock.sendall(f"{frame.num}|{frame.data+'err'}|{frame.checksum}".encode()) #发送有差错的帧
        elif token==1:
            self.sock.sendall(f"{frame.num}|{frame.data}|{frame.checksum}".encode()) #重传必成功
        self.start_timer(num)

    def start_timer(self,num):
        """启动定时器，用于超时重传"""
        if len(self.timer) < self.N: #这个判断因为初始设置了timer的大小，所要没法成立也没什么用，只是也没必要改
            self.timer.append(threading.Timer(3.0, self.timeout))  # 假设3秒超时
            self.timer[num].start()
        else:
            self.timer[num] = None
            self.timer[num] = threading.Timer(3.0, self.timeout)
            self.timer[num].start() #启动序号为num的帧计时器

    def timeout(self):
        """处理超时"""
        print(f"帧 {self.Sf} 超时，重新发送帧！")
        self.send_event.clear()
        for i in range(0,(self.Sn-self.Sf)%self.N):
            self.timer[(i + self.Sf) % self.N].cancel() #从Sf到Sn依次取消计时器
            self.timer[(i + self.Sf) % self.N] = None
        for i in range(self.Sf, (self.Sn if self.Sn > self.Sf else self.Sn + self.N)):#从Sf到Sn依次重发
            if i == self.Sf:
                self.send_frame(i % self.N,1)
            else:
                self.send_frame(i % self.N)
            time.sleep(1)
        self.send_event.set()

    def ack_received(self,data):
        """收到ACK时的处理"""
        ack = self.sock.recv(1024)
        if not ack:
            return -1
        ack_num = int(ack.decode())
        with self.lock:
            if ack_num in self.sent_frames:
                print(f"收到ACK: {ack_num}")
                del self.sent_frames[ack_num]  # 删除发送列表已确认的帧
                for i in range(self.Sf,(ack_num+1 if ack_num + 1 > self.Sf else ack_num + self.N + 1)):
                    if self.timer[i%self.N] is not None:
                        self.timer[i%self.N].cancel()  # 停止定时器
                        self.timer[i%self.N] = None
                    if len(data) > 0 and data[0]!='':
                        self.data_in_buffer(i,data.pop(0))# 更新该序号的帧

                self.Sf = (ack_num + 1) % self.N
                """if self.buffer:
                    self.data_in_buffer(ack_num,f"frame{ack_num}")
                    self.send_frame(self.Sn)  # 发送下一帧
                    self.Sn = (self.Sn+1) % 8"""
                return data
            else:
                return data

# 启动发送方模拟
def start_sender(sender):
    """这里是发送方启动"""
    data = input("请输入要发送的信息：")#输入一串字符自动成帧，我用的是i am a student of school of cyber engineering of xidian university. this is a beautiful school located in xi'an city shaanxi province of china.

    data_list = [data[i:i+8] for i in range(0,len(data),8)]
    data_list.append("--end/")
    #print(data_list)
    l = len(data_list) #所要成帧的数量
    sender.send_event.set()
    for i in range(sender.N):
        sender.data_in_buffer(i,data_list.pop(0))
    def start_send(): #逐个传帧
        for i in range(l):
            #print(i)
            sender.send_event.wait()
            sender.send_data(sender.Sn % sender.N)
            time.sleep(1)

    def start_ack(): #逐帧接收ack
        data = data_list
        for i in range(l):
            data = sender.ack_received(data)
            if data == -1:
                break
            time.sleep(1)

    thread1 = threading.Thread(target=start_send) #创建并行线程
    thread2 = threading.Thread(target=start_ack)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()


if __name__ == "__main__":
    sender = Sender(server_ip="127.0.0.1", server_port=12345)
    start_sender(sender)