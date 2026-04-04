"""Chương trình chính xác thực giáo viên SheerID"""
import logging
import os
import random
import re
import sys
from typing import Dict, Optional, Tuple

import httpx

# Internal build sign ID
_BUILD_SIG = "687579636f6e676465763035"

# Thêm thư mục hiện tại vào sys.path để có thể import các module cùng cấp
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from . import config
    from name_generator import NameGenerator, generate_email, generate_birth_date
    from img_generator import generate_teacher_pdf, generate_teacher_png
except ImportError as e:
    logging.error(f"Lỗi khi import các module trong k12: {e}")
    raise

# Nhập các hằng số cấu hình
PROGRAM_ID = config.PROGRAM_ID
SHEERID_BASE_URL = config.SHEERID_BASE_URL
MY_SHEERID_URL = config.MY_SHEERID_URL
SCHOOLS = config.SCHOOLS
DEFAULT_SCHOOL_ID = config.DEFAULT_SCHOOL_ID

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class SheerIDVerifier:
    """Trình xác thực danh tính giáo viên SheerID"""

    def __init__(self, verification_id: str):
        """
        Khởi tạo trình xác thực

        Args:
            verification_id: ID xác thực SheerID
        """
        self.verification_id = verification_id
        self.device_fingerprint = self._generate_device_fingerprint()
        self.http_client = httpx.Client(timeout=30.0)

    def __del__(self):
        """Dọn dẹp hằng số HTTP client"""
        if hasattr(self, 'http_client'):
            self.http_client.close()

    @staticmethod
    def _generate_device_fingerprint() -> str:
        """Tạo dấu vân tay thiết bị"""
        chars = '0123456789abcdef'
        return ''.join(random.choice(chars) for _ in range(32))

    @staticmethod
    def normalize_url(url: str) -> str:
        """Chuẩn hóa URL"""
        return url

    @staticmethod
    def parse_verification_id(url: str) -> Optional[str]:
        """Giải mã ID xác thực từ URL"""
        match = re.search(r'verificationId=([a-f0-9]+)', url, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _sheerid_request(self, method: str, url: str,
                         body: Optional[Dict] = None) -> Tuple[Dict, int]:
        """
        Gửi yêu cầu API SheerID
        """
        headers = {
            'Content-Type': 'application/json',
        }

        try:
            response = self.http_client.request(
                method=method,
                url=url,
                json=body,
                headers=headers
            )

            try:
                data = response.json()
            except Exception:
                data = response.text

            return data, response.status_code
        except Exception as e:
            logger.error(f"Yêu cầu SheerID thất bại: {e}")
            raise

    def _upload_to_s3(self, upload_url: str, content: bytes, mime_type: str) -> bool:
        """
        Tải tệp lên S3
        """
        try:
            headers = {
                'Content-Type': mime_type,
            }
            response = self.http_client.put(
                upload_url,
                content=content,
                headers=headers,
                timeout=60.0
            )
            return 200 <= response.status_code < 300
        except Exception as e:
            logger.error(f"Tải lên S3 thất bại: {e}")
            return False

    def verify(self, first_name: str = None, last_name: str = None,
               email: str = None, birth_date: str = None,
               school_id: str = None) -> Dict:
        """
        Thực hiện quy trình xác thực hoàn chỉnh, loại bỏ vòng lặp kiểm tra trạng thái để giảm thời gian tiêu tốn
        """
        try:
            current_step = 'initial'

            # Tạo thông tin giáo viên
            if not first_name or not last_name:
                name = NameGenerator.generate()
                first_name = name['first_name']
                last_name = name['last_name']

            school_id = school_id or DEFAULT_SCHOOL_ID
            school = SCHOOLS[school_id]

            if not email:
                email = generate_email()

            if not birth_date:
                birth_date = generate_birth_date()

            logger.info(f"Thông tin giáo viên: {first_name} {last_name}")
            logger.info(f"Email: {email}")
            logger.info(f"Trường: {school['name']}")
            logger.info(f"Ngày sinh: {birth_date}")
            logger.info(f"ID xác thực: {self.verification_id}")

            # Tạo chứng nhận giáo viên PDF + PNG
            logger.info("Bước 1/4: Tạo chứng nhận giáo viên PDF và PNG...")
            pdf_data = generate_teacher_pdf(first_name, last_name)
            png_data = generate_teacher_png(first_name, last_name)
            pdf_size = len(pdf_data)
            png_size = len(png_data)
            logger.info(f"✓ Kích thước PDF: {pdf_size / 1024:.2f}KB, PNG: {png_size / 1024:.2f}KB")

            # Bước 2: Gửi thông tin giáo viên
            logger.info("Bước 2/4: Gửi thông tin giáo viên...")
            step2_body = {
                'firstName': first_name,
                'lastName': last_name,
                'birthDate': birth_date,
                'email': email,
                'phoneNumber': '',
                'organization': {
                    'id': school['id'],
                    'idExtended': school['idExtended'],
                    'name': school['name']
                },
                'deviceFingerprintHash': self.device_fingerprint,
                'locale': 'en-US',
                'metadata': {
                    'marketConsentValue': False,
                    'refererUrl': f"{SHEERID_BASE_URL}/verify/{PROGRAM_ID}/?verificationId={self.verification_id}",
                    'verificationId': self.verification_id,
                    'submissionOptIn': 'By submitting the personal information above, I acknowledge that my personal information is being collected under the privacy policy of the business from which I am seeking a discount'
                }
            }

            step2_data, step2_status = self._sheerid_request(
                'POST',
                f"{SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/collectTeacherPersonalInfo",
                step2_body
            )

            if step2_status != 200:
                raise Exception(f"Bước 2 thất bại (mã trạng thái {step2_status}): {step2_data}")

            if step2_data.get('currentStep') == 'error':
                error_msg = ', '.join(step2_data.get('errorIds', ['Lỗi không xác định']))
                raise Exception(f"Lỗi bước 2: {error_msg}")

            logger.info(f"✓ Bước 2 hoàn thành: {step2_data.get('currentStep')}")
            current_step = step2_data.get('currentStep', current_step)

            # Bước 3: Bỏ qua SSO (nếu cần)
            if current_step in ['sso', 'collectTeacherPersonalInfo']:
                logger.info("Bước 3/4: Bỏ qua xác thực SSO...")
                step3_data, _ = self._sheerid_request(
                    'DELETE',
                    f"{SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/sso"
                )
                logger.info(f"✓ Bước 3 hoàn thành: {step3_data.get('currentStep')}")
                step3_data.get('currentStep', current_step)

            # Bước 4: Tải tài liệu lên và hoàn tất gửi
            logger.info("Bước 4/4: Yêu cầu và tải tài liệu lên...")
            step4_body = {
                'files': [
                    {
                        'fileName': 'teacher_document.pdf',
                        'mimeType': 'application/pdf',
                        'fileSize': pdf_size
                    },
                    {
                        'fileName': 'teacher_document.png',
                        'mimeType': 'image/png',
                        'fileSize': png_size
                    }
                ]
            }

            step4_data, step4_status = self._sheerid_request(
                'POST',
                f"{SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/docUpload",
                step4_body
            )

            documents = step4_data.get('documents') or []
            if len(documents) < 2:
                raise Exception("Không thể lấy URL tải lên")

            pdf_upload_url = documents[0]['uploadUrl']
            png_upload_url = documents[1]['uploadUrl']
            logger.info("✓ Lấy URL tải lên thành công")

            if not self._upload_to_s3(pdf_upload_url, pdf_data, 'application/pdf'):
                raise Exception("Tải lên PDF thất bại")
            if not self._upload_to_s3(png_upload_url, png_data, 'image/png'):
                raise Exception("Tải lên PNG thất bại")
            logger.info("✓ Tải tài liệu giáo viên PDF/PNG lên thành công")

            step6_data, _ = self._sheerid_request(
                'POST',
                f"{SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/completeDocUpload"
            )
            logger.info(f"✓ Hoàn tất gửi tài liệu: {step6_data.get('currentStep')}")
            final_status = step6_data

            # Không thực hiện vòng lặp kiểm tra trạng thái, trả về trực tiếp chờ xét duyệt
            return {
                'success': True,
                'pending': True,
                'message': 'Tài liệu đã được gửi, đang chờ xét duyệt',
                'verification_id': self.verification_id,
                'redirect_url': final_status.get('redirectUrl'),
                'status': final_status
            }

        except Exception as e:
            logger.error(f"✗ Xác thực thất bại: {e}")
            return {
                'success': False,
                'message': str(e),
                'verification_id': self.verification_id
            }
