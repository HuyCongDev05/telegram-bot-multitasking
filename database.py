"""Triển khai cơ sở dữ liệu PostgreSQL (Supabase)

Sử dụng máy chủ PostgreSQL để lưu trữ dữ liệu
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List

import psycopg2
import psycopg2.extras
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv

from netflix.cookie_utils import build_cookie_fingerprint, sanitize_cookie_text

# Tải biến môi trường
load_dotenv()

logger = logging.getLogger(__name__)

_BUILD_SIG = "687579636f6e676465763035"


class MySQLDatabase:
    """Lớp quản lý cơ sở dữ liệu PostgreSQL"""

    def __init__(self):
        """Khởi tạo kết nối cơ sở dữ liệu"""
        import os

        # Ưu tiên sử dụng Connection String (DATABASE_URL) từ Supabase
        self.database_url = os.getenv('DATABASE_URL')
        
        # Nếu không có DATABASE_URL, xây dựng từ các biến lẻ
        if not self.database_url:
            from urllib.parse import quote_plus
            host = os.getenv('DB_HOST', os.getenv('MYSQL_HOST', 'localhost')).lstrip('@').strip()
            port = os.getenv('DB_PORT', os.getenv('MYSQL_PORT', 5432))
            user = quote_plus(os.getenv('DB_USER', os.getenv('MYSQL_USER', 'postgres')).strip())
            password = quote_plus(os.getenv('DB_PASSWORD', os.getenv('MYSQL_PASSWORD', 'password')).strip())
            dbname = os.getenv('DB_NAME', os.getenv('MYSQL_DATABASE', 'postgres')).strip()
            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

        logger.info("Khởi tạo cơ sở dữ liệu PostgreSQL với Connection Pool (Supavisor)")

        # Khóa xác thực cho các dịch vụ nội bộ
        self._val_key = bytes.fromhex("687579636f6e676465763035").decode()

        # Khởi tạo Connection Pool sử dụng DSN (Connection String)
        try:
            self.pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=self.database_url
            )
            logger.info("✅ Đã khởi tạo Connection Pool thành công (Supavisor Compatibility)")
        except Exception as e:
            logger.error(f"❌ Khởi tạo Connection Pool thất bại: {e}")
            raise

        self.init_database()

    @contextmanager
    def get_db_connection(self):
        """Context manager để lấy và trả kết nối về pool."""
        conn = self.pool.getconn()
        conn.autocommit = True
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

    def get_connection(self):
        """Lấy kết nối lẻ từ pool (để duy trì tính tương thích)"""
        return self.pool.getconn()

    def put_connection(self, conn):
        """Trả kết nối về pool"""
        self.pool.putconn(conn)

    @staticmethod
    def _column_exists(cursor, table_name: str, column_name: str) -> bool:
        """Kiểm tra cột đã tồn tại trong bảng chưa."""
        cursor.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s",
            (table_name, column_name)
        )
        return cursor.fetchone() is not None

    @staticmethod
    def _index_exists(cursor, table_name: str, index_name: str) -> bool:
        """Kiểm tra index đã tồn tại trong bảng chưa."""
        cursor.execute(
            "SELECT 1 FROM pg_indexes WHERE tablename = %s AND indexname = %s",
            (table_name, index_name)
        )
        return cursor.fetchone() is not None

    def _backfill_netflix_cookie_fingerprints(self, cursor) -> None:
        """Điền dấu vân tay cookie và xóa các bản ghi trùng lặp, giữ lại bản ghi cũ nhất."""
        cursor.execute(
            """
            SELECT id, cookie_text
            FROM netflix_cookies
            ORDER BY "createdAt" ASC, id ASC
            """
        )
        rows = cursor.fetchall()
        seen_fingerprints = set()

        for row_id, cookie_text in rows:
            fingerprint = build_cookie_fingerprint(cookie_text)
            if not fingerprint:
                continue

            if fingerprint in seen_fingerprints:
                cursor.execute("DELETE FROM netflix_cookies WHERE id = %s", (row_id,))
                continue

            seen_fingerprints.add(fingerprint)
            cursor.execute(
                "UPDATE netflix_cookies SET cookie_fingerprint = %s WHERE id = %s",
                (fingerprint, row_id),
            )

    def init_database(self):
        """Khởi tạo cấu trúc các bảng trong cơ sở dữ liệu"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                # Bảng người dùng
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users
                    (
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        full_name VARCHAR(255),
                        language VARCHAR(10) NULL,
                        balance INT DEFAULT 1,
                        is_blocked SMALLINT DEFAULT 0,
                        invited_by BIGINT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_checkin TIMESTAMP NULL
                    )
                    """
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_username ON users (username)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_invited_by ON users (invited_by)")

                if not self._column_exists(cursor, 'users', 'language'):
                    cursor.execute(
                        """
                        ALTER TABLE users
                        ADD COLUMN language VARCHAR(10) NULL
                        """
                    )

                # Bảng ghi chép mời bạn bè
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS invitations
                    (
                        id SERIAL PRIMARY KEY,
                        inviter_id BIGINT NOT NULL,
                        invitee_id BIGINT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (inviter_id) REFERENCES users (user_id),
                        FOREIGN KEY (invitee_id) REFERENCES users (user_id)
                    )
                    """
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_inviter ON invitations (inviter_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_invitee ON invitations (invitee_id)")

                # Bảng ghi chép xác thực
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS verifications
                    (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        verification_type VARCHAR(50) NOT NULL,
                        verification_url TEXT,
                        verification_id VARCHAR(255),
                        status VARCHAR(50) NOT NULL,
                        result TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                    """
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ver_user_id ON verifications (user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ver_type ON verifications (verification_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ver_created ON verifications (created_at)")

                # Bảng thẻ nạp (card key)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS card_keys
                    (
                        id SERIAL PRIMARY KEY,
                        key_code VARCHAR(100) UNIQUE NOT NULL,
                        balance INT NOT NULL,
                        max_uses INT DEFAULT 1,
                        current_uses INT DEFAULT 0,
                        expire_at TIMESTAMP NULL,
                        created_by BIGINT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_key_code ON card_keys (key_code)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ck_created_by ON card_keys (created_by)")

                # Bảng ghi chép sử dụng thẻ nạp
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS card_key_usage
                    (
                        id SERIAL PRIMARY KEY,
                        key_code VARCHAR(100) NOT NULL,
                        user_id BIGINT NOT NULL,
                        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cku_key_code ON card_key_usage (key_code)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cku_user_id ON card_key_usage (user_id)")

                # Bảng live_cc
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS live_cc
                    (
                        id BIGSERIAL PRIMARY KEY,
                        bin VARCHAR(255),
                        month VARCHAR(10),
                        year VARCHAR(10),
                        cvv VARCHAR(10),
                        status VARCHAR(65),
                        bank VARCHAR(255),
                        country VARCHAR(100),
                        brand VARCHAR(100),
                        card_type VARCHAR(50),
                        level VARCHAR(100),
                        checkAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                # Đảm bảo các cột mới tồn tại cho các DB cũ
                new_columns = [
                    ('bank', 'VARCHAR(255)'),
                    ('country', 'VARCHAR(100)'),
                    ('brand', 'VARCHAR(100)'),
                    ('card_type', 'VARCHAR(50)'),
                    ('level', 'VARCHAR(100)')
                ]
                for col_name, col_type in new_columns:
                    if not self._column_exists(cursor, 'live_cc', col_name):
                        cursor.execute(f"ALTER TABLE live_cc ADD COLUMN {col_name} {col_type}")

                # Bảng proxies
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS proxies
                    (
                        id SERIAL PRIMARY KEY,
                        address VARCHAR(65) NOT NULL,
                        port VARCHAR(20) NOT NULL,
                        username VARCHAR(255),
                        password VARCHAR(65),
                        city VARCHAR(255),
                        country VARCHAR(100),
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (address, port, username, password)
                    )
                    """
                )

                # Migration cho proxies: Chuyển updatedAt (nếu có) sang updated_at hoặc thêm mới
                if not self._column_exists(cursor, 'proxies', 'updated_at'):
                    # Kiểm tra nếu tồn tại updatedAt (Postgres sẽ là updatedat)
                    if self._column_exists(cursor, 'proxies', 'updatedat'):
                        cursor.execute("ALTER TABLE proxies RENAME COLUMN updatedat TO updated_at")
                    else:
                        cursor.execute("ALTER TABLE proxies ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                # Bảng lưu kho cookie Netflix
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS netflix_cookies
                    (
                        id BIGSERIAL PRIMARY KEY,
                        cookie_text TEXT NOT NULL,
                        cookie_fingerprint VARCHAR(64) NULL,
                        createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT uniq_netflix_cookie_fingerprint UNIQUE (cookie_fingerprint)
                    )
                    """
                )

                # Điền dấu vân tay cho cookie Netflix (nếu có dữ liệu cũ)
                self._backfill_netflix_cookie_fingerprints(cursor)

                # Bảng dịch vụ bảo trì
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS services_maintenance
                    (
                        service_id VARCHAR(100) PRIMARY KEY,
                        is_maintenance SMALLINT DEFAULT 0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                # Khởi tạo các dịch vụ mặc định (nếu chưa có)
                default_services = [
                    'verify_chatgpt_k12', 'verify_spotify_student', 'verify_bolt_teacher',
                    'verify_youtube_student', 'verify_gemini_pro', 'convert_url_login_app_netflix',
                    'check_cc', 'discord_quest_auto', 'check_cookie_netflix', 'get_cookie_netflix'
                ]
                for service in default_services:
                    cursor.execute(
                        "INSERT INTO services_maintenance (service_id, is_maintenance) VALUES (%s, 0) ON CONFLICT DO NOTHING",
                        (service,)
                    )

                logger.info("Hoàn tất khởi tạo các bảng cơ sở dữ liệu")

            except Exception as e:
                logger.error(f"Khởi tạo cơ sở dữ liệu thất bại: {e}")
                raise
            finally:
                cursor.close()

    def create_user(
            self, user_id: int, username: str, full_name: str, invited_by: Optional[int] = None
    ) -> bool:
        """Tạo người dùng mới"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO users (user_id, username, full_name, invited_by, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (user_id, username, full_name, invited_by),
                )

                if invited_by:
                    cursor.execute(
                        "UPDATE users SET balance = balance + 2 WHERE user_id = %s",
                        (invited_by,),
                    )

                    cursor.execute(
                        """
                        INSERT INTO invitations (inviter_id, invitee_id, created_at)
                        VALUES (%s, %s, NOW())
                        """,
                        (invited_by, user_id),
                    )

                return True

            except psycopg2.IntegrityError:
                return False
            except Exception as e:
                logger.error(f"Tạo người dùng thất bại: {e}")
                return False
            finally:
                cursor.close()

    def update_user_profile(self, user_id: int, username: str, full_name: str) -> bool:
        """Cập nhật username/full name mới nhất của người dùng."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE users
                    SET username = %s, full_name = %s
                    WHERE user_id = %s
                    """,
                    (username, full_name, user_id),
                )
                return True
            except Exception as e:
                logger.error(f"Cập nhật hồ sơ người dùng thất bại: {e}")
                return False
            finally:
                cursor.close()

    def set_user_language(self, user_id: int, language: str) -> bool:
        """Lưu ngôn ngữ người dùng đã chọn."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE users SET language = %s WHERE user_id = %s",
                    (language, user_id),
                )
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"Cập nhật ngôn ngữ người dùng thất bại: {e}")
                return False
            finally:
                cursor.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin người dùng"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                row = cursor.fetchone()

                if row:
                    result = dict(row)
                    if result.get('created_at'):
                        result['created_at'] = result['created_at'].isoformat()
                    if result.get('last_checkin'):
                        result['last_checkin'] = result['last_checkin'].isoformat()
                    return result
                return None
            finally:
                cursor.close()

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Lấy thông tin người dùng bằng username"""
        if username.startswith('@'):
            username = username[1:]

        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                row = cursor.fetchone()

                if row:
                    result = dict(row)
                    if result.get('created_at'):
                        result['created_at'] = result['created_at'].isoformat()
                    if result.get('last_checkin'):
                        result['last_checkin'] = result['last_checkin'].isoformat()
                    return result
                return None
            finally:
                cursor.close()

    def user_exists(self, user_id: int) -> bool:
        """Kiểm tra người dùng có tồn tại không"""
        return self.get_user(user_id) is not None

    def get_user_language(self, user_id: int) -> Optional[str]:
        """Lấy ngôn ngữ đã lưu của người dùng."""
        user = self.get_user(user_id)
        if not user:
            return None
        return user.get("language")

    def is_user_blocked(self, user_id: int) -> bool:
        """Kiểm tra người dùng có bị chặn (blacklisted) không"""
        user = self.get_user(user_id)
        return user and user["is_blocked"] == 1

    def block_user(self, user_id: int) -> bool:
        """Chặn người dùng"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE users SET is_blocked = 1 WHERE user_id = %s", (user_id,))
                return True
            except Exception as e:
                logger.error(f"Chặn người dùng thất bại: {e}")
                return False
            finally:
                cursor.close()

    def unblock_user(self, user_id: int) -> bool:
        """Hủy chặn người dùng"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE users SET is_blocked = 0 WHERE user_id = %s", (user_id,))
                return True
            except Exception as e:
                logger.error(f"Hủy chặn thất bại: {e}")
                return False
            finally:
                cursor.close()

    def get_blacklist(self) -> List[Dict]:
        """Lấy danh sách đen"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute("SELECT * FROM users WHERE is_blocked = 1")
                return list(cursor.fetchall())
            finally:
                cursor.close()

    def add_balance(self, user_id: int, amount: int) -> bool:
        """Cộng điểm cho người dùng"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                    (amount, user_id),
                )
                return True
            except Exception as e:
                logger.error(f"Cộng điểm thất bại: {e}")
                return False
            finally:
                cursor.close()

    def deduct_balance(self, user_id: int, amount: int) -> bool:
        """Trừ điểm của người dùng"""
        user = self.get_user(user_id)
        if not user or user["balance"] < amount:
            return False

        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE users SET balance = balance - %s WHERE user_id = %s",
                    (amount, user_id),
                )
                return True
            except Exception as e:
                logger.error(f"Trừ điểm thất bại: {e}")
                return False
            finally:
                cursor.close()

    def checkin(self, user_id: int) -> bool:
        """Người dùng điểm danh"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                # Sử dụng CURRENT_DATE thay cho CURDATE() của PostgreSQL
                cursor.execute(
                    """
                    UPDATE users
                    SET balance      = balance + 1,
                        last_checkin = NOW()
                    WHERE user_id = %s
                      AND (
                              last_checkin IS NULL
                                  OR DATE(last_checkin) < CURRENT_DATE
                        )
                    """,
                    (user_id,),
                )
                success = cursor.rowcount > 0
                return success
            except Exception as e:
                logger.error(f"Điểm danh thất bại: {e}")
                return False
            finally:
                cursor.close()

    def add_verification(
            self, user_id: int, verification_type: str, verification_url: str,
            status: str, result: str = "", verification_id: str = ""
    ) -> bool:
        """Thêm ghi chép xác thực"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO verifications
                    (user_id, verification_type, verification_url, verification_id, status, result, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (user_id, verification_type, verification_url, verification_id, status, result),
                )
                return True
            except Exception as e:
                logger.error(f"Thêm ghi chép xác thực thất bại: {e}")
                return False
            finally:
                cursor.close()

    def get_user_verifications(self, user_id: int) -> List[Dict]:
        """Lấy danh sách ghi chép xác thực của người dùng"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute(
                    """
                    SELECT *
                    FROM verifications
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    """,
                    (user_id,),
                )
                return list(cursor.fetchall())
            finally:
                cursor.close()

    def create_card_key(
            self, key_code: str, balance: int, created_by: int,
            max_uses: int = 1, expire_days: Optional[int] = None
    ) -> bool:
        """Tạo thẻ nạp (card key)"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                expire_at = None
                if expire_days:
                    expire_at = datetime.now() + timedelta(days=expire_days)

                logger.info(
                    f"Đang tạo mã thẻ: {key_code}, Balance: {balance}, Max uses: {max_uses}, Created by: {created_by}, Expire: {expire_at}")

                cursor.execute(
                    """
                    INSERT INTO card_keys (key_code, balance, max_uses, created_by, created_at, expire_at)
                    VALUES (%s, %s, %s, %s, NOW(), %s)
                    """,
                    (key_code, balance, max_uses, created_by, expire_at),
                )
                logger.info(f"✅ Mã thẻ {key_code} đã được tạo thành công")
                return True

            except psycopg2.IntegrityError:
                logger.error(f"Thẻ nạp đã tồn tại: {key_code}")
                return False
            except Exception as e:
                logger.error(f"Tạo thẻ nạp thất bại: {e}")
                return False
            finally:
                cursor.close()

    def use_card_key(self, key_code: str, user_id: int) -> Optional[int]:
        """Sử dụng thẻ nạp, trả về số điểm nhận được"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute(
                    "SELECT * FROM card_keys WHERE key_code = %s",
                    (key_code,),
                )
                card = cursor.fetchone()

                if not card:
                    return None

                if card["expire_at"] and datetime.now() > card["expire_at"]:
                    return -2

                if card["current_uses"] >= card["max_uses"]:
                    return -1

                cursor.execute(
                    "SELECT COUNT(*) as count FROM card_key_usage WHERE key_code = %s AND user_id = %s",
                    (key_code, user_id),
                )
                count = cursor.fetchone()
                if count['count'] > 0:
                    return -3

                cursor.execute(
                    "UPDATE card_keys SET current_uses = current_uses + 1 WHERE key_code = %s",
                    (key_code,),
                )

                cursor.execute(
                    "INSERT INTO card_key_usage (key_code, user_id, used_at) VALUES (%s, %s, NOW())",
                    (key_code, user_id),
                )

                cursor.execute(
                    "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                    (card["balance"], user_id),
                )

                return card["balance"]

            except Exception as e:
                logger.error(f"Sử dụng thẻ nạp thất bại: {e}")
                return None
            finally:
                cursor.close()

    def get_card_key_info(self, key_code: str) -> Optional[Dict]:
        """Lấy thông tin thẻ nạp"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute("SELECT * FROM card_keys WHERE key_code = %s", (key_code,))
                return cursor.fetchone()
            finally:
                cursor.close()

    def get_all_card_keys(self, created_by: Optional[int] = None) -> List[Dict]:
        """Lấy tất cả thẻ nạp"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                if created_by:
                    cursor.execute(
                        "SELECT * FROM card_keys WHERE created_by = %s ORDER BY created_at DESC",
                        (created_by,),
                    )
                else:
                    cursor.execute("SELECT * FROM card_keys ORDER BY created_at DESC")

                return list(cursor.fetchall())
            finally:
                cursor.close()

    def get_all_user_ids(self) -> List[int]:
        """Lấy tất cả ID người dùng"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT user_id FROM users")
                rows = cursor.fetchall()
                return [row[0] for row in rows]
            finally:
                cursor.close()

    def get_all_users(self) -> List[Dict]:
        """Lấy tất cả thông tin người dùng"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    user_data = dict(row)
                    if user_data.get('created_at'):
                        user_data['created_at'] = user_data['created_at'].isoformat()
                    if user_data.get('last_checkin'):
                        user_data['last_checkin'] = user_data['last_checkin'].isoformat()
                    result.append(user_data)
                return result
            finally:
                cursor.close()

    def add_live_cc(
            self, bin_num: str, month: str, year: str, cvv: str, status: str,
            bank: str = None, country: str = None, brand: str = None,
            card_type: str = None, level: str = None
    ) -> bool:
        """Lưu thẻ Live hoặc Real vào database"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO live_cc (bin, month, year, cvv, status, bank, country, brand, card_type, level, checkAt)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (bin_num, month, year, cvv, status, bank, country, brand, card_type, level)
                )
                return True
            except Exception as e:
                logger.error(f"Thêm live cc thất bại: {e}")
                return False
            finally:
                cursor.close()

    def get_live_ccs(self, limit: int = 100) -> List[Dict]:
        """Lấy danh sách CC Live"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute(
                    "SELECT * FROM live_cc ORDER BY checkAt DESC LIMIT %s",
                    (limit,)
                )
                return list(cursor.fetchall())
            finally:
                cursor.close()

    def save_netflix_cookie(self, cookie_text: str) -> str:
        """Lưu một cookie Netflix vào kho"""
        normalized_cookie_text = sanitize_cookie_text(cookie_text)
        if not normalized_cookie_text:
            return "invalid"

        cookie_fingerprint = build_cookie_fingerprint(normalized_cookie_text)
        if not cookie_fingerprint:
            return "invalid"

        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT id FROM netflix_cookies WHERE cookie_fingerprint = %s LIMIT 1",
                    (cookie_fingerprint,),
                )
                if cursor.fetchone():
                    return "duplicate"

                cursor.execute(
                    """
                    INSERT INTO netflix_cookies (cookie_text, cookie_fingerprint, createdAt)
                    VALUES (%s, %s, NOW())
                    """,
                    (normalized_cookie_text, cookie_fingerprint),
                )
                return "stored"
            except psycopg2.IntegrityError:
                return "duplicate"
            except Exception as e:
                logger.error(f"Thêm cookie Netflix thất bại: {e}")
                return "error"
            finally:
                cursor.close()

    def add_netflix_cookie(self, cookie_text: str) -> bool:
        """Lưu một cookie Netflix vào kho."""
        return self.save_netflix_cookie(cookie_text) == "stored"

    def get_netflix_cookies(self, limit: int = 20, randomize: bool = False) -> List[Dict]:
        """Lấy danh sách cookie Netflix."""
        order_clause = "ORDER BY RANDOM()" if randomize else "ORDER BY createdAt ASC, id ASC"
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute(
                    f"""
                    SELECT id, cookie_text, createdAt
                    FROM netflix_cookies
                    {order_clause}
                    LIMIT %s
                    """,
                    (limit,),
                )
                return list(cursor.fetchall())
            finally:
                cursor.close()

    def get_random_netflix_cookie(self) -> Optional[Dict]:
        """Lấy một cookie Netflix ngẫu nhiên"""
        cookies = self.get_netflix_cookies(limit=1, randomize=True)
        return cookies[0] if cookies else None

    def delete_netflix_cookie(self, cookie_id: int) -> bool:
        """Xóa một cookie Netflix"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM netflix_cookies WHERE id = %s", (cookie_id,))
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"Xóa cookie Netflix {cookie_id} thất bại: {e}")
                return False
            finally:
                cursor.close()

    def count_netflix_cookies(self) -> int:
        """Đếm số cookie Netflix"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM netflix_cookies")
                row = cursor.fetchone()
                return int(row[0]) if row else 0
            finally:
                cursor.close()

    def get_all_service_status(self) -> Dict[str, bool]:
        """Lấy trạng thái bảo trì"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute("SELECT service_id, is_maintenance FROM services_maintenance")
                rows = cursor.fetchall()
                return {row['service_id']: bool(row['is_maintenance']) for row in rows}
            finally:
                cursor.close()

    def toggle_service_maintenance(self, service_id: str) -> Optional[bool]:
        """Đảo ngược trạng thái bảo trì"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT is_maintenance FROM services_maintenance WHERE service_id = %s", (service_id,))
                row = cursor.fetchone()
                if row is None:
                    cursor.execute("INSERT INTO services_maintenance (service_id, is_maintenance) VALUES (%s, 1)",
                                   (service_id,))
                    new_status = True
                else:
                    new_status = not bool(row[0])
                    cursor.execute("UPDATE services_maintenance SET is_maintenance = %s WHERE service_id = %s",
                                   (int(new_status), service_id))
                return new_status
            except Exception as e:
                logger.error(f"Lỗi khi toggle bảo trì cho {service_id}: {e}")
                return None
            finally:
                cursor.close()

    def is_service_maintenance(self, service_id: str) -> bool:
        """Kiểm tra dịch vụ bảo trì"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT is_maintenance FROM services_maintenance WHERE service_id = %s", (service_id,))
                row = cursor.fetchone()
                return bool(row[0]) if row else False
            finally:
                cursor.close()

    def add_proxy(self, address: str, port: str, username: Optional[str] = None, password: Optional[str] = None,
                  city: Optional[str] = None, country: Optional[str] = None) -> bool:
        """Thêm proxy mới"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO proxies (address, port, username, password, city, country)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (address, port, username, password)
                    DO UPDATE SET city = EXCLUDED.city, country = EXCLUDED.country
                    """,
                    (address, port, username, password, city, country)
                )
                return True
            except Exception as e:
                logger.error(f"Thêm proxy thất bại {address}:{port}: {e}")
                return False
            finally:
                cursor.close()

    def get_random_proxy(self) -> Optional[Dict]:
        """Lấy một proxy ngẫu nhiên"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute("SELECT * FROM proxies ORDER BY RANDOM() LIMIT 1")
                return cursor.fetchone()
            finally:
                cursor.close()

    def get_all_proxies(self) -> List[Dict]:
        """Lấy tất cả proxy"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cursor.execute("SELECT * FROM proxies ORDER BY updated_at DESC")
                return list(cursor.fetchall())
            finally:
                cursor.close()

    def update_proxy_info(self, proxy_id: int, city: str, country: str) -> bool:
        """Cập nhật thông tin proxy"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE proxies SET city = %s, country = %s WHERE id = %s",
                    (city, country, proxy_id)
                )
                return True
            except Exception as e:
                logger.error(f"Cập nhật proxy {proxy_id} thất bại: {e}")
                return False
            finally:
                cursor.close()

    def delete_proxy(self, proxy_id: int) -> bool:
        """Xóa proxy"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM proxies WHERE id = %s", (proxy_id,))
                return True
            except Exception as e:
                logger.error(f"Xóa proxy {proxy_id} thất bại: {e}")
                return False
            finally:
                cursor.close()

    def proxy_exists(self, address, port, username, password) -> bool:
        """Kiểm tra proxy tồn tại"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT id FROM proxies WHERE address = %s AND port = %s AND username = %s AND password = %s",
                    (address, port, username, password)
                )
                return cursor.fetchone() is not None
            finally:
                cursor.close()


# Tạo bí danh cho instance toàn cục
Database = MySQLDatabase
