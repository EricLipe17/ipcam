from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any


class CommonSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    version: str = "0.0.1"
    debug: bool = True
    pwd_context: CryptContext = CryptContext(
        schemes=["sha256_crypt"], deprecated="auto"
    )
    oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="/auth/token")
    jwt_secret_key: str = (
        "b35bcfc081aed758b535ce9dce99a41f4c71697dc39a83cfc33ac2f7db14fa89"
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 30
    allowed_origins: list[str] = ["*"]
    allowed_hosts: list[str] = ["*"]
    path_prefix: str = ""
    storage_dir: str = "/backend/app"
    db_config: Dict[str, Any] = {
        "POSTGRES_DB": "ipcam_project",
        "POSTGRES_PASSWORD": "something_secure",
        "POSTGRES_HOST": "postgres",
        "POSTGRES_PORT": 5432,
        "POSTGRES_USER": "ipcam_user",
    }


settings = CommonSettings()

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$5$rounds=535000$LNhX9Q7KdRIS.rv0$Xs3uJYH5lFAneoMoLVsDoV.ox2EnG6a54qLtF2XMiS.",
        "disabled": False,
    },
}
