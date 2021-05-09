from Database import DBOperate
import random
import psycopg2
import pickle
from datetime import datetime


def getIP():
    return ''


class User:  # 用户类
    def __init__(self):
        self.id = 0  # 用户唯一ID int
        self.name = 'name'  # 昵称      char(20)
        self.password = 'password'  # 密码      char(20)
        self.sex = 'sex'  # 性别      '男'  '女'  ‘保密'  三选一
        self.address = 'address'  # 现地址      char(100)
        self.hometown = 'hometown'  # 故乡      char(100)
        self.occupation = 'occupation'  # 职业  char(30)
        self.birthday = 'birthday'  # 生日      DATE对象
        self.introduction = 'introduction'  # 介绍      char(500)
        self.friends = []  # 好友列表   由用户ID组成的列表
        self.groups = []  # 群组列表 由群ID组成的列表
        self.ip = ''  # 登录ip地址
        self.head = None

    def getinfo(self):
        infolist = {'id': self.id, 'name': self.name, 'password': self.password, 'sex': self.sex,
                    'address': self.address, 'hometown': self.hometown,
                    'occupation': self.occupation, 'birthday': self.birthday, 'introduction': self.introduction,
                    'friends': self.friends, 'group': self.groups, 'head': self.head}
        return infolist

    def register(self, id, name, password, sex='保密', address=' ', hometown=' ', occupation=' ', birthday='1970-1-1',
                 introduction=' ', head=b''):  # 新用户注册，返回id
        Opt = DBOperate()
        head = psycopg2.Binary(head)
        # id = random.randint(100000, 1000000000)
        try:
            if Opt.us_insert(uid=id,
                             upassword=password,
                             uname=name,
                             usex=sex,
                             uhometown=hometown,
                             uoccupation=occupation,
                             ubirthday=birthday,
                             uintroduction=introduction,
                             uaddress=address,
                             uhead=head) != 'OK':
                return '重复'
                # id = random.randint(100000, 1000000000)
            Opt.commit()
            Opt.close()
            self.id = id
            self.name = name
            self.password = password
            self.sex = sex
            self.address = address
            self.birthday = birthday
            self.introduction = introduction
            self.hometown = hometown
            self.occupation = occupation
            self.friends = []
            self.groups = []
            self.ip = getIP()
            self.head = head
            return id
        except Exception:
            return -1

    def existence(self, id):  # 使用现成账号初始化对象
        Opt = DBOperate()
        info = Opt.us_query(uid=id)
        if not info:
            print('用户ID错误!')
            return 'Error'
        self.id = id
        self.name = info[0][1]
        self.password = info[0][2]
        self.sex = info[0][3]
        self.address = info[0][4]
        self.hometown = info[0][5]
        self.occupation = info[0][6]
        self.birthday = info[0][7]
        self.introduction = info[0][8]
        self.friends = Opt.get_friends_info(uid=id)
        if self.friends is None:  # 避免空列表以出现错误
            self.friends = []
        self.groups = Opt.get_groups(uid=id)
        if self.groups is None:
            self.groups = []
        self.ip = getIP()
        if info[0][9]:
            self.head = bytes(info[0][9])
        else:
            self.head = b''
        Opt.close()
        return 'OK'

    def login(self, password):  # 登陆校对账号密码，返回True或False
        Opt = DBOperate()
        info = Opt.us_query(uid=self.id)
        Opt.close()
        try:
            if password == info[0][2]:
                return True
            else:
                return False
        except:
            return False

    def modify_password(self, password):  # 修改密码
        self.password = password
        # 提交至数据库
        Opt = DBOperate()
        Opt.us_modify(self.id, mode=0, upassword=password)
        Opt.commit()
        Opt.close()

    def modify_info(self, name, sex, address, hometown, occupation, birthday, introduction):  # 修改个人信息
        self.name = name
        self.sex = sex
        self.address = address
        self.birthday = birthday
        self.introduction = introduction
        self.hometown = hometown
        self.occupation = occupation
        self.friends = []
        self.groups = []
        # 提交至数据库
        Opt = DBOperate()
        Opt.us_modify(uid=self.id,
                      mode=1,
                      uname=name,
                      usex=sex,
                      uaddress=address,
                      uhometown=hometown,
                      uoccupation=occupation,
                      ubirthday=birthday,
                      uintroduction=introduction)
        Opt.commit()
        Opt.close()

    def modify_head(self, photo):
        photo = psycopg2.Binary(photo)  # 转为二进制流
        self.head = photo
        Opt = DBOperate()
        Opt.us_modify(uid=self.id, mode=2, uhead=photo)
        Opt.commit()
        Opt.close()

    def add_friends(self, fid):  # 根据id添加好友
        Opt = DBOperate()
        id = random.randint(1000, 1000000000)
        if not Opt.isfriend(fone=self.id, ftwo=fid):
            while Opt.fr_insert(id, fone=self.id, ftwo=fid) != 'OK':
                id = random.randint(1000, 1000000000)
        else:
            print('已经是好友，无需添加')
            return 'Error'
        Opt.commit()
        self.friends = Opt.get_friends_info(uid=self.id)
        if self.friends is None:
            self.friends = []
        Opt.close()
        return 'OK'

    def delete_friends(self, fid):  # 删除好友
        Opt = DBOperate()
        if not Opt.isfriend(fone=self.id, ftwo=fid):
            print('你们尚未成为好友')
            return 'Error'
        else:
            Opt.fr_delete(self.id, fid)
        Opt.commit()
        self.friends = Opt.get_friends_info(uid=self.id)
        if self.friends is None:
            self.friends = []
        Opt.close()
        return 'OK'

    # 群
    def create_groups(self, name, address='', introduction=''):  # 创建群，返回群ID
        Opt = DBOperate()
        gid = random.randint(10000, 100000000)
        try:
            while Opt.gr_insert(gid=gid,
                                gleader=self.id,
                                gname=name,
                                gaddress=address,
                                gintroduction=introduction) != 'OK':
                gid = random.randint(10000, 100000000)  # 插入gr表
            Opt.grm_insert(gid, self.id)  # 插入grm表
            self.groups.append((gid,))
            Opt.commit()
            Opt.close()
            return gid
        except Exception:
            return -1

    def add_groups(self, gid):  # 添加群
        Opt = DBOperate()
        if (gid,) in Opt.get_groups(self.id):
            print('你已添加该群，无需重复添加')
            return 'Error'
        else:
            Opt.grm_insert(gid=gid, gmem=self.id)
            self.groups.append((gid,))
            Opt.commit()
            Opt.close()
            return 'OK'

    def exit_groups(self, gid):  # 退出群
        Opt = DBOperate()
        try:
            Opt.grm_delete(gid, gmem=self.id)
        except Exception:
            return 'Error'
        self.groups.remove((gid,))
        Opt.commit()
        Opt.close()
        return 'OK'

    def delete_groups(self, gid):  # 解散群(如果是群主)
        Opt = DBOperate()
        if gid == Opt.get_groups_leader(gid=gid):
            self.groups.remove((gid,))
            Opt.gr_delete(gid=gid)
            Opt.commit()
            Opt.close()
            return 'OK'
        else:
            Opt.close()
            return 'Error'

    # 消息
    def get_message(self, objid, time1='1970-1-1', time2='2100-1-1'):  # 获取与某人的聊天记录
        Opt = DBOperate()
        mes1 = Opt.mes_query(self.id, objid, time1=time1, time2=time2)  # A对B的记录  格式为(时间，记录)
        mes2 = Opt.mes_query(objid, self.id, time1=time1, time2=time2)  # B对A的记录  格式为(时间，记录)
        Opt.close()
        return (mes1, mes2)

    def say_message(self, objid, time, content):  # 给某人发消息, 插入聊天记录到数据库
        Opt = DBOperate()
        try:
            content = psycopg2.Binary(content)
            Opt.mes_insert(uid=self.id, objid=objid, mtime=time, mcontent=content)
            Opt.commit()
            Opt.close()
            return 'OK'
        except Exception:
            Opt.close()
            return 'Error'

    def say_message_group(self, gid, time, content):  # 给某群发消息，插入聊天记录到数据库
        if (gid,) not in self.groups:
            print('尚未添加此群，请先入群再发送消息！')
            return 'Error'
        else:
            Opt = DBOperate()
            try:
                content = psycopg2.Binary(content)
                Opt.mesg_insert(uid=self.id, gid=gid, mtime=time, mcontent=content)
                Opt.commit()
                Opt.close()
                return 'OK'
            except Exception:
                Opt.close()
                return 'Error'


