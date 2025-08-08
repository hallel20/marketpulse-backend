# MarketPulse Commerce API

A professional FastAPI e-commerce backend with comprehensive features for modern online marketplaces.

## 🚀 Features

### Core Functionality
- **User Authentication & Authorization**: JWT-based auth with role management
- **Product Management**: Full CRUD with categories, variants, and reviews
- **Shopping Cart & Wishlist**: Persistent cart with user session management
- **Order Processing**: Complete order lifecycle with status tracking
- **Payment Integration**: Stripe payment processing with webhooks
- **Search & Filtering**: Elasticsearch-powered product search
- **Email Notifications**: Transactional emails for all user actions
- **Admin Dashboard**: Complete admin panel for business management

### Advanced Features
- **Background Tasks**: Celery-based async task processing
- **File Uploads**: AWS S3 integration for product images
- **Caching**: Redis-based caching for performance
- **Rate Limiting**: API protection against abuse
- **Monitoring**: Health checks and metrics endpoints
- **Testing**: Comprehensive test suite with pytest

## 🛠 Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async)
- **Authentication**: JWT with FastAPI-Users
- **Search**: Elasticsearch 8.11
- **Caching**: Redis 7
- **Background Tasks**: Celery
- **Payments**: Stripe
- **File Storage**: AWS S3
- **Email**: SMTP with Jinja2 templates
- **Testing**: Pytest with async support

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Elasticsearch 8.11+
- AWS S3 account (for file uploads)
- Stripe account (for payments)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/marketpulse-api.git
cd marketpulse-api
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Database Setup

```bash
# Start PostgreSQL and create database
createdb marketpulse

# Run migrations
alembic upgrade head

# Seed sample data
python scripts/seed_data.py
```

### 5. Start Services

```bash
# Start Redis
redis-server

# Start Elasticsearch
# Follow Elasticsearch installation guide for your OS

# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Start the API
uvicorn app.main:app --reload
```

## 🐳 Docker Development

### Quick Start with Docker Compose

```bash
# Clone and navigate to project
git clone https://github.com/your-username/marketpulse-api.git
cd marketpulse-api

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up --build

# Run migrations (in another terminal)
docker-compose exec api alembic upgrade head

# Seed sample data
docker-compose exec api python scripts/seed_data.py
```

### Services Started:
- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Elasticsearch: http://localhost:9200
- Flower (Celery monitoring): http://localhost:5555

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `False` |
| `SECRET_KEY` | JWT secret key | Required |
| `DATABASE_URL` | PostgreSQL connection | Required |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://localhost:9200` |
| `STRIPE_SECRET_KEY` | Stripe secret key | Required for payments |
| `AWS_ACCESS_KEY_ID` | AWS access key | Required for file uploads |

See `.env.example` for complete configuration options.

## 📖 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh tokens
- `POST /api/v1/auth/logout` - User logout

### Products
- `GET /api/v1/products` - List products with filtering
- `GET /api/v1/products/{id}` - Get product details
- `POST /api/v1/products` - Create product (admin)
- `PUT /api/v1/products/{id}` - Update product (admin)
- `DELETE /api/v1/products/{id}` - Delete product (admin)

### Orders
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders` - List user orders
- `GET /api/v1/orders/{id}` - Get order details
- `PUT /api/v1/orders/{id}/cancel` - Cancel order

### Cart & Wishlist
- `GET /api/v1/cart` - Get cart contents
- `POST /api/v1/cart/items` - Add item to cart
- `PUT /api/v1/cart/items/{id}` - Update cart item
- `DELETE /api/v1/cart/items/{id}` - Remove cart item

See the interactive API docs for complete endpoint documentation.

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Test Configuration

Tests use a separate test database. Configure `TEST_DATABASE_URL` in your `.env` file.

## 🔍 Database Schema

### Core Models

**Users & Authentication**
- `users` - User accounts and profiles
- `addresses` - User shipping addresses

**Products & Catalog**
- `categories` - Product categories with hierarchy
- `products` - Product information and inventory
- `product_images` - Product image gallery
- `product_variants` - Product options (size, color, etc.)
- `product_reviews` - Customer reviews and ratings

**Orders & Commerce**
- `orders` - Order information and status
- `order_items` - Individual items in orders
- `cart_items` - Shopping cart contents
- `wishlist_items` - User wishlists

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Set all required environment variables
2. **Database**: Use managed PostgreSQL service
3. **Redis**: Use managed Redis service
4. **File Storage**: Configure AWS S3 bucket
5. **Email**: Set up SMTP service
6. **Monitoring**: Enable health checks and logging

### Docker Production

```bash
# Build production image
docker build -t marketpulse-api .

# Run with production settings
docker run -d \
  --name marketpulse-api \
  -p 8000:8000 \
  -e DATABASE_URL=your-production-db-url \
  -e SECRET_KEY=your-production-secret \
  marketpulse-api
```

## 📊 Monitoring & Analytics

### Health Checks
- `GET /health` - Basic health check
- `GET /metrics` - Prometheus metrics

### Logging
The application uses structured logging with different levels:
- **INFO**: General application flow
- **WARNING**: Potential issues
- **ERROR**: Error conditions
- **DEBUG**: Detailed debugging info

### Celery Monitoring
Use Flower to monitor background tasks:
```bash
celery -A app.tasks.celery_app flower
```

## 🔒 Security

### Implemented Security Measures
- JWT token authentication
- Password hashing with bcrypt
- Rate limiting on sensitive endpoints
- Input validation and sanitization
- CORS protection
- SQL injection prevention
- XSS protection

### Security Best Practices
- Use HTTPS in production
- Set strong SECRET_KEY
- Enable database SSL
- Configure proper CORS origins
- Implement proper rate limiting
- Regular security updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Use type hints
- Add docstrings to functions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the API docs at `/docs`
- **Issues**: Report bugs on GitHub Issues
- **Email**: support@marketpulse.com

## 🗺 Roadmap

### Upcoming Features
- [ ] Multi-vendor marketplace support
- [ ] Advanced inventory management
- [ ] Subscription products
- [ ] Mobile app API optimizations
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Advanced recommendation engine
- [ ] Social commerce features

---

**MarketPulse Commerce API** - Professional e-commerce backend for modern marketplaces.