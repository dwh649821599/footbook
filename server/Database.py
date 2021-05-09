import random
from datetime import datetime
import psycopg2


def db_create():  # 创建数据库
    conn = psycopg2.connect(database="footbook", user="postgres", password="admin", host="127.0.0.1", port="5432")
    cur = conn.cursor()
    # 用户信息表
    cur.execute('''CREATE TABLE us
               (UID              INT PRIMARY KEY,
                UNAME            VARCHAR(20) DEFAULT '新用户',
                UPASSWORD        VARCHAR(20) NOT NULL,
                USEX             VARCHAR(5) CHECK (USEX IN('男','女','非二元','保密')) DEFAULT '保密',
                UADDRESS         VARCHAR(100),
                UHOMETOWN        VARCHAR(100),
                UOCCUPATION      VARCHAR(30),
                UBIRTHDAY        DATE DEFAULT '1970-1-1',
                UINTRODUCTION    VARCHAR(500),
                UHEAD            BYTEA                    
                );''')
    # 聊天记录表
    cur.execute('''CREATE TABLE mes
              (UID          INT REFERENCES  us(UID) ON DELETE CASCADE,
               MTIME        TIMESTAMP DEFAULT NOW(),
               OBJID        INT REFERENCES us(UID) ON DELETE CASCADE,
               MCONTENT     BYTEA,
			   PRIMARY  KEY (UID,OBJID,MTIME)
              );''')
    # 群表
    cur.execute('''CREATE TABLE gr
              (GID            INT PRIMARY KEY,
			   GLEADER        INT REFERENCES us(UID) ON DELETE CASCADE NOT NULL,
               GNAME          VARCHAR(30) DEFAULT '新群组',
               GADDRESS       VARCHAR(100),
               GINTRODUCTION   VARCHAR(500)
			   );''')
    # 群聊天记录表
    cur.execute('''CREATE TABLE mes_g
                  (GID          INT REFERENCES gr(GID) ON DELETE CASCADE,
                   UID          INT REFERENCES  us(UID) ON DELETE CASCADE,
                   MTIME        TIMESTAMP DEFAULT NOW(),
                   MCONTENT     BYTEA,
    			   PRIMARY  KEY (GID,UID,MTIME)
                  );''')
    # 好友表
    cur.execute('''CREATE TABLE fr
               (FID            INT PRIMARY KEY,
    			FONE           INT REFERENCES us(UID)ON DELETE CASCADE NOT NULL,
    			FTWO           INT REFERENCES us(UID)ON DELETE CASCADE  NOT NULL,
                FTIME          TIMESTAMP DEFAULT NOW()
    		   );
        ''')
    # 群成员表
    cur.execute('''CREATE TABLE grm
              (GID            INT REFERENCES gr(GID) ON DELETE CASCADE,
			   GMEM           INT REFERENCES us(UID) ON DELETE CASCADE,
			   PRIMARY KEY(GID,GMEM)
			   );
    ''')
    conn.commit()
    conn.close()


def db_delete():  # 删除各表
    conn = psycopg2.connect(database="footbook", user="postgres", password="admin", host="127.0.0.1", port="5432")
    cur = conn.cursor()
    try:
        cur.execute('DROP TABLE us,mes,gr,grm,fr,mes_g')
    except psycopg2.Error as e:
        print(e.pgerror)
    conn.commit()
    conn.close()


def db_us_addhead():  # 给us表增加uhead列
    conn = psycopg2.connect(database="footbook", user="postgres", password="admin", host="127.0.0.1", port="5432")
    cur = conn.cursor()
    try:
        cur.execute('ALTER TABLE us add uhead BYTEA')
    except psycopg2.Error as e:
        print(e.pgerror)
    conn.commit()
    conn.close()


