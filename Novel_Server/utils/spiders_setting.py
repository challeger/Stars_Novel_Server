#!/user/bin/env python
# 每天都要有好心情
"""
爬虫工具的配置
各网站接口设置
"""

# 网站对应的爬虫类
SPIDERS = {
    'https://www.youdubook.com/': 'Spider_YouDu'
}

# 有毒小说网请求头
YOUDU_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
    'cookie': 'saveMemberInfo=%7B%22username%22%3A%22{}%22%2C%22password%22%3A%22{}%22%7D',
    'origin': 'https://www.youdubook.com',
    'x-requested-with': 'XMLHttpRequest'
}
# 有毒小说网个人书架网址
YOUDU_SHELF_URL = 'https://www.youdubook.com/user/favobook'
# 有毒小说网个人钱包网址
YOUDU_WALLET_URL = 'https://www.youdubook.com/user/prepaidrecords'
# 有毒小说网书籍详情网址
YOUDU_BOOK_URL = 'https://www.youdubook.com/book_detail/{}'
# 有毒小说网获取caonima所需的URL
YOUDU_READ_CHAPTER_URL = 'https://www.youdubook.com/readchapter/{}'
# 有毒小说网获取章节JSON数据的URL
YOUDU_CHAPTER_JSON_URL = 'https://www.youdubook.com/booklibrary/membersinglechapter/chapter_id/{}'
# 有毒小说网获取行评论的URL
YOUDU_LINE_COMMENT_URL = 'https://www.youdubook.com/booklibrary/tsukkomilist'
# 有毒小说网发送行评论URL
YOUDU_LINE_COMMENT_SEND_URL = 'https://www.youdubook.com/booklibrary/tsukkomiadd'
# 有毒小说网订阅章节的URL
YOUDU_BUY_CHAPTER_URL = 'https://www.youdubook.com/booklibrary/subscribebookaction'
# 有毒小说网排行榜的URL
YOUDU_RANK_URL = 'https://www.youdubook.com/ranking/ranklist/tag/{}/type/{}?page={}'
# 有毒小说网搜索的URL
YOUDU_SEARCH_URL = 'https://www.youdubook.com/booklibrary/index/str/0_0_0_0_0_0_0_{}?page={}'
# 有毒小说网收藏与取消收藏小说接口
YOUDU_ADD_BOOK_URL = 'https://www.youdubook.com/booklibrary/actionfavo'
