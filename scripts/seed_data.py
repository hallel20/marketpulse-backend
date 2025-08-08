"""
Seed script to populate the database with sample data
"""
import asyncio
import random
from decimal import Decimal
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.user import User, Address
from app.models.product import Category, Product, ProductImage, ProductReview
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.cart import CartItem, WishlistItem
from app.services.auth_service import AuthService

fake = Faker()

# Sample categories
CATEGORIES = [
    {"name": "Electronics", "slug": "electronics", "description": "Latest electronic devices and gadgets"},
    {"name": "Clothing", "slug": "clothing", "description": "Fashion and apparel for all occasions"},
    {"name": "Books", "slug": "books", "description": "Wide selection of books and educational materials"},
    {"name": "Home & Garden", "slug": "home-garden", "description": "Everything for your home and garden"},
    {"name": "Sports", "slug": "sports", "description": "Sports equipment and outdoor gear"},
    {"name": "Beauty", "slug": "beauty", "description": "Beauty and personal care products"},
    {"name": "Toys", "slug": "toys", "description": "Fun toys and games for all ages"},
    {"name": "Automotive", "slug": "automotive", "description": "Car parts and automotive accessories"},
]

# Sample product names by category
PRODUCTS_BY_CATEGORY = {
    "Electronics": [
        "Wireless Bluetooth Headphones", "Smartphone Case", "Laptop Stand", "USB-C Charger", 
        "Portable Speaker", "Tablet Screen Protector", "Gaming Mouse", "Keyboard Cover",
        "Phone Camera Lens", "Smart Watch Band", "Power Bank", "Cable Organizer"
    ],
    "Clothing": [
        "Cotton T-Shirt", "Denim Jeans", "Summer Dress", "Leather Jacket", "Running Shoes",
        "Winter Coat", "Casual Sneakers", "Wool Sweater", "Formal Shirt", "Yoga Pants",
        "Baseball Cap", "Cotton Socks"
    ],
    "Books": [
        "Python Programming Guide", "Mystery Novel", "Cooking Recipes", "Self-Help Book",
        "Science Fiction Novel", "History Textbook", "Art & Design Book", "Biography",
        "Children's Picture Book", "Poetry Collection", "Travel Guide", "Technical Manual"
    ],
    "Home & Garden": [
        "Coffee Maker", "Plant Pot", "LED Desk Lamp", "Throw Pillow", "Garden Tools Set",
        "Kitchen Utensils", "Wall Clock", "Storage Box", "Curtains", "Area Rug",
        "Picture Frame", "Candle Set"
    ],
    "Sports": [
        "Yoga Mat", "Resistance Bands", "Water Bottle", "Tennis Racket", "Basketball",
        "Running Shorts", "Gym Bag", "Protein Shaker", "Exercise Ball", "Dumbbells",
        "Cycling Gloves", "Swimming Goggles"
    ],
    "Beauty": [
        "Face Moisturizer", "Lipstick Set", "Hair Shampoo", "Body Lotion", "Nail Polish",
        "Makeup Brush Set", "Perfume", "Sunscreen", "Face Mask", "Hair Serum",
        "Eye Shadow Palette", "Lip Balm"
    ],
    "Toys": [
        "Building Blocks", "Puzzle Game", "Action Figure", "Board Game", "Remote Control Car",
        "Dollhouse", "Art Supplies Set", "Science Kit", "Musical Instrument Toy", "Stuffed Animal",
        "Educational Game", "Outdoor Play Set"
    ],
    "Automotive": [
        "Car Phone Mount", "Air Freshener", "Tire Pressure Gauge", "Car Charger",
        "Seat Covers", "Floor Mats", "Emergency Kit", "Car Wash Kit", "Dashboard Camera",
        "USB Car Adapter", "Trunk Organizer", "Car Key Holder"
    ]
}

# Sample product images from Pexels
SAMPLE_IMAGES = [
    "https://images.pexels.com/photos/1649771/pexels-photo-1649771.jpeg",
    "https://images.pexels.com/photos/1667088/pexels-photo-1667088.jpeg",
    "https://images.pexels.com/photos/1334597/pexels-photo-1334597.jpeg",
    "https://images.pexels.com/photos/2783873/pexels-photo-2783873.jpeg",
    "https://images.pexels.com/photos/1203803/pexels-photo-1203803.jpeg",
    "https://images.pexels.com/photos/1598300/pexels-photo-1598300.jpeg",
    "https://images.pexels.com/photos/2529148/pexels-photo-2529148.jpeg",
    "https://images.pexels.com/photos/1598505/pexels-photo-1598505.jpeg",
]


async def create_categories(session: AsyncSession) -> dict:
    """Create sample categories"""
    print("Creating categories...")
    categories = {}
    
    for cat_data in CATEGORIES:
        category = Category(**cat_data)
        session.add(category)
        categories[cat_data["name"]] = category
    
    await session.commit()
    
    # Refresh to get IDs
    for category in categories.values():
        await session.refresh(category)
    
    print(f"Created {len(categories)} categories")
    return categories


