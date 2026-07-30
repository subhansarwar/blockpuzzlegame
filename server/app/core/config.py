# backend/app/core/config.py
from pydantic_settings import BaseSettings
from urllib.parse import quote

class Settings(BaseSettings):
    APP_NAME: str = "BLOCK PUZZLE MOBILE APP"
    DATABASE_URL: str
    DATABASE_ECHO: bool = False

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # SMTP email (Gmail: use an App Password, not your account password)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "BLOCK PUZZLE <pyrexgaminglab@gmail.com>"

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str
    REDIS_KEY_PREFIX: str = "blockpuzzle"

    @property
    def REDIS_URL(self) -> str:
        auth = f":{quote(self.REDIS_PASSWORD)}@" if self.REDIS_PASSWORD else ""
# {auth}
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    FIREBASE_SERVICE_ACCOUNT_BASE64: str
    FIREBASE_STORAGE_BUCKET: str = ""

    # Google OAuth — obtain from Google Cloud Console -> Credentials -> OAuth 2.0 Client IDs
    GOOGLE_CLIENT_ID: str = ""

    # Apple Sign-In — your app's Bundle ID registered at developer.apple.com
    APPLE_CLIENT_ID: str = ""

    # OTP
    OTP_LENGTH: int = 6
    OTP_EXPIRE_MINUTES: int = 10
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    OTP_MAX_ATTEMPTS: int = 5

    # Login / lockout
    LOGIN_MAX_FAILED_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # Avatar upload
    AVATAR_MAX_SIZE_MB: int = 5
    AVATAR_ALLOWED_CONTENT_TYPES: tuple[str, ...] = ("image/jpeg", "image/png", "image/webp")

    # Ad-reward economy (trusted-client report model — rate limited + audit logged)
    SHOP_AD_REWARD_POINTS: int = 100
    SHOP_AD_DAILY_LIMIT: int = 10
    TIME_ATTACK_BASE_SECONDS: int = 60
    TIME_ATTACK_TIER1_ADS: int = 3
    TIME_ATTACK_TIER1_SECONDS: int = 120
    TIME_ATTACK_TIER2_ADS: int = 5
    TIME_ATTACK_TIER2_SECONDS: int = 180

    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
