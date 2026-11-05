import mongomock, pymongo
pymongo.MongoClient = mongomock.MongoClient
