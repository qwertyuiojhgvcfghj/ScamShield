"""
image_generator.py

generates fake screenshots and images to send to scammers.
uses FREE image generation APIs.

features:
- fake bank statements
- fake UPI screenshots
- fake payment confirmations
- fake ID cards (blurred/partial)
- fake error screens

uses pollinations.ai (free, no api key needed)
"""

import requests
import base64
import random
import urllib.parse
from datetime import datetime, timedelta
from io import BytesIO


class ImageGenerator:
    """
    generates convincing fake images for scammer engagement.
    uses free APIs - no cost!
    """
    
    def __init__(self):
        # pollinations.ai - free text-to-image
        self.pollinations_url = "https://image.pollinations.ai/prompt/"
        
        # placeholder image services (instant, free)
        self.placeholder_url = "https://placehold.co"
    
    def generate_bank_screenshot(self, bank_name: str = "SBI", balance: str = "₹45,234.50") -> dict:
        """
        generate fake bank balance screenshot
        """
        
        prompt = f"""realistic mobile phone screenshot of {bank_name} bank app showing account balance {balance}, 
        Indian bank mobile app interface, clean UI, professional banking app screenshot, 
        account number partially hidden XXXX1234, realistic mobile banking interface"""
        
        return self._generate_image(prompt, "bank_balance")
    
    def generate_upi_screenshot(self, amount: str = "₹500", status: str = "pending") -> dict:
        """
        generate fake UPI payment screenshot
        """
        
        if status == "pending":
            prompt = f"""realistic mobile screenshot of UPI payment pending screen showing amount {amount},
            PhonePe or Paytm or GPay interface, payment processing, 
            Indian UPI payment app, waiting for confirmation message, realistic mobile UI"""
        elif status == "failed":
            prompt = f"""realistic mobile screenshot of UPI payment failed error screen,
            payment of {amount} failed due to technical issue, 
            PhonePe or Paytm app interface, red error message, try again button, Indian UPI app"""
        else:
            prompt = f"""realistic mobile screenshot of UPI payment successful,
            {amount} sent successfully, green checkmark,
            PhonePe or Paytm interface, transaction ID visible, Indian UPI app"""
        
        return self._generate_image(prompt, f"upi_{status}")
    
    def generate_otp_screenshot(self, partial_otp: str = "XX34") -> dict:
        """
        generate fake OTP message screenshot (partial/blurred)
        """
        
        prompt = f"""realistic mobile SMS screenshot showing OTP message from bank,
        message says 'Your OTP is {partial_otp}XX for transaction...',
        partially visible OTP, Indian bank SMS format, 
        realistic Android or iPhone message app interface"""
        
        return self._generate_image(prompt, "otp_message")
    
    def generate_error_screenshot(self, error_type: str = "network") -> dict:
        """
        generate fake error screens (stalling tactic)
        """
        
        if error_type == "network":
            prompt = """realistic mobile phone screenshot showing network error,
            'No internet connection' or 'Network error occurred',
            Indian mobile app error screen, retry button visible"""
        elif error_type == "app_crash":
            prompt = """realistic mobile screenshot showing app crashed error,
            'Unfortunately app has stopped' Android error dialog,
            or iOS app crash screen, realistic mobile UI"""
        elif error_type == "server":
            prompt = """realistic mobile banking app screenshot showing server error,
            'Server is busy, please try again later' message,
            Indian bank app maintenance screen"""
        else:
            prompt = """realistic mobile phone screenshot showing loading error,
            spinning loader stuck, app not responding,
            realistic mobile interface"""
        
        return self._generate_image(prompt, f"error_{error_type}")
    
    def generate_id_screenshot(self, doc_type: str = "aadhar") -> dict:
        """
        generate fake blurred ID card (for tricking scammers)
        """
        
        if doc_type == "aadhar":
            prompt = """blurry photo of Aadhar card on table,
            most details hidden or blurred, only partial number visible XXXX XXXX 1234,
            realistic photo taken from phone camera, low quality intentional,
            Indian Aadhar card blue color visible"""
        elif doc_type == "pan":
            prompt = """blurry photo of PAN card on table,
            most details hidden, only partial PAN number visible XXXXX1234X,
            realistic phone camera photo, slightly out of focus,
            Indian PAN card with photo area blurred"""
        else:
            prompt = """blurry photo of Indian ID card on desk,
            details not clearly visible, intentionally unclear,
            realistic photo, low lighting"""
        
        return self._generate_image(prompt, f"id_{doc_type}")
    
    def generate_bank_statement(self, bank_name: str = "SBI") -> dict:
        """
        generate fake bank statement image
        """
        
        prompt = f"""screenshot of {bank_name} bank statement PDF on mobile,
        showing recent transactions, some amounts visible,
        account holder name blurred, 
        realistic Indian bank statement format,
        PDF viewer on mobile phone"""
        
        return self._generate_image(prompt, "bank_statement")
    
    def generate_wallet_screenshot(self, balance: str = "₹2,500") -> dict:
        """
        generate fake wallet balance
        """
        
        prompt = f"""realistic mobile screenshot of digital wallet app,
        Paytm or PhonePe wallet showing balance {balance},
        add money button visible, recent transactions list,
        Indian digital wallet interface, clean UI"""
        
        return self._generate_image(prompt, "wallet_balance")
    
    def _generate_image(self, prompt: str, image_type: str) -> dict:
        """
        generate image using pollinations.ai (free)
        returns dict with image url and metadata
        """
        
        try:
            # encode prompt for URL
            encoded_prompt = urllib.parse.quote(prompt)
            
            # pollinations generates image at this URL
            image_url = f"{self.pollinations_url}{encoded_prompt}"
            
            # add parameters for better quality
            image_url += "?width=400&height=700&seed=" + str(random.randint(1, 10000))
            
            return {
                "success": True,
                "image_url": image_url,
                "type": image_type,
                "prompt": prompt[:100] + "...",
                "note": "Image generated via pollinations.ai (free)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "type": image_type,
                "fallback_url": self._get_placeholder(image_type)
            }
    
    def _get_placeholder(self, image_type: str) -> str:
        """fallback placeholder images"""
        
        colors = {
            "bank_balance": "1a73e8/white",
            "upi_pending": "ff9800/white",
            "upi_failed": "f44336/white", 
            "upi_success": "4caf50/white",
            "error_network": "9e9e9e/white",
            "id_aadhar": "0066b3/white",
            "wallet_balance": "00baf2/white"
        }
        
        color = colors.get(image_type, "666666/white")
        text = image_type.replace("_", "+")
        
        return f"{self.placeholder_url}/400x700/{color}?text={text}"
    
    def detect_image_request(self, message: str) -> dict:
        """
        detect if scammer is asking for screenshot/image
        returns type of image they want
        """
        
        msg_lower = message.lower()
        
        # screenshot request patterns
        patterns = {
            "bank_balance": [
                "screenshot", "balance", "bank balance", "account balance",
                "show balance", "send screenshot", "balance screenshot",
                "खाते का स्क्रीनशॉट", "बैलेंस दिखाओ", "बैलेंस स्क्रीनशॉट"
            ],
            "upi_payment": [
                "payment screenshot", "upi screenshot", "send payment",
                "payment proof", "transaction screenshot", "payment ss",
                "पेमेंट स्क्रीनशॉट", "यूपीआई स्क्रीनशॉट"
            ],
            "otp": [
                "otp screenshot", "send otp", "otp photo", "show otp",
                "otp message", "sms screenshot",
                "ओटीपी भेजो", "ओटीपी स्क्रीनशॉट"
            ],
            "id_card": [
                "aadhar", "aadhaar", "pan card", "id proof", "id card",
                "photo id", "aadhar photo", "pan photo",
                "आधार", "पैन कार्ड", "आईडी"
            ],
            "bank_statement": [
                "statement", "bank statement", "account statement",
                "passbook", "transaction history",
                "स्टेटमेंट", "पासबुक"
            ]
        }
        
        for img_type, keywords in patterns.items():
            if any(kw in msg_lower for kw in keywords):
                return {
                    "wants_image": True,
                    "image_type": img_type,
                    "keywords_matched": [kw for kw in keywords if kw in msg_lower]
                }
        
        return {"wants_image": False, "image_type": None}


