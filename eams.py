############## ! CONFIG PART ! ##############
cyrus_username = ''  # 填学号
cyrus_password = ''  # 填密码
nthread = 20  # 预选请使用1，补选抢课请使用更多
port = []  # 选课平台入口（点进选课平台看url）
lesson = []  # 课程id，点进课程看url
op = ['']  # select,change,catch,withdraw
money = [0]  # 预选使用，补选抢课忽略
name = ['']  # 备注
#############################################


__author__ = 'Cyrus'

import requests
import re
import sys
import time
import queue
import threading

init = "http://idas.uestc.edu.cn/authserver/login?service=http%3A%2F%2Fportal.uestc.edu.cn%2F"
init_eams = "http://eams.uestc.edu.cn/eams/home!index.action"
url_lesson = 'http://eams.uestc.edu.cn/eams/electionLessonInfo.action?lesson.id='
url_scan_lesson = "http://eams.uestc.edu.cn/eams/stdElectCourse!data.action?profileId="
url_scan_entrance = "http://eams.uestc.edu.cn/eams/stdElectCourse!defaultPage.action?electionProfile.id="
url_catch = "http://eams.uestc.edu.cn/eams/stdElectCourse!batchOperator.action?profileId="
url_change = "http://eams.uestc.edu.cn/eams/stdVirtualCashElect!changeVirtualCash.action"
url_table = "http://eams.uestc.edu.cn/eams/courseTableForStd.action?_=0&semester.id="  # 163, 17-18, t1
url_test_estimate = "http://eams.uestc.edu.cn/eams/textEvaluateStudent!search.action?semester.id="  # 163, 17-18, t1


def get_mid_text(text, left_text, right_text, start=0):
    #	获取中间文本
    left = text.find(left_text, start)
    if left == -1:
        return ('', -1)
    left += len(left_text)
    right = text.find(right_text, left)
    if right == -1:
        return ('', -1)
    return (text[left:right], right)


def safe_get(session, req):
    #	包括报错的安全get请求
    flag = 1
    while flag > 0:
        if flag > 32:
            print("错误：这他妈网络太差了")
            return ""
        try:
            res = session.get(req).text
        except:
            print("警告：你的网炸了")
            flag += 1
        else:
            flag = 0
    return res


def safe_post(session, req, data):
    #	包括报错的安全post请求
    flag = 1
    while flag > 0:
        if flag > 32:
            print("错误：这他妈网络太差了")
            return ""
        try:
            res = session.post(req, data=data).text
        except:
            print("警告：你的网炸了")
            flag += 1
        else:
            flag = 0
    return res


def login(username, password):
    headers = {
        "Host": "idas.uestc.edu.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36",
        "Referer": "http://idas.uestc.edu.cn/authserver/login?service=http%3A%2F%2Fportal.uestc.edu.cn%2F"
    }
    u = requests.session()
    u.cookies.clear()
    r = u.get(init, headers=headers)
    lt = re.findall('name="lt" value="(.*)"/>', r.text)[0]
    data = {
        "username": username,
        "password": password,
        "lt": lt,
        "dllt": "userNamePasswordLogin",
        "execution": "e1s1",
        "_eventId": "submit",
        "rmShown": "1"
    }
    r = u.post(init, headers=headers, data=data)

    if ("电子科技大学登录" in r.text):
        print("提示：登录失败")
        print("提示：系统已退出")
        sys.exit()
    else:
        print("提示：用户[%s]登录完成" % username)
        s = u.get(init_eams).text
        if s.partition("重复登录")[1] != "":
            url_t = get_mid_text(s, "请<a href=\"", "\">点击此处")
            u.get(url_t[0])
            s = u.get(init_eams).text
            if s.partition("重复登录")[1] != "":
                print("提示：eams提示了重复登录，自动处理失败")
                print("提示：请手动登录平台并依次注销教务系统和信息门户")
                sys.exit()
            else:
                print("提示：eams提示了重复登录，自动处理完成")
                print("提示：搜索关键字“成功”可快速查看结果")
        return u


