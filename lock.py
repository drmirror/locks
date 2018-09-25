#!/usr/local/bin/python                                                                                   
from pymongo import MongoClient
from time import time

def init(session, coll, x):
    if coll.count({"_id":x}) == 0:
        try:
            coll.insert_one({"_id":x, "locked":False})
        except:
            pass # somebody else has inserted the document before us, that's fine                         

def lock(session, coll, x):
    while True:
        result = coll.update_one(
            { "_id" : x, "locked" : False },
            { "$set" : { "locked" : True } },
            session=session)
        if result.modified_count == 1: break
        time = session.operation_time
        cursor = coll.watch([ {"$match" : { "documentKey._id" : x,
                                            "updateDescription.updatedFields.locked" : False }}],
                            start_at_operation_time=time, session=session)
        cursor.next()

def unlock(session, coll, x):
    coll.update_one( {"_id" : x}, { "$set" : { "locked" : False } }, session=session)

try:
    client = MongoClient("localhost:27000")
    session = client.start_session()
    coll = client["test"]["locks"]

    init(session, coll, 1)

    i=0
    start_time = time()
    while True:
        lock(session, coll, 1)
        unlock(session, coll, 1)
        i += 1
        if i % 1000 == 0:
            now = time()
            delta_time = now - start_time
            start_time = now
            print ("{} cycles/s".format(1000.0 / delta_time))

except KeyboardInterrupt:
    unlock(session, coll, 1)
    print ("keyboard interrupt, cleaned up")
