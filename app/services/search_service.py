"""
Elasticsearch service for advanced product search
"""
from typing import Dict, List, Optional, Any
import json

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError

from app.config import get_settings
from app.models.product import Product
from app.schemas.product import ProductSearchResponse, ProductListResponse

settings = get_settings()


class SearchService:
    """Elasticsearch service for product search"""
    
    def __init__(self):
        self.es = AsyncElasticsearch([settings.ELASTICSEARCH_URL])
        self.product_index = "products"
    
    async def create_indices(self):
        """Create Elasticsearch indices with mappings"""
        # Product index mapping
        product_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "description": {"type": "text", "analyzer": "standard"},
                    "short_description": {"type": "text", "analyzer": "standard"},
                    "category_id": {"type": "keyword"},
                    "category_name": {"type": "keyword"},
                    "price": {"type": "float"},
                    "sku": {"type": "keyword"},
                    "stock_quantity": {"type": "integer"},
                    "is_active": {"type": "boolean"},
                    "is_featured": {"type": "boolean"},
                    "rating_average": {"type": "float"},
                    "rating_count": {"type": "integer"},
                    "view_count": {"type": "integer"},
                    "tags": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "product_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop"]
                        }
                    }
                }
            }
        }
        
        try:
            # Create index if it doesn't exist
            if not await self.es.indices.exists(index=self.product_index):
                await self.es.indices.create(
                    index=self.product_index,
                    body=product_mapping
                )
                print(f"Created Elasticsearch index: {self.product_index}")
        except Exception as e:
            print(f"Error creating Elasticsearch indices: {e}")
    
    async def index_product(self, product: Product):
        """Index a single product"""
        try:
            doc = {
                "id": str(product.id),
                "name": product.name,
                "description": product.description,
                "short_description": product.short_description,
                "category_id": str(product.category_id),
                "category_name": product.category.name if product.category else "",
                "price": float(product.price),
                "sku": product.sku,
                "stock_quantity": product.stock_quantity,
                "is_active": product.is_active,
                "is_featured": product.is_featured,
                "rating_average": float(product.rating_average),
                "rating_count": product.rating_count,
                "view_count": product.view_count,
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat()
            }
            
            await self.es.index(
                index=self.product_index,
                id=str(product.id),
                body=doc
            )
            
        except Exception as e:
            print(f"Error indexing product {product.id}: {e}")
    
    async def delete_product(self, product_id: str):
        """Remove product from search index"""
        try:
            await self.es.delete(
                index=self.product_index,
                id=product_id
            )
        except NotFoundError:
            # Product not in index, ignore
            pass
        except Exception as e:
            print(f"Error deleting product {product_id} from index: {e}")
    
    async def search_products(self, search_params: Dict[str, Any]) -> ProductSearchResponse:
        """Search products with advanced filtering"""
        query = search_params.get("query", "")
        category_id = search_params.get("category_id")
        min_price = search_params.get("min_price")
        max_price = search_params.get("max_price")
        page = search_params.get("page", 1)
        page_size = search_params.get("page_size", 20)
        
        # Build Elasticsearch query
        es_query = {
            "bool": {
                "must": [],
                "filter": [
                    {"term": {"is_active": True}}
                ]
            }
        }
        
        # Text search
        if query:
            es_query["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "description", "short_description"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        else:
            es_query["bool"]["must"].append({"match_all": {}})
        
        # Category filter
        if category_id:
            es_query["bool"]["filter"].append({
                "term": {"category_id": category_id}
            })
        
        # Price range filter
        if min_price is not None or max_price is not None:
            price_filter = {"range": {"price": {}}}
            if min_price is not None:
                price_filter["range"]["price"]["gte"] = min_price
            if max_price is not None:
                price_filter["range"]["price"]["lte"] = max_price
            es_query["bool"]["filter"].append(price_filter)
        
        # Aggregations for faceted search
        aggregations = {
            "categories": {
                "terms": {"field": "category_name", "size": 20}
            },
            "price_ranges": {
                "range": {
                    "field": "price",
                    "ranges": [
                        {"to": 25},
                        {"from": 25, "to": 50},
                        {"from": 50, "to": 100},
                        {"from": 100, "to": 200},
                        {"from": 200}
                    ]
                }
            }
        }
        
        # Execute search
        from_offset = (page - 1) * page_size
        
        try:
            response = await self.es.search(
                index=self.product_index,
                body={
                    "query": es_query,
                    "aggs": aggregations,
                    "sort": [
                        {"_score": {"order": "desc"}},
                        {"rating_average": {"order": "desc"}},
                        {"created_at": {"order": "desc"}}
                    ],
                    "from": from_offset,
                    "size": page_size
                }
            )
            
            # Process results
            products = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                product = ProductListResponse(
                    id=source["id"],
                    name=source["name"],
                    slug=source.get("slug", ""),
                    short_description=source.get("short_description"),
                    price=source["price"],
                    sku=source["sku"],
                    stock_quantity=source["stock_quantity"],
                    is_featured=source["is_featured"],
                    rating_average=source["rating_average"],
                    rating_count=source["rating_count"],
                    is_in_stock=source["stock_quantity"] > 0,
                    main_image_url=None,  # Would need to fetch from database
                    category_name=source["category_name"]
                )
                products.append(product)
            
            # Process facets
            facets = {}
            if "aggregations" in response:
                aggs = response["aggregations"]
                
                if "categories" in aggs:
                    facets["categories"] = [
                        {"name": bucket["key"], "count": bucket["doc_count"]}
                        for bucket in aggs["categories"]["buckets"]
                    ]
                
                if "price_ranges" in aggs:
                    facets["price_ranges"] = [
                        {
                            "range": f"{bucket.get('from', 0)}-{bucket.get('to', '+')}",
                            "count": bucket["doc_count"]
                        }
                        for bucket in aggs["price_ranges"]["buckets"]
                    ]
            
            total_count = response["hits"]["total"]["value"]
            total_pages = (total_count + page_size - 1) // page_size
            
            return ProductSearchResponse(
                products=products,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                facets=facets
            )
            
        except Exception as e:
            print(f"Search error: {e}")
            # Return empty results on error
            return ProductSearchResponse(
                products=[],
                total_count=0,
                page=page,
                page_size=page_size,
                total_pages=0,
                facets={}
            )
    
    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search autocomplete suggestions"""
        try:
            response = await self.es.search(
                index=self.product_index,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["name^2", "category_name"],
                                        "type": "phrase_prefix"
                                    }
                                }
                            ],
                            "filter": [
                                {"term": {"is_active": True}}
                            ]
                        }
                    },
                    "_source": ["name"],
                    "size": limit
                }
            )
            
            suggestions = []
            for hit in response["hits"]["hits"]:
                suggestions.append(hit["_source"]["name"])
            
            return suggestions
            
        except Exception as e:
            print(f"Suggestion error: {e}")
            return []
    
    async def close(self):
        """Close Elasticsearch connection"""
        await self.es.close()