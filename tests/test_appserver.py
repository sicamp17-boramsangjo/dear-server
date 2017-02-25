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
    result = db.invitations.delete_many({})
    print '%s items deleted from %s.invitations' % (int(result.deleted_count), db_name)


def generate_answer_id(willitem_id, size):
    return '%s_%s' % (willitem_id, size)


class AppServerTest(unittest.TestCase):
    url_root = 'http://indiweb08.cafe24.com:23233/app/'
    # url_root = 'http://localhost:23233/app/'

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
            self.assertTrue(ret['user']['status'] == "normal")

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
        self.assertTrue(r2['question']['questionID'] == r1['questionID'])
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
        self.assertTrue('willitem' not in r2)

    def test03(self):
        '''
        user update info
        '''
        url_add_question = self.url_root + 'addQuestion'
        data0 = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        r0 = requests.post(url_add_question, data=json.dumps(data0)).json()
        self.assertTrue(r0['status'] == 200)

        # insert user
        data1 = {"userName": u"sjkim", "phoneNumber": u"010-1274-1352", "password": u"sjsj!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r1 = requests.post(url_create, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)

        # update user
        url = self.url_root + 'updateUserInfo'
        data2 = {"sessionToken": r1['sessionToken']}
        r2 = requests.post(url, data=json.dumps(data2)).json()
        self.assertTrue(r2['status'] == 200)

        # update user including option fields
        data3 = {"sessionToken": r1['sessionToken'], "profileImageUrl": u"/static/profile_chh.png", "pushDuration": 15768000, "lastLoginAlarmDuration": 7884000}
        r3 = requests.post(url, data=json.dumps(data3)).json()
        self.assertTrue(r3['status'] == 200)

        url_get = self.url_root + 'getUserInfo'
        ret = requests.post(url_get, data=json.dumps({"sessionToken": r1['sessionToken']})).json()
        self.assertTrue(ret['status'] == 200)
        for f in ['profileImageUrl', 'pushDuration', 'lastLoginAlarmDuration']:
            self.assertTrue(data3[f] == ret['user'][f])

        # invalid sessionToken
        data4 = {"sessionToken": u"58ac500abf825f120f773d22"}
        r4 = requests.post(url, data=json.dumps(data4)).json()
        self.assertTrue(r4['status'] == 400)

    def test04(self):
        '''
        delete user
        '''
        url = self.url_root + 'deleteUser'

        # insert question
        url_add_question = self.url_root + 'addQuestion'
        data0 = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        r0 = requests.post(url_add_question, data=json.dumps(data0)).json()
        self.assertTrue(r0['status'] == 200)

        # insert user
        data1 = {"userName": u"sjkim", "phoneNumber": u"010-1274-1352", "password": u"sjsj!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r1 = requests.post(url_create, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)

        # delete user
        data2 = {"sessionToken": r1['sessionToken']}
        r2 = requests.post(url, data=json.dumps(data2)).json()
        self.assertTrue(r2['status'] == 200)

        url_get = self.url_root + 'getUserInfo'
        ret = requests.post(url_get, data=json.dumps({"sessionToken": r1['sessionToken']})).json()
        self.assertTrue(ret['status'] == 400)

        # invalid sessionToken
        data3 = {"sessionToken": u"58ac500abf825f120f773d22"}
        r3 = requests.post(url, data=json.dumps(data3)).json()
        self.assertTrue(r3['status'] == 400)

    def test05(self):
        '''
        check already join
        '''
        url_check_already_join = self.url_root + 'checkAlreadyJoin'

        # insert question
        url_add_question = self.url_root + 'addQuestion'
        data0 = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        r0 = requests.post(url_add_question, data=json.dumps(data0)).json()
        self.assertTrue(r0['status'] == 200)

        # create user
        data1 = {"userName": u"hhcha", "phoneNumber": u"011-1234-1233", "password": u"hhhh!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r1 = requests.post(url_create, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)

        # joined phoneNumber
        data2 = {"phoneNumber": data1['phoneNumber']}
        r2 = requests.post(url_check_already_join, data=json.dumps(data2)).json()
        self.assertTrue(r2['status'] == 200)
        self.assertTrue(r2['result'] == True)

        # not joined phoneNumber
        data3 = {"phoneNumber": u"019-1234-1233"}
        r3 = requests.post(url_check_already_join, data=json.dumps(data3)).json()
        self.assertTrue(r3['status'] == 200)
        self.assertTrue(r3['result'] == False)

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

        data = {"text": u"가장 기억에 남는 여행은?"}
        r_q3 = requests.post(url, data=json.dumps(data)).json()
        self.assertTrue(r_q3['status'] == 200)

        data = {"userName": u"sjkim", "phoneNumber": u"010-1274-1352", "password": u"sjsj!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r_user = requests.post(url_create, data=json.dumps(data)).json()
        self.assertTrue(r_user['status'] == 200)

        # add receiver
        url_add_receiver = self.url_root + 'addReceiver'
        data_rcv1 = {"sessionToken": r_user['sessionToken'], "name": u"누렁이", "phoneNumber": u"011-1234-1233"}
        r_rcv1 = requests.post(url_add_receiver, data=json.dumps(data_rcv1)).json()
        self.assertTrue(r_rcv1['status'] == 200)

        data_rcv2 = {"sessionToken": r_user['sessionToken'], "name": u"바둑이", "phoneNumber": u"010-1934-1233"}
        r_rcv2 = requests.post(url_add_receiver, data=json.dumps(data_rcv2)).json()
        self.assertTrue(r_rcv2['status'] == 200)

        rcv1 = r_rcv1['receiverID']
        rcv2 = r_rcv2['receiverID']

        data = {'sessionToken': r_user['sessionToken']}
        url_todayq = self.url_root + 'getTodaysQuestion'
        r_todayq = requests.post(url_todayq, data=json.dumps(data)).json()
        self.assertTrue(r_todayq['status'] == 200)
        self.assertTrue('question' in r_todayq)
        self.assertTrue('willitem' not in r_todayq)
        question_id = r_todayq['question']['questionID']

        # create 1st answer
        url_create_ans = self.url_root + 'createAnswer'
        data_ans = {'sessionToken': r_user['sessionToken'],
                    'questionID': question_id,
                    'answerText': u'맨날 그래',
                    'mediaWidth': 120,
                    'mediaHeight': 80,
                    'receivers': [rcv1, rcv2],
                    }
        r_create_ans = requests.post(url_create_ans, data=json.dumps(data_ans)).json()
        self.assertTrue(r_create_ans['status'] == 200)
        self.assertTrue(r_create_ans['answerID'] == '%s_%s' % (r_create_ans['willitemID'], str(0)))
        time.sleep(1)

        # create 2nd answer
        data_ans2 = {'sessionToken': r_user['sessionToken'],
                     'questionID': question_id,
                     'answerText': u'이게 무슨 질문이지',
                    'receivers': [rcv1],
                     }
        r_create_ans2 = requests.post(url_create_ans, data=json.dumps(data_ans2)).json()
        self.assertTrue(r_create_ans2['status'] == 200)
        self.assertTrue(r_create_ans2['answerID'] == '%s_%s' % (r_create_ans2['willitemID'], str(1)))
        time.sleep(1)

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
        self.assertTrue(willitem['questionID'] == question_id)
        answers = willitem['answers']
        self.assertTrue(len(answers) == 2)
        self.assertTrue(answers[1]['answerText'] == data_ans['answerText'])
        self.assertTrue(answers[0]['answerText'] == data_ans2['answerText'])
        self.assertTrue(answers[1]['mediaWidth'] == data_ans['mediaWidth'])
        self.assertTrue(answers[1]['mediaHeight'] == data_ans['mediaHeight'])

        # check willitems
        url_get_willitems = self.url_root + 'getWillItems'
        data_get_willitems = {'sessionToken': r_user['sessionToken']}
        r_get_willitems = requests.post(url_get_willitems, data=json.dumps(data_get_willitems)).json()
        self.assertTrue(r_get_willitems['status'] == 200)
        self.assertTrue(r_get_willitems['size'] == 1)
        willitems = r_get_willitems['willitems']
        self.assertTrue(willitems[0] == willitem)
        time.sleep(1)

        data_today2 = {'sessionToken': r_user['sessionToken']}
        url_todayq2 = self.url_root + 'getTodaysQuestion'
        r_todayq2 = requests.post(url_todayq2, data=json.dumps(data_today2)).json()
        self.assertTrue(r_todayq2['status'] == 200)
        self.assertTrue('willitem' in r_todayq2)
        self.assertTrue(r_todayq2['willitem']['willitemID'] == willitem['willitemID'])

        # add a answer for another question
        url_create_ans = self.url_root + 'createAnswer'
        data_ans2 = {'sessionToken': r_user['sessionToken'],
                     'questionID': r_q2['questionID'],
                     'answerText': u'인생은 아름다워',
                     }
        r_create_ans_a1 = requests.post(url_create_ans, data=json.dumps(data_ans2)).json()
        self.assertTrue(r_create_ans_a1['status'] == 200)
        self.assertTrue(r_create_ans_a1['answerID'] == generate_answer_id(r_create_ans_a1['willitemID'], str(0))
                        or r_create_ans_a1['answerID'] == generate_answer_id(r_create_ans_a1['willitemID'], str(2)))

        # check created answers
        url_get_willitem = self.url_root + 'getWillItem'
        data_get_willitem = {'willitemID': r_create_ans_a1['willitemID'],
                             'sessionToken': r_user['sessionToken'],
                             }
        r_get_willitem2 = requests.post(url_get_willitem, data=json.dumps(data_get_willitem)).json()
        self.assertTrue(r_get_willitem2['status'] == 200)
        willitem2 = r_get_willitem2['willitem']
        self.assertTrue(willitem2['size'] in {1, 3})

        # re-check willitems
        url_get_willitems = self.url_root + 'getWillItems'
        data_get_willitems = {'sessionToken': r_user['sessionToken']}
        r_get_willitems = requests.post(url_get_willitems, data=json.dumps(data_get_willitems)).json()
        self.assertTrue(r_get_willitems['status'] == 200)
        self.assertTrue(r_get_willitems['size'] in {1, 2})
        willitems = r_get_willitems['willitems']
        self.assertTrue(willitem2 in willitems)

        data_get_willitems = {'sessionToken': '111111111111111111111111'}
        r_get_willitems = requests.post(url_get_willitems, data=json.dumps(data_get_willitems)).json()
        self.assertTrue(r_get_willitems['status'] == 400)

        # get another question
        time.sleep(1)
        another_question_id = None
        for r_q in [r_q1, r_q2, r_q3]:
            if question_id != r_q['questionID']:
                another_question_id = r_q['questionID']

        url_create_ans = self.url_root + 'createAnswer'
        data_ans2 = {'sessionToken': r_user['sessionToken'],
                     'questionID': another_question_id,
                     'answerText': u'아하하하',
                     'receivers': [rcv1],
                     }
        r_create_ans_a1 = requests.post(url_create_ans, data=json.dumps(data_ans2)).json()
        self.assertTrue(r_create_ans_a1['status'] == 200)

        # check willitems_with_receiver
        url_get_willitems_with_receiver = self.url_root + 'getWillItemsWithReceiver'
        data_11 = {'sessionToken': r_user['sessionToken'], 'receiverID': rcv1}
        r_11 = requests.post(url_get_willitems_with_receiver, data=json.dumps(data_11)).json()
        self.assertTrue(r_11['status'] == 200)
        self.assertTrue(len(r_11['willitems']) == 2)
        self.assertTrue(len(r_11['willitems'][0]['answers']) == 1)
        self.assertTrue(len(r_11['willitems'][1]['answers']) == 2)

        data_12 = {'sessionToken': r_user['sessionToken'], 'receiverID': rcv2}
        r_12 = requests.post(url_get_willitems_with_receiver, data=json.dumps(data_12)).json()
        self.assertTrue(r_12['status'] == 200)
        self.assertTrue(len(r_12['willitems']) == 1)
        self.assertTrue(len(r_12['willitems'][0]['answers']) == 1)

    def test06_logout(self):
        '''
        logout
        '''
        url_logout = self.url_root + 'logout'

        # insert question
        url_add_question = self.url_root + 'addQuestion'
        data0 = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        r0 = requests.post(url_add_question, data=json.dumps(data0)).json()
        self.assertTrue(r0['status'] == 200)

        # create user
        data1 = {"userName": u"hhcha", "phoneNumber": u"011-1234-1233", "password": u"hhhh!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r1 = requests.post(url_create, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)

        # logout
        data2 = {"sessionToken": r1['sessionToken']}
        r2 = requests.post(url_logout, data=json.dumps(data2)).json()
        self.assertTrue(r2['status'] == 200)

        url_get_user_info = self.url_root + 'getUserInfo'
        r3 = requests.post(url_get_user_info, data=json.dumps(data2)).json()
        self.assertTrue(r3['status'] == 400)

    def test07_readonly(self):
        # insert question
        url_add_question = self.url_root + 'addQuestion'
        data0 = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        r0 = requests.post(url_add_question, data=json.dumps(data0)).json()
        self.assertTrue(r0['status'] == 200)

        # create user
        data1 = {"userName": u"hhcha", "phoneNumber": u"011-1234-1233", "password": u"hhhh!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r1 = requests.post(url_create, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)
        self.assertTrue('readOnlyToken' in r1)

        # get readonly session-key by readOnlyToken
        data_ro = {"readOnlyToken": r1["readOnlyToken"], "birthDay": 49881200}
        url_readonly = self.url_root + 'getSessionTokenForReadOnly'
        r_ro = requests.post(url_readonly, data=json.dumps(data_ro)).json()
        self.assertTrue(r_ro['status'] == 200)
        self.assertTrue(r_ro['sessionToken'] == r1['sessionToken'])

        '''
        data_ro2 = {"readOnlyToken": r1["readOnlyToken"], "birthDay": 49871200}
        r_ro2 = requests.post(url_readonly, data=json.dumps(data_ro2)).json()
        self.assertTrue(r_ro2['status'] == 400)
        '''

    def test07_receiver(self):
        '''
        receiver add
        '''
        # insert question
        url_add_question = self.url_root + 'addQuestion'
        data0 = {"text": u"현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"}
        r0 = requests.post(url_add_question, data=json.dumps(data0)).json()
        self.assertTrue(r0['status'] == 200)

        # create user
        data1 = {"userName": u"hhcha", "phoneNumber": u"011-1234-1233", "password": u"hhhh!", "birthDay": 49881200}
        url_create = self.url_root + 'createUser'
        r1 = requests.post(url_create, data=json.dumps(data1)).json()
        self.assertTrue(r1['status'] == 200)
        self.assertTrue('readOnlyToken' in r1)

        # add receiver
        url_add_receiver = self.url_root + 'addReceiver'
        data2 = {"sessionToken": r1['sessionToken'], "name": u"홍길동", "phoneNumber": u"011-1234-1233"}
        r2 = requests.post(url_add_receiver, data=json.dumps(data2)).json()
        self.assertTrue(r2['status'] == 200)

        # add receiver
        data3 = {"sessionToken": r1['sessionToken'], "name": u"심청이", "phoneNumber": u"010-1222-3344"}
        r3 = requests.post(url_add_receiver, data=json.dumps(data3)).json()
        self.assertTrue(r3['status'] == 200)

        # get receiver
        url_get_receivers = self.url_root + 'getReceivers'
        data5 = {"sessionToken": r1['sessionToken']}
        r5 = requests.post(url_get_receivers, data=json.dumps(data5)).json()
        self.assertTrue(r5['status'] == 200)

        # confirm add
        self.assertTrue(len(r5['receivers']) == 2)

        # remove receiver
        data4 = {"sessionToken": r1['sessionToken'], 'receiverID': r2['receiverID']}
        url_remove_receiver = self.url_root + 'removeReceiver'
        r4 = requests.post(url_remove_receiver, data=json.dumps(data4)).json()
        self.assertTrue(r4['status'] == 200)

        # confirm remove
        r6 = requests.post(url_get_receivers, data=json.dumps(data5)).json()
        self.assertTrue(len(r6['receivers']) == 1)
