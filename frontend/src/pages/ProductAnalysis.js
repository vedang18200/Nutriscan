import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { AlertTriangle, CheckCircle, Clock, Zap, Heart, Shield } from 'lucide-react';
import { scannerService } from '../services/scannerService';

const ProductAnalysis = () => {
  const { scanId } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadAnalysis();
  }, [scanId]);

  const loadAnalysis = async () => {
    try {
      const data = await scannerService.getAnalysis(scanId);
      setAnalysis(data);
    } catch (error) {
      console.error('Failed to load analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading-container">Loading analysis...</div>;
  }

  if (!analysis) {
    return <div className="error-container">Analysis not found</div>;
  }

  return (
    <div className="product-analysis">
      <div className="analysis-header">
        <div className="product-overview">
          <div className="product-image-container">
            {analysis.product.product_image && (
              <img 
                src={analysis.product.product_image} 
                alt={analysis.product.name}
                className="product-image-large"
              />
            )}
          </div>
          <div className="product-details">
            <h1>{analysis.product.name}</h1>
            <p className="brand">{analysis.product.brand}</p>
            <div className={`safety-badge ${analysis.safety_level.toLowerCase()}`}>
              {analysis.safety_level.replace('_', ' ')}
            </div>
            <div className="risk-score-display">
              Risk Score: <span className="score">{analysis.risk_score}/100</span>
            </div>
          </div>
        </div>
      </div>

      <div className="analysis-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Shield className="tab-icon" />
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'health' ? 'active' : ''}`}
          onClick={() => setActiveTab('health')}
        >
          <Heart className="tab-icon" />
          Health Impact
        </button>
        <button
          className={`tab ${activeTab === 'longterm' ? 'active' : ''}`}
          onClick={() => setActiveTab('longterm')}
        >
          <Clock className="tab-icon" />
          Long-term Effects
        </button>
        <button
          className={`tab ${activeTab === 'ingredients' ? 'active' : ''}`}
          onClick={() => setActiveTab('ingredients')}
        >
          <Zap className="tab-icon" />
          Ingredients
        </button>
      </div>

      <div className="analysis-content">
        {activeTab === 'overview' && (
          <OverviewTab analysis={analysis} />
        )}
        {activeTab === 'health' && (
          <HealthImpactTab analysis={analysis} />
        )}
        {activeTab === 'longterm' && (
          <LongTermTab analysis={analysis} />
        )}
        {activeTab === 'ingredients' && (
          <IngredientsTab analysis={analysis} />
        )}
      </div>
    </div>
  );
};

const OverviewTab = ({ analysis }) => (
  <div className="overview-tab">
    {analysis.specific_concerns && analysis.specific_concerns.length > 0 && (
      <div className="section">
        <h3><AlertTriangle className="section-icon" /> Specific Concerns</h3>
        <ul className="concern-list">
          {analysis.specific_concerns.map((concern, index) => (
            <li key={index} className="concern-item">{concern}</li>
          ))}
        </ul>
      </div>
    )}

    {analysis.health_benefits && analysis.health_benefits.length > 0 && (
      <div className="section">
        <h3><CheckCircle className="section-icon" /> Health Benefits</h3>
        <ul className="benefit-list">
          {analysis.health_benefits.map((benefit, index) => (
            <li key={index} className="benefit-item">{benefit}</li>
          ))}
        </ul>
      </div>
    )}

    {analysis.recommendations && analysis.recommendations.length > 0 && (
      <div className="section">
        <h3>💡 Recommendations</h3>
        <ul className="recommendation-list">
          {analysis.recommendations.map((rec, index) => (
            <li key={index} className="recommendation-item">{rec}</li>
          ))}
        </ul>
      </div>
    )}

    {analysis.alternatives && analysis.alternatives.length > 0 && (
      <div className="section">
        <h3>🔄 Better Alternatives</h3>
        <div className="alternatives-grid">
          {analysis.alternatives.map((alt, index) => (
            <div key={index} className="alternative-card">
              <h4>{alt.name}</h4>
              <p>{alt.reason}</p>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
);

const HealthImpactTab = ({ analysis }) => (
  <div className="health-impact-tab">
    {analysis.health_impact && (
      <div className="health-impact-sections">
        {analysis.health_impact.immediate && (
          <div className="section">
            <h3>⚡ Immediate Effects</h3>
            <ul>
              {analysis.health_impact.immediate.map((effect, index) => (
                <li key={index}>{effect}</li>
              ))}
            </ul>
          </div>
        )}

        {analysis.health_impact.short_term && (
          <div className="section">
            <h3>📅 Short-term Effects (Days to Weeks)</h3>
            <ul>
              {analysis.health_impact.short_term.map((effect, index) => (
                <li key={index}>{effect}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )}

    {analysis.harmful_additives && analysis.harmful_additives.length > 0 && (
      <div className="section">
        <h3>⚠️ Harmful Additives Detected</h3>
        <div className="additives-grid">
          {analysis.harmful_additives.map((additive, index) => (
            <div key={index} className="additive-card warning">
              <h4>{additive.name}</h4>
              <p className="e-number">{additive.e_number}</p>
              <p>{additive.concern}</p>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
);

const LongTermTab = ({ analysis }) => (
  <div className="longterm-tab">
    {analysis.health_impact && analysis.health_impact.long_term && (
      <div className="section">
        <h3>📈 Long-term Health Effects</h3>
        <div className="longterm-effects">
          {analysis.health_impact.long_term.map((effect, index) => (
            <div key={index} className="effect-card">
              <h4>{effect.category}</h4>
              <p>{effect.description}</p>
              <div className="risk-timeline">
                <span className="timeline-label">Risk Timeline:</span>
                <span className="timeline-value">{effect.timeline}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    )}

    {analysis.preservative_concerns && analysis.preservative_concerns.length > 0 && (
      <div className="section">
        <h3>🧪 Preservative Concerns</h3>
        <div className="preservative-list">
          {analysis.preservative_concerns.map((concern, index) => (
            <div key={index} className="preservative-item">
              <h4>{concern.name}</h4>
              <p>{concern.long_term_effect}</p>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
);

const IngredientsTab = ({ analysis }) => (
  <div className="ingredients-tab">
    <div className="section">
      <h3>🥘 Full Ingredients List</h3>
      <div className="ingredients-breakdown">
        {analysis.product.ingredients.map((ingredient, index) => (
          <div key={index} className="ingredient-item">
            <span className="ingredient-name">{ingredient.name}</span>
            {ingredient.category && (
              <span className="ingredient-category">{ingredient.category}</span>
            )}
            {ingredient.concern_level && (
              <span className={`concern-level ${ingredient.concern_level}`}>
                {ingredient.concern_level}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>

    <div className="nutrition-facts">
      <h3>📊 Nutrition Facts (per 100g)</h3>
      <div className="nutrition-grid">
        {Object.entries(analysis.product.nutrition_facts).map(([key, value]) => (
          <div key={key} className="nutrition-item">
            <span className="nutrient-name">{key.replace('_', ' ').toUpperCase()}</span>
            <span className="nutrient-value">{value}</span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default ProductAnalysis;