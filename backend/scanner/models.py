

from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()

class ScanSession(models.Model):
    SCAN_TYPES = [
        ('barcode', 'Barcode Scan'),
        ('ingredient', 'Ingredient OCR'),
        ('nutrition', 'Nutrition Label OCR'),
        ('manual', 'Manual Entry'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scan_type = models.CharField(max_length=20, choices=SCAN_TYPES)
    scanned_image = models.ImageField(upload_to='scans/', null=True, blank=True)
    extracted_text = models.TextField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ScanResult(models.Model):
    SAFETY_LEVELS = [
        ('HIGH_RISK', 'High Risk - Avoid'),
        ('MODERATE_RISK', 'Moderate Risk - Consume with Caution'),
        ('LOW_RISK', 'Low Risk - Generally Safe'),
        ('GOOD_TO_GO', 'Good to Go - Recommended'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    scan_session = models.ForeignKey(ScanSession, on_delete=models.SET_NULL, null=True)
    
    # AI Analysis Results
    safety_level = models.CharField(max_length=20, choices=SAFETY_LEVELS)
    risk_score = models.FloatField(help_text="Risk score from 0-100")
    
    # Detailed analysis
    health_impact = models.JSONField(help_text="Immediate and long-term health impacts")
    specific_concerns = models.JSONField(default=list, help_text="Specific health concerns for this user")
    recommendations = models.JSONField(default=list, help_text="Personalized recommendations")
    alternatives = models.JSONField(default=list, help_text="Alternative product suggestions")
    
    # Additive analysis
    harmful_additives = models.JSONField(default=list, help_text="Harmful additives found")
    preservative_concerns = models.JSONField(default=list, help_text="Preservative-related concerns")
    
    # Benefits (for healthy products)
    health_benefits = models.JSONField(default=list, help_text="Health benefits of the product")
    nutritional_highlights = models.JSONField(default=list, help_text="Positive nutritional aspects")
    
    # AI metadata
    ai_model_used = models.CharField(max_length=50, default='gemini-pro')
    analysis_timestamp = models.DateTimeField(auto_now_add=True)
    prompt_version = models.CharField(max_length=20, default='1.0')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['safety_level']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.safety_level}"

class UserScanHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    scan_count = models.IntegerField(default=1)
    last_scanned = models.DateTimeField(auto_now=True)
    favorite = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'product')
