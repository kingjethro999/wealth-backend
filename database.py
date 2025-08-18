from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import asyncio
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection URL from environment
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/wealthinvest")
DATABASE_NAME = os.getenv("DATABASE_NAME", "wealthinvest")

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None

# Global MongoDB instance
mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection with better error handling"""
    try:
        print("Attempting to connect to MongoDB...")
        print(f"Using database: {DATABASE_NAME}")
        
        # Create client with optimized settings for connection issues
        mongodb.client = AsyncIOMotorClient(
            MONGODB_URL,
            maxPoolSize=10,
            minPoolSize=1,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=45000,
            heartbeatFrequencyMS=10000,
            retryWrites=True,
            w="majority",
            directConnection=False,
            maxIdleTimeMS=50000,
        )
        
        # Test the connection
        await mongodb.client.admin.command('ping')
        print("MongoDB connection successful!")
        
        mongodb.database = mongodb.client[DATABASE_NAME]
        
        # Import models after MongoDB connection
        from models import User, Package, Investment, Transaction
        
        # Initialize beanie with the models
        await init_beanie(
            database=mongodb.database,
            document_models=[User, Package, Investment, Transaction]
        )
        print("Connected to MongoDB and initialized Beanie")
        
    except Exception as e:
        print(f"Failed to connect to MongoDB: {str(e)}")
        print("Possible solutions:")
        print("1. Check your internet connection")
        print("2. Verify your MongoDB Atlas credentials")
        print("3. Check if your IP address is whitelisted in MongoDB Atlas")
        print("4. Try using a standard connection string instead of SRV")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        print("Disconnected from MongoDB")

def get_database():
    """Get database instance"""
    return mongodb.database

# Alternative connection function with multiple retry strategies
async def connect_with_retry():
    """Connect with multiple strategies and retry logic"""
    connection_strings = [
        # Primary connection string from environment
        MONGODB_URL,
        
        # Fallback connection strings
        "mongodb+srv://emmanuelking:iamemmyking@cluster0.bkonqre.mongodb.net/wealthinvest?retryWrites=true&w=majority&appName=Cluster0&serverSelectionTimeoutMS=30000&connectTimeoutMS=30000&socketTimeoutMS=45000",
        
        # Local fallback (if you have local MongoDB for development)
        "mongodb://localhost:27017/wealthinvest"
    ]
    
    for i, connection_string in enumerate(connection_strings):
        try:
            print(f"Trying connection method {i + 1}...")
            
            mongodb.client = AsyncIOMotorClient(
                connection_string,
                maxPoolSize=10,
                minPoolSize=1,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=45000,
            )
            
            # Test connection
            await mongodb.client.admin.command('ping')
            print(f"Successfully connected using method {i + 1}")
            
            mongodb.database = mongodb.client[DATABASE_NAME]
            
            # Import and initialize models
            from models import User, Package, Investment, Transaction
            await init_beanie(
                database=mongodb.database,
                document_models=[User, Package, Investment, Transaction]
            )
            
            print("Connected to MongoDB and initialized Beanie")
            return
            
        except Exception as e:
            print(f"Connection method {i + 1} failed: {str(e)}")
            if mongodb.client:
                mongodb.client.close()
                mongodb.client = None
            
            if i == len(connection_strings) - 1:
                print("All connection methods failed!")
                raise
            else:
                print("Trying next connection method...")
                await asyncio.sleep(2)  # Wait before next attempt