import asyncio
import time
import pickle
import threading
from socket import *

from . import cv, audio, message

UDP_MESSAGE_FORMAT = message.Message(['sent_from', 'send_to', 'timestamp', 'type', 'text'],
                                     '([0-9]*)\$([0-9]*)\$([0-9\.]*)\$([0-9]*)\$(.*)')
# type: # 0,text, 1,pic  2,video  3,audio   4,request    6438, open_local_video

QUEUE_IDLE_TIME = 0.1  # 队列检查最大等待时间 /s
VIDEO_SHUTDOWN_TIME = 5  # 视频队列为空超时自动关闭
VIDEO_FRAMES_PER_ROUND = 4  # 每个包视频帧的数量
AUDIO_SHUTDOWN_TIME = 5  # 音频队列为空超时自动关闭
AUDIO_FRAMES_PER_ROUND = 5*16  # 每个包音频帧的数量
VIDEO_AUDIO_SEP = 0.1  # 可容忍的音画不同步间隔 /s
REQUEST_LIST = ['online/offline', 'search', 'friend request', 'friend accept', 'friend reject']

bytes_len = 0

class EchoClientProtocol(object):
    def __init__(self, user_id, message, on_con_lost, **kwargs):
        self.message = message  # 建立连接发送的消息
        self.on_con_lost = on_con_lost
        self.transport = None
        self.user_id = user_id  # 当前用户id
        self.network_state = 'ok'  # 'ok' or 'not_ok'

        self.message_queue = kwargs['message_queue'] if 'message_queue' in kwargs else []  # 发送缓冲区
        self.recv_buff = []  # 接收缓冲区
        self.text_buff = kwargs['text_buff'] if 'text_buff' in kwargs else []  # 收到的文本缓冲区
        self.pic_buff = kwargs['pic_buff'] if 'pic_buff' in kwargs else []  # 收到的图片缓冲区
        self.audio_buff = kwargs['audio_buff'] if 'audio_buff' in kwargs else []  # 收到的图片缓冲区
        self.video_buff = kwargs['video_buff'] if 'video_buff' in kwargs else []  # 收到的视频缓冲区
        self.request_recv_buff = kwargs['request_recv_buff'] if 'request_recv_buff' in kwargs else []  # 接收请求结果的缓冲区
        self.outer_func_buff = kwargs['outer_func_buff'] if 'outer_func_buff' in kwargs else []  # 需要调用的外界函数的缓冲区

        self.audio_running_flag = False
        self.audio1 = None
        self.audio2 = None
        self.audio_timestamp = 0
        self.audio_recv_flag = False
        self.audio_ends_flag = False

        self.cv = cv.cv([])  # 用于捕获当前机器的视频
        self.cv2 = cv.cv(self.video_buff)  # 用于显示远端获取的视频
        self.recv_timestamp = 0  # 当前接收的视频的时间戳
        self.video_ends_flag = False
        self.video_buff_bind = True if 'video_buff' in kwargs else False

        self.send_num = 0
        self.recv_num = 0

    def connection_made(self, transport):
        self.transport = transport
        print(self.transport.get_extra_info('socket').getsockname())
        import socket

        self.transport.set_write_buffer_limits(high=0, low=0)
        '''print(self.transport.get_write_buffer_limits())
        print(self.transport.get_extra_info('socket').setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536*2))
        print(self.transport.get_extra_info('socket').setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536*2))
        print(self.transport.get_extra_info('socket').getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF))
        print(self.transport.get_extra_info('socket').getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF))'''
        # print(self.transport.get_write_buffer_limits())

        print(self.user_id, 'send:', self.message)
        self.transport.sendto(self.message.encode())

        # if self.user_id == '1':
        # threading.Thread(target=self.send_message, args=()).start()
        # threading.Thread(target=self.send_audioaa, args=()).start()
        # threading.Thread(target=self.audio1.open_audio, args=()).start()

        # threading.Thread(target=self.start_video, args=('2')).start()
        threading.Thread(target=self.check_network, args=()).start()
        threading.Thread(target=self.check_recv, args=()).start()
        # if self.user_id == '2':
        # threading.Thread(target=self.recv_video, args=()).start()

        # threading.Thread(target=self.send_message, args=()).start()

    def send_audioa(self, target):
        """
        发送音频
        :param target:
        :return:
        """
        try:
            if not self.audio1:
                self.audio1 = audio.audio(send=True)
            self.audio1.open_audio()
        except OSError:  # [Errno -9988] Stream closed
            print("OSError:", self.audio1)
            if not self.audio1:
                self.audio1 = audio.audio(send=True)
            self.audio1.open_audio()
        # print('start audio successfully')
        frames_per_round = AUDIO_FRAMES_PER_ROUND

        while not self.audio_ends_flag:
            time.sleep(QUEUE_IDLE_TIME/(len(self.audio1.SEND_BUFFER) + 1))
            if len(self.audio1.SEND_BUFFER) > frames_per_round:
                # t = self.audio1.SEND_BUFFER.pop(0)
                # print('get one')
                timestamp = self.audio1.SEND_BUFFER[0][1]
                '''self.message_queue.append(UDP_MESSAGE_FORMAT.encode(self.user_id, target, str(t[1]), '3', '').encode()
                                          + t[0])'''
                audio_bin = pickle.dumps([self.audio1.SEND_BUFFER.pop(0) for _ in range(frames_per_round)])
                '''import zlib
                com_data = zlib.compress(audio_bin)
                print(len(audio_bin), len(com_data))'''
                self.message_queue.append(UDP_MESSAGE_FORMAT.encode(self.user_id, target, str(timestamp), '3', '')
                                          .encode() + audio_bin)
                # print('send one')
                # print('audio send', self.audio2)
        # print('send audio end')

    def send_audioaa(self, func_called_when_end=None):
        """
        接收音频
        :return:
        """
        start_time = time.time()
        # if self.user_id == '2':
        while not self.audio_recv_flag:
            if start_time + AUDIO_SHUTDOWN_TIME < time.time():
                if func_called_when_end:
                    if self.audio_ends_flag:
                        return
                    func_called_when_end()
                # self.end_audio()
                return
            time.sleep(0.05)

        while not self.audio_buff:
            if self.audio_ends_flag:
                return
            if start_time + AUDIO_SHUTDOWN_TIME < time.time():
                if func_called_when_end:
                    if self.audio_ends_flag:
                        return
                    func_called_when_end()
                # self.end_audio()
                return
            time.sleep(0.05)
        if not self.audio2:
            self.audio2 = audio.audio(recv=True, recv_buff=self.audio_buff)

        # threading.Thread(target=self.audio2.open_audio, args=()).start()
        # print(self.audio2.time + AUDIO_SHUTDOWN_TIME < time.time())
        self.audio2.open_audio()

        idle_time = QUEUE_IDLE_TIME
        beta = 0.1

        while not self.audio_ends_flag:
            # print('here')
            # time.sleep(0.1)

            idle_time = (1 - beta) * idle_time + beta * QUEUE_IDLE_TIME / (len(self.audio_buff) + 1)
            time.sleep(idle_time)

            try:
                if not self.audio2 or self.audio2.time + AUDIO_SHUTDOWN_TIME < time.time():
                    if func_called_when_end:
                        if self.audio_ends_flag:
                            return
                        func_called_when_end()
                    # self.end_audio()
                    break
            except TypeError:
                if func_called_when_end:
                    if self.audio_ends_flag:
                        return
                    func_called_when_end()
                break
        # print('recv audio end')

        # threading.Thread(target=self.check_recv, args=()).start()

    def end_audio(self):
        """
        结束音频
        :return:
        """
        # print('start')
        self.audio_ends_flag = True
        time.sleep(QUEUE_IDLE_TIME*2)

        # print('start end audio')

        try:
            self.audio1.close_audio()
        except AttributeError:   # 'NoneType' object has no attribute 'close_audio'
            print(self.audio1)

        try:
            self.audio2.close_audio()
        except AttributeError:   # 'NoneType' object has no attribute 'close_audio'
            print(self.audio2)
        # print('midele', self.audio1, self.audio2)

        # 置为初始状态
        # self.audio1 = None
        # self.audio2 = None
        self.audio_timestamp = 0
        self.audio_recv_flag = False

        time.sleep(QUEUE_IDLE_TIME*2)
        # self.audio_buff.clear()
        self.audio_ends_flag = False
        self.audio_running_flag = False
        # print('end end video', self.audio2, self.audio1)

    def start_video(self, target):
        """
        打开本地的摄像头开始传输
        :return:
        """
        self.cv.open_video()
        while not self.video_ends_flag:
            time.sleep(QUEUE_IDLE_TIME / (len(self.cv.send_buffer) + 1))
            # print('send a video photo')
            if self.cv.send_buffer:
                temp = self.cv.send_buffer.pop(0)  # 一个二元组 第一个元素是frame 第二个元素是时间戳
                # self.send_video(temp[0], target, temp[1])  # $$$$$
                self.message_queue.append(UDP_MESSAGE_FORMAT.encode(
                    self.user_id, target, str(temp[1]), '2', '').encode() + temp[0])
            if not self.cv.cap.isOpened():
                break

    def start_video(self, target):
        """
        上面为优化前方法 此处为优化后方法
        优化步骤为：一个包内传n个frame
        :param target:
        :return:
        """
        self.video_buff.clear()
        self.cv.open_video()
        while True:
            frames_per_round = VIDEO_FRAMES_PER_ROUND
            time.sleep(QUEUE_IDLE_TIME / (int(len(self.cv.send_buffer)/frames_per_round) + 1))
            # print('send a video photo')

            if len(self.cv.send_buffer) > frames_per_round:
                temp = []
                for i in range(frames_per_round):
                    temp.append(self.cv.send_buffer.pop(0))
                # self.send_video(temp[0], target, temp[1])  # $$$$$

                self.message_queue.append(UDP_MESSAGE_FORMAT.encode(
                    self.user_id, target, str(temp[0][1]), '2', '').encode() + pickle.dumps(
                    [i[0] for i in temp]
                ))


            if not self.cv.cap.isOpened():
                break
        # print('send video ends')

    def end_video(self):
        """
        关闭当前的摄像头并关闭传输
        :return:
        """
        self.video_ends_flag = True
        time.sleep(QUEUE_IDLE_TIME*2)
        try:
            self.cv.close_video()
        except AttributeError:   # 'NoneType' object has no attribute 'release'
            pass
        try:
            self.cv2.close_screen()
        except AttributeError:   # 'NoneType' object has no attribute 'release'
            pass
        try:
            self.cv2.close_video()
        except AttributeError:   # 'NoneType' object has no attribute 'release'
            pass

        # 重置为初始状态
        self.cv = cv.cv([])  # 用于捕获当前机器的视频
        self.cv2 = cv.cv(self.video_buff)  # 用于显示远端获取的视频
        self.recv_timestamp = 0  # 当前接收的视频的时间戳

        # 清空当前发送缓冲区
        self.video_buff.clear()
        time.sleep(QUEUE_IDLE_TIME*2)
        self.video_ends_flag = False

        # print('end video ends')

    def recv_video(self, func_called_when_overtime=None):
        """
        将视频队列中的东西显示在屏幕上
        :param func_called_when_overtime:
        :return:
        """
        self.recv_timestamp = 0
        # time.sleep(2)
        ok_time = time.time()
        over_time = VIDEO_SHUTDOWN_TIME  # 如果缓冲为空超过10秒

        idle_time = QUEUE_IDLE_TIME
        beta = 0.1

        while not self.video_ends_flag:
            idle_time = (1 - beta) * idle_time + beta*QUEUE_IDLE_TIME/(len(self.video_buff) + 1)
            time.sleep(idle_time)
            if not self.cv2.decode():
                # print("time to close:", time.time() - (ok_time + over_time))
                if ok_time + over_time < time.time():
                    if func_called_when_overtime:
                        func_called_when_overtime()
                    # self.end_video()
                    '''for item in self.message_queue[::-1]:   # 清空将要发送的视频帧
                        if UDP_MESSAGE_FORMAT.get_header_bin(item, b'$')['type'] == '2':
                            self.message_queue.remove(item)'''
                    break
            else:
                ok_time = time.time()
        # print('recv video ends')


    '''def buff2video(self):

        while True:
            time.sleep(1/(len(self.recv_buff) + 1))
            if not self.recv_buff:
                print('nothing')
                continue
            d = UDP_MESSAGE_FORMAT.get_header_bin(self.recv_buff.pop(0), b'$')
            t_timestamp = float(d['timestamp'])
            if t_timestamp < self.recv_timestamp:
                continue
            self.recv_timestamp = t_timestamp
            print(self.recv_timestamp)
            self.video_buff.append(d['text'])'''

    def datagram_received(self, data, addr):
        self.recv_num += 1
        # print(time.time() - float(UDP_MESSAGE_FORMAT.get_header_bin(data, b'$')['timestamp']))

        # print(self.user_id, "received:", data)

        # print(time.time() - float(UDP_MESSAGE_FORMAT.get_header_bin(data, b'$')['timestamp']))

        self.recv_buff.append(data)

    def pause_writing(self):
        print('pause')
        self.network_state = 'not_ok'

    def resume_writing(self):
        print('resume')
        self.network_state = 'ok'

    def error_received(self, exc):
        print(self.user_id, 'Error received:', exc)

    def connection_lost(self, exc):
        print(self.user_id, "Connection closed")
        self.on_con_lost.set_result(True)

    def check_network(self):
        """
        用于发送队列
        检查网络状态，如果缓冲区内容过多，则销毁部分可销毁的发送内容（如音视频流）
        :return:
        """
        while True:
            if self.network_state not in ['ok', 'not_ok']:
                raise ValueError("self.network_state状态不在'ok', 'not_ok'中")
            elif self.network_state == 'not_ok':
                self.eat_queue()
            elif self.network_state == 'ok':
                self.check_queue()

    def check_recv(self):
        """
        用于接收队列
        分发到各个类型的接收队列
        :return:
        """
        while True:
            time.sleep(QUEUE_IDLE_TIME/(len(self.recv_buff) + 1))
            if not self.recv_buff:
                continue

            print('send: ', self.send_num, 'recv:', self.recv_num)

            d = UDP_MESSAGE_FORMAT.get_header_bin(self.recv_buff.pop(0), b'$')
            if d['type'] == '0':  # text
                self.text_buff.append(d)
            elif d['type'] == '1':  # pic
                self.pic_buff.append(d)
            elif d['type'] == '2':  # video
                # self.recv_buff.sort(key=lambda x: float(x['timestamp']))
                t_timestamp = float(d['timestamp'])
                if t_timestamp < self.recv_timestamp or t_timestamp < self.audio_timestamp - VIDEO_AUDIO_SEP:
                    print('video skip')
                    continue
                self.recv_timestamp = t_timestamp
                # self.video_buff.append(d['text'])
                self.video_buff += pickle.loads(d['text'])

            elif d['type'] == '3':  # audio
                t_timestamp = float(d['timestamp'])
                if t_timestamp < self.audio_timestamp or t_timestamp < self.recv_timestamp - VIDEO_AUDIO_SEP:
                    print('audio skip')
                    continue
                self.audio_timestamp = t_timestamp
                # print('self.audio2', self.audio2)
                self.audio_recv_flag = True
                # self.audio_buff.append((d['text'], float(d['timestamp'])))
                print('recv audio from remote')
                self.audio_buff += pickle.loads(d['text'])
                if len(self.audio_buff) > AUDIO_FRAMES_PER_ROUND*4:
                    tmp = self.audio_buff[int(len(self.audio_buff) / 2):]
                    self.audio_buff.clear()
                    self.audio_buff += tmp
                '''print([i[1] for i in self.audio_buff])
                self.audio_buff.sort(key=lambda x: x[1])'''

            elif d['type'] == '4':  # request
                self.request_recv_buff.append(d)


    def check_queue(self):
        """
        检查将要发送的消息队列
        无需调用
        :return:
        """
        # print('check')
        time.sleep(QUEUE_IDLE_TIME/(len(self.message_queue) + 1))
        try:
            tmp = self.message_queue.pop(0)

            global bytes_len
            bytes_len += len(tmp)
            # print('len: {}'.format(bytes_len))

            tmp = UDP_MESSAGE_FORMAT.get_header_bin(tmp, b'$')

            self.send_num += 1

            if tmp['type'] == '0':
                self.send_text(tmp['text'].decode(), tmp['send_to'], float(tmp['timestamp']))
            elif tmp['type'] == '1':
                self.send_picture(tmp[0], tmp[1], float(tmp[2]))
            elif tmp['type'] == '2':
                # print(time.time() - float(tmp['timestamp']))
                self.send_video(tmp['text'], tmp['send_to'], float(tmp['timestamp']))
            elif tmp['type'] == '3':
                self.send_audio(tmp['text'], tmp['send_to'], float(tmp['timestamp']))
            elif tmp['type'] == '4':
                self.send_request(tmp['text'], tmp['send_to'], float(tmp['timestamp']))
            elif tmp['type'] == '6437':  # 开始音频
                # 如果当前已有在运行的audio
                if self.audio_running_flag:
                    print('aaaaaaa')
                    return

                self.audio_running_flag = True
                threading.Thread(target=self.send_audioa, args=[tmp['send_to']]).start()
                # 如果需要调用外部函数
                if not tmp['text'].decode() == 'None':
                    # 找到所需的外部函数
                    for func in self.outer_func_buff:
                        # 如果需要的外部函数名与当前函数的函数名相等
                        if str(func) == tmp['text'].decode():
                            # 传入该函数并开启线程
                            threading.Thread(target=self.send_audioaa, args=[func]).start()
                            # print('recv start')
                            break
                # 如果不需要调用外部函数
                else:
                    threading.Thread(target=self.send_audioaa, args=()).start()

            elif tmp['type'] == '6438':   # 开始视频
                send_video_thread = threading.Thread(target=self.start_video, args=[tmp['send_to']])
                send_video_thread.start()

                # 如果外部不需要获取视频接收缓冲区 则调用cv.decode函数
                if not self.video_buff_bind:
                    # 如果需要调用外部函数
                    if not tmp['text'].decode() == 'None':
                        # 找到所需的外部函数
                        for func in self.outer_func_buff:
                            # 如果需要的外部函数名与当前函数的函数名相等
                            if str(func) == tmp['text'].decode():
                                # 传入该函数并开启线程
                                recv_video_thread = threading.Thread(target=self.recv_video, args=[func])
                                recv_video_thread.start()
                                # print('recv start')
                                break
                    # 如果不需要调用外部函数
                    else:
                        recv_video_thread = threading.Thread(target=self.recv_video, args=[])
                        recv_video_thread.start()
            elif tmp['type'] == '6439':   # 结束视频
                threading.Thread(target=self.end_video, args=()).start()
            elif tmp['type'] == '6440':  # 结束音频
                threading.Thread(target=self.end_audio, args=()).start()
        except IndexError:
            pass

    def eat_queue(self):
        """
        销毁不分当前将要发现送的消息
        无需调用
        :return:
        """
        # print('eat')

        time.sleep(QUEUE_IDLE_TIME / (len(self.message_queue) + 1))
        try:
            tmp = UDP_MESSAGE_FORMAT.get_header_bin(self.message_queue.pop(0), b'$')

            self.send_num += 1

            if tmp['type'] == '0':
                self.send_text(tmp['text'].decode(), tmp['send_to'], float(tmp['timestamp']))
            elif tmp['type'] == '1':
                self.send_picture(tmp[0], tmp[1], float(tmp[2]))
            elif tmp['type'] == '2':
                pass
            elif tmp['type'] == '3':
                pass
            elif tmp['type'] == '4':
                self.send_request(tmp['text'], tmp['send_to'], float(tmp['timestamp']))
            elif tmp['type'] == '6437':  # 开始音频
                threading.Thread(target=self.send_audioa, args=[tmp['send_to']]).start()
                threading.Thread(target=self.send_audioaa, args=()).start()
            elif tmp['type'] == '6438':  # 开始视频
                send_video_thread = threading.Thread(target=self.start_video, args=[tmp['send_to']])
                send_video_thread.start()

                # 如果外部不需要获取视频接收缓冲区 则调用cv.decode函数
                if not self.video_buff_bind:
                    # 如果需要调用外部函数
                    if not tmp['text'].decode() == 'None':
                        # 找到所需的外部函数
                        for func in self.outer_func_buff:
                            # 如果需要的外部函数名与当前函数的函数名相等
                            if str(func) == tmp['text'].decode():
                                # 传入该函数并开启线程
                                recv_video_thread = threading.Thread(target=self.recv_video, args=[func])
                                recv_video_thread.start()
                                print('recv start')
                                break
                    # 如果不需要调用外部函数
                    else:
                        recv_video_thread = threading.Thread(target=self.recv_video, args=[])
                        recv_video_thread.start()
            elif tmp['type'] == '6439':  # 结束视频
                threading.Thread(target=self.end_video, args=()).start()
            elif tmp['type'] == '6440':  # 结束音频
                threading.Thread(target=self.end_audio, args=()).start()
        except IndexError:
            pass

        '''time.sleep(1/(len(self.message_queue) + 1))
        for item in self.message_queue:
            type_ = UDP_MESSAGE_FORMAT.get_header_bin(item, b'$')['type']
            if type_ in ['2', '3']:  # 如果为视频或音频，则可以选择删除
                self.message_queue.remove(item)
                break
            elif type_ == '6439':  # 结束视频
                threading.Thread(target=self.end_video, args=()).start()
            elif type_ == '6440':  # 结束音频
                threading.Thread(target=self.end_audio, args=()).start()'''
        '''try:
            self.message_queue = self.message_queue[:int(len(self.message_queue)/2)]
        except IndexError:
            pass'''



    def send_text(self, text, to_user, timestamp):
        """
        发送文字消息
        无需调用
        :param self:
        :param text:
        :param to_user:
        :param timestamp:
        :return:
        """
        assert type(text) == str
        assert type(to_user) == str
        assert type(timestamp) == float

        self.message = UDP_MESSAGE_FORMAT.encode(self.user_id, to_user, str(timestamp), '0', text)  # 0表示文本类型

        print(self.user_id, 'send:', self.message)
        self.transport.sendto(self.message.encode())

    def send_picture(self, path, to_user, timestamp):
        """
        发送图片消息
        无需调用
        :param self:
        :param path:
        :param to_user:
        :param timestamp:
        :return:
        """
        assert type(path) == str
        assert type(to_user) == str
        assert type(timestamp) == float

        try:
            with open(path, 'rb') as f:
                image_bin = f.read()
        except:
            raise FileNotFoundError('图片读取错误')

        message_head = UDP_MESSAGE_FORMAT.encode(self.user_id, to_user, str(timestamp), '1', '')  # 1表示图片类型

        self.message = message_head.encode() + image_bin

        print(self.user_id, 'send a picture.')
        self.transport.sendto(self.message)

    def send_video(self, video, to_user, timestamp):
        """
        发送视频消息
        无需调用
        :param self:
        :param video:
        :param to_user:
        :param timestamp:
        :return:
        """
        assert type(video) == bytes
        assert type(to_user) == str
        assert type(timestamp) == float

        self.message = UDP_MESSAGE_FORMAT.encode(self.user_id, to_user, str(timestamp), '2', '')
        print(self.user_id, 'send a frame.')
        self.transport.sendto(self.message.encode() + video)

    def send_audio(self, audio, to_user, timestamp):
        """
        发送音频消息
        无需调用
        :param self:
        :param audio:
        :param to_user:
        :param timestamp:
        :return:
        """
        assert type(audio) == bytes
        assert type(to_user) == str
        assert type(timestamp) == float

        self.message = UDP_MESSAGE_FORMAT.encode(self.user_id, to_user, str(timestamp), '3', '')
        # print(self.user_id, 'send a audio.')
        self.transport.sendto(self.message.encode() + audio)

    def send_request(self, request, to_user, timestamp):
        """
        发送请求
        无需调用
        :param request: online/offline, search
        :param to_user:
        :param timestamp:
        :return:
        """
        # assert request in REQUEST_LIST
        assert type(to_user) == str
        assert type(timestamp) == float
        if type(request) == bytes:
            self.message = UDP_MESSAGE_FORMAT.encode(self.user_id, to_user, str(timestamp), '4', '').encode() + request
        elif type(request) == str:
            self.message = UDP_MESSAGE_FORMAT.encode(self.user_id, to_user, str(timestamp), '4', request).encode()

        print(self.user_id, 'send request:', self.message)
        self.transport.sendto(self.message)