async def create_users(session: AsyncSession, count: int = 50) -> list:
    """Create sample users"""
    print(f"Creating {count} users...")
    users = []
    auth_service = AuthService()
    
    # Create admin user
    admin_user = User(
        email="admin@marketpulse.com",
        password_hash=auth_service.get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        is_admin=True,
        is_verified=True,
        phone="+1234567890"
    )
    session.add(admin_user)
    users.append(admin_user)
    
    # Create regular users
    for i in range(count - 1):
        user = User(
            email=fake.email(),
            password_hash=auth_service.get_password_hash("password123"),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            is_verified=random.choice([True, False]),
            phone=fake.phone_number() if random.choice([True, False]) else None
        )
        session.add(user)
        users.append(user)
    
    await session.commit()
    
    # Refresh to get IDs
    for user in users:
        await session.refresh(user)
    
    print(f"Created {len(users)} users")
    return users


async def create_addresses(session: AsyncSession, users: list):
    """Create sample addresses for users"""
    print("Creating addresses...")
    address_count = 0
    
    for user in users[:30]:  # Add addresses for first 30 users
        # Each user gets 1-3 addresses
        num_addresses = random.randint(1, 3)
        
        for i in range(num_addresses):
            address = Address(
                user_id=user.id,
                street=fake.street_address(),
                city=fake.city(),
                state=fake.state(),
                country="United States",
                postal_code=fake.zipcode(),
                is_default=(i == 0)  # First address is default
            )
            session.add(address)
            address_count += 1
    
    await session.commit()
    print(f"Created {address_count} addresses")


async def create_products(session: AsyncSession, categories: dict, count: int = 200) -> list:
    """Create sample products"""
    print(f"Creating {count} products...")
    products = []
    
    for i in range(count):
        # Random category
        category_name = random.choice(list(categories.keys()))
        category = categories[category_name]
        
        # Random product name from category
        product_names = PRODUCTS_BY_CATEGORY[category_name]
        base_name = random.choice(product_names)
        
        # Add variation to name
        variations = ["Premium", "Deluxe", "Pro", "Classic", "Essential", ""]
        variation = random.choice(variations)
        name = f"{variation} {base_name}".strip()
        
        # Generate SKU
        sku = f"{category.slug[:3].upper()}-{i+1:04d}"
        
        # Generate slug
        slug = name.lower().replace(" ", "-").replace("&", "and")
        
        product = Product(
            name=name,
            slug=f"{slug}-{i+1}",  # Add ID to ensure uniqueness
            description=fake.text(max_nb_chars=500),
            short_description=fake.sentence(nb_words=12),
            category_id=category.id,
            price=Decimal(str(random.uniform(9.99, 299.99))).quantize(Decimal("0.01")),
            cost_price=Decimal(str(random.uniform(5.00, 150.00))).quantize(Decimal("0.01")),
            sku=sku,
            stock_quantity=random.randint(0, 100),
            weight=Decimal(str(random.uniform(0.1, 5.0))).quantize(Decimal("0.01")),
            is_active=True,
            is_featured=random.choice([True, False, False, False]),  # 25% chance of featured
            rating_average=Decimal(str(random.uniform(3.0, 5.0))).quantize(Decimal("0.1")),
            rating_count=random.randint(0, 50),
            view_count=random.randint(0, 1000)
        )
        
        session.add(product)
        products.append(product)
    
    await session.commit()
    
    # Refresh to get IDs
    for product in products:
        await session.refresh(product)
    
    print(f"Created {len(products)} products")
    return products


async def create_product_images(session: AsyncSession, products: list):
    """Create sample product images"""
    print("Creating product images...")
    image_count = 0
    
    for product in products:
        # Each product gets 1-4 images
        num_images = random.randint(1, 4)
        
        for i in range(num_images):
            image = ProductImage(
                product_id=product.id,
                image_url=random.choice(SAMPLE_IMAGES),
                alt_text=f"{product.name} - Image {i + 1}",
                sort_order=i
            )
            session.add(image)
            image_count += 1
    
    await session.commit()
    print(f"Created {image_count} product images")


async def create_reviews(session: AsyncSession, products: list, users: list):
    """Create sample product reviews"""
    print("Creating product reviews...")
    review_count = 0
    
    # Select subset of products to have reviews
    reviewed_products = random.sample(products, min(100, len(products)))
    
    for product in reviewed_products:
        # Each product gets 1-8 reviews
        num_reviews = random.randint(1, 8)
        review_users = random.sample(users, min(num_reviews, len(users)))
        
        for user in review_users:
            review = ProductReview(
                product_id=product.id,
                user_id=user.id,
                rating=random.randint(1, 5),
                title=fake.sentence(nb_words=6),
                comment=fake.paragraph(nb_sentences=3),
                is_verified_purchase=random.choice([True, False]),
                created_at=fake.date_time_between(start_date="-1y", end_date="now")
            )
            session.add(review)
            review_count += 1
    
    await session.commit()
    print(f"Created {review_count} reviews")


