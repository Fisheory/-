import csv
from lxml import etree
import time
import requests

headers = {
    "Cookie":"", #请填入浏览器cookie
    'User-Agent':"" #请填入浏览器user-agent
}
zero_count = 0
comment_count = 0
pre_url = "https://s.weibo.com/weibo?"


def parse_detail(js, detailed_js):
    try:
        if js["data"]["user"]["gender"] == "f":
            gender = "女"
        if js["data"]["user"]["gender"] == "m":
            gender = "男"
    except:
        gender = "未知"

    try:
        school = detailed_js["data"]["education"]["school"]
    except:
        school = "未知"

    try:
        company = detailed_js["data"]["career"]["company"]
    except:
        company = "未知"

    try:
        description = js["data"]["user"]["description"]
    except:
        description = "无"

    try:
        birthday = detailed_js["data"]["birthday"]
    except:
        birthday = "无"

    fans = js["data"]["user"]["followers_count"]

    friends = js["data"]["user"]["friends_count"]

    try:
        verified = js["data"]["user"]["verified_reason"]
    except:
        verified = "无"

    try:
        register = detailed_js["data"]["created_at"]
    except:
        register = "无"

    return gender, school, company, description, birthday, fans, friends, verified, register


def getArticleId(id_str):
    end = id_str.find('?')
    start = id_str.rfind('/', 0, end)
    url_id = "https://weibo.com/ajax/statuses/show?id={}".format(id_str[start +
                                                                        1:end])
    try:
        response_id = requests.get(url_id, headers=headers)
    except:
        response_id = requests.get(url_id, headers=headers)
    if response_id is None:
        return -1
    resp = response_id.json()

    url_custom = "https://weibo.com/ajax/profile/info?custom={}".format(
        resp["user"]["idstr"])
    try:
        response_custom = requests.get(url_custom, headers=headers)
    except:
        response_custom = requests.get(url_custom, headers=headers)
    try:
        cust = response_custom.json()
    except:
        return -1

    url_detail = "https://weibo.com/ajax/profile/detail?uid={}".format(
        resp["user"]["idstr"])
    try:
        response_detail = requests.get(url_detail, headers=headers)
    except:
        response_detail = requests.get(url_detail, headers=headers)
    try:
        detail = response_detail.json()
    except:
        return -1

    rel_time = resp["created_at"].replace("+0800", "")
    timel = rel_time.split()
    mon = 0
    if timel[1] == "Oct": mon = 10
    elif timel[1] == "Nov": mon = 11
    else: mon = 12
    dat = timel[2]
    tim = timel[3][0:5]
    try:
        location = resp["region_name"].split()[1]
    except:
        location = '无'

    gender, school, company, description, birthday, fans, friends, verified, register = parse_detail(
        cust, detail)

    data_dict = {
        "编号": comment_count,
        "发帖人": resp["user"]["screen_name"],
        "主帖内容": resp["text_raw"].replace('\n', ' '),
        "点赞量": resp["comments_count"],
        "回复量": resp["attitudes_count"],
        "回复对象": "无",
        "ip地址": location,
        "性别": gender,
        "学校": school,
        "公司": company,
        "简介": description,
        "生日": birthday,
        "粉丝数": fans,
        "关注数": friends,
        "大V认证": verified,
        "注册时间": register,
        "发布时间": str(mon) + "月" + str(dat) + "日 " + str(tim)
    }
    saveData(data_dict)
    return resp["id"]


def get_url(tag, time_start, time_end, page):
    url = pre_url + f"q={tag}&typeall=1&suball=1&timescope=custom%3A{time_start}%3A{time_end}&Refer=g&page={page}"
    return url


