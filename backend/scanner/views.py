
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import io
import base64
from PIL import Image
import pytesseract
from pyzbar import pyzbar
import cv2
import numpy as np
import logging

from .models import ScanSession, ScanResult, UserScanHistory
from .serializers import ScanSessionSerializer, ScanResultSerializer, UserScanHistorySerializer
from accounts.models import UserProfile
from products.models import Product
from ai_analysis.services import GeminiAnalysisService
from .services import BarcodeService, OCRService, ProductService

logger = logging.getLogger(__name__)

class ScannerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ScanResultSerializer

    def get_queryset(self):
        return ScanResult.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def barcode(self, request):
        """Scan product by barcode"""
        barcode = request.data.get('barcode')
        if not barcode:
            return Response({'error': 'Barcode is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create scan session
            scan_session = ScanSession.objects.create(
                user=request.user,
                scan_type='barcode'
            )

            # Get or create product
            product = ProductService.get_or_create_by_barcode(barcode)
            
            if not product:
                return Response({'error': 'Product not found'}, 
                              status=status.HTTP_404_NOT_FOUND)

            # Perform AI analysis
            analysis_service = GeminiAnalysisService()
            user_profile = UserProfile.objects.get(user=request.user)
            analysis_result = analysis_service.analyze_product_for_user(
                user_profile, product
            )

            # Create scan result
            scan_result = ScanResult.objects.create(
                user=request.user,
                product=product,
                scan_session=scan_session,
                safety_level=analysis_result['safety_level'],
                risk_score=analysis_result['risk_score'],
                health_impact=analysis_result['health_impact'],
                specific_concerns=analysis_result['specific_concerns'],
                recommendations=analysis_result['recommendations'],
                alternatives=analysis_result['alternatives'],
                harmful_additives=analysis_result['harmful_additives'],
                preservative_concerns=analysis_result['preservative_concerns'],
                health_benefits=analysis_result['health_benefits'],
                nutritional_highlights=analysis_result['nutritional_highlights']
            )

            # Update scan history
            history, created = UserScanHistory.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'scan_count': 1}
            )
            if not created:
                history.scan_count += 1
                history.save()

            serializer = ScanResultSerializer(scan_result)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found. Please complete your profile first.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in barcode scan: {str(e)}")
            return Response({'error': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def image(self, request):
        """Scan product image using OCR"""
        image_file = request.FILES.get('image')
        scan_type = request.data.get('scan_type', 'general')

        if not image_file:
            return Response({'error': 'Image is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate image format
            if not image_file.content_type.startswith('image/'):
                return Response({'error': 'Invalid image format'}, 
                              status=status.HTTP_400_BAD_REQUEST)

            # Save uploaded image
            image_path = default_storage.save(
                f'scans/{request.user.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}_{image_file.name}',
                ContentFile(image_file.read())
            )

            # Create scan session
            scan_session = ScanSession.objects.create(
                user=request.user,
                scan_type=scan_type,
                scanned_image=image_path
            )

            # Process image based on scan type
            ocr_service = OCRService()
            
            if scan_type == 'ingredients':
                extracted_data = ocr_service.extract_ingredients(image_path)
            elif scan_type == 'nutrition':
                extracted_data = ocr_service.extract_nutrition_facts(image_path)
            elif scan_type == 'barcode':
                extracted_data = ocr_service.extract_barcode(image_path)
            else:
                extracted_data = ocr_service.extract_general_text(image_path)

            # Update scan session with extracted text
            scan_session.extracted_text = extracted_data.get('text', '')
            scan_session.confidence_score = extracted_data.get('confidence', 0)
            scan_session.save()

            # Try to find or create product from extracted data
            product = ProductService.create_from_ocr_data(extracted_data)

            if product:
                # Perform AI analysis
                analysis_service = GeminiAnalysisService()
                user_profile = UserProfile.objects.get(user=request.user)
                analysis_result = analysis_service.analyze_product_for_user(
                    user_profile, product
                )

                # Create scan result
                scan_result = ScanResult.objects.create(
                    user=request.user,
                    product=product,
                    scan_session=scan_session,
                    safety_level=analysis_result['safety_level'],
                    risk_score=analysis_result['risk_score'],
                    health_impact=analysis_result['health_impact'],
                    specific_concerns=analysis_result['specific_concerns'],
                    recommendations=analysis_result['recommendations'],
                    alternatives=analysis_result['alternatives'],
                    harmful_additives=analysis_result['harmful_additives'],
                    preservative_concerns=analysis_result['preservative_concerns'],
                    health_benefits=analysis_result['health_benefits'],
                    nutritional_highlights=analysis_result['nutritional_highlights']
                )

                # Update scan history
                history, created = UserScanHistory.objects.get_or_create(
                    user=request.user,
                    product=product,
                    defaults={'scan_count': 1}
                )
                if not created:
                    history.scan_count += 1
                    history.save()

                serializer = ScanResultSerializer(scan_result)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'message': 'Text extracted but product could not be identified',
                    'extracted_data': extracted_data,
                    'scan_session_id': scan_session.id
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in image scan: {str(e)}")
            return Response({'error': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get user's scan history"""
        limit = int(request.query_params.get('limit', 50))
        scan_type = request.query_params.get('scan_type')
        
        queryset = ScanResult.objects.filter(user=request.user)
        
        if scan_type:
            queryset = queryset.filter(scan_session__scan_type=scan_type)
        
        results = queryset.order_by('-created_at')[:limit]
        serializer = ScanResultSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user's scanning statistics"""
        try:
            # Get stats for last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            total_scans = ScanResult.objects.filter(user=request.user).count()
            recent_scans = ScanResult.objects.filter(
                user=request.user,
                created_at__gte=thirty_days_ago
            ).count()
            
            # Get most scanned products
            most_scanned = UserScanHistory.objects.filter(
                user=request.user
            ).order_by('-scan_count')[:5]
            
            # Safety level distribution
            safety_distribution = ScanResult.objects.filter(
                user=request.user
            ).values('safety_level').annotate(count=Count('safety_level'))
            
            return Response({
                'total_scans': total_scans,
                'recent_scans': recent_scans,
                'most_scanned_products': UserScanHistorySerializer(most_scanned, many=True).data,
                'safety_distribution': list(safety_distribution)
            })
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return Response({'error': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def batch_scan(self, request):
        """Scan multiple products at once"""
        barcodes = request.data.get('barcodes', [])
        
        if not barcodes or not isinstance(barcodes, list):
            return Response({'error': 'Barcodes list is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if len(barcodes) > 20:  # Limit batch size
            return Response({'error': 'Maximum 20 barcodes allowed per batch'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        results = []
        errors = []
        
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            analysis_service = GeminiAnalysisService()
            
            for barcode in barcodes:
                try:
                    # Create scan session
                    scan_session = ScanSession.objects.create(
                        user=request.user,
                        scan_type='barcode_batch'
                    )
                    
                    # Get or create product
                    product = ProductService.get_or_create_by_barcode(barcode)
                    
                    if product:
                        # Perform AI analysis
                        analysis_result = analysis_service.analyze_product_for_user(
                            user_profile, product
                        )
                        
                        # Create scan result
                        scan_result = ScanResult.objects.create(
                            user=request.user,
                            product=product,
                            scan_session=scan_session,
                            safety_level=analysis_result['safety_level'],
                            risk_score=analysis_result['risk_score'],
                            health_impact=analysis_result['health_impact'],
                            specific_concerns=analysis_result['specific_concerns'],
                            recommendations=analysis_result['recommendations'],
                            alternatives=analysis_result['alternatives'],
                            harmful_additives=analysis_result['harmful_additives'],
                            preservative_concerns=analysis_result['preservative_concerns'],
                            health_benefits=analysis_result['health_benefits'],
                            nutritional_highlights=analysis_result['nutritional_highlights']
                        )
                        
                        results.append(ScanResultSerializer(scan_result).data)
                    else:
                        errors.append({'barcode': barcode, 'error': 'Product not found'})
                        
                except Exception as e:
                    errors.append({'barcode': barcode, 'error': str(e)})
            
            return Response({
                'results': results,
                'errors': errors,
                'processed': len(results),
                'failed': len(errors)
            }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

