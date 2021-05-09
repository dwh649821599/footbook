"""
客户端网络的封装类
用于gui类和槽函数直接调用
"""
import time
import pickle
import asyncio
import threading
from functools import partial

from client.client import ClientNetwork, TCP_MESSAGE_FORMAT, UDP_MESSAGE_FORMAT

QUEUE_CHECK_SEP = 0.1
MAX_QUEUE_CHECK_SEP = 0.5
MAX_UDP_IDLE_TIME = 1
MAX_TCP_CHECK_TIME = 10


class ClientWrapper(object):
    def __init__(self):
        self.client = None
        self.id = None
        self.password = None
        self.send_queue = []
        self.text_recv_queue = []
        self.pic_recv_queue = []
        self.request_recv_queue = []
        self.video_buff = None  # 默认为None，即不关心内部视频调控
        self.outer_func_buff = []

        '''# !!!!!!!!!!!发送请求的函数定义开始!!!!!!!!!!!!!!
        request_list = {
            # 发送加好友请求 只有一个参数target 即目标id 类型为str
            # 查询是否有加好友请求 没有参数
            'add_friend': (False, None, None),

            # 发送加群组请求 只有一个参数target 即目标群组id 类型为str
            'add_group': (False, None, None),
            'create_group': (False, None, None),
            'online_offline': (False, None, None)
        }

        for item in request_list:
            send_request = f'self.send_{item}_request = partial(self.send_request, request_content="{item}", ' \
                f'need_to_recv={request_list[item][0]}, ' \
                f'fuc_called_when_recv={request_list[item][1]}, ' \
                f'recv_content_startswith={request_list[item][2]})'

            exec(send_request)
            check_request = f'self.check_add_friend_request = partial(self.check_certain_type_of_request_response,' \
                            f' text_startswith="{item}")'
            exec(check_request)

        # !!!!!!!!!!!!!!!发送请求的函数定义终止!!!!!!!!!!!!!!!!!!!!!'''

    def bind_video_buff(self, video_buff):
        """
        获取内部视频数据  用于外部界面显示
        :param video_buff:
        :return:
        """
        assert type(video_buff) == list
        self.video_buff = video_buff

    def get_init_info(self):
        """

        :return: 初始化信息
        """
        self.send_request(b'get_user_info', str(self.id), True, self._update_init_info, b'get_user_info')
        # print(self.client.init_personal_info)
        return self.client.init_personal_info

    def _update_init_info(self, info):
        self.client.init_personal_info = pickle.loads(info['text'][len(b'get_user_info'):])
        # print(self.client.init_personal_info)

    def login(self, id_, password, no_thread=False):
        """
        登陆
        :param id_: 用户id str
        :param password: 密码 str
        :param no_thread:
        :return: True or False 是否登陆成功  以及 错误原因 str 两个元素的元组
        """
        self.client = ClientNetwork(id_, password)
        try:
            state = asyncio.run(self.client.tcp_connect(TCP_MESSAGE_FORMAT.encode(id_, password)))
            if not state:
                state = (state, '用户名或密码错误')
            else:   # 登陆成功
                state = (state, str(''))
        except ConnectionRefusedError as e:
            state = (False, str(e))
        except ConnectionError as e:
            state = (False, str(e))
        except OSError:    # OSError: [WinError 121] 信号灯超时时间已到
            state = (False, '服务器连接超时')
        except Exception as e:
            state = (False, str(e))

        if not state[0]:
            try:
                asyncio.run(self.client.tcp_disconnect())
            except RuntimeError:   # Event loop is closed
                pass
            except AttributeError:   # 已经关闭了
                pass

            self.client = None
        else:
            self.id = id_
            self.password = password
            threading.Thread(target=self._udp_connection_keep, args=()).start()
            if not no_thread:
                threading.Thread(target=self._tcp_connection_keep, args=()).start()
        return state

    def logout(self):
        """
        登出
        :return:
        """
        assert self.client, '登陆成功才可以使用logout'
        try:
            asyncio.run(self.client.tcp_disconnect())
        except RuntimeError:  # Event loop is closed
            pass
        self.client = None

    def send_text(self, target, timestamp, text):
        """
        发送文字信息
        :param target: 发送目标id str
        :param timestamp: 时间戳字符串 str
        :param text: 要发的消息 str
        :return:
        """
        assert self.client, '非登陆状态不能发送text'
        self.send_queue.append(UDP_MESSAGE_FORMAT.encode(
            self.id, target, timestamp, '0', text
        ).encode())

    def send_request(self, request_content, target,
                     need_to_recv=False, fuc_called_when_recv=None, recv_content_startswith=None):
        """
        发送请求        并可用于即时接收消息
        :param request_content:    要发送的请求的text部分   str or bytes
        :param target:             发送的目标id     str
        :param need_to_recv:       用于表示是否需要实时接收  如需要 最好开个线程跑该函数  True or False
        :param fuc_called_when_recv:    表示收到回复时要调用的函数 至少有一个参数  为收到回复的字典  其中text字段为bytes
                                        例如{'sent_from': '692370170', 'send_to': '662970425', 'timestamp':
                                        '1619574553.3684475', 'type': '4', 'text': b'offline'}
        :param recv_content_startswith: 表示收到的消息字段的开头   用于标识该回复属于该亲求  str
        :return:
        """
        if need_to_recv:
            assert fuc_called_when_recv
            assert recv_content_startswith

        if type(request_content) == str:
            self.send_queue.append(UDP_MESSAGE_FORMAT.encode(
                self.id, target, str(time.time()), '4', request_content
            ).encode())
        elif type(request_content) == bytes:
            self.send_queue.append(UDP_MESSAGE_FORMAT.encode(
                self.id, target, str(time.time()), '4', ''
            ).encode() + request_content)

        '''print(UDP_MESSAGE_FORMAT.encode(
            self.id, target, str(time.time()), '4', request_content
        ).encode())'''

        if need_to_recv:
            while self.client:
                time.sleep(QUEUE_CHECK_SEP)
                for item in self.request_recv_queue:
                    try:
                        if type(recv_content_startswith) == str:
                            temp = item['text'].decode()
                        elif type(recv_content_startswith) == bytes:
                            temp = item['text']
                        else:
                            continue
                    except UnicodeDecodeError:
                        continue
                    if temp.startswith(recv_content_startswith):
                        self.request_recv_queue.remove(item)   # 删除该request
                        fuc_called_when_recv(item)   # 调用该函数并传一个参数
                        return

    def recv_text_message(self, func_called_when_recv):
        """
        请开线程调用该函数
        :param func_called_when_recv:  为收到一条消息后调用的函数 必须为一个参数 为（send_from, timestamp, text）元组
        :return:
        """
        while self.client:
            time.sleep(QUEUE_CHECK_SEP)
            text = self.check_text_queue()
            if text:
                func_called_when_recv(text)


    def check_text_queue(self):
        """
        无需调用
        ！！！！！ 请定期调用这个函数确认是否有收到消息 ！！！！！

        :return: 如果没有消息返回None 否则返回消息内容 内容有三个部分:发送方id 时间戳 消息内容 三者均为字符串
        """
        if self.text_recv_queue:
            text = self.text_recv_queue.pop(0)
            # text = UDP_MESSAGE_FORMAT.decode(text)
            send_from = text['sent_from']
            timestamp = text['timestamp']
            text = text['text']
            return send_from, timestamp, text
        else:
            return None

    def check_certain_type_of_request_response(self, text_startswith):
        """
        ！！！！！ 请定期调用这个函数确认是否有收到请求 ！！！！！
        查询请求接收队列 是否有特定消息开头的回复
        :param text_startswith: text段的消息头 str or bytes
        :return:  None即为没有 否则返回元组
        """
        response = None
        if type(text_startswith) == str:
            for item in self.request_recv_queue:
                try:
                    temp = item['text'].decode()
                except UnicodeDecodeError:   # 无法解码
                    continue
                if temp.startswith(text_startswith):
                    response = (item['sent_from'], item['timestamp'], item['text'])
                    self.request_recv_queue.remove(item)
                    break
        elif type(text_startswith) == bytes:
            for item in self.request_recv_queue:
                if item['text'].startswith(text_startswith):
                    response = (item['sent_from'], item['timestamp'], item['text'])
                    self.request_recv_queue.remove(item)
                    break
        return response

    @staticmethod
    def sign_in(infolist):
        """
        注册
        :param infolist: example = {'name': nickname, 'password': password, 'sex': sex,
                             'address': address, 'hometown': hometown,
                             'occupation': occupation, 'birthday': birthday,
                             'introduction': intro}
        :return:  二元组   第一位 True or False   第二位 错误原因
        """
        cc = ClientNetwork('', '')
        try:
            infolist_message = asyncio.run(cc.tcp_connect(b'$' + pickle.dumps(infolist)))
            if not infolist_message:
                infolist_message = (infolist_message, '用户名重复')
            else:  # 注册成功
                infolist_message = (infolist_message, '')
        except ConnectionRefusedError as e:
            infolist_message = (False, str(e))
        except ConnectionError as e:
            infolist_message = (False, str(e))

        try:
            asyncio.run(cc.tcp_disconnect())
        except RuntimeError:  # Event loop is closed
            pass
        except AttributeError:  # 已经关闭了
            pass

        return infolist_message

    def open_video(self, target, func_when_overtime=None):
        """
        开启视频通话
        :param target:  目标id str
        :param func_when_overtime:   超时调用的函数  请务必没有参数或全为缺省参数
        :return:
        """
        self.send_queue.append(UDP_MESSAGE_FORMAT.encode(
            self.id, str(target), str(time.time()), '6438', ''
        ).encode() + str(func_when_overtime).encode())
        if func_when_overtime:
            self.outer_func_buff.append(func_when_overtime)
        self.open_audio(target)

    def end_video(self):
        """
        关闭视频通话
        :return:
        """
        self.send_queue.append(UDP_MESSAGE_FORMAT.encode(
            self.id, '', str(time.time()), '6439', 'video_local_ends'
        ).encode())
        self.end_audio()

    def open_audio(self, target, func_when_overtime=None):
        """
        ！！！！！！！！语音通话注意事项！！！！！！！
        1 请在调用end_audio函数之后等待至少2秒再调用open_audio函数 否则可能会出问题

        开启语音通话
        :param target: 目标id  str
        :param func_when_overtime:
        :return:
        """
        self.send_queue.append(UDP_MESSAGE_FORMAT.encode(
            self.id, str(target), str(time.time()), '6437', ''
        ).encode() + str(func_when_overtime).encode())
        if func_when_overtime:
            self.outer_func_buff.append(func_when_overtime)

    def end_audio(self):
        """
        关闭语音通话
        :return:
        """
        self.send_queue.append(UDP_MESSAGE_FORMAT.encode(
            self.id, '', str(time.time()), '6440', 'audio_local_ends'
        ).encode())

    def _tcp_connection_keep(self):
        """
        私有方法 确保TCP连接
        :return:
        """
        def reconnect(response):
            if not response or response['text'].decode().split()[1] == 'offline':
                print("TCP RECONNECT")
                assert self.login(self.id, self.password, no_thread=True)[0], 'TCP重新连接失败'
        while self.client:
            time.sleep(MAX_TCP_CHECK_TIME)
            self.send_request('online/offline', self.id, True, reconnect, 'online/offline ')

    def _udp_connection_keep(self):
        """
        私有方法 建立udp连接
        :return:
        """
        def not_anync_udp(self):
            # 如果需要外部界面获取video
            if type(self.video_buff) == list:
                asyncio.run(self.client.udp_connect(message_queue=self.send_queue,
                                                    text_buff=self.text_recv_queue,
                                                    pic_buff=self.pic_recv_queue,
                                                    request_recv_buff=self.request_recv_queue,
                                                    outer_func_buff=self.outer_func_buff,
                                                    video_buff=self.video_buff))
            else:
                asyncio.run(self.client.udp_connect(message_queue=self.send_queue,
                                                    text_buff=self.text_recv_queue,
                                                    pic_buff=self.pic_recv_queue,
                                                    outer_func_buff=self.outer_func_buff,
                                                    request_recv_buff=self.request_recv_queue))
        check_time = 0
        while self.client:
            if time.time() > check_time + MAX_UDP_IDLE_TIME:
                try:
                    not_anync_udp(self)
                except Exception as e:
                    print('UDP Exception: ', e)
                    check_time = 0
                    continue
                    # self.client = None
                time.sleep(MAX_QUEUE_CHECK_SEP)
                check_time = time.time()
            else:
                time.sleep(MAX_QUEUE_CHECK_SEP)


