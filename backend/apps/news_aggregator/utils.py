"""
Utility functions for news aggregator app
"""
from pymongo import MongoClient
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """MongoDB connection manager for document storage"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self):
        """Get or create MongoDB client"""
        if self._client is None:
            try:
                self._client = MongoClient(
                    settings.MONGO_CONFIG['connection_string'],
                    serverSelectionTimeoutMS=5000
                )
                # Test connection
                self._client.admin.command('ping')
                logger.info("MongoDB connection established")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
        
        return self._client
    
    def get_database(self):
        """Get MongoDB database"""
        client = self.get_client()
        return client[settings.MONGO_CONFIG['database']]
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("MongoDB connection closed")


# Singleton instance
mongodb = MongoDBConnection()


def get_mongodb():
    """Get MongoDB database instance"""
    return mongodb.get_database()


def store_document(collection_name: str, document: dict):
    """Store a document in MongoDB"""
    try:
        db = get_mongodb()
        collection = db[collection_name]
        result = collection.insert_one(document)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error storing document in {collection_name}: {e}")
        raise


def get_document(collection_name: str, document_id: str):
    """Retrieve a document from MongoDB"""
    try:
        from bson import ObjectId
        db = get_mongodb()
        collection = db[collection_name]
        return collection.find_one({"_id": ObjectId(document_id)})
    except Exception as e:
        logger.error(f"Error retrieving document from {collection_name}: {e}")
        return None