class DBOperate:  # 数据库操作
    def __init__(self):  # Operate类初始化，连接数据库，获取游标
        self.conn = psycopg2.connect(database="footbook", user="postgres", password="admin", host="127.0.0.1",
                                     port="5432")
        self.cur = self.conn.cursor()

    def commit(self):  # 提交事务修改
        self.conn.commit()

    def close(self):  # 关闭数据库
        self.conn.close()

    # us表
    def us_insert(self, uid, upassword, **kwargs):
        # uid和upassword为必填参数，可选参数有uname,usex,uaddress,uhometown,uoccupation,ubirthday,uintroduction,uhead
        # 获取额外参数
        upassword = '\'' + upassword + '\''
        arglist = list(kwargs.keys())
        argnum = len(arglist)
        arg = list(kwargs.values())
        # 给每个参数加入引号以便写SQL
        for i in range(len(arg)):
            if arglist[i] != 'uhead':
                arg[i] = '\'' + str(arg[i]) + '\''
        # 拼装SQL语句
        sql1 = (('INSERT INTO us (uid,upassword,' + argnum * '{},').strip(',') + ') ').format(*arglist)
        sql2 = (('VALUES ({},{},' + argnum * '{},').strip(',') + ')').format(uid, upassword, *arg)
        sql = sql1 + sql2
        # print(sql)
        try:
            self.cur.execute(sql)
            return 'OK'

        except psycopg2.Error as e:
            return 'ERROR'

    def us_delete(self, uid):
        # 根据uid删除用户信息
        sql = ('DELETE FROM us WHERE uid={}'.format(uid))
        try:
            self.cur.execute(sql)
            return 'OK'
        except psycopg2.Error as e:
            print(e.pgerror)
            return 'Error'

    def us_query(self, uid):  # 根据uid查找信息
        sql = ('select * from us where uid={}'.format(uid))
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            return data
        except psycopg2.Error as e:
            print(e.pgerror)

    def us_modify(self, uid, mode, **kwargs):  # uid必填  mode=0 修改密码  mode=1 修改信息  mode=2 修改头像
        # 1模式下可选参数uname,usex,uaddress,uhometown,uoccupation,ubirthday,uintroduction
        arglist = list(kwargs.keys())
        argnum = len(arglist)
        arg = list(kwargs.values())

        # 0模式下参数upassword
        if mode == 0:  # 修改密码 参数为upassword
            try:
                upassword = kwargs['upassword']
                upassword = '\'' + upassword + '\''
                sql = ('UPDATE us SET upassword=' + '{}' + ' WHERE uid=' + '{}').format(upassword, uid)
                try:
                    # print(sql)
                    self.cur.execute(sql)
                    return 'OK'
                except psycopg2.Error as e:
                    print(e.pgerror)
                    return 'Error'
            except Exception:
                print('Argument ' + '\'' + 'upassword' '\'' + ' error!')
                return 'Error'

        elif mode == 1:  # 修改个人信息
            # 给每个参数加引号
            for i in range(len(arg)):
                arg[i] = '\'' + str(arg[i]) + '\''
            exp = []
            for i in range(argnum):
                exp.append(arglist[i] + '=' + arg[i] + ',')
            sql1 = ('UPDATE us SET ' + argnum * '{}').format(*exp)
            sql2 = ' WHERE uid=' + str(uid)
            sql = sql1.strip(',') + sql2
            try:
                # print(sql)
                self.cur.execute(sql)
                return 'OK'
            except psycopg2.Error as e:
                print(e.pgerror)

        # 2模式下参数uhead
        elif mode == 2:  # 修改头像
            # try:
            uhead = kwargs['uhead']
            sql = ('UPDATE us SET uhead=' + '{}' + ' WHERE uid=' + '{}').format(uhead, uid)
            try:
                # print(sql)
                self.cur.execute(sql)
                return 'OK'
            except psycopg2.Error as e:
                print(e.pgerror)
                return 'Error'
            # except Exception:
            # print('Argument ' + '\'' + 'uhead' '\'' + ' error!')
            # return 'Error'

        else:
            print("Argument error:" + str(arglist))
            return 'Error'

    def us_get_all(self):
        sql = 'SELECT uid FROM us'
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            return data
        except psycopg2.Error as e:
            print(e.pgerror)

    # mes表
    def mes_insert(self, uid, objid, mtime, **kwargs):  # 必选参数mid uid mtime 可选参数mcontent
        arglist = list(kwargs.keys())
        argnum = len(arglist)
        arg = list(kwargs.values())
        mtime = '\'' + str(mtime) + '\''
        # 拼装SQL语句
        sql1 = (('INSERT INTO mes (uid,objid,mtime,' + argnum * '{},').strip(',') + ') ').format(*arglist)
        sql2 = (('VALUES ({},{},{},' + argnum * '{},').strip(',') + ')').format(uid, objid, mtime, *arg)
        sql = sql1 + sql2
        try:
            # print(sql)
            self.cur.execute(sql)
            return 'OK'
        except psycopg2.Error as e:
            print(e.pgerror)
            return 'Error'

    def mes_delete(self, uid):
        # 根据uid，删除该用户的所有聊天记录
        sql = 'DELETE FROM mes WHERE uid={}'.format(uid)
        try:
            self.cur.execute(sql)
        except psycopg2.Error as e:
            print(e.pgerror)

    def mes_query(self, uid, objid, **kwargs):  # 查找用户对应的聊天记录 可选参数time1, time2 必选参数uid, objid
        try:
            time1 = '\'' + str(kwargs['time1']) + '\''
            time2 = '\'' + str(kwargs['time2']) + '\''
        except Exception:
            time1 = '\'' + '1970-1-1' + '\''
            time2 = '\'' + '2100-1-1' + '\''
        sql1 = 'SELECT mtime,mcontent FROM mes WHERE uid={} AND objid={}'.format(uid, objid)
        sql2 = 'AND mtime BETWEEN {} AND {} ORDER BY mtime'.format(time1, time2)
        sql = sql1 + sql2
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            data_new = []
            # print(data)
            for item in data:
                content_new = bytes(item[1])
                mtime_new = item[0]
                data_new.append((mtime_new, content_new))
            # print(data_new)
            return data_new
        except psycopg2.Error as e:
            print(e.pgerror)

    # mesg表
    def mesg_insert(self, gid, uid, mtime, **kwargs):  # 必选参数gid uid mtime可选参数mcontent
        arglist = list(kwargs.keys())
        argnum = len(arglist)
        arg = list(kwargs.values())
        mtime = '\'' + str(mtime) + '\''

        # 拼装SQL语句
        sql1 = (('INSERT INTO mes_g (gid,uid,mtime,' + argnum * '{},').strip(',') + ') ').format(*arglist)
        sql2 = (('VALUES ({},{},{},' + argnum * '{},').strip(',') + ')').format(gid, uid, mtime, *arg)
        sql = sql1 + sql2
        try:
            self.cur.execute(sql)
            # print(sql)
        except psycopg2.Error as e:
            print(e.pgerror)

    def mesg_query(self, gid, **kwargs):  # 查询群聊天记录，必填gid，可选uid，time1，time2
        try:
            time1 = kwargs['time1']
            time2 = kwargs['time2']
        except Exception:
            time1 = '1970-1-1'
            time2 = '2100-1-1'
        sql1 = 'SELECT mcontent FROM mes_g WHERE gid={}'.format(gid)
        try:
            sql2 = ' AND uid={}'.format(kwargs['uid'])
        except Exception:
            sql2 = ''
        sql3 = ' AND mtime BETWEEN \'{}\' AND \'{}\''.format(time1, time2)
        sql = sql1 + sql2 + sql3
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            # print(sql)
            return data
        except psycopg2.Error as e:
            print(e.pgerror)

    def mesg_delete(self, gid):
        # 根据gid，删除该群的所有聊天记录
        sql = 'DELETE FROM mes_g WHERE uid={}'.format(gid)
        try:
            self.cur.execute(sql)
        except psycopg2.Error as e:
            print(e.pgerror)

    # gr表
    def gr_insert(self, gid, gleader, **kwargs):  # 必选参数gid,gleader 可选参数gname, gaddress, gintroduction
        arglist = list(kwargs.keys())
        argnum = len(arglist)
        arg = list(kwargs.values())
        # 给每个参数加入引号以便写SQL
        for i in range(len(arg)):
            arg[i] = '\'' + str(arg[i]) + '\''

        # 拼装SQL语句
        sql1 = (('INSERT INTO gr (gid,gleader,' + argnum * '{},').strip(',') + ') ').format(*arglist)
        sql2 = (('VALUES ({},{},' + argnum * '{},').strip(',') + ')').format(gid, gleader, *arg)
        sql = sql1 + sql2
        try:
            self.cur.execute(sql)
            return 'OK'
            # print(sql)
        except psycopg2.Error as e:
            # print(e.pgerror)
            return 'ERROR'

    def gr_delete(self, gid):
        # 根据gid删除群信息
        sql = ('DELETE FROM gr WHERE gid={}'.format(gid))
        try:
            self.cur.execute(sql)
        except psycopg2.Error as e:
            print(e.pgerror)

    def gr_query(self, gid):
        # 根据gid查找群信息
        sql = 'select * from gr where gid={}'.format(gid)
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            return data
        except psycopg2.Error as e:
            print(e.pgerror)

    def gr_get_all(self):
        # 获取所有群的群号，以及它们的群成员
        sql = 'select gid,gmem from grm'
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            return data
        except psycopg2.Error as e:
            print(e.pgerror)

    # fr表
    def gr_modify(self, gid, **kwargs):  # 修改群信息，必选参数gid，可选gleader gname gaddress gintroduction
        arglist = list(kwargs.keys())
        argnum = len(arglist)
        arg = list(kwargs.values())
        # 给每个参数加引号
        for i in range(len(arg)):
            arg[i] = '\'' + str(arg[i]) + '\''
        exp = []
        for i in range(argnum):
            exp.append(arglist[i] + '=' + arg[i] + ',')
        sql1 = ('UPDATE gr SET ' + argnum * '{}').format(*exp)
        sql2 = ' WHERE gid=' + str(gid)
        sql = sql1.strip(',') + sql2
        try:
            # print(sql)
            self.cur.execute(sql)
        except psycopg2.Error as e:
            print(e.pgerror)

    def fr_insert(self, fid, fone, ftwo, **kwargs):  # 必选参数fid,fone,ftwo 可选参数ftime
        arglist = list(kwargs.keys())
        argnum = len(arglist)
        arg = list(kwargs.values())
        # 给每个参数加入引号以便写SQL
        for i in range(len(arg)):
            arg[i] = '\'' + str(arg[i]) + '\''

        # 拼装SQL语句
        sql1 = (('INSERT INTO fr (fid,fone,ftwo,' + argnum * '{},').strip(',') + ') ').format(*arglist)
        sql2 = (('VALUES ({},{},{},' + argnum * '{},').strip(',') + ')').format(fid, fone, ftwo, *arg)
        sql3 = (('VALUES ({},{},{},' + argnum * '{},').strip(',') + ')').format(fid + 1, ftwo, fone, *arg)  # 双向添加
        sql_one = sql1 + sql2
        sql_two = sql1 + sql3
        try:
            if fone != ftwo:
                self.cur.execute(sql_one)
                self.cur.execute(sql_two)
                return 'OK'
            else:                                      # 给自己加好友不需双向添加
                self.cur.execute(sql_one)
                return 'OK'
            # print(sql)
        except psycopg2.Error as e:
            print(e.pgerror)
            return 'Error'

    def fr_delete(self, fone, ftwo):
        # 根据fone ftwo 解除二人的好友关系
        sql1 = 'DELETE FROM fr WHERE fone={} AND ftwo={}'.format(fone, ftwo)
        sql2 = 'DELETE FROM fr WHERE ftwo={} AND fone={}'.format(fone, ftwo)  # 双向解除
        try:
            if fone != ftwo:
                self.cur.execute(sql1)
                self.cur.execute(sql2)
            else:
                self.cur.execute(sql1)
            return 'OK'                         # 删除自己好友只需单向
        except psycopg2.Error as e:
            print(e.pgerror)
            return 'Error'

    def fr_query(self, uid):  # 根据uid查找其好友列表
        sql = 'SELECT ftwo FROM fr WHERE fone={}'.format(uid)
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            return data
        except psycopg2.Error as e:
            print(e.pgerror)

    # grm表
    def grm_insert(self, gid, gmem):  # 必选参数gid, gmem
        # 拼装SQL语句
        sql = 'INSERT INTO grm (gid,gmem) VALUES ({},{})'.format(gid, gmem)
        try:
            self.cur.execute(sql)
            return 'OK'
            # print(sql)
        except psycopg2.Error as e:
            print(e.pgerror)
            return 'Error'

    def grm_delete(self, gid, gmem):
        # 删除某群中的某个成员
        sql = 'DELETE FROM grm WHERE gid={} AND gmem={}'.format(gid, gmem)
        try:
            self.cur.execute(sql)
            return 'OK'
        except psycopg2.Error as e:
            print(e.pgerror)
            return 'Error'

    def grm_query(self, gid):  # 查询群成员，返回群成员列表
        sql = 'SELECT gmem FROM grm WHERE gid={}'.format(gid)
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            return data
        except psycopg2.Error as e:
            print(e.pgerror)
            return None

    # 连接查询
    def get_groups(self, uid):  # 获取指定人的群聊列表
        sql = 'SELECT gr.gid FROM us,gr,grm WHERE us.uid=grm.gmem AND grm.gid=gr.gid AND us.uid={}'.format(uid)
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            # print(sql)
            return data
        except psycopg2.Error as e:
            print(e.pgerror)
            return None

    def isfriend(self, fone, ftwo):  # 判断2人是否是好友
        sql = 'SELECT fid FROM fr WHERE fone={} AND ftwo={}'.format(fone, ftwo)
        try:
            self.cur.execute(sql)
            if self.cur.fetchall():
                return True
            else:
                return False
        except psycopg2.Error as e:
            print(e.pgerror)

    def get_groups_leader(self, gid):  # 获取群的群主
        sql = 'SELECT gr.gleader FROM gr WHERE gid={}'.format(gid)
        try:
            self.cur.execute(sql)
            return self.cur.fetchall()[0][0]
        except psycopg2.Error as e:
            print(e.pgerror)
            return None

    # 嵌套查询
    def get_friends_info(self, uid):  # 获取某一用户所有好友的个人信息
        sql = '''SELECT uid,uname,usex,uaddress,uhometown,uoccupation,ubirthday,uintroduction,uhead 
          from us,fr WHERE (us.uid = fr.ftwo AND fr.fone={}) order by ftime'''.format(uid)
        try:
            self.cur.execute(sql)
            raw = self.cur.fetchall()
            data = []
            for item in raw:
                dic = {}
                dic['id'] = item[0]
                dic['name'] = item[1]
                dic['sex'] = item[2]
                if item[3]:
                    dic['address'] = item[3]
                else:
                    dic['address'] = ''
                if item[4]:
                    dic['hometown'] = item[4]
                else:
                    dic['hometown'] = ''
                if item[5]:
                    dic['occupation'] = item[5]
                else:
                    dic['occupation'] = ''
                dic['birthday'] = item[6]
                if item[7]:
                    dic['introduction'] = item[7]
                else:
                    dic['introduction'] = ''
                if item[8]:
                    dic['head'] = bytes(item[8])
                else:
                    dic['head'] = b''
                data.append(dic)
            # print(data)
            return data
        except psycopg2.Error as e:
            print(e.pgerror)
            return None


if __name__ == '__main__':
    pass
    # db_us_addhead()
    # db_delete()
    # db_create()
    # Opt = DBOperate()
    # Opt.us_insert(
    #     uid=random.randint(10000, 10000000),
    #     uname='KmjGeorge',
    #     upassword='123456',
    #     usex='男',
    #     uaddress='辽宁省沈阳市',
    #     uhometown='重庆市',
    #     uoccupation='学生',
    #     ubirthday='2020-2-10',
    #     uintroduction='我是傻逼'
    # )
    # gid = random.randint(100000,1000000)
    # Opt.gr_insert(gid=gid,
    #               gleader=2786480,
    #               gname='name',
    #               gaddress='address',
    #               gintroduction='introduction')
    # Opt.commit()
    # Opt.close()