# 静态方法
def get_group_info(gid):  # 获取群信息
    Opt = DBOperate()
    info = Opt.gr_query(gid)
    return info


def get_gmessage_all(gid, time1='1970-1-1', time2='2100-1-1'):  # 获取指定时间的群聊天记录
    Opt = DBOperate()
    mes_g = Opt.mesg_query(gid, time1=time1, time2=time2)
    Opt.close()
    return mes_g


def get_gmessage_user(gid, uid, time1='1970-1-1', time2='2100-1-1'):  # 获取指定时间，指定人的群聊天记录
    Opt = DBOperate()
    mes_g = Opt.mesg_query(gid, uid=uid, time1=time1, time2=time2)
    Opt.close()
    return mes_g


def get_all_users():  # 获取所有用户的id
    Opt = DBOperate()
    data = Opt.us_get_all()
    Opt.close()
    return data


def get_all_groups():  # 获取所有群的id以及它们的群成员
    Opt = DBOperate()
    raw = Opt.gr_get_all()
    Opt.close()
    data = {}
    for item in raw:
        gid = item[0]
        gmem = item[1]
        data.setdefault(gid, []).append(gmem)
    return data


if __name__ == '__main__':
    # pass
    us = User()
    us.existence(19191919)
    print(us.getinfo())
    us.add_friends(250250)
    print(us.getinfo())

    # print(message)
    # info = us.infolist
    # pickle.dumps(info)
    # print(info)
    # print(us.register(2020201, info['name'], info['password'], info['sex'], info['address'], info['hometown'],
    #                    info['occupation'],
    #                    info['birthday'], info['introduction'], info['head']))
    # with open('1.jpg', 'rb') as f:
    #     p = f.read()
    #     print(us.register(id=1911561, name='wocao', password='2020', address='地球', occupation='学生', head=p))
    # print(us.head)

    # us.existence(498431961)
    # id = us.create_groups(name='群')

    # us.add_friends(290739826)
    # with open('picture.jpg', 'rb') as f:
    #     b = f.read()
    # us.say_message_group(gid=64562314, time=datetime.now(), content=b)
    # mes_g = get_gmessage_user(uid=345951881, gid=64562314)
    # with open('picture2.jpg', 'wb') as f:
    #     f.write(mes_g[1][0])
    # with open('picture1.jpg', 'wb') as f:
    #     f.write(mes[0][0][1])

    # mes = us.get_message(507541611)
    # for item in mes[0]:
    #     s = item[1].tolist()
    #     with open('sb.txt', 'ab') as f:
    #         for ele in s:
    #             f.write(ele)

    # print(us.get_message(507541611))
    # us.say_message(210901332, time=datetime.now(), content='feef')
    # print(us.groups)
    # us.existence(662970425)
    # us.add_groups(id)
    # print(get_all_users())
    # print(get_all_groups())
    # us.say_message_group(835784, time=datetime.now(), content='efe')

    # id = us.register(name='新用户', password='rjeaiojtoea')
    # print(id)
    # us.modify_info(
    #     name='KKKK', sex='女', address='地球', hometown='火星', occupation='搬砖人', birthday='1970-1-1', introduction='这是介绍'
    # )
    # us.modify_password('a020109')