async def create_cart_items(session: AsyncSession, users: list, products: list):
    """Create sample cart items"""
    print("Creating cart items...")
    cart_count = 0
    
    # 40% of users have items in cart
    users_with_carts = random.sample(users, int(len(users) * 0.4))
    
    for user in users_with_carts:
        # Each user has 1-5 items in cart
        num_items = random.randint(1, 5)
        cart_products = random.sample(products, min(num_items, len(products)))
        
        for product in cart_products:
            cart_item = CartItem(
                user_id=user.id,
                product_id=product.id,
                quantity=random.randint(1, 3)
            )
            session.add(cart_item)
            cart_count += 1
    
    await session.commit()
    print(f"Created {cart_count} cart items")


async def create_wishlist_items(session: AsyncSession, users: list, products: list):
    """Create sample wishlist items"""
    print("Creating wishlist items...")
    wishlist_count = 0
    
    # 30% of users have wishlist items
    users_with_wishlists = random.sample(users, int(len(users) * 0.3))
    
    for user in users_with_wishlists:
        # Each user has 1-10 items in wishlist
        num_items = random.randint(1, 10)
        wishlist_products = random.sample(products, min(num_items, len(products)))
        
        for product in wishlist_products:
            wishlist_item = WishlistItem(
                user_id=user.id,
                product_id=product.id
            )
            session.add(wishlist_item)
            wishlist_count += 1
    
    await session.commit()
    print(f"Created {wishlist_count} wishlist items")


async def create_orders(session: AsyncSession, users: list, products: list):
    """Create sample orders"""
    print("Creating orders...")
    order_count = 0
    
    # 60% of users have placed orders
    users_with_orders = random.sample(users, int(len(users) * 0.6))
    
    for user in users_with_orders:
        # Each user has 1-5 orders
        num_orders = random.randint(1, 5)
        
        for i in range(num_orders):
            # Order date within last year
            order_date = fake.date_time_between(start_date="-1y", end_date="now")
            
            # Generate order number
            order_number = f"MP{order_date.strftime('%Y%m%d')}{random.randint(1000, 9999)}"
            
            # Random order items
            num_items = random.randint(1, 5)
            order_products = random.sample(products, min(num_items, len(products)))
            
            # Calculate totals
            subtotal = Decimal("0")
            order_items = []
            
            for product in order_products:
                quantity = random.randint(1, 3)
                unit_price = product.price
                total_price = unit_price * quantity
                subtotal += total_price
                
                order_item_data = {
                    "product_id": product.id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "product_name": product.name,
                    "product_sku": product.sku
                }
                order_items.append(order_item_data)
            
            tax_amount = subtotal * Decimal("0.08")  # 8% tax
            shipping_cost = Decimal("5.99") if subtotal < 50 else Decimal("0")
            total_amount = subtotal + tax_amount + shipping_cost
            
            # Create order
            order = Order(
                order_number=order_number,
                user_id=user.id,
                status=random.choice(list(OrderStatus)),
                payment_status=random.choice(list(PaymentStatus)),
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_cost=shipping_cost,
                total_amount=total_amount,
                shipping_address=f"{fake.street_address()}, {fake.city()}, {fake.state()} {fake.zipcode()}",
                billing_address=f"{fake.street_address()}, {fake.city()}, {fake.state()} {fake.zipcode()}",
                payment_method="stripe",
                created_at=order_date,
                updated_at=order_date
            )
            
            session.add(order)
            await session.flush()  # Get order ID
            
            # Create order items
            for item_data in order_items:
                order_item = OrderItem(
                    order_id=order.id,
                    **item_data
                )
                session.add(order_item)
            
            order_count += 1
    
    await session.commit()
    print(f"Created {order_count} orders")


async def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    
    async with async_session_maker() as session:
        try:
            # Create categories
            categories = await create_categories(session)
            
            # Create users
            users = await create_users(session, count=50)
            
            # Create addresses
            await create_addresses(session, users)
            
            # Create products
            products = await create_products(session, categories, count=200)
            
            # Create product images
            await create_product_images(session, products)
            
            # Create reviews
            await create_reviews(session, products, users)
            
            # Create cart items
            await create_cart_items(session, users, products)
            
            # Create wishlist items
            await create_wishlist_items(session, users, products)
            
            # Create orders
            await create_orders(session, users, products)
            
            print("✅ Database seeding completed successfully!")
            print("\nSample data created:")
            print(f"- {len(categories)} categories")
            print(f"- {len(users)} users (including admin@marketpulse.com)")
            print(f"- {len(products)} products")
            print("- Addresses, reviews, cart items, wishlist items, and orders")
            print("\nAdmin login:")
            print("Email: admin@marketpulse.com")
            print("Password: admin123")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())