# singleton
image_gen = ImageGenerator()


def generate_image_for_request(request_type: str, **kwargs) -> dict:
    """convenience function to generate images"""
    
    if request_type == "bank_balance":
        return image_gen.generate_bank_screenshot(**kwargs)
    elif request_type == "upi_payment":
        return image_gen.generate_upi_screenshot(**kwargs)
    elif request_type == "otp":
        return image_gen.generate_otp_screenshot(**kwargs)
    elif request_type == "id_card":
        return image_gen.generate_id_screenshot(**kwargs)
    elif request_type == "bank_statement":
        return image_gen.generate_bank_statement(**kwargs)
    elif request_type == "error":
        return image_gen.generate_error_screenshot(**kwargs)
    else:
        return image_gen.generate_error_screenshot(error_type="network")


def check_image_request(message: str) -> dict:
    """check if message is asking for image"""
    return image_gen.detect_image_request(message)


# test
if __name__ == "__main__":
    print("Testing image generation...")
    
    # test detection
    test_msgs = [
        "Send me your bank balance screenshot",
        "Share your aadhar card photo",
        "Show payment proof",
        "What is the weather today?"
    ]
    
    for msg in test_msgs:
        result = check_image_request(msg)
        print(f"\n'{msg[:40]}...'")
        print(f"  Wants image: {result['wants_image']}")
        if result['wants_image']:
            print(f"  Type: {result['image_type']}")
