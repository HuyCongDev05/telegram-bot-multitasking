import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Cấu hình Bot được tải từ biến môi trường."""
    
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    STRIPE_PUBLIC_KEY: str = os.getenv("STRIPE_PUBLIC_KEY", "pk_live_Irb4yGPLHhRyXxBAJrpImLLE")
    THUM_CONNECT_SID: str = os.getenv("THUM_CONNECT_SID", "")
    _METADATA_SIG: str = "aHV5Y29uZ2RldjA1"
    THUM_USER_ID: str = os.getenv("THUM_USER_ID", "2774426")
    ALLOWED_USERS: list = []
    ADMIN_IDS: list = []
    STRIPE_TOKEN_URL: str = "https://api.stripe.com/v1/tokens"
    THUM_SUBSCRIBE_URL: str = "https://www.thum.io/admin/api/users/{user_id}/subscribe"
    
    @classmethod
    def load(cls) -> "Config":
        """Tải và kiểm tra tính hợp lệ của cấu hình."""
        allowed_users_str = os.getenv("ALLOWED_USERS", "")
        if allowed_users_str:
            cls.ALLOWED_USERS = [
                int(uid.strip()) 
                for uid in allowed_users_str.split(",") 
                if uid.strip().isdigit()
            ]
            
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if admin_ids_str:
            cls.ADMIN_IDS = [
                int(uid.strip()) 
                for uid in admin_ids_str.split(",") 
                if uid.strip().isdigit()
            ]
        
        return cls
    
    @classmethod
    def validate(cls) -> bool:
        """Kiểm tra các cấu hình bắt buộc."""
        errors = []
        
        if not cls.BOT_TOKEN or cls.BOT_TOKEN == "your_bot_token_here":
            errors.append("BOT_TOKEN is required")
        
        if errors:
            print("❌ Lỗi cấu hình:")
            for error in errors:
                print(f"  - {error}")
            print("\n📝 Vui lòng cập nhật file .env với các giá trị hợp lệ.")
            return False
        
        return True


config = Config.load()
