const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ScannerService {
  async scanBarcode(barcode) {
    const response = await fetch(`${API_BASE_URL}/scan/barcode/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ barcode })
    });

    if (!response.ok) {
      throw new Error('Barcode scan failed');
    }

    return response.json();
  }

  async scanImage(imageFile, scanType) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('scan_type', scanType);

    const response = await fetch(`${API_BASE_URL}/scan/image/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error('Image scan failed');
    }

    return response.json();
  }

  async getAnalysis(scanId) {
    const response = await fetch(`${API_BASE_URL}/scan/analysis/${scanId}/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch analysis');
    }

    return response.json();
  }

  async getScanHistory() {
    const response = await fetch(`${API_BASE_URL}/scan/history/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch scan history');
    }

    return response.json();
  }
}

export const scannerService = new ScannerService();
