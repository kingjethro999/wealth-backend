import asyncio
import argparse
from database import connect_to_mongo, close_mongo_connection
from models import User

async def make_admin(email: str):
    """Finds a user by email and sets their is_admin flag to True."""
    print(f"Attempting to make user with email '{email}' an admin...")
    try:
        await connect_to_mongo()
        
        user = await User.find_one(User.email == email)
        
        if not user:
            print(f"Error: User with email '{email}' not found.")
            return

        if user.is_admin:
            print(f"User '{email}' is already an admin.")
            return
            
        user.is_admin = True
        await user.save()
        
        print(f"Successfully promoted '{email}' to admin.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Admin management script for Wealth Investment API.")
    parser.add_argument("email", type=str, help="The email of the user to be promoted to admin.")
    
    args = parser.parse_args()
    
    asyncio.run(make_admin(args.email))
