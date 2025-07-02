import React, { useState, useRef, useCallback } from 'react';
import { Camera, Scan, Upload, Zap } from 'lucide-react';
import BarcodeScanner from '../components/Scanner/BarcodeScanner';
import ImageUpload from '../components/Scanner/ImageUpload';
import ScanResults from '../components/Scanner/ScanResults';
import { scannerService } from '../services/scannerService';
import { useToast } from '../contexts/ToastContext';

const Scanner = () => {
  const [activeTab, setActiveTab] = useState('barcode');
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const handleBarcodeScan = async (barcode) => {
    setLoading(true);
    try {
      const result = await scannerService.scanBarcode(barcode);
      setScanResult(result);
      showToast('Product scanned successfully!', 'success');
    } catch (error) {
      showToast('Failed to scan product. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleImageScan = async (imageFile, scanType) => {
    setLoading(true);
    try {
      const result = await scannerService.scanImage(imageFile, scanType);
      setScanResult(result);
      showToast('Image processed successfully!', 'success');
    } catch (error) {
      showToast('Failed to process image. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scanner-container">
      <div className="scanner-header">
        <h1 className="page-title">
          <Scan className="icon" />
          Product Scanner
        </h1>
        <p className="page-description">
          Scan products to get personalized health insights
        </p>
      </div>

      <div className="scanner-tabs">
        <button
          className={`tab ${activeTab === 'barcode' ? 'active' : ''}`}
          onClick={() => setActiveTab('barcode')}
        >
          <Scan className="tab-icon" />
          Barcode
        </button>
        <button
          className={`tab ${activeTab === 'ingredients' ? 'active' : ''}`}
          onClick={() => setActiveTab('ingredients')}
        >
          <Camera className="tab-icon" />
          Ingredients
        </button>
        <button
          className={`tab ${activeTab === 'nutrition' ? 'active' : ''}`}
          onClick={() => setActiveTab('nutrition')}
        >
          <Zap className="tab-icon" />
          Nutrition
        </button>
        <button
          className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          <Upload className="tab-icon" />
          Upload
        </button>
      </div>

      <div className="scanner-content">
        {activeTab === 'barcode' && (
          <BarcodeScanner
            onScan={handleBarcodeScan}
            loading={loading}
          />
        )}
        
        {activeTab === 'ingredients' && (
          <ImageUpload
            scanType="ingredients"
            onScan={handleImageScan}
            loading={loading}
            title="Scan Ingredients List"
            description="Take a photo of the ingredients list on the product"
          />
        )}
        
        {activeTab === 'nutrition' && (
          <ImageUpload
            scanType="nutrition"
            onScan={handleImageScan}
            loading={loading}
            title="Scan Nutrition Facts"
            description="Take a photo of the nutrition facts table"
          />
        )}
        
        {activeTab === 'upload' && (
          <ImageUpload
            scanType="general"
            onScan={handleImageScan}
            loading={loading}
            title="Upload Product Image"
            description="Upload any product image for analysis"
            allowUpload={true}
          />
        )}
      </div>

      {scanResult && (
        <ScanResults result={scanResult} />
      )}
    </div>
  );
};

export default Scanner;
