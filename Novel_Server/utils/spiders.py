#!/user/bin/env python
# 每天都要有好心情
# 信息获取模块
import base64
import re
import threading
import requests
import urllib3
from bs4 import BeautifulSoup
from abc import ABCMeta, abstractmethod

from Novel_Server.utils.spiders_setting import *


class Spider(metaclass=ABCMeta):
    all_type = 'Spider'

    @abstractmethod
    def login(self):
        """
        进行模拟登录
        :return:
        """
        pass

    @abstractmethod
    def get_shelf(self):
        """
        获取书架信息
        :return: 书架数据
        """
        pass

    @abstractmethod
    def get_wallet(self):
        """
        获取钱包信息
        :return: 钱包信息
        """
        pass

    @abstractmethod
    def get_rank(self, rank_type, data_type, page):
        """
        获取排行榜信息
        :return:
        """
        pass

    @abstractmethod
    def search_book(self, keyword, page=1):
        """
        按照关键词搜索书籍
        :param keyword: 关键词
        :param page: 页数
        :return:
        """
        pass

    @abstractmethod
    def get_book(self, book_id):
        """
        获取书籍详情信息
        :param: book_id: 书籍id(原网站的id)
        :return: 书籍数据
        """
        pass

    @abstractmethod
    def favo_book(self, book_id):
        """
        当书籍已收藏时,会取消收藏
        当书籍未收藏时,会收藏书籍
        :param book_id: 书籍Id
        :return:
        """
        pass

    @abstractmethod
    def buy_chapter(self, book_id, chapter_id):
        """
        订阅章节
        :param book_id: 书籍id(原网站的id)
        :param chapter_id: 章节id(原网站的id)
        :return: 原网站返回的数据
        """
        pass

    @abstractmethod
    def get_chapter(self, chapter_id):
        """
        获取章节数据
        :param chapter_id: 章节id(原网站的章节id)
        :return:
        """
        pass

    @abstractmethod
    def get_line_comment(self, chapter_id, count, index):
        """
        获取间贴
        :param chapter_id: 章节Id
        :param count: 获取的数量
        :param index: 行索引
        :return:
        """
        pass

    @abstractmethod
    def send_line_comment(self, book_id, chapter_id, index, line_content, comment):
        """

        :param book_id: 书籍id
        :param chapter_id: 章节id
        :param index: 行索引
        :param line_content: 行内容
        :param comment: 评论内容
        :return:
        """
        pass


