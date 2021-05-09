import pyaudio
import time
import sys

# 一帧的宽度
WIDTH = 2
# 发声的通道数
CHANNELS = 1
# 频率
RATE = 8000

total = 0

FRAMES_PER_BUFFER = 32

class audio:
    def __init__(self, send=False, recv=False, recv_buff=[]):
        self.last_data = (b'\x00\x00'*FRAMES_PER_BUFFER, pyaudio.paContinue)
        self.SEND_BUFFER = []
        self.RECV_BUFFER = recv_buff
        self.p = pyaudio.PyAudio()
        self.issend = send
        self.isrecv = recv
        # self.last_data = None
        self.time = time.time()
        if send:
            self.sstream = self.p.open(format=self.p.get_format_from_width(WIDTH),
                                       channels=CHANNELS,
                                       rate=RATE,
                                       input=True,
                                       output=False,
                                       frames_per_buffer=FRAMES_PER_BUFFER,
                                       stream_callback=self.scallback)
        if recv:
            self.dstream = self.p.open(format=self.p.get_format_from_width(WIDTH),
                                       channels=CHANNELS,
                                       rate=RATE,
                                       input=False,
                                       output=True,
                                       frames_per_buffer=FRAMES_PER_BUFFER,
                                       stream_callback=self.dcallback)

    def open_audio(self):
        if self.issend:
            self.sstream.start_stream()
        if self.isrecv:
            self.dstream.start_stream()
            self.time = time.time()

    def close_audio(self):
        if self.issend:
            self.sstream.stop_stream()
            # self.sstream.close()
        if self.isrecv:
            self.dstream.stop_stream()
            # self.dstream.close()

        # self.p.terminate()

    def scallback(self, in_data, frame_count, time_info, status):
        self.SEND_BUFFER.append((in_data, time.time()))
        #print('S:', len(self.SEND_BUFFER))
        # print('sdasdasdsadada')
        if len(self.SEND_BUFFER) > 500:
            self.SEND_BUFFER.clear()
        return (in_data, pyaudio.paContinue)

    def dcallback(self, in_data, frame_count, time_info, status):
        # print('dcallback')
        if self.RECV_BUFFER:
            self.time = time.time()
            data = self.RECV_BUFFER.pop(0)
            # print(data)
            # self.last_data = data
        else:
            data = self.last_data
        # print('R:', len(self.RECV_BUFFER))
        return (data[0], pyaudio.paContinue)


if __name__ == '__main__':
    a = audio(True, True)
    a.open_audio()
    a.open_audio()

    while a.sstream.is_active():
        # time.sleep(0.01)
        print(a.dstream.is_active())
        if a.SEND_BUFFER:
            a.RECV_BUFFER.append(a.SEND_BUFFER.pop(0))
        # break
    a.close_audio()
