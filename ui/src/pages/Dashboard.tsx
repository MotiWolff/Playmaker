import React, { useState, useEffect } from 'react';
import { MatchPrediction, Stats, League } from '../types';
import apiService from '../services/api';
import { Calendar, Target, TrendingUp, BarChart3, Clock, Trophy, Globe } from 'lucide-react';

const Dashboard: React.FC = () => {
  const [predictions, setPredictions] = useState<MatchPrediction[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [leagues, setLeagues] = useState<Record<string, League>>({});
  const [selectedLeague, setSelectedLeague] = useState<string>('PL');
  const [loading, setLoading] = useState(true);
  const [selectedMatchday, setSelectedMatchday] = useState<number>(1);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadPredictions();
  }, [selectedLeague]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsData, leaguesData] = await Promise.all([
        apiService.getStats(selectedLeague),
        apiService.getLeagues()
      ]);
      setStats(statsData);
      setLeagues(leaguesData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPredictions = async () => {
    try {
      setLoading(true);
      const [predictionsData, statsData] = await Promise.all([
        apiService.getPredictions(selectedLeague),
        apiService.getStats(selectedLeague)
      ]);
      setPredictions(predictionsData);
      setStats(statsData);
    } catch (error) {
      console.error('Error loading predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMatchdayPredictions = () => {
    return predictions.filter(p => p.matchday === selectedMatchday);
  };

  const getBettingValueColor = (value: string) => {
    switch (value) {
      case 'HIGH': return 'text-green-600 bg-green-100';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-100';
      case 'LOW': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getPredictionColor = (prediction: string) => {
    switch (prediction) {
      case 'HOME WIN': return 'text-blue-600 bg-blue-100';
      case 'AWAY WIN': return 'text-purple-600 bg-purple-100';
      case 'DRAW': return 'text-orange-600 bg-orange-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const matchdays = Array.from(new Set(predictions.map(p => p.matchday))).sort();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Playmaker predictions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center space-x-3 mb-4">
          <Trophy className="w-10 h-10 text-primary-600" />
          <h1 className="text-4xl font-bold text-gray-900">Playmaker</h1>
        </div>
        <p className="text-xl text-gray-600">
          Professional Football Predictions & Fixtures
        </p>
        <p className="text-sm text-gray-500 mt-2">
          {leagues[selectedLeague]?.name || 'Premier League'} • Based on Dixon & Coles methodology • 51-65% accuracy target
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center space-x-3">
              <Target className="w-8 h-8 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Confident Predictions</p>
                <p className="text-2xl font-bold text-gray-900">{stats.confident_predictions}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center space-x-3">
              <TrendingUp className="w-8 h-8 text-green-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">High Value Bets</p>
                <p className="text-2xl font-bold text-gray-900">{stats.high_value_bets}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center space-x-3">
              <BarChart3 className="w-8 h-8 text-purple-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Average Confidence</p>
                <p className="text-2xl font-bold text-gray-900">{(stats.average_confidence * 100).toFixed(1)}%</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center space-x-3">
              <Calendar className="w-8 h-8 text-orange-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Total Fixtures</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_fixtures}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* League and Matchday Selector */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* League Selector */}
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <Globe className="w-5 h-5 mr-2" />
              Select League
            </h2>
            <div className="flex flex-wrap gap-2">
              {Object.entries(leagues).map(([code, league]) => (
                <button
                  key={code}
                  onClick={() => setSelectedLeague(code)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedLeague === code
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {league.name}
                </button>
              ))}
            </div>
          </div>

          {/* Matchday Selector */}
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <Calendar className="w-5 h-5 mr-2" />
              Select Matchday
            </h2>
            <div className="flex flex-wrap gap-2">
              {matchdays.map((matchday) => (
                <button
                  key={matchday}
                  onClick={() => setSelectedMatchday(matchday)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedMatchday === matchday
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Matchday {matchday}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Fixtures */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Matchday {selectedMatchday} Fixtures
        </h2>
        
        {getMatchdayPredictions().length === 0 ? (
          <div className="text-center py-12">
            <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">
              {selectedLeague === 'PL' 
                ? 'No fixtures available for this matchday' 
                : `${leagues[selectedLeague]?.name || 'This league'} predictions coming soon! Currently only Premier League predictions are available.`
              }
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {getMatchdayPredictions().map((match) => (
              <div key={match.match_id} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
                {/* Match Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">{match.match_time}</span>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getBettingValueColor(match.betting_value)}`}>
                    {match.betting_value} VALUE
                  </span>
                </div>

                {/* Teams */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <img 
                      src={match.home_team_logo} 
                      alt={match.home_team_short}
                      className="w-12 h-12 object-contain"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/48px-Association_football.svg.png';
                      }}
                    />
                    <div>
                      <p className="font-semibold text-gray-900">{match.home_team_short}</p>
                      <p className="text-sm text-gray-500">Home</p>
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-400">VS</p>
                    <p className="text-xs text-gray-500">Odds: {match.fair_odds.toFixed(2)}</p>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">{match.away_team_short}</p>
                      <p className="text-sm text-gray-500">Away</p>
                    </div>
                    <img 
                      src={match.away_team_logo} 
                      alt={match.away_team_short}
                      className="w-12 h-12 object-contain"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/48px-Association_football.svg.png';
                      }}
                    />
                  </div>
                </div>

                {/* Prediction */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPredictionColor(match.prediction)}`}>
                      {match.prediction}
                    </span>
                    <span className="text-sm font-semibold text-gray-700">
                      {(match.confidence * 100).toFixed(1)}% confidence
                    </span>
                  </div>
                  
                  {/* Probability Bars */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Home Win</span>
                      <span className="font-medium">{(match.home_prob * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${match.home_prob * 100}%` }}
                      ></div>
                    </div>
                    
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Draw</span>
                      <span className="font-medium">{(match.draw_prob * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${match.draw_prob * 100}%` }}
                      ></div>
                    </div>
                    
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Away Win</span>
                      <span className="font-medium">{(match.away_prob * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${match.away_prob * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;