# Locking documents in MongoDB
Here's some sample code that shows how to lock a document in MongoDB. The idea is that your document has a boolean flag, `locked`, which is either `false` (document is not locked), or `true` (document is locked). Applications are only allowed to change the document if they first acquire the lock by setting it to `true`. Once done, the application clears the lock by setting it back to `false`.

This is called **advisory locking**. In order for it to work, applications must play by the rules. There is nothing that prevents an application from changing a document without acquiring the lock first. (Note that since MongoDB 4.0, ACID transactions let you protect documents from concurrent modifications in a **mandatory** way, which means applications cannot get around it. But it is also more complex than the simple locking scheme shown here.)

The key requirement for this kind of locking is to **test and set** the lock in the same, atomic operation. In other words, the code needs to determine whether the `locked` attribute is currently `false`, and if so, set it to `true`, without any other process having a chance to intervene between the _test_ and the _set_. Fortunately, that is exactly how an update in MongoDB works, and so we can just write:

``result = db.locks.updateOne({"_id":1, "locked":false}, {"$set":{"locked":true}})``

To determine whether the operation succeeded, we can check the value of `result.modifiedCount`. If it is 1, we know that the update succeeded, and that **we** were the one that actually set `locked` to `true`. But what if the update failed? What if the `locked` attribute is currently `true` and we have to wait until whoever is using it clears the lock again?

A simple way to do that would be check the lock again and again and again until finally we find it to be `false` and then immediately set it to `true` ourselves. This is called "busy waiting". The problem is that it wastes CPU resources. Ideally, you'd want the application to go to sleep and be woken up by the operating system once the lock is open. The way to do that in MongoDB is to open up a **change stream** on the document. When the application listens to the change stream, it blocks, or sleeps, until the event happens that it is waiting for. Here's the code:

``db.locks.watch([ { "$match" : { "documentKey._id" : 1,
                     "updateDescription.updatedFields.locked" : false }} ])``
                     
In the actual code, you will see that this is just a little more complex, because we need to make sure that we listen only to changes that happen *after* we ourselves checked the document the last time. In order to do that, we open a client-side session and use the last operation time of that session as the starting point for the change stream that we watch.
