import React, { useEffect, useRef, useState } from 'react';
import Quagga from 'quagga';
import { Scan, X } from 'lucide-react';

const BarcodeScanner = ({ onScan, loading }) => {
  const scannerRef = useRef(null);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState(null);

  const startScanner = () => {
    setError(null);
    setIsScanning(true);
    
    Quagga.init({
      inputStream: {
        name: "Live",
        type: "LiveStream",
        target: scannerRef.current,
        constraints: {
          width: 640,
          height: 480,
          facingMode: "environment"
        }
      },
      decoder: {
        readers: [
          "code_128_reader",
          "ean_reader",
          "ean_8_reader",
          "code_39_reader"
        ]
      }
    }, (err) => {
      if (err) {
        setError('Camera access denied or not available');
        setIsScanning(false);
        return;
      }
      Quagga.start();
    });

    Quagga.onDetected((result) => {
      const code = result.codeResult.code;
      if (code && code.length >= 8) {
        stopScanner();
        onScan(code);
      }
    });
  };

  const stopScanner = () => {
    if (isScanning) {
      Quagga.stop();
      setIsScanning(false);
    }
  };

  useEffect(() => {
    return () => {
      stopScanner();
    };
  }, []);

  return (
    <div className="barcode-scanner">
      {!isScanning && !loading && (
        <div className="scanner-placeholder">
          <Scan className="scanner-icon" size={64} />
          <h3>Ready to Scan</h3>
          <p>Position the barcode within the camera frame</p>
          <button 
            className="start-scan-btn"
            onClick={startScanner}
          >
            Start Scanning
          </button>
        </div>
      )}

      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={() => setError(null)}>Try Again</button>
        </div>
      )}

      {isScanning && (
        <div className="scanner-active">
          <div className="scanner-controls">
            <button 
              className="stop-scan-btn"
              onClick={stopScanner}
            >
              <X size={20} />
              Stop Scanning
            </button>
          </div>
          <div ref={scannerRef} className="scanner-viewport" />
          <div className="scanner-overlay">
            <div className="scanner-frame"></div>
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Analyzing product...</p>
        </div>
      )}
    </div>
  );
};

export default BarcodeScanner;