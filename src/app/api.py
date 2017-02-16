# -*- coding: utf-8 -*-
import sys
import logging

import ujson as json
import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.log import enable_pretty_logging

enable_pretty_logging()


class RequestHandler(tornado.web.RequestHandler):
    def initialize(self, logger):
        self.logger = logger
        self.post_handlers = {'createUser': self.create_user,
                              'getUser': self.get_user,
                              'addUserProps': self.add_user_props,
                              'addWillItem': self.add_willitem,
                              'getWillItem': self.get_willitem,
                              'addQuestion': self.add_question,
                              'getQuestion': self.get_question,
                              'listQuestions': self.list_questions,
                              }

    @tornado.gen.coroutine
    def write_error(self, code, msg):
        self.write({'status': code, 'msg': msg})
        self.finish()

    @tornado.gen.coroutine
    def post(self, opcode):
        self.set_header('Content-Type', 'application/json')
        handler = self.post_handlers.get(opcode, None)
        data = json.loads(self.request.body)
        if handler is None:
            self.write_error(400, 'Invalid opcode: %s' % opcode)
            self.finish()
        try:
            handler(data)
        except Exception as e:
            self.set_status(500)
            self.logger.error('Exception occured at %s: %s' % (self.handler.__name__, str(e)))
            self.logger.error('Data: %s' % str(data))
            self.write({'status': 500, 'msg': str(e)})
            self.finish()

    @tornado.gen.coroutine
    def create_user(self, data):
        self.write({'status': 200, 'msg': 'OK', 'userid': 'xxyy'})
        self.finish()

    @tornado.gen.coroutine
    def get_user(self, data):
        user_info = {'userid': 'xxyy',
                     'name': '김철수',
                     'phone_number': 'xxxxx'}
        self.write({'status': 200, 'msg': 'OK', 'user': user_info})
        self.finish()

    @tornado.gen.coroutine
    def add_user_props(self, data):
        self.write({'status': 200, 'msg': 'OK', 'user_id': 'xxyy'})
        self.finish()

    @tornado.gen.coroutine
    def add_willitem(self, data):
        self.write({'status': 200, 'msg': 'OK', 'willitem_id': 'zzz'})
        self.finish()

    @tornado.gen.coroutine
    def get_willitem(self, data):
        willitem = {'question_id': 'q123',
                    'question_text': '가장 좋아하는 음식은?',
                    'size': 2,
                    'regts': 14207204749,
                    'modts': 14539543894,
                    'thread': [
                        {'thread_id': 1,
                         'regts': 14030812730,
                         'text': '떡볶이'
                        },
                        {'thread_id': 2,
                         'regts': 14040812730,
                         'text': '나이가 들어보니, 김치찌개가 참 좋더라'
                        },
                        ]
                    }
        self.write({'status': 200, 'msg': 'OK', 'willitem': willitem})
        self.finish()

    @tornado.gen.coroutine
    def add_question(self, data):
        self.write({'status': 200, 'msg': 'OK', 'question_id': 'q123'})
        self.finish()

    @tornado.gen.coroutine
    def get_question(self, data):
        self.write({'status': 200, 'msg': 'OK', 'question': {}})
        self.finish()

    @tornado.gen.coroutine
    def list_questions(self, data):
        self.write({'status': 200, 'msg': 'OK', 'list': []})
        self.finish()


if __name__ == "__main__":
    global SVR

    port = sys.argv[1]
    logging.basicConfig(format='%(asctime)-15s %(message)s')
    logger = logging.getLogger('app_server')
    opts = dict(logger=logger)

    application = tornado.web.Application([(r'/(.+)', RequestHandler, opts)])

    logger.info('Ready to serve. (port: %s)' % port)

    SVR = tornado.httpserver.HTTPServer(application)
    SVR.listen(int(port))
    tornado.ioloop.IOLoop.current().start()
