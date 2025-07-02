

from django.db import models

class PromptTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=20)
    template = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('name', 'version')

class AIAnalysisLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    prompt_used = models.TextField()
    ai_response = models.TextField()
    processing_time = models.FloatField(help_text="Processing time in seconds")
    tokens_used = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

