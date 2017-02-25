# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import uuid

from bson.objectid import ObjectId
import pymongo


def push(user_key):
    client = pymongo.MongoClient()
    database_name = 'test_database'
    print 'Database:', database_name
    DB = client[database_name]
    # dump json file
    user = DB.users.find_one({'_id': ObjectId(user_key)})
    if not user:
        print 'Failed to find user:', user_key
        return
    question = DB.questions.find_one({'_id': ObjectId(user['todaysQuestion']['questionID'])})
    if not question:
        print 'Failed to find question:', question
    d = {"name": user['userName'], "devices": [user['deviceToken']], "question": question["text"]}
    data = [d]
    fname = os.path.join('/home/boram/sjkim/server/src/push/to_send', str(uuid.uuid4()) + '.json')
    with open(fname, 'w') as fout:
        json.dump(data, fout)
    print 'Data dumped:', fname
    print 'Pushing...'
    ret = subprocess.call(['node', '/home/boram/sjkim/server/src/push/index2.js', fname])
    print ret
    print 'Delete file:', fname
    # os.remove(fname)
    print 'Done'


if __name__ == '__main__':
    if len(sys.argv) == 2:
        push(sys.argv[1])
