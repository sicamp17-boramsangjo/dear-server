# -*- coding: utf-8 -*-
import time
import ujson as json
import unittest

import pymongo
import requests


def delete_all_items_from_test_db(db_name='unittest_database'):
    assert 'test' in db_name
    print 'Delete all documents from unittest-db'
    client = pymongo.MongoClient()
    db = client[db_name]
    result = db.users.delete_many({})
    print '%s items deleted from %s.users' % (int(result.deleted_count), db_name)
    result = db.items.delete_many({})
    print '%s items deleted from %s.items' % (int(result.deleted_count), db_name)
    result = db.questions.delete_many({})
    print '%s items deleted from %s.questions' % (int(result.deleted_count), db_name)


class AppServerTest(unittest.TestCase):
    url_root = 'http://indiweb08.cafe24.com:23233/app/'

    @classmethod
    def setUp(self):
        delete_all_items_from_test_db()

    @classmethod
    def tearDown(self):
        delete_all_items_from_test_db()

    def test00(self):
        '''
        user creating & checking & login
        '''
        url = self.url_root + 'addQuestion'
        data1 = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        r1 = requests.post(url, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)

        data1 = {"userName": u"sjkim", "phoneNumber": u"010-1274-1352", "password": u"sjsj!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r1 = requests.post(url_create, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)

        data2 = {"userName": u"김철수", "phoneNumber": u"010-8274-1252", "password": u"sjsjbb2!", "birthDay": 49881200}
        r2 = requests.post(url_create, data=json.dumps(data2)).json()
        self.assertTrue(r2['status'] == 200)

        url_login = self.url_root + 'login'
        data_login1 = {"phoneNumber": "010-8274-1252", "password": "sjsjbb2!"}
        r_login1 = requests.post(url_login, data=json.dumps(data_login1)).json()
        self.assertTrue(r_login1['status'] == 200)
        self.assertTrue(r_login1['sessionToken'] == r2['sessionToken'])

        # password matching failed
        data_login2 = {"phoneNumber": "010-8274-1252", "password": "sjsjbb2"}
        r_login2 = requests.post(url_login, data=json.dumps(data_login2)).json()
        self.assertTrue(r_login2['status'] == 400)

        url_get = self.url_root + 'getUserInfo'
        for rr, dd in [(r1, data1), (r2, data2)]:
            ret = requests.post(url_get, data=json.dumps({"sessionToken": rr['sessionToken']})).json()
            for f in ['userName', 'password', 'phoneNumber', 'birthDay']:
                self.assertTrue(ret['status'] == 200)
                self.assertTrue(dd[f] == ret['user'][f])

        # duplicate phone number
        dupled_data = {"userName": u"artemis", "phoneNumber": u"010-1274-1352", "password": u"38fjfij1", "birthDay": 149881200}
        self.assertTrue(requests.post(url_create, data=json.dumps(dupled_data)).json()['status'] == 400)

        # invalid birthday
        invalid_data = {"userName": u"김철수", "phoneNumber": u"010-8274-1252", "password": u"sjsj!", "birthDay": 498812002727}
        self.assertTrue(requests.post(url_create, data=json.dumps(invalid_data)).json()['status'] == 400)

        # missing required fields
        invalid_data = {"userNam": u"김철수", "phoneNumber": u"010-8274-1252", "password": u"sjsj!"}
        self.assertTrue(requests.post(url_create, data=json.dumps(invalid_data)).json()['status'] == 400)

        # not allowed fields
        invalid_data = {"userName": u"김철수", "phoneNumber": u"010-8274-7788", "password": u"sjsj!", "birthDay": 49881200, "friendName": u'김영희'}
        r = requests.post(url_create, data=json.dumps(invalid_data)).json()
        self.assertTrue(r['status'] == 400)

    def test01(self):
        '''
        question creating & checking
        '''
        url = self.url_root + 'addQuestion'
        data1 = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        r1 = requests.post(url, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)

        url = self.url_root + 'getQuestion'
        data2 = {"questionID": r1['questionID']}
        r2 = requests.post(url, data=json.dumps(data2)).json()
        self.assertTrue(r2['status'] == 200)
        self.assertTrue(r2['question']['_id'] == r1['questionID'])
        self.assertTrue(r2['question']['text'] == data1['text'])

    def test02(self):
        '''
        today's question
        '''
        url = self.url_root + 'addQuestion'
        data0 = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        r0 = requests.post(url, data=json.dumps(data0)).json()
        self.assertTrue(r0['status'] == 200)

        data1 = {"userName": u"sjkim", "phoneNumber": u"010-1274-1352", "password": u"sjsj!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r1 = requests.post(url_create, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)

        url_today = self.url_root + 'getTodaysQuestion'
        data2 = {"sessionToken": r1['sessionToken']}
        r2 = requests.post(url_today, data=json.dumps(data2)).json()
        self.assertTrue(r2['status'] == 200)
        self.assertTrue('question' in r2)


    def test03_willitem01(self):
        '''
        create willitem & check
        '''
        data = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        url = self.url_root + 'addQuestion'
        r_q1 = requests.post(url, data=json.dumps(data)).json()
        self.assertTrue(r_q1['status'] == 200)

        data = {"text": u"가장 재밌게 보셨던 영화 제목은?"}
        r_q2 = requests.post(url, data=json.dumps(data)).json()
        self.assertTrue(r_q2['status'] == 200)

        data = {"userName": u"sjkim", "phoneNumber": u"010-1274-1352", "password": u"sjsj!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r_user = requests.post(url_create, data=json.dumps(data)).json()
        self.assertTrue(r_user['status'] == 200)

        data = {'sessionToken': r_user['sessionToken']}
        url_todayq = self.url_root + 'getTodaysQuestion'
        r_todayq = requests.post(url_todayq, data=json.dumps(data)).json()
        self.assertTrue(r_todayq['status'] == 200)
        question_id = r_todayq['question']['questionID']

        # create 1st answer
        url_create_ans = self.url_root + 'createAnswer'
        data_ans = {'sessionToken': r_user['sessionToken'],
                    'questionID': question_id,
                    'answerText': u'맨날 그래',
                    }
        r_create_ans = requests.post(url_create_ans, data=json.dumps(data_ans)).json()
        self.assertTrue(r_create_ans['status'] == 200)
        self.assertTrue(r_create_ans['answerID'] == str(0))

        # create 2nd answer
        data_ans2 = {'sessionToken': r_user['sessionToken'],
                    'questionID': question_id,
                    'answerText': u'이게 무슨 질문이지',
                    }
        r_create_ans2 = requests.post(url_create_ans, data=json.dumps(data_ans2)).json()
        self.assertTrue(r_create_ans2['status'] == 200)
        self.assertTrue(r_create_ans2['answerID'] == str(1))

        self.assertTrue(r_create_ans['willitemID'] == r_create_ans2['willitemID'])

        # create 3rd answer (invalid request)
        data_ans3 = {'sessionToken': r_user['sessionToken'],
                    'questionID': question_id + 'a',
                    'answerText': u'이게 무슨 질문이지33333',
                    }
        r_create_ans3 = requests.post(url_create_ans, data=json.dumps(data_ans3)).json()
        self.assertTrue(r_create_ans3['status'] == 500)

        # check created answers
        url_get_willitem = self.url_root + 'getWillItem'
        data_get_willitem = {'willitemID': r_create_ans2['willitemID'],
                             'sessionToken': r_user['sessionToken'],
                             }
        r_get_willitem = requests.post(url_get_willitem, data=json.dumps(data_get_willitem)).json()
        self.assertTrue(r_get_willitem['status'] == 200)
        willitem = r_get_willitem['willitem']
        self.assertTrue(willitem['size'] == 2)
        self.assertTrue(willitem['authorID'] == r_user['sessionToken'])
        self.assertTrue(willitem['status'] == 'normal')
        self.assertTrue(willitem['question']['_id'] == question_id)
        answers = willitem['answers']
        self.assertTrue(len(answers) == 2)
        self.assertTrue(answers[str(0)]['answerText'] == data_ans['answerText'])
        self.assertTrue(answers[str(1)]['answerText'] == data_ans2['answerText'])

        # check willitems
        url_get_willitems = self.url_root + 'getWillItems'
        data_get_willitems = {'sessionToken': r_user['sessionToken']}
        r_get_willitems = requests.post(url_get_willitems, data=json.dumps(data_get_willitems)).json()
        self.assertTrue(r_get_willitems['status'] == 200)
        self.assertTrue(r_get_willitems['size'] == 1)
        willitems = r_get_willitems['willitems']
        self.assertTrue(willitems[0] == willitem)
        time.sleep(1)

        # add a answer for another question
        url_create_ans = self.url_root + 'createAnswer'
        data_ans2 = {'sessionToken': r_user['sessionToken'],
                     'questionID': r_q2['questionID'],
                     'answerText': u'인생은 아름다워',
                     }
        r_create_ans_a1 = requests.post(url_create_ans, data=json.dumps(data_ans2)).json()
        self.assertTrue(r_create_ans_a1['status'] == 200)
        self.assertTrue(r_create_ans_a1['answerID'] == str(0))

        # check created answers
        url_get_willitem = self.url_root + 'getWillItem'
        data_get_willitem = {'willitemID': r_create_ans_a1['willitemID'],
                             'sessionToken': r_user['sessionToken'],
                             }
        r_get_willitem2 = requests.post(url_get_willitem, data=json.dumps(data_get_willitem)).json()
        self.assertTrue(r_get_willitem2['status'] == 200)
        willitem2 = r_get_willitem2['willitem']
        self.assertTrue(willitem2['size'] == 1)

        # re-check willitems
        url_get_willitems = self.url_root + 'getWillItems'
        data_get_willitems = {'sessionToken': r_user['sessionToken']}
        r_get_willitems = requests.post(url_get_willitems, data=json.dumps(data_get_willitems)).json()
        self.assertTrue(r_get_willitems['status'] == 200)
        self.assertTrue(r_get_willitems['size'] == 2)
        willitems = r_get_willitems['willitems']
        self.assertTrue(willitems[1] == willitem)
        self.assertTrue(willitems[0] == willitem2)