if __name__ == '__main__':
    def f(a):
        print('f(): ', a)

    def show_something():
        print('something')
    '''c1 = ClientWrapper()
    c1.login("498431961", "aa")'''

    c = ClientWrapper()
    # c.bind_video_buff(video_buff)
    # result = c.login("498431961", "aa")
    result = c.login("2", "2")
    # result = c.login("123123", "123123")
    # print(c.get_init_info())
    print(result)

    '''for _ in range(5):
        c.open_audio("2", show_something)
        time.sleep(50)
        c.end_audio()
        time.sleep(3)'''

    '''while True:
        time.sleep(10)
        c.send_request('online/offline', "662970425", True, f, 'o')
        c.send_text("662970425", str(time.time()), 'text')'''

    '''print(threading.active_count())
    print(threading.enumerate())
    time.sleep(2)
    print(threading.active_count())
    print(threading.enumerate())
    c.open_video("1", show_something)
    time.sleep(1)
    print(threading.active_count())
    print(threading.enumerate())
    time.sleep(12)
    print(threading.active_count())
    print(threading.enumerate())
    time.sleep(5)
    c.end_video()
    time.sleep(3)'''
    # 0.5 553750
    # 0.133 88271
    # 0.066 505557
    # 0.033 369138
    '''for i in range(500):
        time.sleep(0.033)
        c.send_text('1', str(time.time()), f'{i%10}'*8000)

    while True:
        time.sleep(100)'''

    '''c.open_video("2")
    time.sleep(50)
    c.end_video()
    time.sleep(1)'''


    c.open_audio("2", show_something)
    time.sleep(2)
    for i in range(4):
        print(i)
        time.sleep(0.1)
        c.end_audio()
    time.sleep(3)

    c.open_audio("2", show_something)
    time.sleep(5)
    c.end_audio()
    time.sleep(3)

    c.open_audio("2", show_something)
    time.sleep(5)
    c.end_audio()
    time.sleep(1)
    # c.open_video("692370170")




    '''c.send_request('online/offline', target="662970425", need_to_recv=True, fuc_called_when_recv=f,
                   recv_content_startswith='o')
    # c.open_video("662970425")
    c.logout()'''



    '''a = ClientWrapper.sign_in(
        {'name': '1', 'password': '1', 'sex': '1',
         'address': '1', 'hometown': '1',
         'occupation': '1', 'birthday': '1',
         'introduction': '1'}
    )
    print(a)'''
