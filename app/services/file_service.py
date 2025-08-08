"""
File management service for handling uploads, image processing, and storage
"""
import os
import uuid
import asyncio
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import aiofiles
import aiofiles.os
from PIL import Image, ImageOps
import cloudinary
import cloudinary.api
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
import hashlib
import mimetypes
from fastapi import UploadFile, HTTPException, status
from app.config import get_settings
from app.utils.exceptions import ValidationException
import logging

logger = logging.getLogger(__name__)

class FileService:
    """
    Comprehensive file management service supporting both local and Cloudinary storage
    """
    
    # Supported image formats
    SUPPORTED_IMAGE_FORMATS = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'
    }
    
    # Image size configurations for local storage
    IMAGE_SIZES = {
        'thumbnail': (150, 150),
        'small': (300, 300),
        'medium': (600, 600),
        'large': (1200, 1200),
        'original': None  # Keep original size
    }
    
    # Cloudinary transformation configurations
    CLOUDINARY_TRANSFORMATIONS = {
        'thumbnail': {'width': 150, 'height': 150, 'crop': 'fill', 'quality': 'auto'},
        'small': {'width': 300, 'height': 300, 'crop': 'fill', 'quality': 'auto'},
        'medium': {'width': 600, 'height': 600, 'crop': 'fill', 'quality': 'auto'},
        'large': {'width': 1200, 'height': 1200, 'crop': 'fill', 'quality': 'auto'},
        'original': {'quality': 'auto', 'fetch_format': 'auto'}  # Original with optimizations
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        'image': 10 * 1024 * 1024,  # 10MB for images
        'document': 50 * 1024 * 1024,  # 50MB for documents
        'video': 100 * 1024 * 1024,  # 100MB for videos
    }
    
    def __init__(self):
        self.settings = get_settings()
        self._setup_storage()
    
    def _setup_storage(self):
        """Setup storage based on environment"""
        if self.settings.STORAGE_TYPE == "cloudinary":
            # Configure Cloudinary
            cloudinary.config(
                cloud_name=self.settings.CLOUDINARY_CLOUD_NAME,
                api_key=self.settings.CLOUDINARY_API_KEY,
                api_secret=self.settings.CLOUDINARY_API_SECRET,
                secure=True
            )
            logger.info("Cloudinary storage configured")
        else:
            # Setup local directories
            self._setup_local_directories()
            logger.info("Local storage configured")
    
    def _setup_local_directories(self):
        """Create necessary local directories if they don't exist"""
        directories = [
            self.settings.UPLOAD_DIR,
            os.path.join(self.settings.UPLOAD_DIR, 'products'),
            os.path.join(self.settings.UPLOAD_DIR, 'products', 'images'),
            os.path.join(self.settings.UPLOAD_DIR, 'users'),
            os.path.join(self.settings.UPLOAD_DIR, 'temp'),
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _generate_filename(self, original_filename: str | None, prefix: str = "") -> str:
        """Generate unique filename"""
        if not original_filename:
            raise ValidationException("No original filename provided")
        
        file_extension = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        
        if prefix:
            return f"{prefix}_{unique_id}{file_extension}"
        return f"{unique_id}{file_extension}"
    
    def _generate_cloudinary_public_id(self, folder: str, filename: str) -> str:
        """Generate Cloudinary public ID"""
        # Remove file extension for Cloudinary public ID
        name_without_ext = Path(filename).stem
        return f"{folder}/{name_without_ext}"
    
    def _get_file_hash(self, content: bytes) -> str:
        """Generate SHA256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    async def _validate_file(self, file: UploadFile, file_type: str = "image") -> None:
        """Validate uploaded file"""
        # Check file size
        if file_type in self.MAX_FILE_SIZES:
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            if file_size > self.MAX_FILE_SIZES[file_type]:
                raise ValidationException(
                    f"File too large. Maximum size: {self.MAX_FILE_SIZES[file_type] / 1024 / 1024:.1f}MB"
                )
        
        # Check content type for images
        if file_type == "image":
            if file.content_type not in self.SUPPORTED_IMAGE_FORMATS:
                raise ValidationException(
                    f"Unsupported image format. Supported: {', '.join(self.SUPPORTED_IMAGE_FORMATS)}"
                )
    
    async def _resize_image(self, image_path: str, size_name: str) -> str:
        """Resize image to specified dimensions (for local storage only)"""
        if size_name not in self.IMAGE_SIZES:
            raise ValidationException(f"Unknown image size: {size_name}")
        
        size = self.IMAGE_SIZES[size_name]
        if size is None:  # Original size
            return image_path
        
        # Generate resized image path
        path_obj = Path(image_path)
        resized_path = str(path_obj.parent / f"{path_obj.stem}_{size_name}{path_obj.suffix}")
        
        # Resize image
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._resize_image_sync, image_path, resized_path, size)
        
        return resized_path
    
    def _resize_image_sync(self, input_path: str, output_path: str, size: Tuple[int, int]) -> None:
        """Synchronous image resizing (for local storage only)"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize with maintaining aspect ratio
                img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
                
                # Save with optimization
                img.save(output_path, optimize=True, quality=85)
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            raise ValidationException("Failed to process image")
    
    async def _upload_to_cloudinary(
        self, 
        file_content: bytes, 
        public_id: str, 
        resource_type: str = "image",
        folder: Optional[str] = None
    ) -> Dict[str, str]:
        """Upload file to Cloudinary and return URLs for different sizes"""
        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                resource_type=resource_type,
                folder=folder,
                quality="auto",
                fetch_format="auto",
                overwrite=True
            )
            
            # Generate URLs for different transformations
            urls = {}
            base_public_id = upload_result['public_id']
            
            for size_name, transformation in self.CLOUDINARY_TRANSFORMATIONS.items():
                if size_name == 'original':
                    # Original with basic optimizations
                    urls[size_name] = cloudinary.CloudinaryImage(base_public_id).build_url(**transformation)
                else:
                    # Transformed versions
                    urls[size_name] = cloudinary.CloudinaryImage(base_public_id).build_url(**transformation)
            
            return urls
            
        except CloudinaryError as e:
            logger.error(f"Failed to upload to Cloudinary: {e}")
            raise Exception("Failed to upload file to cloud storage")
        except Exception as e:
            logger.error(f"Unexpected error uploading to Cloudinary: {e}")
            raise Exception("Failed to upload file")
    
    async def _save_file_local(self, file: UploadFile, file_path: str) -> None:
        """Save file to local storage"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
                
            # Reset file pointer
            await file.seek(0)
            
        except Exception as e:
            logger.error(f"Failed to save file locally: {e}")
            raise Exception("Failed to save file")
    
    async def upload_product_image(
        self, 
        file: UploadFile, 
        product_id: uuid.UUID,
        generate_sizes: bool = True
    ) -> Dict[str, str]:
        """
        Upload product image with multiple size variants
        
        Returns:
            Dict with image URLs for different sizes
        """
        await self._validate_file(file, "image")
        
        # Generate filename
        filename = self._generate_filename(file.filename, f"product_{product_id}")
        
        if self.settings.STORAGE_TYPE == "cloudinary":
            # Cloudinary storage
            file_content = await file.read()
            public_id = self._generate_cloudinary_public_id("products/images", filename)
            
            if generate_sizes:
                # Upload and get all size variants
                image_urls = await self._upload_to_cloudinary(
                    file_content, 
                    public_id, 
                    folder=f"products/images/{product_id}"
                )
            else:
                # Upload original only
                upload_result = cloudinary.uploader.upload(
                    file_content,
                    public_id=public_id,
                    folder=f"products/images/{product_id}",
                    quality="auto",
                    fetch_format="auto"
                )
                image_urls = {
                    'original': upload_result['secure_url']
                }
            
            # Reset file pointer
            await file.seek(0)
            
        else:
            # Local storage
            base_path = os.path.join(self.settings.UPLOAD_DIR, 'products', 'images')
            original_path = os.path.join(base_path, filename)
            
            # Save original file
            await self._save_file_local(file, original_path)
            
            image_urls = {}
            
            if generate_sizes:
                # Generate different sizes
                for size_name in self.IMAGE_SIZES.keys():
                    if size_name == 'original':
                        size_path = original_path
                    else:
                        size_path = await self._resize_image(original_path, size_name)
                    
                    # Generate URL
                    relative_path = os.path.relpath(size_path, self.settings.UPLOAD_DIR)
                    image_urls[size_name] = f"{self.settings.BASE_URL}/static/{relative_path.replace(os.sep, '/')}"
            else:
                relative_path = os.path.relpath(original_path, self.settings.UPLOAD_DIR)
                image_urls['original'] = f"{self.settings.BASE_URL}/static/{relative_path.replace(os.sep, '/')}"
        
        return image_urls
    
    async def upload_user_avatar(self, file: UploadFile, user_id: uuid.UUID) -> str:
        """Upload user avatar image"""
        await self._validate_file(file, "image")
        
        filename = self._generate_filename(file.filename, f"avatar_{user_id}")
        
        if self.settings.STORAGE_TYPE == "cloudinary":
            # Cloudinary storage with avatar-specific transformation
            file_content = await file.read()
            public_id = self._generate_cloudinary_public_id("users/avatars", filename)
            
            upload_result = cloudinary.uploader.upload(
                file_content, # type: ignore
                public_id=public_id,
                folder=f"users/avatars/{user_id}",
                transformation=[
                    {'width': 300, 'height': 300, 'crop': 'fill'},
                    {'quality': 'auto', 'fetch_format': 'auto'} # type: ignore
                ]
            )
            
            return upload_result['secure_url']
            
        else:
            # Local storage
            file_path = os.path.join(self.settings.UPLOAD_DIR, 'users', filename)
            await self._save_file_local(file, file_path)
            
            # Resize to avatar size (300x300)
            avatar_path = await self._resize_image(file_path, 'small')
            
            relative_path = os.path.relpath(avatar_path, self.settings.UPLOAD_DIR)
            return f"{self.settings.BASE_URL}/static/{relative_path.replace(os.sep, '/')}"
    
    async def delete_file(self, file_url: str) -> bool:
        """Delete file from storage"""
        try:
            if self.settings.STORAGE_TYPE == "cloudinary":
                # Extract public_id from Cloudinary URL
                if "cloudinary.com" in file_url:
                    # Parse Cloudinary URL to extract public_id
                    # URL format: https://res.cloudinary.com/{cloud_name}/image/upload/v{version}/{public_id}.{format}
                    url_parts = file_url.split('/')
                    if len(url_parts) >= 7:
                        # Find the public_id part (after 'upload' and version)
                        upload_index = url_parts.index('upload')
                        if upload_index + 2 < len(url_parts):
                            public_id_with_ext = '/'.join(url_parts[upload_index + 2:])
                            # Remove file extension
                            public_id = '.'.join(public_id_with_ext.split('.')[:-1])
                            
                            result = cloudinary.uploader.destroy(public_id)
                            return result.get('result') == 'ok'
                
            else:
                # Local storage
                if "/static/" in file_url:
                    relative_path = file_url.split("/static/", 1)[1]
                    file_path = os.path.join(self.settings.UPLOAD_DIR, relative_path.replace("/", os.sep))
                    
                    if os.path.exists(file_path):
                        await aiofiles.os.remove(file_path)
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_url}: {e}")
            return False
    
    async def delete_product_images(self, product_id: uuid.UUID) -> bool:
        """Delete all images for a product"""
        try:
            if self.settings.STORAGE_TYPE == "cloudinary":
                # Delete by folder prefix
                folder_path = f"products/images/{product_id}"
                
                # List resources in the folder
                result = cloudinary.api.resources(
                    type="upload",
                    prefix=folder_path,
                    max_results=500  # Adjust as needed
                )
                
                # Delete all resources
                if 'resources' in result:
                    public_ids = [resource['public_id'] for resource in result['resources']]
                    if public_ids:
                        cloudinary.api.delete_resources(public_ids)
                
                # Try to delete the folder itself
                try:
                    cloudinary.api.delete_folder(folder_path)
                except:
                    pass  # Folder might not be empty or might not exist
                
            else:
                # Local storage
                product_dir = os.path.join(self.settings.UPLOAD_DIR, 'products', 'images')
                
                # Find all files with product_id in name
                if os.path.exists(product_dir):
                    for filename in os.listdir(product_dir):
                        if str(product_id) in filename:
                            file_path = os.path.join(product_dir, filename)
                            await aiofiles.os.remove(file_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete product images for {product_id}: {e}")
            return False
    
    def get_file_info(self, file_url: str) -> Dict[str, Any]:
        """Get information about a file"""
        try:
            if self.settings.STORAGE_TYPE == "cloudinary":
                # For Cloudinary, we can't easily get file info without the public_id
                # This would require parsing the URL and making API calls
                # For now, we'll assume the file exists if it's a Cloudinary URL
                if "cloudinary.com" in file_url:
                    return {
                        'exists': True,
                        'storage_type': 'cloudinary',
                        'url': file_url
                    }
                
            else:
                # Local storage
                if "/static/" in file_url:
                    relative_path = file_url.split("/static/", 1)[1]
                    file_path = os.path.join(self.settings.UPLOAD_DIR, relative_path.replace("/", os.sep))
                    
                    if os.path.exists(file_path):
                        stat = os.stat(file_path)
                        return {
                            'exists': True,
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'path': file_path,
                            'storage_type': 'local'
                        }
            
            return {'exists': False}
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_url}: {e}")
            return {'exists': False}
    
    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """Clean up temporary files (only relevant for local storage)"""
        if self.settings.STORAGE_TYPE == "cloudinary":
            # No temp files to clean up with Cloudinary
            return 0
            
        try:
            temp_dir = os.path.join(self.settings.UPLOAD_DIR, 'temp')
            if not os.path.exists(temp_dir):
                return 0
            
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            deleted_count = 0
            
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > max_age_seconds:
                        await aiofiles.os.remove(file_path)
                        deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return 0
    
    def get_optimized_url(self, base_url: str, transformation: Dict[str, Any]) -> str:
        """
        Get an optimized URL for Cloudinary images, or return original URL for local storage
        """
        if self.settings.STORAGE_TYPE == "cloudinary" and "cloudinary.com" in base_url:
            try:
                # Extract public_id from URL
                url_parts = base_url.split('/')
                upload_index = url_parts.index('upload')
                if upload_index + 2 < len(url_parts):
                    public_id_with_ext = '/'.join(url_parts[upload_index + 2:])
                    public_id = '.'.join(public_id_with_ext.split('.')[:-1])
                    
                    return cloudinary.CloudinaryImage(public_id).build_url(**transformation)
            except Exception as e:
                logger.error(f"Failed to generate optimized Cloudinary URL: {e}")
        
        return base_url