import React from 'react';
import { AlertTriangle, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const ScanResults = ({ result }) => {
  const navigate = useNavigate();

  const getSafetyIcon = (level) => {
    switch (level) {
      case 'HIGH_RISK':
        return <AlertTriangle className="risk-icon high-risk" />;
      case 'MODERATE_RISK':
        return <AlertCircle className="risk-icon moderate-risk" />;
      case 'LOW_RISK':
        return <Info className="risk-icon low-risk" />;
      case 'GOOD_TO_GO':
        return <CheckCircle className="risk-icon good-to-go" />;
      default:
        return <Info className="risk-icon" />;
    }
  };

  const getSafetyColor = (level) => {
    switch (level) {
      case 'HIGH_RISK': return '#dc3545';
      case 'MODERATE_RISK': return '#fd7e14';
      case 'LOW_RISK': return '#20c997';
      case 'GOOD_TO_GO': return '#28a745';
      default: return '#6c757d';
    }
  };

  const handleViewDetails = () => {
    navigate(`/analysis/${result.id}`);
  };

  return (
    <div className="scan-results">
      <div className="result-header">
        <div className="product-info">
          <h3>{result.product.name}</h3>
          <p className="brand">{result.product.brand}</p>
        </div>
        {result.product.product_image && (
          <img 
            src={result.product.product_image} 
            alt={result.product.name}
            className="product-image"
          />
        )}
      </div>

      <div className="safety-assessment">
        <div className="safety-level" style={{ borderColor: getSafetyColor(result.safety_level) }}>
          {getSafetyIcon(result.safety_level)}
          <div className="safety-info">
            <h4>{result.safety_level.replace('_', ' ')}</h4>
            <div className="risk-score">
              Risk Score: {result.risk_score}/100
            </div>
          </div>
        </div>
      </div>

      {result.specific_concerns && result.specific_concerns.length > 0 && (
        <div className="concerns-section">
          <h4>⚠️ Specific Concerns</h4>
          <ul>
            {result.specific_concerns.map((concern, index) => (
              <li key={index}>{concern}</li>
            ))}
          </ul>
        </div>
      )}

      {result.health_benefits && result.health_benefits.length > 0 && (
        <div className="benefits-section">
          <h4>✅ Health Benefits</h4>
          <ul>
            {result.health_benefits.map((benefit, index) => (
              <li key={index}>{benefit}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="action-buttons">
        <button 
          className="view-details-btn"
          onClick={handleViewDetails}
        >
          View Detailed Analysis
        </button>
        <button 
          className="new-scan-btn"
          onClick={() => window.location.reload()}
        >
          Scan Another Product
        </button>
      </div>
    </div>
  );
};

export default ScanResults;
