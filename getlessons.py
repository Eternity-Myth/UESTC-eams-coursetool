import os
import requests
import re
import sys

cyrus_username = ''  # 填学号
cyrus_password = ''  # 填密码

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
        "User-Agent": "CYRUS/5.0 (Windows CNSS; WOW64; rv:51.0) CNSS/20100101 CYRUS/51.0",
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


print("初始化系统中...")

try:
    for id in range(300000, 360000):
        print(id)
        if id % 50 == 0:
            session = login(cyrus_username, cyrus_password)
        pre0 = safe_get(session, "http://eams.uestc.edu.cn/eams/electionLessonInfo.action?lesson.id=" + str(id))
        status = pre0.find("课程名称")
        if status != -1:
            with open(os.getcwd()+"\\lessondata.txt", "a+") as fp:
                fp.write("id:" + str(id) + "\t" + pre0[2715:pre0.find("学分") - 39] + "\n")

except Exception as e:
    print(e)
    print("提示：系统已退出")
    sys.exit()
