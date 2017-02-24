# -*- coding: utf-8 -*-
import datetime
import logging
import re
import sys
import time

import ujson as json

from bson.objectid import ObjectId
import pymongo

import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.log import enable_pretty_logging

enable_pretty_logging()


class RequestHandler(tornado.web.RequestHandler):
    def initialize(self, logger, config_fname):
        self.logger = logger
        self.opt = json.load(open(config_fname))
        self.post_book = {
            'createUser': self.create_user,
            'getUserInfo': self.get_user_info,
            'updateUserInfo': self.update_user_info,
            'addQuestion': self.add_question,
            'getQuestion': self.get_question,
            'getTodaysQuestion': self.get_todays_question,
        }
        for k, f in self.post_book.iteritems():
            self.post_book[k] = (f, set(self.opt['fields'][k]['required']), set(self.opt['fields'][k]['allowed']))

    @tornado.gen.coroutine
    def write_error(self, code, msg):
        self.write({'status': code, 'msg': msg})
        self.finish()

    def check_fields(self, data, required, allowed):
        query_fields = set(data.keys())
        return required - query_fields, query_fields - (allowed | required)

    @tornado.gen.coroutine
    def post(self, opcode):
        try:
            self.set_header('Content-Type', 'application/json')
            handler, required_fields, allowed_fields = self.post_book.get(opcode, (None, None, None))
            self.logger.info('Query: %s' % self.request.body)
            data = json.loads(self.request.body)
            if handler is None or required_fields is None or allowed_fields is None:
                self.write_error(400, 'Invalid opcode: %s' % opcode)
            missing_fields, not_allowed_fields = self.check_fields(data, required_fields, allowed_fields)
            if len(missing_fields) > 0:
                self.write_error(400, 'Missing fields: %s' % ','.join(list(missing_fields)))
            elif len(not_allowed_fields) > 0:
                self.write_error(400, 'Not allowed fields: %s' % ','.join(list(not_allowed_fields)))
            else:
                handler(data)
        except Exception as e:
            self.write_error(500, 'Internal server error: %s' % str(e))

    def is_valid_ts(self, ts):
        if not isinstance(ts, int):
            return False
        try:
            datetime.datetime.fromtimestamp(ts)
            return True
        except:
            return False

    def is_valid_phone_num(self, phone_num):
        if re.match('^01\d-\d{4}-\d{4}$', phone_num):
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

    def find_question(self, question_key):
        return DB.questions.find_one({'_id': ObjectId(question_key)})

    def get_random_question(self):
        # not random yet...
        return DB.questions.find_one({})

    @tornado.gen.coroutine
    def create_user(self, data):
        try:
            if not self.is_valid_ts(data['birthDay']):
                self.write_error(400, 'Invalid birthDay value')
            elif not self.is_valid_phone_num(data['phoneNumber']):
                self.write_error(400, 'Invalid phone number format')
            elif self.is_existing_user(data['phoneNumber']):
                self.write_error(400, 'The phone number is already exist')
            else:
                now_ts = int(time.time())
                todays_question = self.get_random_question()
                if not todays_question:
                    self.write_error(400, 'Failed to get todays question')
                    return
                record = {'userName': data['userName'],
                          'phoneNumber': data['phoneNumber'],
                          'password': data['password'],
                          'birthDay': data['birthDay'],
                          'deviceToken': "",
                          'profileImageUrl': "",
                          'pushDuration': self.opt['settings']['user']['pushDuration'],
                          'willitems': {},
                          'receivers': [],
                          'lastLoginTime': now_ts,
                          'todaysQuestion': {
                              'questionId': str(todays_question['_id']),
                              'deliveredAt': now_ts
                              }
                          }
                users = DB.users
                user_id = users.insert_one(record)
                self.write({'status': 200, 'msg': 'OK', 'sessionToken': str(user_id.inserted_id)})
                self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def get_user_info(self, data):
        try:
            record = self.find_user(data['sessionToken'])
            if record:
                record['_id'] = str(record['_id'])
                self.write({'status': 200, 'msg': 'OK', 'user': record})
            else:
                self.write({'status': 400, 'msg': 'Not exist', 'user': None})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def update_user_info(self, data):
        try:
            record = self.find_user(data['sessionToken'])
            if record:
                record['_id'] = str(record['_id'])
                recordUpdated = {'profileImageUrl': "",
                                 'pushDuration': self.opt['settings']['user']['pushDuration'],
                                 'lastLoginAlarmDuration': ""
                }
                users = DB.users
                user_id = users.update(
                    {'_id': record['_id']},
                    {
                        '$set': recordUpdated
                    }
                )
                self.write({'status': 200, 'msg': 'OK', 'resultCode': 1}) # FIXME resultCode
            else:
                self.write({'status': 400, 'msg': 'Not exist', 'resultCode': 0}) # FIXME resultCode
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def add_question(self, data):
        try:
            questions = DB.questions
            record = {'text': data['text'],
                      'answered': 0,
                      'registeredTime': int(time.time()),
                      }
            question_id = questions.insert_one(record)
            self.write({'status': 200, 'msg': 'OK', 'questionId': str(question_id.inserted_id)})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def get_question(self, data):
        try:
            record = self.find_question(data['questionId'])
            if record:
                record['_id'] = str(record['_id'])
                self.write({'status': 200, 'msg': 'OK', 'question': record})
            else:
                self.write({'status': 400, 'msg': 'Not exist', 'question': None})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def get_todays_question(self, data):
        try:
            user = self.find_user(data['sessionToken'])
            if user:
                question = self.find_question(user['todaysQuestion']['questionId'])
                if question:
                    record = {'text': question['text'],
                              'answered': question['answered'],
                              'questionId': str(question['_id']),
                              'deliveredAt': user['todaysQuestion']['deliveredAt'],
                              }
                    self.write({'status': 200, 'msg': 'OK', 'question': record})
                else:
                    self.write({'status': 400, 'msg': 'Failed to find todaysQuestion', 'question': None})
            else:
                self.write({'status': 400, 'msg': 'Invalid seesionToken', 'question': None})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))


if __name__ == "__main__":
    global SVR
    global DB
    global LOGGER

    port = sys.argv[1]
    logging.basicConfig(format='%(asctime)-15s %(message)s')
    LOGGER = logging.getLogger('app_server')
    opts = dict(logger=LOGGER, config_fname='./conf/api.conf.json')

    client = pymongo.MongoClient()
    if len(sys.argv) < 3:
        database_name = 'test_database'
        # database_name = 'real_database'
    elif sys.argv[2] == 'test':
        database_name = 'unittest_database'
    else:
        raise Exception('Invalid argument:' % sys.argv[2])

    LOGGER.info('Use database: %s' % database_name)
    DB = client[database_name]

    application = tornado.web.Application([(r'/app/(.+)', RequestHandler, opts)])

    LOGGER.info('Ready to serve. (port: %s)' % port)

    SVR = tornado.httpserver.HTTPServer(application)
    SVR.listen(int(port))
    tornado.ioloop.IOLoop.current().start()
