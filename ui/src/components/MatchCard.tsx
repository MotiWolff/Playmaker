import React from 'react';
import { MatchPrediction, PredictionOutcome } from '../types';
import { TrendingUp, Calendar, Users } from 'lucide-react';

interface MatchCardProps {
  prediction: MatchPrediction;
  className?: string;
}

const MatchCard: React.FC<MatchCardProps> = ({ prediction, className = '' }) => {
  const { home_team, away_team, predictions, confidence, match_date, elo_home, elo_away } = prediction;

  // Determine the most likely outcome
  const mostLikely: PredictionOutcome = 
    predictions.home > predictions.draw && predictions.home > predictions.away ? 'home' :
    predictions.away > predictions.draw && predictions.away > predictions.home ? 'away' : 'draw';

  const getPredictionColor = (outcome: PredictionOutcome) => {
    switch (outcome) {
      case 'home': return 'text-blue-600 bg-blue-50';
      case 'draw': return 'text-gray-600 bg-gray-50';
      case 'away': return 'text-red-600 bg-red-50';
    }
  };

  const getConfidenceColor = () => {
    if (confidence >= 0.6) return 'text-green-600 bg-green-50';
    if (confidence >= 0.4) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`bg-white rounded-xl shadow-lg p-6 card-hover ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Calendar className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600">{formatDate(match_date)}</span>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-semibold ${getConfidenceColor()}`}>
          {(confidence * 100).toFixed(0)}% confidence
        </div>
      </div>

      {/* Teams */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex-1">
            <div className="text-lg font-semibold text-gray-900">{home_team}</div>
            <div className="text-sm text-gray-500">ELO: {elo_home.toFixed(0)}</div>
          </div>
          <div className="px-4 py-2 bg-gray-100 rounded-lg">
            <Users className="w-5 h-5 text-gray-600" />
          </div>
          <div className="flex-1 text-right">
            <div className="text-lg font-semibold text-gray-900">{away_team}</div>
            <div className="text-sm text-gray-500">ELO: {elo_away.toFixed(0)}</div>
          </div>
        </div>
      </div>

      {/* Predictions */}
      <div className="space-y-3 mb-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Home Win</span>
          <div className="flex items-center space-x-2">
            <div className="w-24 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${predictions.home * 100}%` }}
              />
            </div>
            <span className="text-sm font-semibold text-gray-900 w-12 text-right">
              {(predictions.home * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Draw</span>
          <div className="flex items-center space-x-2">
            <div className="w-24 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gray-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${predictions.draw * 100}%` }}
              />
            </div>
            <span className="text-sm font-semibold text-gray-900 w-12 text-right">
              {(predictions.draw * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Away Win</span>
          <div className="flex items-center space-x-2">
            <div className="w-24 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-red-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${predictions.away * 100}%` }}
              />
            </div>
            <span className="text-sm font-semibold text-gray-900 w-12 text-right">
              {(predictions.away * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Prediction Summary */}
      <div className={`px-3 py-2 rounded-lg text-center ${getPredictionColor(mostLikely)}`}>
        <div className="flex items-center justify-center space-x-1">
          <TrendingUp className="w-4 h-4" />
          <span className="text-sm font-semibold">
            Most likely: {
              mostLikely === 'home' ? `${home_team} Win` :
              mostLikely === 'away' ? `${away_team} Win` : 'Draw'
            }
          </span>
        </div>
      </div>
    </div>
  );
};

export default MatchCard;