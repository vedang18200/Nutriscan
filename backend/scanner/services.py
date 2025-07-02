
# backend/scanner/services.py (Complete version)
import requests
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from pyzbar import pyzbar
import re
from products.models import Product
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.cache import cache
import logging
import hashlib
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class BarcodeService:
    """Service for handling barcode-related operations"""
    
    @staticmethod
    def get_product_info(barcode: str) -> Optional[Dict[str, Any]]:
        """Fetch product info from external APIs with caching"""
        cache_key = f"barcode_{barcode}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Try Open Food Facts API
        try:
            response = requests.get(
                f'https://world.openfoodfacts.org/api/v0/product/{barcode}.json',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 1:
                    product = data['product']
                    result = {
                        'name': product.get('product_name', ''),
                        'brand': product.get('brands', ''),
                        'ingredients': product.get('ingredients_text', ''),
                        'nutrition_facts': product.get('nutriments', {}),
                        'image_url': product.get('image_url', ''),
                        'categories': product.get('categories', ''),
                        'allergens': product.get('allergens', ''),
                        'additives': product.get('additives_tags', []),
                        'nova_group': product.get('nova_group', ''),
                        'ecoscore_grade': product.get('ecoscore_grade', ''),
                        'nutriscore_grade': product.get('nutriscore_grade', '')
                    }
                    # Cache for 1 hour
                    cache.set(cache_key, result, 3600)
                    return result
        except Exception as e:
            logger.error(f"Error fetching from Open Food Facts: {e}")

        # Try UPC Database API as fallback
        try:
            response = requests.get(
                f'https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 'OK' and data['items']:
                    item = data['items'][0]
                    result = {
                        'name': item.get('title', ''),
                        'brand': item.get('brand', ''),
                        'ingredients': '',
                        'nutrition_facts': {},
                        'image_url': item.get('images', [''])[0] if item.get('images') else '',
                        'categories': item.get('category', ''),
                        'allergens': '',
                        'additives': [],
                        'nova_group': '',
                        'ecoscore_grade': '',
                        'nutriscore_grade': ''
                    }
                    # Cache for 1 hour
                    cache.set(cache_key, result, 3600)
                    return result
        except Exception as e:
            logger.error(f"Error fetching from UPC Database: {e}")

        return None

class OCRService:
    """Enhanced OCR service with better accuracy and language support"""
    
    def __init__(self):
        # Configure Tesseract for better multilingual support
        self.config_eng = '--oem 3 --psm 6 -l eng'
        self.config_ara = '--oem 3 --psm 6 -l ara'
        self.config_multi = '--oem 3 --psm 6 -l eng+ara'

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Advanced image preprocessing for better OCR results"""
        # Read image
        if isinstance(image_path, str):
            full_path = default_storage.path(image_path)
            image = cv2.imread(full_path)
        else:
            image = image_path
        
        if image is None:
            raise ValueError("Could not read image")
        
        # Convert to PIL for enhancement
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Enhance contrast and sharpness
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.5)
        
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(2.0)
        
        # Convert back to OpenCV
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # Denoise
        denoised = cv2.medianBlur(cleaned, 3)
        
        return denoised

    def extract_barcode(self, image_path: str) -> Dict[str, Any]:
        """Extract barcode from image with enhanced detection"""
        try:
            if isinstance(image_path, str):
                full_path = default_storage.path(image_path)
                image = cv2.imread(full_path)
            else:
                image = image_path
            
            # Try multiple preprocessing approaches
            approaches = [
                image,  # Original
                self.preprocess_image(image),  # Preprocessed
                cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Simple grayscale
            ]
            
            for processed_image in approaches:
                barcodes = pyzbar.decode(processed_image)
                if barcodes:
                    barcode_data = barcodes[0].data.decode('utf-8')
                    return {
                        'barcode': barcode_data,
                        'type': barcodes[0].type,
                        'confidence': 100,
                        'text': barcode_data
                    }
            
            return {'barcode': None, 'confidence': 0, 'text': ''}
            
        except Exception as e:
            logger.error(f"Error extracting barcode: {e}")
            return {'barcode': None, 'confidence': 0, 'text': ''}

    def extract_ingredients(self, image_path: str) -> Dict[str, Any]:
        """Extract ingredients list from image with enhanced parsing"""
        try:
            processed_image = self.preprocess_image(image_path)
            
            # Try multiple OCR configurations
            texts = []
            configs = [self.config_multi, self.config_eng, self.config_ara]
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(processed_image, config=config)
                    if text.strip():
                        texts.append(text)
                except:
                    continue
            
            # Use the best result
            best_text = max(texts, key=len) if texts else ""
            
            # Parse ingredients
            ingredients = self._parse_ingredients(best_text)
            
            return {
                'text': best_text,
                'ingredients': ingredients,
                'confidence': self._calculate_confidence(best_text)
            }
            
        except Exception as e:
            logger.error(f"Error extracting ingredients: {e}")
            return {'text': '', 'ingredients': [], 'confidence': 0}

    def extract_nutrition_facts(self, image_path: str) -> Dict[str, Any]:
        """Extract nutrition facts from image with enhanced parsing"""
        try:
            processed_image = self.preprocess_image(image_path)
            
            # Try multiple OCR configurations
            texts = []
            configs = [self.config_multi, self.config_eng, self.config_ara]
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(processed_image, config=config)
                    if text.strip():
                        texts.append(text)
                except:
                    continue
            
            # Use the best result
            best_text = max(texts, key=len) if texts else ""
            
            # Parse nutrition facts
            nutrition = self._parse_nutrition_facts(best_text)
            
            return {
                'text': best_text,
                'nutrition_facts': nutrition,
                'confidence': self._calculate_confidence(best_text)
            }
            
        except Exception as e:
            logger.error(f"Error extracting nutrition facts: {e}")
            return {'text': '', 'nutrition_facts': {}, 'confidence': 0}

    def extract_general_text(self, image_path: str) -> Dict[str, Any]:
        """Extract general text from image"""
        try:
            processed_image = self.preprocess_image(image_path)
            text = pytesseract.image_to_string(processed_image, config=self.config_multi)
            
            return {
                'text': text,
                'confidence': self._calculate_confidence(text)
            }
            
        except Exception as e:
            logger.error(f"Error extracting general text: {e}")
            return {'text': '', 'confidence': 0}

    def _parse_ingredients(self, text: str) -> List[str]:
        """Enhanced ingredients parsing with better accuracy"""
        ingredients = []
        
        if not text:
            return ingredients
        
        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text.strip())
        lines = text.split('\n')
        
        # Look for ingredients section
        ingredients_section = False
        ingredients_keywords = [
            'ingredients', 'مكونات', 'ingrédients', 'ingredientes', 
            'zutaten', 'ingredienti', 'składniki'
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line contains ingredients keyword
            if any(keyword in line.lower() for keyword in ingredients_keywords):
                ingredients_section = True
                # Extract ingredients from the same line if present
                for keyword in ingredients_keywords:
                    if keyword in line.lower():
                        parts = line.lower().split(keyword)
                        if len(parts) > 1:
                            ingredients_text = parts[1]
                            self._extract_ingredients_from_text(ingredients_text, ingredients)
                continue
            
            # If we're in ingredients section, process the line
            if ingredients_section:
                self._extract_ingredients_from_text(line, ingredients)
        
        # Remove duplicates and clean up
        unique_ingredients = []
        seen = set()
        for ingredient in ingredients:
            clean_ingredient = re.sub(r'[^\w\s\-()]', '', ingredient).strip()
            if clean_ingredient and len(clean_ingredient) > 2 and clean_ingredient.lower() not in seen:
                unique_ingredients.append(clean_ingredient)
                seen.add(clean_ingredient.lower())
        
        return unique_ingredients[:50]  # Limit to 50 ingredients

    def _extract_ingredients_from_text(self, text: str, ingredients: List[str]) -> None:
        """Extract ingredients from a text line"""
        # Split by common separators
        separators = r'[,;،؛\n\r]'
        items = re.split(separators, text)
        
        for item in items:
            item = item.strip()
            # Remove common prefixes/suffixes
            item = re.sub(r'^[-:\s]*', '', item)
            item = re.sub(r'[-:\s]*$', '', item)
            
            if item and len(item) > 2 and not item.isdigit():
                # Clean up common OCR errors
                item = re.sub(r'\s+', ' ', item)
                ingredients.append(item)

    def _parse_nutrition_facts(self, text: str) -> Dict[str, float]:
        """Enhanced nutrition facts parsing"""
        nutrition = {}
        
        if not text:
            return nutrition
        
        # Comprehensive nutrition patterns (English and Arabic)
        patterns = {
            'energy': r'(?:energy|calories?|طاقة|سعرات)[:\s]*(\d+(?:\.\d+)?)\s*(?:kcal|cal|kj)?',
            'protein': r'(?:protein|بروتين)[:\s]*(\d+(?:\.\d+)?)\s*(?:g|gm|grams?)?',
            'total_fat': r'(?:total\s*fat|fat|دهون)[:\s]*(\d+(?:\.\d+)?)\s*(?:g|gm|grams?)?',
            'saturated_fat': r'(?:saturated\s*fat|دهون\s*مشبعة)[:\s]*(\d+(?:\.\d+)?)\s*(?:g|gm|grams?)?',
            'trans_fat': r'(?:trans\s*fat|دهون\s*متحولة)[:\s]*(\d+(?:\.\d+)?)\s*(?:g|gm|grams?)?',
            'cholesterol': r'(?:cholesterol|كوليسترول)[:\s]*(\d+(?:\.\d+)?)\s*(?:mg|milligrams?)?',
            'sodium': r'(?:sodium|صوديوم)[:\s]*(\d+(?:\.\d+)?)\s*(?:mg|milligrams?)?',
            'total_carbs': r'(?:total\s*carb|carbohydrate|كربوهيدرات)[:\s]*(\d+(?:\.\d+)?)\s*(?:g|gm|grams?)?',
            'dietary_fiber': r'(?:dietary\s*fiber|fiber|fibre|ألياف)[:\s]*(\d+(?:\.\d+)?)\s*(?:g|gm|grams?)?',
            'sugars': r'(?:total\s*sugars?|sugars?|سكر)[:\s]*(\d+(?:\.\d+)?)\s*(?:g|gm|grams?)?',
            'added_sugars': r'(?:added\s*sugars?|سكر\s*مضاف)[:\s]*(\d+(?:\.\d+)?)\s*(?:g|gm|grams?)?',
            'vitamin_c': r'(?:vitamin\s*c|فيتامين\s*ج)[:\s]*(\d+(?:\.\d+)?)\s*(?:mg|milligrams?)?',
            'calcium': r'(?:calcium|كالسيوم)[:\s]*(\d+(?:\.\d+)?)\s*(?:mg|milligrams?)?',
            'iron': r'(?:iron|حديد)[:\s]*(\d+(?:\.\d+)?)\s*(?:mg|milligrams?)?'
        }
        
        text_lower = text.lower()
        
        for nutrient, pattern in patterns.items():
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    # Take the first valid match
                    value = float(matches[0])
                    if value >= 0:  # Ensure non-negative values
                        nutrition[nutrient] = value
                except (ValueError, IndexError):
                    continue
        
        return nutrition

    def _calculate_confidence(self, text: str) -> int:
        """Enhanced confidence calculation"""
        if not text or len(text.strip()) < 5:
            return 0
        
        # Basic text quality metrics
        words = text.split()
        if len(words) < 2:
            return 20
        
        # Check for food-related keywords (multilingual)
        food_keywords = [
            'ingredients', 'nutrition', 'calories', 'protein', 'fat', 'carb',
            'مكونات', 'سعرات', 'بروتين', 'دهون', 'كربوهيدرات',
            'vitamin', 'mineral', 'sodium', 'sugar', 'fiber'
        ]
        
        keyword_count = sum(1 for word in words if any(kw in word.lower() for kw in food_keywords))
        
        # Calculate confidence
        base_confidence = min(70, len(words) * 3)
        keyword_bonus = min(25, keyword_count * 5)
        
        # Penalty for too many special characters (OCR errors)
        special_char_ratio = len(re.findall(r'[^\w\s]', text)) / len(text)
        special_char_penalty = int(special_char_ratio * 30)
        
        final_confidence = max(0, base_confidence + keyword_bonus - special_char_penalty)
        return min(100, final_confidence)


class ProductService:
    """Enhanced product service with better data handling"""
    
    @staticmethod
    def get_or_create_by_barcode(barcode: str) -> Optional[Product]:
        """Get product by barcode or create new one with enhanced data"""
        try:
            return Product.objects.get(barcode=barcode)
        except Product.DoesNotExist:
            # Try to fetch from external API
            barcode_service = BarcodeService()
            product_info = barcode_service.get_product_info(barcode)
            
            if product_info and product_info.get('name'):
                # Parse ingredients
                ingredients_text = product_info.get('ingredients', '')
                ingredients = ProductService._parse_ingredients_text(ingredients_text)
                
                # Clean and validate nutrition facts
                nutrition_facts = ProductService._clean_nutrition_facts(
                    product_info.get('nutrition_facts', {})
                )
                
                product = Product.objects.create(
                    barcode=barcode,
                    name=product_info.get('name', f'Product {barcode}'),
                    brand=product_info.get('brand', 'Unknown'),
                    ingredients=ingredients,
                    nutrition_facts=nutrition_facts,
                    product_image=product_info.get('image_url', ''),
                    country_of_origin='Unknown',
                    # Additional fields from enhanced API data
                    categories=product_info.get('categories', ''),
                    allergens=product_info.get('allergens', ''),
                    additives=product_info.get('additives', []),
                    nova_group=product_info.get('nova_group', ''),
                    ecoscore_grade=product_info.get('ecoscore_grade', ''),
                    nutriscore_grade=product_info.get('nutriscore_grade', '')
                )
                return product
            
            return None

    @staticmethod
    def create_from_ocr_data(ocr_data: Dict[str, Any]) -> Optional[Product]:
        """Create product from OCR extracted data with validation"""
        if not ocr_data:
            return None
            
        # Check if we have sufficient data
        has_ingredients = 'ingredients' in ocr_data and ocr_data['ingredients']
        has_nutrition = 'nutrition_facts' in ocr_data and ocr_data['nutrition_facts']
        has_barcode = 'barcode' in ocr_data and ocr_data['barcode']
        
        if not (has_ingredients or has_nutrition or has_barcode):
            return None
        
        try:
            # Generate a unique identifier for OCR-based products
            if has_barcode:
                temp_barcode = ocr_data['barcode']
            else:
                # Create hash based on available data
                data_string = str(ocr_data.get('ingredients', '')) + str(ocr_data.get('nutrition_facts', ''))
                temp_barcode = 'OCR_' + hashlib.md5(data_string.encode()).hexdigest()[:12]
            
            # Check if product already exists
            try:
                existing_product = Product.objects.get(barcode=temp_barcode)
                return existing_product
            except Product.DoesNotExist:
                pass
            
            # Extract product name from OCR text if available
            product_name = ProductService._extract_product_name_from_ocr(ocr_data)
            
            product = Product.objects.create(
                barcode=temp_barcode,
                name=product_name,
                brand="Scanned Product",
                ingredients=ocr_data.get('ingredients', []),
                nutrition_facts=ProductService._clean_nutrition_facts(
                    ocr_data.get('nutrition_facts', {})
                ),
                country_of_origin='Unknown',
                categories='',
                allergens='',
                additives=[],
                nova_group='',
                ecoscore_grade='',
                nutriscore_grade=''
            )
            return product
            
        except Exception as e:
            logger.error(f"Error creating product from OCR data: {e}")
            return None

    @staticmethod
    def _parse_ingredients_text(ingredients_text: str) -> List[str]:
        """Parse ingredients text into structured format with validation"""
        if not ingredients_text:
            return []
        
        # Clean the text
        ingredients_text = re.sub(r'\s+', ' ', ingredients_text.strip())
        
        # Split by common separators
        separators = r'[,;،؛]'
        ingredients = re.split(separators, ingredients_text)
        
        # Clean and validate each ingredient
        cleaned_ingredients = []
        for ingredient in ingredients:
            ingredient = ingredient.strip()
            # Remove parenthetical information and percentages
            ingredient = re.sub(r'\([^)]*\)', '', ingredient)
            ingredient = re.sub(r'\d+%?', '', ingredient)
            ingredient = ingredient.strip()
            
            # Validate ingredient
            if (ingredient and 
                len(ingredient) > 2 and 
                not ingredient.isdigit() and
                len(ingredient) < 100):  # Reasonable length limit
                cleaned_ingredients.append(ingredient)
        
        return cleaned_ingredients[:50]  # Limit to 50 ingredients

    @staticmethod
    def _clean_nutrition_facts(nutrition_data: Dict[str, Any]) -> Dict[str, float]:
        """Clean and validate nutrition facts data"""
        if not nutrition_data:
            return {}
        
        cleaned_nutrition = {}
        
        # Define valid nutrition keys and their expected ranges
        valid_nutrients = {
            'energy': (0, 9000),  # kcal per 100g
            'protein': (0, 100),  # g per 100g
            'total_fat': (0, 100),  # g per 100g
            'saturated_fat': (0, 100),  # g per 100g
            'trans_fat': (0, 100),  # g per 100g
            'cholesterol': (0, 1000),  # mg per 100g
            'sodium': (0, 10000),  # mg per 100g
            'total_carbs': (0, 100),  # g per 100g
            'dietary_fiber': (0, 100),  # g per 100g
            'sugars': (0, 100),  # g per 100g
            'added_sugars': (0, 100),  # g per 100g
            'vitamin_c': (0, 1000),  # mg per 100g
            'calcium': (0, 2000),  # mg per 100g
            'iron': (0, 100),  # mg per 100g
        }
        
        for key, value in nutrition_data.items():
            try:
                # Convert to float
                if isinstance(value, str):
                    # Remove units and convert
                    value = re.sub(r'[^\d.]', '', value)
                    if not value:
                        continue
                    value = float(value)
                elif isinstance(value, (int, float)):
                    value = float(value)
                else:
                    continue
                
                # Validate range
                if key in valid_nutrients:
                    min_val, max_val = valid_nutrients[key]
                    if min_val <= value <= max_val:
                        cleaned_nutrition[key] = value
                else:
                    # For unknown nutrients, just ensure they're positive
                    if value >= 0:
                        cleaned_nutrition[key] = value
                        
            except (ValueError, TypeError):
                continue
        
        return cleaned_nutrition

    @staticmethod
    def _extract_product_name_from_ocr(ocr_data: Dict[str, Any]) -> str:
        """Extract product name from OCR data"""
        text = ocr_data.get('text', '')
        if not text:
            return f"Scanned Product {ocr_data.get('barcode', '')[-6:]}"
        
        # Look for product name patterns
        lines = text.split('\n')
        
        # Usually the product name is in the first few lines and is the longest
        potential_names = []
        
        for i, line in enumerate(lines[:5]):  # Check first 5 lines
            line = line.strip()
            if (line and 
                len(line) > 5 and 
                len(line) < 100 and
                not line.lower().startswith(('ingredients', 'nutrition', 'مكونات'))):
                potential_names.append((line, len(line), i))
        
        if potential_names:
            # Sort by length (descending) and position (ascending)
            potential_names.sort(key=lambda x: (-x[1], x[2]))
            return potential_names[0][0]
        
        return f"Scanned Product {hashlib.md5(text.encode()).hexdigest()[:6]}"

    @staticmethod
    def search_products(query: str, user=None) -> List[Product]:
        """Search for products by name, brand, or ingredients"""
        if not query or len(query) < 2:
            return []
        
        # Build search query
        search_query = Q(name__icontains=query) | Q(brand__icontains=query)
        
        # Search in ingredients (if stored as list)
        try:
            products = Product.objects.filter(search_query)
            
            # If user is provided, prioritize their previously scanned products
            if user:
                from .models import UserScanHistory
                user_products = UserScanHistory.objects.filter(
                    user=user
                ).values_list('product_id', flat=True)
                
                # Split results into user's products and others
                user_scanned = products.filter(id__in=user_products)
                others = products.exclude(id__in=user_products)
                
                # Combine with user's products first
                products = list(user_scanned) + list(others)
            
            return products[:20]  # Limit results
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []

    @staticmethod
    def get_similar_products(product: Product, limit: int = 5) -> List[Product]:
        """Get similar products based on ingredients and categories"""
        if not product:
            return []
        
        try:
            # Search by brand first
            similar_by_brand = Product.objects.filter(
                brand=product.brand
            ).exclude(id=product.id)[:limit//2]
            
            # Search by categories
            similar_by_category = []
            if product.categories:
                similar_by_category = Product.objects.filter(
                    categories__icontains=product.categories.split(',')[0]
                ).exclude(id=product.id)[:limit//2]
            
            # Combine and remove duplicates
            similar_products = []
            seen_ids = set()
            
            for prod in list(similar_by_brand) + list(similar_by_category):
                if prod.id not in seen_ids:
                    similar_products.append(prod)
                    seen_ids.add(prod.id)
                    
                if len(similar_products) >= limit:
                    break
            
            return similar_products
            
        except Exception as e:
            logger.error(f"Error finding similar products: {e}")
            return []


# Additional utility functions and services

class ImageProcessingService:
    """Service for advanced image processing operations"""
    
    @staticmethod
    def enhance_image_for_ocr(image_path: str) -> str:
        """Apply advanced image enhancement for better OCR results"""
        try:
            # Load image
            full_path = default_storage.path(image_path)
            image = cv2.imread(full_path)
            
            if image is None:
                raise ValueError("Could not load image")
            
            # Apply multiple enhancement techniques
            enhanced_images = []
            
            # Method 1: Standard preprocessing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            enhanced_images.append(thresh)
            
            # Method 2: Adaptive threshold
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            enhanced_images.append(adaptive)
            
            # Method 3: Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            enhanced_images.append(enhanced)
            
            # Save enhanced versions and return the best one
            best_image = enhanced_images[0]  # Default to first
            
            # Save enhanced image
            enhanced_path = image_path.replace('.', '_enhanced.')
            cv2.imwrite(default_storage.path(enhanced_path), best_image)
            
            return enhanced_path
            
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return image_path  # Return original if enhancement fails

    @staticmethod
    def detect_text_regions(image_path: str) -> List[Dict[str, Any]]:
        """Detect text regions in image for targeted OCR"""
        try:
            full_path = default_storage.path(image_path)
            image = cv2.imread(full_path)
            
            if image is None:
                return []
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply morphological operations to detect text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 6))
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_regions = []
            for i, contour in enumerate(contours):
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter out small regions
                if w > 50 and h > 20:
                    text_regions.append({
                        'id': i,
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'area': w * h
                    })
            
            # Sort by area (largest first)
            text_regions.sort(key=lambda x: x['area'], reverse=True)
            
            return text_regions[:10]  # Return top 10 regions
            
        except Exception as e:
            logger.error(f"Error detecting text regions: {e}")
            return []


class ValidationService:
    """Service for validating extracted data"""
    
    @staticmethod
    def validate_barcode(barcode: str) -> bool:
        """Validate barcode format"""
        if not barcode:
            return False
        
        # Remove any non-digit characters
        clean_barcode = re.sub(r'[^\d]', '', barcode)
        
        # Check common barcode lengths
        valid_lengths = [8, 12, 13, 14]  # EAN-8, UPC-A, EAN-13, EAN-14
        
        return len(clean_barcode) in valid_lengths

    @staticmethod
    def validate_ingredients(ingredients: List[str]) -> List[str]:
        """Validate and clean ingredients list"""
        if not ingredients:
            return []
        
        validated = []
        
        # Common ingredient keywords to validate against
        valid_patterns = [
            r'^[a-zA-Z\s\-\(\)]+,  # Letters, spaces, hyphens, parentheses
            r'^[a-zA-Z\s\-\(\)]+\s*\d+%?,  # With percentage
            r'^[أ-ي\s\-\(\)]+,  # Arabic text
        ]
        
        for ingredient in ingredients:
            ingredient = ingredient.strip()
            
            # Skip if too short or too long
            if len(ingredient) < 2 or len(ingredient) > 100:
                continue
            
            # Check against valid patterns
            if any(re.match(pattern, ingredient) for pattern in valid_patterns):
                validated.append(ingredient)
        
        return validated[:50]  # Limit to 50 ingredients

    @staticmethod
    def validate_nutrition_facts(nutrition: Dict[str, float]) -> Dict[str, float]:
        """Validate nutrition facts values"""
        if not nutrition:
            return {}
        
        validated = {}
        
        # Define reasonable ranges for nutrition values (per 100g)
        ranges = {
            'energy': (0, 9000),
            'protein': (0, 100),
            'total_fat': (0, 100),
            'saturated_fat': (0, 100),
            'trans_fat': (0, 50),
            'cholesterol': (0, 1000),
            'sodium': (0, 10000),
            'total_carbs': (0, 100),
            'dietary_fiber': (0, 100),
            'sugars': (0, 100),
            'vitamin_c': (0, 1000),
            'calcium': (0, 2000),
            'iron': (0, 100)
        }
        
        for key, value in nutrition.items():
            try:
                value = float(value)
                
                if key in ranges:
                    min_val, max_val = ranges[key]
                    if min_val <= value <= max_val:
                        validated[key] = value
                elif value >= 0:  # For unknown nutrients, just ensure positive
                    validated[key] = value
                    
            except (ValueError, TypeError):
                continue
        
        return validated


# Export all services
__all__ = [
    'BarcodeService',
    'OCRService', 
    'ProductService',
    'ImageProcessingService',
    'ValidationService'
]