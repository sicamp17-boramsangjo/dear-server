# -*- coding: utf-8 -*-

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
    result = db.questions.delete_many({})
    print '%s items deleted from %s.questions' % (int(result.deleted_count), db_name)


class AppServerTest(unittest.TestCase):
    # url_root = 'http://indiweb08.cafe24.com:23233/app/'
    url_root = 'http://localhost:23233/app/'

    @classmethod
    def setUp(self):
        delete_all_items_from_test_db()

    @classmethod
    def tearDown(self):
        delete_all_items_from_test_db()

    def test00(self):
        '''
        user creating & checking
        '''
        url = self.url_root + 'addQuestion'
        data1 = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        r1 = requests.post(url, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)

        data1 = {"userName": u"sjkim", "phoneNumber": u"010-1274-1352", "password": u"sjsj!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r1 = requests.post(url_create, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)

        data2 = {"userName": u"김철수", "phoneNumber": u"010-8274-1252", "password": u"sjsj!", "birthDay": 49881200}
        r2 = requests.post(url_create, data=json.dumps(data2)).json()
        self.assertTrue(r2['status'] == 200)

        url_get = self.url_root + 'getUserInfo'
        for rr, dd in [(r1, data1), (r2, data2)]:
            ret = requests.post(url_get, data=json.dumps({"sessionToken": rr['sessionToken']})).json()
            for f in ['userName', 'password', 'phoneNumber', 'birthDay']:
                self.assertTrue(ret['status'] == 200)
                self.assertTrue(dd[f] == ret['user'][f])

        # duplicate phone number
        dupled_data = {"userName": u"artemis", "phoneNumber": u"010-1274-1352", "password": u"38fjfij1", "birthDay": 149881200}
        self.assertTrue(requests.post(url_create, data=json.dumps(dupled_data)).json()['status'] == 400)

        # invalid phone number
        invalid_data = {"userName": u"김철수", "phoneNumber": u"01082741252", "password": u"sjsj!", "birthDay": 49881200}
        self.assertTrue(requests.post(url_create, data=json.dumps(invalid_data)).json()['status'] == 400)

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
        data2 = {"questionId": r1['questionId']}
        r2 = requests.post(url, data=json.dumps(data2)).json()
        self.assertTrue(r2['status'] == 200)
        self.assertTrue(r2['question']['_id'] == r1['questionId'])
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

    def test03(self):
        '''
        user update info
        '''
        # url = self.url_root + 'updateUserInfo'
        #
        # # invalid sessionToken
        # data0 = {"sessionToken": u"58ac500abf825f120f773d22"}
        # r0 = requests.post(url, data=json.dumps(data0)).json()
        # self.assertTrue(r0['resultCode'] == 0)
        #
        # # insert user
        # data1 = {"userName": u"sjkim", "phoneNumber": u"010-1274-1352", "password": u"sjsj!", "birthDay": 49881200}
        # url_create = self.url_root + 'createUser'
        # r1 = requests.post(url_create, data=json.dumps(data1)).json()
        # self.assertTrue(r1['status'] == 200)
        #
        # # update user
        # data2 = {"sessionToken": r1['sessionToken']}
        # r2 = requests.post(url, data=json.dumps(data2)).json()
        # self.assertTrue(r2['status'] == 200)
        # self.assertTrue(r2['resultCode'] == 1)
        #
        # # update user including option fields
        # data3 = {"sessionToken": r1['sessionToken'], 'profileImageUrl': u"", 'pushDuration': 31536000, 'lastLoginAlarmDuration': u""} # FIXME fields values
        # r3 = requests.post(url, data=json.dumps(data3)).json()
        # self.assertTrue(r3['status'] == 200)
        # self.assertTrue(r3['resultCode'] == 1)

    def test04(self):
        '''
        delete user
        '''
        # url = self.url_root + 'deleteUser'
        #
        # # invalid sessionToken
        # data0 = {"sessionToken": u"58ac500abf825f120f773d22"}
        # r0 = requests.post(url, data=json.dumps(data0)).json()
        # self.assertTrue(r0['status'] == 400)
        #
        # # insert user
        # data1 = {"userName": u"sjkim", "phoneNumber": u"010-1274-1352", "password": u"sjsj!", "birthDay": 49881200}
        # url_create = self.url_root + 'createUser'
        # r1 = requests.post(url_create, data=json.dumps(data1)).json()
        # self.assertTrue(r1['status'] == 200)
        #
        # # delete user
        # data2 = {"sessionToken": r1['sessionToken']}
        # r2 = requests.post(url, data=json.dumps(data2)).json()
        # self.assertTrue(r2['status'] == 200)

    def test05(self):
        '''
        check already join
        '''
        url_check_already_join = self.url_root + 'checkAlreadyJoin'

        url_add_question = self.url_root + 'addQuestion'
        data0 = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        r0 = requests.post(url_add_question, data=json.dumps(data0)).json()
        self.assertTrue(r0['status'] == 200)

        # create user
        data1 = {"userName": u"hhcha", "phoneNumber": u"011-1234-1233", "password": u"hhhh!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r1 = requests.post(url_create, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)

        # get user info
        # data2 = {"sessionToken": r1['sessionToken']}
        # url_get_user_info = self.url_root + 'getUserInfo'
        # r2 = requests.post(url_get_user_info, data=json.dumps(data2)).json()
        # self.assertTrue(r1['status'] == 200)

        # invalid phoneNumber
        data2 = {"phoneNumber": u"011-1234-1233"}
        r2 = requests.post(url_check_already_join, data=json.dumps(data2)).json()
        self.assertTrue(r2['status'] == 200)
        self.assertTrue(r2['result'] == True)

        # valid phoneNumber
        data3 = {"phoneNumber": u"019-1234-1233"}
        r3 = requests.post(url_check_already_join, data=json.dumps(data3)).json()
        self.assertTrue(r3['status'] == 400)
        self.assertTrue(r3['result'] == False)