def scan(url, minx, maxx, wrongword, out):
    #	url		模板链接
    #	minx  		起始值（包含）
    #	maxx		终止值（包含）
    #	wrongword	错误关键字（list）
    #	out		[=1]为需要临时输出
    res = []
    for i in range(minx, maxx + 1):
        req = url + str(i)
        s = safe_get(session, req)
        flag = 1
        for key in wrongword:
            if s.find(key) != -1:
                print("扫描：%-5d-失败" % i)
                flag = 0
                break
        if flag:
            print("扫描：%-5d-成功" % i)
            res.append(i)
            if out == 1:
                print(s)
    return res


def biu(session, port, class_info, name, op, money, choose=True, sleep=0):
    oplist = {
        "select": "课程预选",
        "change": "修改权重",
        "catch": "课程补选",
        "withdraw": "退课"
    }

    global count
    global t
    global m
    global success
    global success_int
    while success[t % m] == 0:

        response = ""

        if str(op) == "select":
            postdata = {
                'operator0': '%s:%s:0' % (str(class_info), str(choose).lower()),
                'virtualCashCost%s' % (str(class_info)): str(money)
            }
            pre0 = safe_get(session, url_scan_entrance + str(port))
            response = safe_post(session, url_catch + str(port), postdata)

        if str(op) == "change":
            postdata = {
                'profileId': str(port),
                'lessonId': str(class_info),
                'changeCost': str(money)
            }
            pre0 = safe_get(session, url_scan_entrance + str(port))
            response = safe_post(session, url_change, postdata)

        if str(op) == "catch":
            postdata = {
                'operator0': '%s:%s:0' % (str(class_info), str(choose).lower())
            }
            pre0 = safe_get(session, url_scan_entrance + str(port))
            response = safe_post(session, url_catch + str(port), postdata)

        if str(op) == "withdraw":
            postdata = {
                'operator0': '%s:false' % (str(class_info))
            }
            pre0 = safe_get(session, url_scan_entrance + str(port))
            response = safe_post(session, url_catch + str(port), postdata)

        count += 1
        print(name + '正在进行第%d次%s尝试' % (count, oplist[str(op)]))

        # 针对change
        if '更改对任务' in response:
            print(response.partition(';')[0] + '  id:%s  port:%s' % (class_info, port))
            print("%s%s成功" % (name, oplist[str(op)]))
            success[t % m] = 1
            success_int += 1
            break

        # 其他情况返回
        info, end = get_mid_text(response, 'text-align:left;margin:auto;">', '</br>')
        if end == -1:
            info += '网络错误！'
        info = info.replace(' ', '').replace('\n', '').replace('\t', '')
        info += '  id:%s  port:%s' % (class_info, port)
        print(info)
        if '成功' in info:
            print("%s%s成功" % (name, oplist[str(op)], name))
            success[t % m] = 1
            success_int += 1
            break

        # 意外情况
        if '本批次' in info or '只开放给' in info:
            print("emmmm...真的选不了")
            break
        elif '网络错误' in info:
            print('jesession已经过期 正在获取jesession')
            while True:
                try:
                    response = safe_get(session, url_catch + str(port))
                except Exception:
                    print('获取获取jesession失败：网络错误！')
                    continue
                if '(possibly due to' not in response:
                    print('获取获取jesession完成')
                    break
                else:
                    print('获取获取jesession失败：傻逼你电抽风了！')
        time.sleep(sleep)


print("初始化系统中...")
try:
    session = login(cyrus_username, cyrus_password)
except Exception as e:
    print(e)
    print("提示：系统已退出")
    sys.exit()
count = 0
success_int = 0

# 查找入口请关闭这段注释
entrance = scan(url_scan_entrance, 1000, 2000, ["没有开放的选课轮次", "不在选课时间内"], 0)
print(entrance)
exit()

m = len(lesson)
success = []
for i in range(m):
    success.append(0)
if nthread < m:
    nthread = m

free = queue.LifoQueue(nthread)
for t in range(nthread):
    if success_int == m:
        print("所有课程已完成")
        sys.exit()
    free.put("thread" + str(t))
    if success[t % m] == 0:
        th = threading.Thread(target=biu,
                              args=(session, port[t % m], lesson[t % m], name[t % m], op[t % m], money[t % m]))
        th.start()
