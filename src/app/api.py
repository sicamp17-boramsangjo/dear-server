# -*- coding: utf-8 -*-
import datetime
import logging
import re
import sys

import ujson as json

from bson.objectid import ObjectId
import pymongo

import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.log import enable_pretty_logging

enable_pretty_logging()


class RequestHandler(tornado.web.RequestHandler):
    def initialize(self, logger):
        self.logger = logger
        self.post_book = {
            'createUser': (self.create_user, {'userName', 'phoneNumber', 'password', 'birthDay'}),
            'getUserInfo': (self.get_user_info, {'sessionToken'}),
            'addWillItem': (self.add_willitem, {}),
            'getWillItem': (self.get_willitem, {}),
            'addQuestion': (self.add_question, {}),
            'getQuestion': (self.get_question, {}),
            'listQuestions': (self.list_questions, {}),
        }

    @tornado.gen.coroutine
    def write_error(self, code, msg):
        self.write({'status': code, 'msg': msg})
        self.finish()

    def get_missing_fields(self, data, fields):
        return fields - set(data.keys())

    @tornado.gen.coroutine
    def post(self, opcode):
        self.set_header('Content-Type', 'application/json')
        handler, required_fields = self.post_book.get(opcode, (None, None))
        data = json.loads(self.request.body)
        if handler is None or required_fields is None:
            self.write_error(400, 'Invalid opcode: %s' % opcode)
            return
        missing_fields = self.get_missing_fields(data, required_fields)
        if len(missing_fields) > 0:
            self.write_error(400, 'Missing fields: %s' % ','.join(list(missing_fields)))
        else:
            handler(data)

    def is_valid_ts(self, ts):
        if not isinstance(ts, int):
            return False
        try:
            datetime.datetime.fromtimestamp(ts)
            return True
        except:
            return False

    def is_valid_phone_num(self, phone_num):
        if isinstance(phone_num, str) and re.match('^01\d-\d{4}-\d{4}$', phone_num):
            return True
        else:
            return False

    def is_existing_user(self, phone_num):
        if DB.users.find_one({'phoneNumber': phone_num}):
            return True
        else:
            return False

    def find_user(self, user_key):
        return DB.users.find_one({'_id': ObjectId(user_key)})

    @tornado.gen.coroutine
    def create_user(self, data):
        if not self.is_valid_ts(data['birthDay']):
            self.write({'status': 400, 'msg': 'Invalid birthDay value: %s' % str(data['birthDay'])})
        elif not self.is_valid_phone_num(data['phoneNumber']):
            self.write({'status': 400, 'msg': 'Invalid phone number format: %s (should be 01X-XXXX-XXXX)' % str(data['phoneNumber'])})
        elif self.is_existing_user(data['phoneNumber']):
            self.write({'status': 200, 'msg': 'Phone number %s is already exist' % data['phoneNumber'], 'userid': None})
        else:
            record = {'userName': data['userName'],
                      'phoneNumber': data['phoneNumber'],
                      'passwd': data['phoneNumber'],
                      'birthDay': data['birthDay'],
                      }
            users = DB.users
            user_id = users.insert_one(record)
            self.write({'status': 200, 'msg': 'OK', 'sessionToken': str(user_id.inserted_id)})
        self.finish()

    @tornado.gen.coroutine
    def get_user_info(self, data):
        try:
            record = self.find_user(data['sessionToken'])
            if record:
                record['_id'] = str(record['_id'])
                self.write({'status': 200, 'msg': 'OK', 'user': record})
            else:
                self.write({'status': 200, 'msg': 'Not exist', 'user': None})
        except Exception as e:
            self.write({'status': 500, 'msg': str(e)})
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
    global DB

    port = sys.argv[1]
    logging.basicConfig(format='%(asctime)-15s %(message)s')
    logger = logging.getLogger('app_server')
    opts = dict(logger=logger)

    client = pymongo.MongoClient()
    DB = client.test_database
    # DB = client.real_database

    application = tornado.web.Application([(r'/app/(.+)', RequestHandler, opts)])

    logger.info('Ready to serve. (port: %s)' % port)

    SVR = tornado.httpserver.HTTPServer(application)
    SVR.listen(int(port))
    tornado.ioloop.IOLoop.current().start()
