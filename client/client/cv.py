import pickle
import cv2
import threading
import sys
import time

# 临时使用 用于recv窗口显示不出来的情况
TEMP_USE = 0


class cv:
    def __init__(self, buffer):
        self.cap = None
        self.buffer = buffer  # 接受缓冲区
        self.send_buffer = []   # 发送缓冲区
        self.last_frame = None

        global TEMP_USE
        TEMP_USE += 1
        self.temp_use = TEMP_USE
        # print(cv2.getWindowImageRect('recv'))
        # print(cv2.getWindowImageRect('send{}'.format(TEMP_USE)))

    def open_video(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        '''if not self.cap.isOpened():
            self.cap.open()'''
        self.cap.set(3, 160)
        self.cap.set(4, 120)
        t1 = threading.Thread(target=self.encode)
        t1.start()

    def encode(self):
        while True:
            if not self.cap.isOpened():
                break
            success, img = self.cap.read()
            timestamp = time.time()
            if not success:
                img = self.last_frame
            self.last_frame = img

            cv2.imshow('send{}'.format(self.temp_use), cv2.resize(img, (800, 600), interpolation=cv2.INTER_CUBIC))
            # 防止数据丢失>30fps
            k = cv2.waitKey(33)
            if k == 27:
                # 通过esc键退出摄像
                cv2.destroyAllWindows()
                break
            img = cv2.resize(img, (160, 120), interpolation=cv2.INTER_AREA)
            img_encode_array = cv2.imencode(".jpeg", img)[1]
            print(sys.getsizeof(img_encode_array))
            # print(sys.getsizeof(img_encode_array))
            # print(self.cap.get(3))
            # print(self.cap.get(4))
            self.send_buffer.append((pickle.dumps(img_encode_array), timestamp))

    def decode(self):
        if self.buffer:
            img_decode_array = pickle.loads(self.buffer.pop(0))
            img = cv2.imdecode(img_decode_array, cv2.IMREAD_COLOR)
            cv2.imshow("recv{}".format(self.temp_use), cv2.resize(img, (800, 600), interpolation=cv2.INTER_CUBIC))
            cv2.waitKey(int(100/(len(self.buffer) + 1)) + 20)
            return True
        else:
            cv2.waitKey(int(100/(len(self.buffer) + 1)) + 20)
            return False

    def close_video(self):
        print('关闭摄像头')
        cv2.destroyAllWindows()
        self.cap.release()

    def close_screen(self):
        cv2.destroyWindow("recv")


if __name__ == '__main__':
    CV = cv

    start_time = time.time()
    cvv = CV([])
    cv = CV(cvv.send_buffer)
    try:
        cvv.open_video()
    except Exception as e:
        print(e)
        pass

    while time.time() < start_time + 5:
        time.sleep(0.1)
        if cvv.send_buffer:
            cvv.send_buffer[0] = cvv.send_buffer[0][0]
        if cvv.send_buffer:
            cv.decode()
    try:
        cv.close_video()
    except Exception as e:
        print(e)
        pass
    cvv.close_video()
    time.sleep(3)

    start_time = time.time()
    cvv = CV([])
    cv = CV(cvv.send_buffer)
    cvv.open_video()
    while time.time() < start_time + 5:
        time.sleep(0.01)
        if cvv.send_buffer:
            cvv.send_buffer[0] = cvv.send_buffer[0][0]
        if cvv.send_buffer:
            cv.decode()
    try:
        cv.close_video()
    except Exception as e:
        print(e)
        pass
    cvv.close_video()
    time.sleep(3)

    start_time = time.time()
    cvv = CV([])
    cv = CV(cvv.send_buffer)
    cvv.open_video()
    while time.time() < start_time + 5:
        time.sleep(0.01)
        if cvv.send_buffer:
            cvv.send_buffer[0] = cvv.send_buffer[0][0]
        if cvv.send_buffer:
            cv.decode()
    try:
        cv.close_video()
    except Exception as e:
        print(e)
        pass
    cvv.close_video()
    time.sleep(3)

