import React, { useState, useEffect } from 'react';
import { Stats } from '../types';
import apiService from '../services/api';
import { BarChart3, TrendingUp, Target, Calendar, Trophy } from 'lucide-react';

const AnalyticsPage: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await apiService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No analytics data available</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center space-x-2 mb-4">
          <BarChart3 className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        </div>
        <p className="text-lg text-gray-600">
          Model performance and prediction insights
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center space-x-3">
            <Target className="w-8 h-8 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Total Fixtures</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_fixtures}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center space-x-3">
            <TrendingUp className="w-8 h-8 text-green-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Confident Predictions</p>
              <p className="text-2xl font-bold text-gray-900">{stats.confident_predictions}</p>
              <p className="text-xs text-gray-500">
                {((stats.confident_predictions / stats.total_fixtures) * 100).toFixed(1)}% of total
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center space-x-3">
            <Trophy className="w-8 h-8 text-yellow-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">High Value Bets</p>
              <p className="text-2xl font-bold text-gray-900">{stats.high_value_bets}</p>
              <p className="text-xs text-gray-500">
                {((stats.high_value_bets / stats.confident_predictions) * 100).toFixed(1)}% of confident
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center space-x-3">
            <BarChart3 className="w-8 h-8 text-purple-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Confidence</p>
              <p className="text-2xl font-bold text-gray-900">{(stats.average_confidence * 100).toFixed(1)}%</p>
              <p className="text-xs text-gray-500">Target: 51-65%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Prediction Distribution */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Prediction Distribution</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-24 h-24 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-blue-600">{stats.home_wins}</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Home Wins</h3>
            <p className="text-sm text-gray-600">
              {((stats.home_wins / stats.confident_predictions) * 100).toFixed(1)}% of confident predictions
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-24 h-24 mx-auto mb-4 bg-orange-100 rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-orange-600">{stats.draws}</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Draws</h3>
            <p className="text-sm text-gray-600">
              {((stats.draws / stats.confident_predictions) * 100).toFixed(1)}% of confident predictions
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-24 h-24 mx-auto mb-4 bg-purple-100 rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-purple-600">{stats.away_wins}</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Away Wins</h3>
            <p className="text-sm text-gray-600">
              {((stats.away_wins / stats.confident_predictions) * 100).toFixed(1)}% of confident predictions
            </p>
          </div>
        </div>
      </div>

      {/* Betting Value Analysis */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Betting Value Analysis</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Value Distribution</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">High Value</span>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${(stats.high_value_bets / stats.confident_predictions) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-bold text-gray-900">{stats.high_value_bets}</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Medium Value</span>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-yellow-500 h-2 rounded-full"
                      style={{ width: `${(stats.medium_value_bets / stats.confident_predictions) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-bold text-gray-900">{stats.medium_value_bets}</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Low Value</span>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-red-500 h-2 rounded-full"
                      style={{ width: `${((stats.confident_predictions - stats.high_value_bets - stats.medium_value_bets) / stats.confident_predictions) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-bold text-gray-900">
                    {stats.confident_predictions - stats.high_value_bets - stats.medium_value_bets}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Performance</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-600">Confidence Threshold</span>
                <span className="text-sm font-bold text-gray-900">≥45%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-600">Accuracy Target</span>
                <span className="text-sm font-bold text-gray-900">51-65%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-600">Methodology</span>
                <span className="text-sm font-bold text-gray-900">Dixon & Coles</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-600">Research Based</span>
                <span className="text-sm font-bold text-green-600">✓ Penaltyblog</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Model Information */}
      <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">About Playmaker</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Key Features</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Dixon & Coles goals model implementation</li>
              <li>• Time-weighted data with exponential decay</li>
              <li>• Realistic 51-65% accuracy targets</li>
              <li>• Betting value assessment (HIGH/MEDIUM/LOW)</li>
              <li>• Fair odds calculation</li>
              <li>• Professional team logos and fixtures</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Research Foundation</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Based on penaltyblog research</li>
              <li>• Optimal parameters: 4 seasons, ξ=0.001</li>
              <li>• RPS evaluation metric</li>
              <li>• Low-score bias correction</li>
              <li>• Home advantage modeling</li>
              <li>• Real Premier League API integration</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;