class Spider_YouDu(Spider):
    _instance_lock = threading.Lock()
    _instance = {}

    def __new__(cls, shelf):
        if shelf.id not in cls._instance:
            with cls._instance_lock:
                if shelf.id not in cls._instance:
                    cls._instance[shelf.id] = super(Spider_YouDu, cls).__new__(cls)
                    # 用于发送请求的会话
                    cls._instance[shelf.id].session = None
                    # 书架
                    cls._instance[shelf.id].shelf = shelf
                    # 登录状态
                    cls._instance[shelf.id].is_login = False
        return cls._instance[shelf.id]

    def login(self):
        """
        有毒小说网只通过cookie来验证用户登录,所以只需要设置cookie即可
        :return:
        """
        urllib3.disable_warnings()
        self.session = requests.session()
        # 设置cookies直接模拟登录
        headers = YOUDU_HEADERS
        headers['cookie'] = headers['cookie'].format(self.shelf.account, self.shelf.password)
        self.session.headers = headers
        # 取消SSL认证
        self.session.verify = False
        self.check_login()

    def check_login(self):
        """
        验证是否登录成功,如果登录成功则可以成功请求个人中心网址
        否则会重定向到登录页面,所以只需要判断响应的url是否与个人中心网址相等即可
        :return:
        """
        resp = self.session.get(YOUDU_SHELF_URL)
        if resp.url == YOUDU_SHELF_URL:
            self.is_login = True
        else:
            raise ValueError('无法登录有毒小说网!')

    def get_shelf(self):
        """
        获取该账号的书架收藏书籍
        :return:
        """
        resp = self.session.get(YOUDU_SHELF_URL)
        soup = BeautifulSoup(resp.text, 'lxml')
        book_list = soup.find('div', class_='favoList').findAll('li')
        books = {}

        for book in book_list:
            title = book.find('a')['title']
            last_chapter = book.find('div', class_='updateChapter').find('a')
            books[title] = {
                'id': book.find('a')['href'].split('/')[-1],
                'title': title,
                'cover': book.find('img')['data-original'],
                'last_chapter': last_chapter.get_text().strip(),
                'last_chapter_id': last_chapter['href'].split('/')[-1]
            }
        return books

    def get_wallet(self):
        """
        获取有毒小说网登录用户的钱包信息
        :return: 用户的钱包信息
        """
        resp = self.session.get(YOUDU_WALLET_URL)
        soup = BeautifulSoup(resp.text, 'lxml')
        my_wallet = soup.find('div', class_='Top').findAll('li')

        my_wallet_data = dict()
        my_wallet_data['re_ticket'] = my_wallet[0].find('em').get_text()
        my_wallet_data['mon_ticket'] = my_wallet[1].find('em').get_text()
        my_wallet_data['san'] = my_wallet[2].find('em').get_text()
        my_wallet_data['temp_san'] = my_wallet[3].find('em').get_text()
        return my_wallet_data

    def get_rank(self, rank_type, data_type, page):
        """
        查询排行榜数据
        :param rank_type: Favo:收藏榜;Subscribe:畅销榜;Recommendeds:推荐榜;
                          Hit:点击榜;pushTickets:催更榜;MonthlyTickets:月票榜;
        :param data_type: Week:周榜;Month:月榜;All:总榜
        :param page: 页数
        :return:
        """
        rank_type = rank_type if rank_type else 'Favo'
        data_type = data_type if data_type else 'Week'
        page = page if page else 1
        url = YOUDU_RANK_URL.format(rank_type, data_type, page)
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')
        book_list = soup.find('div', class_='piclist').findAll('li')
        data = {
            'total': len(book_list),
            'page': page,
            'books': []
        }
        for book in book_list:
            data['books'].append({
                'book_id': book.find('a')['href'].split('/')[-1],
                'book_title': book.find('a')['title'],
                'book_cover': book.find('img')['data-original'],
                'book_author': book.find('div', class_='nicheng').get_text().strip(),
                'book_favo': book.find('div', class_='shoucang').get_text().strip(),
                'book_popalrity': book.find('div', class_='renqi').get_text().strip()
            })
        return data

    def search_book(self, keyword, page=1):
        """
        有毒小说网搜索接口
        :param keyword: 搜索关键词
        :param page: 页数
        :return:
        """
        url = YOUDU_SEARCH_URL.format(keyword, page)
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')
        book_list = soup.find('div', class_='BooklibraryList').findAll('li')[:-1]
        book_page = soup.find('div', class_='pageInfo').findAll('em')
        pages = int(book_page[-3].get_text()) if book_page else 0
        data = {
            'pages': pages,
            'page': page,
            'total': 0,
            'books': []
        }
        for book in book_list:
            # 因为网页中有<li class='clear'>..</li>的标签,所以需要过滤掉这部分
            if 'class' in book.attrs:
                continue
            data['books'].append({
                'book_id': book.find('a')['href'].split('/')[-1],
                'book_title': book.find('a')['title'],
                'book_cover': book.find('img', class_='img1')['data-original'],
                'book_author': book.find('dd', class_='nickname').get_text().strip(),
                'book_favo': book.find('dd', class_='favo').get_text().strip(),
                'book_popalrity': book.find('dd', class_='hit').get_text().strip()
            })
        data['total'] = len(data['books'])
        return data

    def get_book(self, book_id):
        """
        获取书籍的详情信息,包括书籍的:
        标题,作者,简介,卷名,章节
        :param book_id: 书籍的id
        :return: 书籍信息的dict
        """
        url = YOUDU_BOOK_URL.format(book_id)
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')

        title_author = soup.find('div', class_='title')
        book_labels = soup.find('div', class_='label').findAll('li')
        book_fonts = soup.find('div', class_='Font').findAll('span')
        book_Reward = soup.find('ul', class_='Reward').findAll('li')
        book_data = {
            'book_title': title_author.find('span').get_text().strip(),
            'book_author': title_author.find('em').get_text().strip(),
            'book_label': [label.get_text().strip() for label in book_labels],
            'book_fonts': book_fonts[0].get_text().strip(),
            'book_click': book_fonts[1].get_text().strip(),
            'book_favo': book_fonts[2].get_text().strip(),
            'book_reward': {
                'book_monTicket': book_Reward[0].get_text().strip(),
                'book_reTicket': book_Reward[1].get_text().strip(),
                'book_money': book_Reward[2].get_text().strip(),
                'book_fuck': book_Reward[3].get_text().strip()
            },
            'book_cover': soup.find('div', class_='pic').find('img')['data-original'],
            'book_disc': soup.find('div', class_='synopsisCon').prettify(),
            'book_volume_list': [],
            'chapter_lock': {},
        }
        # 书籍卷名
        book_volume_list = soup.findAll('div', class_='volume_name')
        book_chapter_list = soup.findAll('div', class_='chapter_list')
        for volume in book_volume_list:
            book_data['book_volume_list'].append({
                'volume_name': volume.get_text().strip(),
                'chapter_list': []
            })
        # 每卷包含的章节列表
        for idx, volume in enumerate(book_data['book_volume_list']):
            chapter_list = book_chapter_list[idx].findAll('li')
            for chapter in chapter_list:
                status = chapter.attrs.get('class', None)
                if status:
                    # 未解锁
                    if status[0] == 'lock_fill':
                        is_lock = 1
                    # 已解锁
                    else:
                        is_lock = 0
                # 免费章节
                else:
                    is_lock = -1
                chapter_id = chapter.find('a')['href'].split('/')[-1]
                volume['chapter_list'].append({
                    'chapter_title': chapter.find('a').get_text().strip(),
                    'chapter_id': chapter_id,
                    'is_lock': is_lock
                })
                book_data['chapter_lock'][chapter_id] = is_lock
        return book_data

    def favo_book(self, book_id):
        """
        当书籍未收藏时,发送该请求会收藏书籍
        当书籍已收藏时,发送该请求会取消收藏书籍
        :param book_id: 书籍id(对应网站中的)
        :return: 网站返回的json数据
        """
        data = {
            'BookID': book_id
        }
        resp = self.session.post(YOUDU_ADD_BOOK_URL, data)
        return resp.json()

    def buy_chapter(self, book_id, chapter_id):
        """
        订阅章节
        :param book_id: 书籍id
        :param chapter_id: 章节id
        :return: 订阅消息
        """
        data = {
            'BookID': book_id,
            'ChapterID': chapter_id,
            'isSingleWsCount': 0,
            'isAllWsCount': 0,
            'isMethod': 1,
            'isAuto': 0
        }
        resp = self.session.post(YOUDU_BUY_CHAPTER_URL, data=data)
        return resp.json()

    def get_post_data(self, url):
        """
        获取章节页面里的caonima字符串,这是发送post请求必须的字段
        :param url: 章节阅读页面
        :return: post数据
        """
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')
        btn_list = soup.find('div', class_='chapterBtn').findAll('a')
        # 上一章
        prev_btn = btn_list[0]['href'].split('/')[-1] if btn_list[0]['href'] != "javascript:void(0);" else None
        # 下一章
        next_btn = btn_list[-1]['href'].split('/')[-1] if btn_list[-1]['href'] != "javascript:void(0);" else None
        btns = {
            'prev_btn': prev_btn,
            'next_btn': next_btn
        }
        data = {
            'sign': 'a3NvcnQoJHBhcmEpOw==',
            'caonima': re.findall(r'MemberSingleChapter.+?;', resp.text)[-1].split('"')[-2]
        }
        return btns, data

    @staticmethod
    def parse_chapter_data(resp):
        """
        根据传入的章节json数据,对章节内容进行base64解码.
        :param resp: 章节的Json数据
        :return: 解码后的章节数据
        """
        if not resp:
            return {}
        data = {
            'chapter_id': resp['id'],
            'book_id': resp['BookID'],
            'title': resp['title'],
            'FontCount': resp['FontCount'],
            'content': []
        }
        for line in resp['show_content']:
            data['content'].append({
                'index': line['paragraph_index'],
                'content': base64.b64decode(line['content']).decode('utf-8').strip(),
                'tsukkomi': line['tsukkomi']
            })
        return data

    def get_chapter(self, chapter_id):
        """
        获取对应章节的章节数据
        :param chapter_id: 章节id
        :return: 章节数据
        """
        # 获取发送请求必要的数据的地址
        post_data_url = YOUDU_READ_CHAPTER_URL.format(chapter_id)
        # 发送请求的地址
        json_url = YOUDU_CHAPTER_JSON_URL.format(chapter_id)
        # 发送post请求需要的数据
        post_data = self.get_post_data(post_data_url)
        # 加上referer来反 反爬
        self.session.headers.update({
            'referer': post_data_url
        })
        resp = self.session.post(json_url, data=post_data[1])
        # 进行数据解密
        data = self.parse_chapter_data(resp.json()['data'])
        data['btns'] = post_data[0]
        return data

    def get_line_comment(self, chapter_id, count, index):
        """
        获取间贴数据
        :param chapter_id: 章节信息
        :param count: 要获取的数量
        :param index: 行所在的索引
        :return:
        """
        data = {
            'page': 1,
            'count': count,
            'chapter_id': chapter_id,
            'paragraph_index': index
        }
        resp = self.session.post(YOUDU_LINE_COMMENT_URL, data=data).json()['data']
        data['comments'] = []
        data['count'] = len(resp['data'])
        for comment in resp['data']:
            data['comments'].append({
                'user_id': comment['theUser'],
                'user_name': comment['nickname'],
                'content': comment['tsukkomi_content'],
                'add_time': comment['addTime']
            })
        return data

    def send_line_comment(self, book_id, chapter_id, index, line_content, comment):
        """
        发送间贴
        :param book_id: 书籍id
        :param chapter_id: 章节id
        :param index: 行索引
        :param line_content: 行内容
        :param comment: 评论内容
        :return:
        """
        data = {
            'BookID': book_id,
            'ChapterID': chapter_id,
            'paragraph_index': index,
            'chapter_content': line_content,
            'tsukkomi_content': comment
        }
        resp = self.session.post(url=YOUDU_LINE_COMMENT_SEND_URL, data=data)
        return resp.json()
