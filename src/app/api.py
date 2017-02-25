# -*- coding: utf-8 -*-
import datetime
import logging
import mimetypes
import os
import sys
import time
import uuid

import magic
import ujson as json

from bson.objectid import ObjectId
import pymongo

import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.log import enable_pretty_logging

enable_pretty_logging()

STATIC_FS_ROOT = '/home/boram/static/'
STATIC_URL_ROOT = 'http://indiweb08.cafe24.com:8888/'
VALID_EXTS = {'images': {'.png', '.jpg', '.jpeg', '.gif', '.bmp'},
              'videos': {'.qt', '.mov', '.mp4', '.mkv', '.avi'},
              }


class RequestHandler(tornado.web.RequestHandler):

    def initialize(self, logger, config_fname):
        self.logger = logger
        self.opt = json.load(open(config_fname))
        self.post_book = {
            'createUser': self.create_user,
            'checkAlreadyJoin': self.check_already_join,
            'login': self.login,
            'logout': self.logout,
            'getUserInfo': self.get_user_info,
            'deleteUser': self.delete_user,
            'updateUserInfo': self.update_user_info,
            'addQuestion': self.add_question,
            'getQuestion': self.get_question,
            'getTodaysQuestion': self.get_todays_question,
            'createAnswer': self.create_answer,
            'getWillItem': self.get_willitem,
            'getWillItems': self.get_willitems,
            'uploadImage': self.upload_image,
            'uploadVideo': self.upload_video,
        }
        for k, f in self.post_book.iteritems():
            if k.startswith('upload'):
                continue
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
            if opcode.startswith('upload'):
                handler = self.post_book.get(opcode, None)
                if handler is None:
                    self.write_error(400, 'Invalid opcode: %s' % opcode)
                else:
                    handler()
            else:
                self.set_header('Content-Type', 'application/json')
                handler, required_fields, allowed_fields = self.post_book.get(opcode, (None, None, None))
                self.logger.info('Query: %s' % self.request.body)
                data = json.loads(self.request.body)
                if handler is None or required_fields is None or allowed_fields is None:
                    self.write_error(400, 'Invalid opcode: %s' % opcode)
                else:
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

    def is_existing_user(self, phone_num):
        if DB.users.find_one({'phoneNumber': phone_num}):
            return True
        else:
            return False

    def id_postprocessing(self, data, field):
        data[field] = str(data['_id'])
        data.pop('_id')
        return data

    def find_user(self, user_key):
        r = DB.users.find_one({'_id': ObjectId(user_key)})
        if r:
            return self.id_postprocessing(r, 'userID') if r['status'] == 'normal' else None
        else:
            return None

    def find_user_by_phonenumber(self, phone_number):
        r = DB.users.find_one({'phoneNumber': phone_number})
        return self.id_postprocessing(r, 'userID') if r else None

    def find_willitem(self, willitem_key):
        r = DB.items.find_one({'_id': ObjectId(willitem_key)})
        return self.id_postprocessing(r, 'willitemID') if r else None

    def find_question(self, question_key):
        r = DB.questions.find_one({'_id': ObjectId(question_key)})
        return self.id_postprocessing(r, 'questionID') if r else None

    def get_random_question(self):
        # not random yet...
        r = DB.questions.find_one({})
        return self.id_postprocessing(r, 'questionID') if r else None

    def _get_willitem(self, data):
        willitem = self.find_willitem(data['willitemID'])
        if willitem:
            if willitem['authorID'] == data['sessionToken']:
                question = self.find_question(willitem['questionID'])
                if question:
                    willitem['willitemID'] = willitem['willitemID']
                    willitem['text'] = question['text']
                    willitem['answers'] = sorted(willitem['answers'].itervalues(),
                                                 key=lambda x: x['modifiedAt'],
                                                 reverse=True)
                    return willitem, 'OK'
                else:
                    return None, 'Question is not exist'
            else:
                return None, 'Invalid sessionToken'
        else:
            return None, 'The willitem is not exist'

    def generate_answer_id(self, willitem_id, num_answers):
        return '%s_%s' % (willitem_id, num_answers)

    @tornado.gen.coroutine
    def create_user(self, data):
        try:
            if not self.is_valid_ts(data['birthDay']):
                self.write_error(400, 'Invalid birthDay value')
            elif self.is_existing_user(data['phoneNumber']):
                self.write_error(400, 'The phone number is already exist')
            else:
                now_ts = int(time.time())
                todays_question = self.get_random_question()
                if not todays_question:
                    self.write_error(400, 'Failed to get todays question')
                else:
                    record = {'userName': data['userName'],
                              'phoneNumber': data['phoneNumber'],
                              'password': data['password'],
                              'birthDay': data['birthDay'],
                              'deviceToken': '',
                              'profileImageUrl': '',
                              'pushDuration': self.opt['settings']['user']['pushDuration'],
                              'willitems': {},
                              'receivers': [],
                              'lastLoginTime': now_ts,
                              'todaysQuestion': {
                                  'questionID': todays_question['questionID'],
                                  'deliveredAt': now_ts
                                  },
                              'status': 'normal'
                              }
                    users = DB.users
                    user_id = users.insert_one(record)
                    self.write({'status': 200, 'msg': 'OK', 'sessionToken': str(user_id.inserted_id)})
                    self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def login(self, data):
        try:
            record = self.find_user_by_phonenumber(data['phoneNumber'])
            if record:
                if record['password'] == data['password']:
                    DB.users.find_one_and_update({'_id': ObjectId(record['userID'])},
                                                 {'$set': {'lastLoginTime': int(time.time()), 'status': 'normal'}}
                                                )
                    self.write({'status': 200, 'msg': 'OK', 'sessionToken': str(record['userID'])})
                else:
                    self.write({'status': 400, 'msg': 'Password is not matched', 'user': None})
            else:
                self.write({'status': 400, 'msg': 'Not exist', 'user': None})
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def logout(self, data):
        try:
            record = self.find_user(data['sessionToken'])
            if record:
                users = DB.users
                users.find_one_and_update({'_id': ObjectId(record['userID'])},
                                          {'$set': {'status': "logout", 'deviceToken': ""}})
                self.write({'status': 200, 'msg': 'OK'})
            else:
                self.write({'status': 400, 'msg': 'Not exist'})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def check_already_join(self, data):
        try:
            if self.is_existing_user(data['phoneNumber']):
                self.write({'status': 200, 'msg': 'OK', 'result': True})
            else:
                self.write({'status': 200, 'msg': 'Not exist', 'result': False})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def get_user_info(self, data):
        try:
            record = self.find_user(data['sessionToken'])
            if record:
                self.write({'status': 200, 'msg': 'OK', 'user': record})
            else:
                self.write({'status': 400, 'msg': 'Not exist', 'user': None})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def delete_user(self, data):
        try:
            record = self.find_user(data['sessionToken'])
            if record:
                users = DB.users
                users.find_one_and_update({'_id': ObjectId(record['userID'])}, {'$set': {'status': "deleted"}})
                self.write({'status': 200, 'msg': 'OK'})
            else:
                self.write({'status': 400, 'msg': 'Not exist'})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def update_user_info(self, data):
        try:
            record = self.find_user(data['sessionToken'])
            if record:
                fields = {'profileImageUrl', 'pushDuration', 'lastLoginAlarmDuration', 'deviceToken'}
                record_updated = {f: v for f, v in data.iteritems() if f in fields}
                if len(record_updated) > 0:
                    DB.users.find_one_and_update({'_id': ObjectId(record['userID'])}, {'$set': record_updated})
                self.write({'status': 200, 'msg': 'OK'})
            else:
                self.write({'status': 400, 'msg': 'Not exist'})
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
            self.write({'status': 200, 'msg': 'OK', 'questionID': str(question_id.inserted_id)})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def get_question(self, data):
        try:
            record = self.find_question(data['questionID'])
            if record:
                self.write({'status': 200, 'msg': 'OK', 'question': record})
            else:
                self.write({'status': 400, 'msg': 'Not exist'})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def get_todays_question(self, data):
        try:
            user = self.find_user(data['sessionToken'])
            if user:
                question = self.find_question(user['todaysQuestion']['questionID'])
                if question:
                    record = {'text': question['text'],
                              'answered': question['answered'],
                              'questionID': question['questionID'],
                              'deliveredAt': user['todaysQuestion']['deliveredAt'],
                              }
                    res = {'status': 200, 'msg': 'OK', 'question': record}
                    user_willitem = user['willitems'].get(record['questionID'], None)
                    if user_willitem:
                        willitem, _ = self._get_willitem({'sessionToken': data['sessionToken'],
                                                          'willitemID': user_willitem['willitemID']})
                        if willitem:
                            res['willitem'] = willitem
                    self.write(res)
                else:
                    self.write({'status': 400, 'msg': 'Failed to find todaysQuestion', 'question': None})
            else:
                self.write({'status': 400, 'msg': 'Invalid seesionToken', 'question': None})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def create_answer(self, data):
        try:
            user = self.find_user(data['sessionToken'])
            question = self.find_question(data['questionID'])
            if user and question:
                answer = {'answerText': data.get('answerText', None),
                          'answerPhoto': data.get('answerPhoto', None),
                          'answerVideo': data.get('answerVideo', None),
                          'receivers': data.get('receivers', []),
                          'createdAt': int(time.time()),
                          'mediaWidth': data.get('mediaWidth', 0),
                          'mediaHeight': data.get('mediaHeight', 0),
                          'modifiedAt': int(time.time()),
                          'status': 'normal',
                          }
                user_willitem_info = user['willitems'].get(data['questionID'], None)
                if user_willitem_info:
                    willitem = self.find_willitem(user_willitem_info['willitemID'])
                    if willitem:
                        answer['answerID'] = self.generate_answer_id(willitem['willitemID'], str(willitem['size']))
                        DB.items.find_one_and_update({'_id': ObjectId(willitem['willitemID'])},
                                                     {'$set': {'modifiedAt': int(time.time()),
                                                               'answers.%s' % answer['answerID']: answer},
                                                      '$inc': {'size': 1},
                                                      }
                                                     )
                        DB.users.find_one_and_update({'_id': ObjectId(data['sessionToken'])},
                                                     {'$set': {'willitems.%s.modifiedAt' % data['questionID']: int(time.time())},
                                                      })
                        self.write({'status': 200, 'msg': 'OK', 'answerID': answer['answerID'], 'willitemID': str(willitem['willitemID'])})
                    else:
                        self.write({'status': 500, 'msg': 'Failed to find existing willitem'})
                else:
                    willitem = {'createdAt': int(time.time()),
                                'modifiedAt': int(time.time()),
                                'size': 1,
                                'answers': {},
                                'status': 'normal',
                                'authorID': user['userID'],
                                'questionID': data['questionID']
                                }
                    willitem_id = DB.items.insert_one(willitem)
                    user_willitem_info = {'modifiedAt': int(time.time()),
                                          'willitemID': str(willitem_id.inserted_id)}
                    answer['answerID'] = self.generate_answer_id(str(willitem_id.inserted_id), str(0))
                    DB.items.find_one_and_update({'_id': ObjectId(str(willitem_id.inserted_id))},
                                                 {'$set': {'answers.%s' % answer['answerID']: answer}
                                                  })
                    DB.users.find_one_and_update({'_id': ObjectId(data['sessionToken'])},
                                                 {'$set': {'willitems.%s' % data['questionID']: user_willitem_info},
                                                  })
                    self.write({'status': 200, 'msg': 'OK', 'answerID': answer['answerID'], 'willitemID': str(willitem_id.inserted_id)})
            else:
                self.write({'status': 400, 'msg': 'Invalid seesionToken or questionID', 'question': None})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def get_willitem(self, data):
        try:
            willitem, msg = self._get_willitem(data)
            if willitem:
                self.write({'status': 200, 'msg': msg, 'willitem': willitem})
            else:
                self.write({'status': 400, 'msg': msg})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def get_willitems(self, data):
        try:
            user = self.find_user(data['sessionToken'])
            if user:
                user_willitems = user['willitems']
                Q = [{'willitemID': w['willitemID'], 'sessionToken': data['sessionToken']}
                     for w in user_willitems.itervalues()]
                willitems = map(self._get_willitem, Q)
                willitems = [w for w, _ in willitems if w]
                willitems.sort(key=lambda x: x['modifiedAt'], reverse=True)
                self.write({'status': 200, 'msg': 'OK', 'size': len(willitems), 'willitems': willitems})
            else:
                self.write({'status': 400, 'msg': 'The user is not exist'})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    def select_ext(self, exts, data_type):
        candidates = set(exts) & VALID_EXTS[data_type]
        if len(candidates) == 0:
            raise Exception('Failed to selecte extension: %s' % ','.join(exts))
        else:
            self.logger.info('ext candidates: %s' % ','.join(exts))
            return list(candidates)[0]

    def get_extension(self, fname, data_type):
        mime_text = magic.from_buffer(open(fname).read(1024), mime=True)
        exts = mimetypes.guess_all_extensions(mime_text)
        return self.select_ext(exts, data_type)

    @tornado.gen.coroutine
    def _upload(self, data_type):
        try:
            cname = str(uuid.uuid4()) + '_' + str(uuid.uuid1())
            fname = os.path.join(STATIC_FS_ROOT, data_type, cname)
            with open(fname, 'w') as fout:
                fout.write(self.request.body)
            ext = self.get_extension(fname, data_type)
            fname_with_ext = fname + ext
            os.rename(fname, fname_with_ext)
            url = STATIC_URL_ROOT + data_type + '/' + cname + ext
            self.logger.info('uploaded: %s' % url)
            self.write({'status': 200, 'msg': 'OK', 'url': url})
            self.finish()
        except Exception as e:
            self.write_error(500, str(e))

    @tornado.gen.coroutine
    def upload_image(self):
        self._upload('images')

    @tornado.gen.coroutine
    def upload_video(self):
        self._upload('videos')


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
