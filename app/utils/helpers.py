"""
Utility helper functions
"""
import uuid
import re
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime
import secrets
import string


def generate_uuid() -> str:
    """Generate a new UUID string"""
    return str(uuid.uuid4())


def generate_order_number() -> str:
    """Generate unique order number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = ''.join(secrets.choice(string.digits) for _ in range(6))
    return f"MP{timestamp}{random_part}"


def generate_sku(category_prefix: str, product_name: str) -> str:
    """Generate product SKU"""
    # Clean product name
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', product_name.upper())[:8]
    random_suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
    return f"{category_prefix}-{clean_name}-{random_suffix}"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Simple validation for demonstration
    pattern = r'^\+?[\d\s\-\(\)]{10,}$'
    return re.match(pattern, phone) is not None


def format_currency(amount: Decimal, currency: str = "USD") -> str:
    """Format decimal amount as currency string"""
    if currency == "USD":
        return f"${amount:.2f}"
    elif currency == "EUR":
        return f"€{amount:.2f}"
    elif currency == "GBP":
        return f"£{amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"


def calculate_tax(subtotal: Decimal, tax_rate: Decimal = Decimal("0.08")) -> Decimal:
    """Calculate tax amount"""
    return subtotal * tax_rate


def calculate_shipping(weight: Optional[Decimal], distance: str = "standard") -> Decimal:
    """Calculate shipping cost based on weight and distance"""
    base_cost = Decimal("5.99")
    
    if weight is None:
        return base_cost
    
    # Simple weight-based calculation
    if weight <= 1:
        weight_cost = Decimal("0")
    elif weight <= 5:
        weight_cost = Decimal("2.99")
    elif weight <= 10:
        weight_cost = Decimal("5.99")
    else:
        weight_cost = weight * Decimal("0.99")
    
    # Distance modifier
    distance_multiplier = {
        "local": Decimal("1.0"),
        "standard": Decimal("1.2"),
        "express": Decimal("2.0"),
        "international": Decimal("3.0")
    }.get(distance, Decimal("1.0"))
    
    return (base_cost + weight_cost) * distance_multiplier


def paginate_query_params(page: int, page_size: int, total_count: int) -> Dict[str, Any]:
    """Generate pagination metadata"""
    total_pages = (total_count + page_size - 1) // page_size
    has_previous = page > 1
    has_next = page < total_pages
    
    return {
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_previous": has_previous,
        "has_next": has_next,
        "previous_page": page - 1 if has_previous else None,
        "next_page": page + 1 if has_next else None
    }


def sanitize_search_query(query: str) -> str:
    """Sanitize search query to prevent injection"""
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', query)
    # Limit length
    sanitized = sanitized[:200]
    return sanitized.strip()


def generate_verification_code(length: int = 6) -> str:
    """Generate numeric verification code"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def mask_email(email: str) -> str:
    """Mask email address for privacy"""
    if '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        masked_local = local
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone number for privacy"""
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) < 4:
        return phone
    
    # Show last 4 digits
    return '*' * (len(digits) - 4) + digits[-4:]


def clean_html(text: str) -> str:
    """Remove HTML tags from text"""
    return re.sub(r'<[^>]+>', '', text)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def generate_referral_code(user_id: str) -> str:
    """Generate referral code for user"""
    # Use first 8 chars of user_id + random suffix
    prefix = user_id.replace('-', '')[:8].upper()
    suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    return f"{prefix}{suffix}"


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return feedback"""
    issues = []
    score = 0
    
    if len(password) >= 8:
        score += 1
    else:
        issues.append("Password must be at least 8 characters long")
    
    if re.search(r'[a-z]', password):
        score += 1
    else:
        issues.append("Password must contain lowercase letters")
    
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        issues.append("Password must contain uppercase letters")
    
    if re.search(r'\d', password):
        score += 1
    else:
        issues.append("Password must contain numbers")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        issues.append("Password must contain special characters")
    
    strength_levels = {
        0: "Very Weak",
        1: "Weak", 
        2: "Fair",
        3: "Good",
        4: "Strong",
        5: "Very Strong"
    }
    
    return {
        "score": score,
        "strength": strength_levels[score],
        "is_valid": score >= 3,
        "issues": issues
    }


def convert_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert SQLAlchemy model to dictionary"""
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            if not key.startswith('_'):
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    result[key] = float(value)
                elif isinstance(value, uuid.UUID):
                    result[key] = str(value)
                else:
                    result[key] = value
        return result
    return {}


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result