def get_one_page(param, father):
    url = "https://weibo.com/ajax/statuses/buildComments"
    try:
        response = requests.get(url, headers=headers, params=param)
    except:
        response = requests.get(url, headers=headers, params=param)
    
    data_list = response.json()["data"]
    global zero_count
    global comment_count
    if len(data_list) == 0:
        zero_count += 1
    else:
        zero_count = 0

    for data in data_list:
        rel_time = data["created_at"].replace("+0800", "")
        timel = rel_time.split()
        mon = 0
        if timel[1] == "Oct": mon = 10
        elif timel[1] == "Nov": mon = 11
        else: mon = 12
        dat = timel[2]
        tim = timel[3][0:5]

        userid = data["user"]["idstr"]
        url_custom = "https://weibo.com/ajax/profile/info?custom={}".format(
            userid)
        try:
            response_custom = requests.get(url_custom, headers=headers)
        except:
            response_custom = requests.get(url_custom, headers=headers)
        try:
            cust = response_custom.json()
        except:
            continue

        url_detail = "https://weibo.com/ajax/profile/detail?uid={}".format(
            userid)
        try:
            response_detail = requests.get(url_detail, headers=headers)
        except:
            response_detail = requests.get(url_detail, headers=headers)
        try:
            detail = response_detail.json()
        except:
            continue
        
        comment_count += 1

        gender, school, company, description, birthday, fans, friends, verified, register = parse_detail(
        cust, detail)

        data_dict = {
            "编号": comment_count,
            "发帖人": data["user"]["screen_name"],
            "主帖内容": data["text_raw"].replace('\n', ' '),
            "点赞量": data["total_number"],
            "回复量": data["like_counts"],
            "回复对象": "编号" + str(father),
            "ip地址": data["user"]["location"],
            "性别": gender,
            "学校": school,
            "公司": company,
            "简介": description,
            "生日": birthday,
            "粉丝数": fans,
            "关注数": friends,
            "大V认证": verified,
            "注册时间": register,
            "发布时间": str(mon) + "月" + dat + "日 " + tim
        }
        saveData(data_dict)
    max_id = response.json()["max_id"]
    if max_id:
        return max_id
    else:
        return


def get_data(param, father):
    max_id = get_one_page(param, father)
    param["max_id"] = max_id
    param["count"] = 20
    while max_id:
        if zero_count == 20:
            break
        param["max_id"] = max_id
        time.sleep(.5)
        max_id = get_one_page(param, father)


def saveData(data_dict):
    print('=' * 90)
    print(data_dict)
    print('=' * 90)
    writer.writerow(data_dict)


if __name__ == "__main__":

    uid = 100000000 #请填入uid
    comment_count = 0
    csv_header = [
        "编号", "发帖人", "主帖内容", "点赞量", "回复量", "回复对象", "ip地址", "性别", "学校", "公司",
        "简介", "生日", "粉丝数", "关注数", "大V认证", "注册时间", "发布时间"
    ]
    f = open(f"./data1.csv", "a", encoding="utf-8", newline="")
    writer = csv.DictWriter(f, csv_header)
    writer.writeheader()
    for ti in range(1,31):
        page = 1
        if ti < 10: 
            start_time = "2023-10-0{}-0".format(ti)
        else:
            start_time = "2023-10-{}-0".format(ti)
        if ti+1 < 10:
            end_time = "2023-10-0{}-0".format(ti+1)
        else:
            end_time = "2023-10-{}-0".format(ti+1)
        print(start_time, " to ", end_time)
        while True:
            print(f"Current page: {page}")
            url = get_url("巴以冲突", start_time, end_time, page)
            try:
                response = requests.get(url, headers=headers)
            except:
                response = requests.get(url, headers=headers)
            html = etree.HTML(response.text,
                            parser=etree.HTMLParser(encoding='utf-8'))
            total_entry = len(html.xpath('//div[@class="card-wrap"]')) - 1
            for i in range(total_entry):
                now_tree = '//div[@class="card-wrap"][' + str(i + 1) + ']'
                blog_url = html.xpath(now_tree + '//div[@class="from"]/a/@href')[0]
                comment_count += 1
                id = getArticleId(blog_url)
                if id == -1:
                    comment_count -= 1
                    continue
                param = {
                    "is_reload": 1,
                    "id": id,
                    "is_show_bulletin": 2,
                    "is_mix": 0,
                    "count": 10,
                    "uid": int(uid)
                }
                father = comment_count
                get_data(param, father)
            try:
                if page == 1:
                    pageA = html.xpath(
                        '//*[@id="pl_feedlist_index"]/div[3]/div/a')[0].text
                    page = page + 1
                elif page == 50:
                    break
                else:
                    pageA = html.xpath(
                        '//*[@id="pl_feedlist_index"]/div[3]/div/a[2]')[0].text
                    page = page + 1
            except:
                break
