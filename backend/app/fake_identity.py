"""
fake_identity.py

generates consistent fake victim identities for each session.
makes the honeypot more believable to scammers.

generates:
- indian names (first + last)
- partial bank account (masked)
- partial aadhar (masked)
- age, occupation
- city, state
- fake UPI ID
"""

import random
import hashlib
from typing import Dict
from dataclasses import dataclass


# indian first names
FIRST_NAMES_MALE = [
    "Ramesh", "Suresh", "Mahesh", "Rajesh", "Mukesh", "Dinesh", "Ganesh",
    "Anil", "Sunil", "Vijay", "Sanjay", "Ajay", "Ravi", "Kumar", "Mohan",
    "Sohan", "Gopal", "Krishna", "Shyam", "Ram", "Lakshman", "Bharat",
    "Amit", "Sumit", "Rohit", "Mohit", "Nitin", "Sachin", "Rahul", "Deepak"
]

FIRST_NAMES_FEMALE = [
    "Sunita", "Anita", "Kavita", "Savita", "Geeta", "Seema", "Neeta",
    "Rekha", "Shobha", "Usha", "Asha", "Nisha", "Ritu", "Manju", "Anju",
    "Suman", "Poonam", "Kiran", "Priya", "Pooja", "Neha", "Sneha", "Divya",
    "Meera", "Lakshmi", "Sarita", "Mamta", "Kamla", "Radha", "Sita"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Yadav", "Patel", "Shah",
    "Mehta", "Joshi", "Pandey", "Mishra", "Tiwari", "Dubey", "Shukla",
    "Agarwal", "Bansal", "Goel", "Jain", "Khanna", "Malhotra", "Kapoor",
    "Reddy", "Nair", "Menon", "Iyer", "Pillai", "Naidu", "Rao", "Choudhary"
]

CITIES = [
    ("Mumbai", "Maharashtra"), ("Delhi", "Delhi"), ("Bangalore", "Karnataka"),
    ("Chennai", "Tamil Nadu"), ("Kolkata", "West Bengal"), ("Hyderabad", "Telangana"),
    ("Pune", "Maharashtra"), ("Ahmedabad", "Gujarat"), ("Jaipur", "Rajasthan"),
    ("Lucknow", "Uttar Pradesh"), ("Kanpur", "Uttar Pradesh"), ("Nagpur", "Maharashtra"),
    ("Indore", "Madhya Pradesh"), ("Bhopal", "Madhya Pradesh"), ("Patna", "Bihar"),
    ("Chandigarh", "Punjab"), ("Coimbatore", "Tamil Nadu"), ("Kochi", "Kerala"),
    ("Surat", "Gujarat"), ("Vadodara", "Gujarat")
]

OCCUPATIONS = [
    "Retired Government Employee", "Retired Teacher", "Housewife", "Small Business Owner",
    "Farmer", "Shop Owner", "Auto Driver", "Factory Worker", "Security Guard",
    "Clerk", "Accountant", "Teacher", "Nurse", "Bank Employee (Retired)",
    "Railway Employee (Retired)", "Post Office Employee", "Electrician", "Carpenter",
    "Tailor", "Grocery Store Owner"
]

BANKS = ["SBI", "PNB", "BOB", "HDFC", "ICICI", "Axis", "Canara", "Union", "BOI", "IDBI"]

UPI_SUFFIXES = ["@ybl", "@paytm", "@okaxis", "@oksbi", "@ibl", "@apl", "@upi"]


@dataclass
class FakeIdentity:
    """holds a fake victim identity"""
    
    first_name: str
    last_name: str
    full_name: str
    gender: str
    age: int
    occupation: str
    city: str
    state: str
    
    # masked financial info (partial - for "verification")
    bank_name: str
    account_last4: str
    aadhar_last4: str
    pan_prefix: str  # first 5 chars only
    upi_id: str
    
    # phone (partial)
    phone_last4: str
    
    def to_dict(self) -> Dict:
        return {
            "name": self.full_name,
            "gender": self.gender,
            "age": self.age,
            "occupation": self.occupation,
            "location": f"{self.city}, {self.state}",
            "bank": self.bank_name,
            "account_hint": f"XXXX{self.account_last4}",
            "aadhar_hint": f"XXXX XXXX {self.aadhar_last4}",
            "pan_hint": f"{self.pan_prefix}XXXX",
            "upi_id": self.upi_id,
            "phone_hint": f"+91 XXXXX X{self.phone_last4}",
        }
    
    def get_intro(self) -> str:
        """get a natural introduction"""
        return f"My name is {self.full_name}, I am a {self.occupation} from {self.city}."
    
    def get_partial_account(self) -> str:
        """return masked account for 'verification'"""
        return f"My account ends with {self.account_last4} in {self.bank_name}"
    
    def get_partial_aadhar(self) -> str:
        """return masked aadhar"""
        return f"My Aadhar last 4 digits are {self.aadhar_last4}"


class IdentityGenerator:
    """
    generates consistent fake identities per session.
    same session_id always returns same identity (deterministic).
    """
    
    def __init__(self):
        self._cache: Dict[str, FakeIdentity] = {}
    
    def get_identity(self, session_id: str) -> FakeIdentity:
        """
        get or generate identity for session.
        deterministic - same session always gets same identity.
        """
        if session_id in self._cache:
            return self._cache[session_id]
        
        # use session_id as seed for consistency
        seed = int(hashlib.md5(session_id.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        
        # generate identity
        gender = rng.choice(["male", "female"])
        first_name = rng.choice(FIRST_NAMES_MALE if gender == "male" else FIRST_NAMES_FEMALE)
        last_name = rng.choice(LAST_NAMES)
        city, state = rng.choice(CITIES)
        
        # generate consistent "partial" financial info
        account_last4 = str(rng.randint(1000, 9999))
        aadhar_last4 = str(rng.randint(1000, 9999))
        phone_last4 = str(rng.randint(1000, 9999))
        
        # PAN format: 5 letters
        pan_letters = "".join(rng.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
        
        # UPI ID based on name
        upi_name = first_name.lower() + str(rng.randint(10, 99))
        upi_id = upi_name + rng.choice(UPI_SUFFIXES)
        
        identity = FakeIdentity(
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}",
            gender=gender,
            age=rng.randint(45, 72),  # older = more believable victim
            occupation=rng.choice(OCCUPATIONS),
            city=city,
            state=state,
            bank_name=rng.choice(BANKS),
            account_last4=account_last4,
            aadhar_last4=aadhar_last4,
            pan_prefix=pan_letters,
            upi_id=upi_id,
            phone_last4=phone_last4
        )
        
        self._cache[session_id] = identity
        return identity
    
    def clear_session(self, session_id: str):
        """remove cached identity"""
        self._cache.pop(session_id, None)


# singleton
identity_gen = IdentityGenerator()


def get_fake_identity(session_id: str) -> FakeIdentity:
    """convenience function"""
    return identity_gen.get_identity(session_id)


# test
if __name__ == "__main__":
    print("Testing fake identity generator...")
    
    # same session = same identity
    id1 = get_fake_identity("session-123")
    id2 = get_fake_identity("session-123")
    id3 = get_fake_identity("session-456")
    
    print(f"\nSession 123: {id1.to_dict()}")
    print(f"\nSame session: {id2.full_name} (should match above)")
    print(f"\nDifferent session: {id3.full_name} (should be different)")
    print(f"\nIntro: {id1.get_intro()}")
