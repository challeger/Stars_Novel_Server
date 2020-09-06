#!/user/bin/env python
# 每天都要有好心情
# 信息获取模块
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
    def get_rank(self):
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
        pass

    def get_rank(self):
        pass

    def search_book(self, keyword, page=1):
        pass

    def get_book(self, book_id):
        pass

    def favo_book(self, book_id):
        pass

    def buy_chapter(self, book_id, chapter_id):
        pass

    def get_chapter(self, chapter_id):
        pass

    def get_line_comment(self, chapter_id, count, index):
        pass

    def send_line_comment(self, book_id, chapter_id, index, line_content, comment):
        pass
