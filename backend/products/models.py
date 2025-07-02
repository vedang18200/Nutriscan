
# backend/products/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Product(models.Model):
    SAFETY_LEVELS = [
        ('HIGH_RISK', 'High Risk'),
        ('MODERATE_RISK', 'Moderate Risk'),
        ('LOW_RISK', 'Low Risk'),
        ('GOOD_TO_GO', 'Good to Go'),
    ]

    # Basic product information
    barcode = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    category = models.CharField(max_length=100, null=True, blank=True)
    
    # Product details
    ingredients = models.JSONField(help_text="List of ingredients")
    nutrition_facts = models.JSONField(help_text="Nutrition information per 100g")
    serving_size = models.CharField(max_length=50, null=True, blank=True)
    
    # Additives and preservatives
    additives = models.JSONField(default=list, help_text="List of additives with E-numbers")
    preservatives = models.JSONField(default=list, help_text="List of preservatives")
    artificial_colors = models.JSONField(default=list)
    artificial_flavors = models.JSONField(default=list)
    
    # Regulatory information
    country_of_origin = models.CharField(max_length=50)
    is_uae_approved = models.BooleanField(default=True)
    halal_certified = models.BooleanField(default=False)
    organic_certified = models.BooleanField(default=False)
    
    # Product images
    product_image = models.URLField(null=True, blank=True)
    nutrition_label_image = models.URLField(null=True, blank=True)
    ingredients_image = models.URLField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_verified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['brand', 'name']),
        ]

    def __str__(self):
        return f"{self.brand} - {self.name}"

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')
