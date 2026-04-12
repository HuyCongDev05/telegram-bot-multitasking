"""Triển khai cơ sở dữ liệu MySQL

Sử dụng máy chủ MySQL để lưu trữ dữ liệu
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

from netflix.cookie_utils import build_cookie_fingerprint, sanitize_cookie_text

# Tải biến môi trường
load_dotenv()

logger = logging.getLogger(__name__)

_BUILD_SIG = "687579636f6e676465763035"


class MySQLDatabase:
    """Lớp quản lý cơ sở dữ liệu MySQL"""

    def __init__(self):
        """Khởi tạo kết nối cơ sở dữ liệu"""
        import os

        # Đọc cấu hình từ biến môi trường (khuyên dùng) hoặc sử dụng giá trị mặc định
        self.config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', '12345678'),
            'database': os.getenv('MYSQL_DATABASE', 'telegram-bot-verify'),
            'charset': 'utf8mb4',
            'autocommit': True,
        }
        logger.info(
            f"Khởi tạo cơ sở dữ liệu MySQL: {self.config['user']}@{self.config['host']}/{self.config['database']}")

        # Khóa xác thực cho các dịch vụ nội bộ
        self._val_key = bytes.fromhex("687579636f6e676465763035").decode()

        self.init_database()


    def get_connection(self):
        """Lấy kết nối cơ sở dữ liệu"""
        return pymysql.connect(**self.config)

    @staticmethod
    def _column_exists(cursor, table_name: str, column_name: str) -> bool:
        """Kiểm tra cột đã tồn tại trong bảng chưa."""
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE %s", (column_name,))
        return cursor.fetchone() is not None

    @staticmethod
    def _index_exists(cursor, table_name: str, index_name: str) -> bool:
        """Kiểm tra index đã tồn tại trong bảng chưa."""
        cursor.execute(f"SHOW INDEX FROM `{table_name}` WHERE Key_name = %s", (index_name,))
        return cursor.fetchone() is not None

    def _backfill_netflix_cookie_fingerprints(self, cursor) -> None:
        """Điền dấu vân tay cookie và xóa các bản ghi trùng lặp, giữ lại bản ghi cũ nhất."""
        cursor.execute(
            """
            SELECT id, cookie_text
            FROM netflix_cookies
            ORDER BY createdAt ASC, id ASC
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
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Bảng người dùng
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users
                (
                    user_id
                    BIGINT
                    PRIMARY
                    KEY,
                    username
                    VARCHAR
                (
                    255
                ),
                    full_name VARCHAR
                (
                    255
                ),
                    language VARCHAR
                (
                    10
                ) NULL,
                    balance INT DEFAULT 1,
                    is_blocked TINYINT
                (
                    1
                ) DEFAULT 0,
                    invited_by BIGINT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_checkin DATETIME NULL,
                    INDEX idx_username
                (
                    username
                ),
                    INDEX idx_invited_by
                (
                    invited_by
                )
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            if not self._column_exists(cursor, 'users', 'language'):
                cursor.execute(
                    """
                    ALTER TABLE users
                    ADD COLUMN language VARCHAR(10) NULL AFTER full_name
                    """
                )

            # Bảng ghi chép mời bạn bè
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS invitations
                (
                    id
                    INT
                    AUTO_INCREMENT
                    PRIMARY
                    KEY,
                    inviter_id
                    BIGINT
                    NOT
                    NULL,
                    invitee_id
                    BIGINT
                    NOT
                    NULL,
                    created_at
                    DATETIME
                    DEFAULT
                    CURRENT_TIMESTAMP,
                    INDEX
                    idx_inviter
                (
                    inviter_id
                ),
                    INDEX idx_invitee
                (
                    invitee_id
                ),
                    FOREIGN KEY
                (
                    inviter_id
                ) REFERENCES users
                (
                    user_id
                ),
                    FOREIGN KEY
                (
                    invitee_id
                ) REFERENCES users
                (
                    user_id
                )
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Bảng ghi chép xác thực
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS verifications
                (
                    id
                    INT
                    AUTO_INCREMENT
                    PRIMARY
                    KEY,
                    user_id
                    BIGINT
                    NOT
                    NULL,
                    verification_type
                    VARCHAR
                (
                    50
                ) NOT NULL,
                    verification_url TEXT,
                    verification_id VARCHAR
                (
                    255
                ),
                    status VARCHAR
                (
                    50
                ) NOT NULL,
                    result TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id
                (
                    user_id
                ),
                    INDEX idx_type
                (
                    verification_type
                ),
                    INDEX idx_created
                (
                    created_at
                ),
                    FOREIGN KEY
                (
                    user_id
                ) REFERENCES users
                (
                    user_id
                )
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Bảng thẻ nạp (card key)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS card_keys
                (
                    id
                    INT
                    AUTO_INCREMENT
                    PRIMARY
                    KEY,
                    key_code
                    VARCHAR
                (
                    100
                ) UNIQUE NOT NULL,
                    balance INT NOT NULL,
                    max_uses INT DEFAULT 1,
                    current_uses INT DEFAULT 0,
                    expire_at DATETIME NULL,
                    created_by BIGINT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_key_code
                (
                    key_code
                ),
                    INDEX idx_created_by
                (
                    created_by
                )
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Bảng ghi chép sử dụng thẻ nạp
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS card_key_usage
                (
                    id
                    INT
                    AUTO_INCREMENT
                    PRIMARY
                    KEY,
                    key_code
                    VARCHAR
                (
                    100
                ) NOT NULL,
                    user_id BIGINT NOT NULL,
                    used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_key_code
                (
                    key_code
                ),
                    INDEX idx_user_id
                (
                    user_id
                )
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Bảng live_cc
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS live_cc
                (
                    id
                    BIGINT
                    AUTO_INCREMENT
                    PRIMARY
                    KEY,
                    bin
                    VARCHAR
                (
                    255
                ),
                    month VARCHAR
                (
                    10
                ),
                    year VARCHAR
                (
                    10
                ),
                    cvv VARCHAR
                (
                    10
                ),
                    status VARCHAR
                (
                    65
                ),
                    checkAt DATETIME DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Bảng proxies
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS proxies
                (
                    id
                    INT
                    AUTO_INCREMENT
                    PRIMARY
                    KEY,
                    address
                    VARCHAR
                (
                    65
                ) NOT NULL,
                    port VARCHAR
                (
                    20
                ) NOT NULL,
                    username VARCHAR
                (
                    255
                ),
                    password VARCHAR
                (
                    65
                ),
                    city VARCHAR
                (
                    255
                ),
                    country VARCHAR
                (
                    100
                ),
                    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY idx_proxy
                (
                    address,
                    port,
                    username,
                    password
                )
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Bảng lưu kho cookie Netflix
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS netflix_cookies
                (
                    id
                    BIGINT
                    AUTO_INCREMENT
                    PRIMARY
                    KEY,
                    cookie_text
                    LONGTEXT
                    NOT
                    NULL,
                    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            if not self._column_exists(cursor, 'netflix_cookies', 'cookie_fingerprint'):
                cursor.execute(
                    """
                    ALTER TABLE netflix_cookies
                        ADD COLUMN cookie_fingerprint VARCHAR(64) NULL AFTER cookie_text
                    """
                )

            self._backfill_netflix_cookie_fingerprints(cursor)

            if not self._index_exists(cursor, 'netflix_cookies', 'uniq_netflix_cookie_fingerprint'):
                cursor.execute(
                    """
                    ALTER TABLE netflix_cookies
                        ADD UNIQUE KEY uniq_netflix_cookie_fingerprint (cookie_fingerprint)
                    """
                )

            # Bảng dịch vụ bảo trì
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS services_maintenance
                (
                    service_id
                    VARCHAR
                (
                    100
                ) PRIMARY KEY,
                    is_maintenance TINYINT
                (
                    1
                ) DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
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
                    "INSERT IGNORE INTO services_maintenance (service_id, is_maintenance) VALUES (%s, 0)",
                    (service,)
                )

            conn.commit()
            logger.info("Hoàn tất khởi tạo các bảng cơ sở dữ liệu MySQL")

        except Exception as e:
            logger.error(f"Khởi tạo cơ sở dữ liệu thất bại: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def create_user(
            self, user_id: int, username: str, full_name: str, invited_by: Optional[int] = None
    ) -> bool:
        """Tạo người dùng mới"""
        conn = self.get_connection()
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

            conn.commit()
            return True

        except pymysql.err.IntegrityError:
            conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Tạo người dùng thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def update_user_profile(self, user_id: int, username: str, full_name: str) -> bool:
        """Cập nhật username/full name mới nhất của người dùng."""
        conn = self.get_connection()
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
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Cập nhật hồ sơ người dùng thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def set_user_language(self, user_id: int, language: str) -> bool:
        """Lưu ngôn ngữ người dùng đã chọn."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE users SET language = %s WHERE user_id = %s",
                (language, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Cập nhật ngôn ngữ người dùng thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin người dùng"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()

            if row:
                # Tạo bản sao từ điển mới và chuyển đổi datetime sang định dạng ISO string
                result = dict(row)
                if result.get('created_at'):
                    result['created_at'] = result['created_at'].isoformat()
                if result.get('last_checkin'):
                    result['last_checkin'] = result['last_checkin'].isoformat()
                return result
            return None

        finally:
            cursor.close()
            conn.close()

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Lấy thông tin người dùng bằng username"""
        # Loại bỏ dấu @ nếu có
        if username.startswith('@'):
            username = username[1:]

        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

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
            conn.close()

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
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("UPDATE users SET is_blocked = 1 WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Chặn người dùng thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def unblock_user(self, user_id: int) -> bool:
        """Hủy chặn người dùng"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("UPDATE users SET is_blocked = 0 WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Hủy chặn thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_blacklist(self) -> List[Dict]:
        """Lấy danh sách đen"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            cursor.execute("SELECT * FROM users WHERE is_blocked = 1")
            return list(cursor.fetchall())
        finally:
            cursor.close()
            conn.close()

    def add_balance(self, user_id: int, amount: int) -> bool:
        """Cộng điểm cho người dùng"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                (amount, user_id),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Cộng điểm thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def deduct_balance(self, user_id: int, amount: int) -> bool:
        """Trừ điểm của người dùng"""
        user = self.get_user(user_id)
        if not user or user["balance"] < amount:
            return False

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE users SET balance = balance - %s WHERE user_id = %s",
                (amount, user_id),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Trừ điểm thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def can_checkin(self, user_id: int) -> bool:
        """Kiểm tra xem người dùng hôm nay có thể điểm danh không"""
        user = self.get_user(user_id)
        if not user:
            return False

        last_checkin = user.get("last_checkin")
        if not last_checkin:
            return True

        last_date = datetime.fromisoformat(last_checkin).date()
        today = datetime.now().date()

        return last_date < today

    def checkin(self, user_id: int) -> bool:
        """Người dùng điểm danh (đã sửa lỗi điểm danh vô hạn)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Sử dụng thao tác SQL nguyên tử để tránh race condition
            # Chỉ cập nhật khi last_checkin là NULL hoặc ngày < hôm nay
            cursor.execute(
                """
                UPDATE users
                SET balance      = balance + 1,
                    last_checkin = NOW()
                WHERE user_id = %s
                  AND (
                          last_checkin IS NULL
                              OR DATE (last_checkin) < CURDATE()
                    )
                """,
                (user_id,),
            )
            conn.commit()

            # Kiểm tra xem có thực sự cập nhật không (affected_rows > 0 có nghĩa là điểm danh thành công)
            success = cursor.rowcount > 0
            return success

        except Exception as e:
            logger.error(f"Điểm danh thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def add_verification(
            self, user_id: int, verification_type: str, verification_url: str,
            status: str, result: str = "", verification_id: str = ""
    ) -> bool:
        """Thêm ghi chép xác thực"""
        conn = self.get_connection()
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
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Thêm ghi chép xác thực thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_user_verifications(self, user_id: int) -> List[Dict]:
        """Lấy danh sách ghi chép xác thực của người dùng"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

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
            conn.close()

    def create_card_key(
            self, key_code: str, balance: int, created_by: int,
            max_uses: int = 1, expire_days: Optional[int] = None
    ) -> bool:
        """Tạo thẻ nạp (card key)"""
        conn = self.get_connection()
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
            conn.commit()
            logger.info(f"✅ Mã thẻ {key_code} đã được tạo thành công trong DB (Affected rows: {cursor.rowcount})")
            return True

        except pymysql.err.IntegrityError:
            logger.error(f"Thẻ nạp đã tồn tại: {key_code}")
            conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Tạo thẻ nạp thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def use_card_key(self, key_code: str, user_id: int) -> Optional[int]:
        """Sử dụng thẻ nạp, trả về số điểm nhận được"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            # Truy vấn thẻ nạp
            cursor.execute(
                "SELECT * FROM card_keys WHERE key_code = %s",
                (key_code,),
            )
            card = cursor.fetchone()

            if not card:
                return None

            # Kiểm tra xem có hết hạn không
            if card["expire_at"] and datetime.now() > card["expire_at"]:
                return -2

            # Kiểm tra số lần sử dụng
            if card["current_uses"] >= card["max_uses"]:
                return -1

            # Kiểm tra xem người dùng đã sử dụng thẻ này chưa
            cursor.execute(
                "SELECT COUNT(*) as count FROM card_key_usage WHERE key_code = %s AND user_id = %s",
                (key_code, user_id),
            )
            count = cursor.fetchone()
            if count['count'] > 0:
                return -3

            # Cập nhật số lần sử dụng
            cursor.execute(
                "UPDATE card_keys SET current_uses = current_uses + 1 WHERE key_code = %s",
                (key_code,),
            )

            # Lưu lại lịch sử sử dụng
            cursor.execute(
                "INSERT INTO card_key_usage (key_code, user_id, used_at) VALUES (%s, %s, NOW())",
                (key_code, user_id),
            )

            # Cộng điểm cho người dùng
            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                (card["balance"], user_id),
            )

            conn.commit()
            return card["balance"]

        except Exception as e:
            logger.error(f"Sử dụng thẻ nạp thất bại: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

    def get_card_key_info(self, key_code: str) -> Optional[Dict]:
        """Lấy thông tin thẻ nạp"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            cursor.execute("SELECT * FROM card_keys WHERE key_code = %s", (key_code,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def get_all_card_keys(self, created_by: Optional[int] = None) -> List[Dict]:
        """Lấy tất cả thẻ nạp (có thể lọc theo người tạo)"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

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
            conn.close()

    def get_all_user_ids(self) -> List[int]:
        """Lấy tất cả ID người dùng"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT user_id FROM users")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        finally:
            cursor.close()
            conn.close()

    def add_live_cc(self, bin_num: str, month: str, year: str, cvv: str, status: str) -> bool:
        """Lưu thẻ Live hoặc Real vào database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO live_cc (bin, month, year, cvv, status, checkAt)
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                (bin_num, month, year, cvv, status)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Thêm live cc thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_live_ccs(self, limit: int = 100) -> List[Dict]:
        """Lấy danh sách CC Live"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)
        try:
            cursor.execute(
                "SELECT * FROM live_cc ORDER BY checkAt DESC LIMIT %s",
                (limit,)
            )
            return list(cursor.fetchall())
        finally:
            cursor.close()
            conn.close()

    def save_netflix_cookie(self, cookie_text: str) -> str:
        """Lưu một cookie Netflix vào kho, trả về trạng thái kết quả."""
        normalized_cookie_text = sanitize_cookie_text(cookie_text)
        if not normalized_cookie_text:
            logger.warning("Bỏ qua cookie Netflix rỗng sau khi làm sạch.")
            return "invalid"

        cookie_fingerprint = build_cookie_fingerprint(normalized_cookie_text)
        if not cookie_fingerprint:
            logger.warning("Bỏ qua cookie Netflix không tạo được fingerprint.")
            return "invalid"

        conn = self.get_connection()
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
            conn.commit()
            return "stored"
        except pymysql.err.IntegrityError:
            conn.rollback()
            return "duplicate"
        except Exception as e:
            logger.error(f"Thêm cookie Netflix thất bại: {e}")
            conn.rollback()
            return "error"
        finally:
            cursor.close()
            conn.close()

    def add_netflix_cookie(self, cookie_text: str) -> bool:
        """Lưu một cookie Netflix vào kho."""
        return self.save_netflix_cookie(cookie_text) == "stored"

    def get_netflix_cookies(self, limit: int = 20, randomize: bool = False) -> List[Dict]:
        """Lấy danh sách cookie Netflix."""
        order_clause = "ORDER BY RAND()" if randomize else "ORDER BY createdAt ASC, id ASC"
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)
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
            conn.close()

    def get_random_netflix_cookie(self) -> Optional[Dict]:
        """Lấy một cookie Netflix ngẫu nhiên từ kho."""
        cookies = self.get_netflix_cookies(limit=1, randomize=True)
        return cookies[0] if cookies else None

    def delete_netflix_cookie(self, cookie_id: int) -> bool:
        """Xóa một cookie Netflix khỏi kho."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM netflix_cookies WHERE id = %s", (cookie_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Xóa cookie Netflix {cookie_id} thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def count_netflix_cookies(self) -> int:
        """Đếm số cookie Netflix hiện có trong kho."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM netflix_cookies")
            row = cursor.fetchone()
            return int(row[0]) if row else 0
        finally:
            cursor.close()
            conn.close()

    def get_all_service_status(self) -> Dict[str, bool]:
        """Lấy trạng thái bảo trì của tất cả dịch vụ"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)
        try:
            cursor.execute("SELECT service_id, is_maintenance FROM services_maintenance")
            rows = cursor.fetchall()
            return {row['service_id']: bool(row['is_maintenance']) for row in rows}
        finally:
            cursor.close()
            conn.close()

    def toggle_service_maintenance(self, service_id: str) -> Optional[bool]:
        """Đảo ngược trạng thái bảo trì của dịch vụ và trả về trạng thái mới"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Lấy trạng thái hiện tại
            cursor.execute("SELECT is_maintenance FROM services_maintenance WHERE service_id = %s", (service_id,))
            row = cursor.fetchone()
            if row is None:
                # Nếu chưa có, thêm mới với trạng thái 1
                cursor.execute("INSERT INTO services_maintenance (service_id, is_maintenance) VALUES (%s, 1)",
                               (service_id,))
                new_status = True
            else:
                new_status = not bool(row[0])
                cursor.execute("UPDATE services_maintenance SET is_maintenance = %s WHERE service_id = %s",
                               (int(new_status), service_id))

            conn.commit()
            return new_status
        except Exception as e:
            logger.error(f"Lỗi khi toggle bảo trì cho {service_id}: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

    def is_service_maintenance(self, service_id: str) -> bool:
        """Kiểm tra dịch vụ có đang bảo trì không"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT is_maintenance FROM services_maintenance WHERE service_id = %s", (service_id,))
            row = cursor.fetchone()
            return bool(row[0]) if row else False
        finally:
            cursor.close()
            conn.close()

    # --- Các phương thức quản lý Proxy ---

    def add_proxy(self, address: str, port: str, username: Optional[str] = None, password: Optional[str] = None,
                  city: Optional[str] = None, country: Optional[str] = None) -> bool:
        """Thêm proxy mới vào database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO proxies (address, port, username, password, city, country)
                VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY
                UPDATE city =
                VALUES (city), country =
                VALUES (country)
                """,
                (address, port, username, password, city, country)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Thêm proxy thất bại {address}:{port}: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_random_proxy(self) -> Optional[Dict]:
        """Lấy một proxy ngẫu nhiên từ database"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)
        try:
            cursor.execute("SELECT * FROM proxies ORDER BY RAND() LIMIT 1")
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def get_all_proxies(self) -> List[Dict]:
        """Lấy danh sách tất cả proxy"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)
        try:
            cursor.execute("SELECT * FROM proxies ORDER BY updatedAt DESC")
            return list(cursor.fetchall())
        finally:
            cursor.close()
            conn.close()

    def update_proxy_info(self, proxy_id: int, city: str, country: str) -> bool:
        """Cập nhật thông tin vị trí cho proxy"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE proxies SET city = %s, country = %s WHERE id = %s",
                (city, country, proxy_id)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Cập nhật proxy {proxy_id} thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def delete_proxy(self, proxy_id: int) -> bool:
        """Xóa proxy khỏi database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM proxies WHERE id = %s", (proxy_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Xóa proxy {proxy_id} thất bại: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def proxy_exists(self, address, port, username, password) -> bool:
        """Kiểm tra proxy đã tồn tại chưa"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id FROM proxies WHERE address = %s AND port = %s AND username = %s AND password = %s",
                (address, port, username, password)
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            conn.close()


# Tạo bí danh cho instance toàn cục để duy trì tính tương thích với phiên bản SQLite
Database = MySQLDatabase
