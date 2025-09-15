import React, { useState, useEffect } from 'react';
import { MatchPrediction, Team, League } from '../types';
import apiService from '../services/api';
import { Target, Loader2, Calendar, Clock, Globe } from 'lucide-react';

const PredictPage: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [leagues, setLeagues] = useState<Record<string, League>>({});
  const [selectedLeague, setSelectedLeague] = useState<string>('PL');
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [prediction, setPrediction] = useState<MatchPrediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadTeams();
  }, [selectedLeague]);

  const loadData = async () => {
    try {
      const leaguesData = await apiService.getLeagues();
      setLeagues(leaguesData);
    } catch (err) {
      console.error('Error loading leagues:', err);
    }
  };

  const loadTeams = async () => {
    try {
      const data = await apiService.getTeams(selectedLeague);
      setTeams(data);
      // Reset team selections when league changes
      setHomeTeam('');
      setAwayTeam('');
      setPrediction(null);
    } catch (err) {
      console.error('Error loading teams:', err);
    }
  };

  const handlePredict = async () => {
    if (!homeTeam || !awayTeam) {
      setError('Please select both teams');
      return;
    }

    if (homeTeam === awayTeam) {
      setError('Please select different teams');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await apiService.predictMatch(homeTeam, awayTeam);
      setPrediction(result);
    } catch (err) {
      setError('Failed to generate prediction. Please try again.');
      console.error('Error predicting match:', err);
    } finally {
      setLoading(false);
    }
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

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center space-x-2 mb-4">
          <Target className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900">Custom Match Predictor</h1>
        </div>
        <p className="text-lg text-gray-600">
          Select two teams to generate an AI-powered match prediction
        </p>
      </div>

      {/* League Selector */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
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

      {/* Prediction Form */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Home Team */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Home Team
            </label>
            <select
              value={homeTeam}
              onChange={(e) => setHomeTeam(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Select home team...</option>
              {teams.map((team) => (
                <option key={team.id} value={team.name}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>

          {/* Away Team */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Away Team
            </label>
            <select
              value={awayTeam}
              onChange={(e) => setAwayTeam(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Select away team...</option>
              {teams.map((team) => (
                <option key={team.id} value={team.name}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Predict Button */}
        <button
          onClick={handlePredict}
          disabled={loading || !homeTeam || !awayTeam}
          className="w-full py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Generating Prediction...</span>
            </>
          ) : (
            <>
              <Target className="w-4 h-4" />
              <span>Predict Match</span>
            </>
          )}
        </button>
      </div>

      {/* Prediction Result */}
      {prediction && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-gray-900 text-center">
            Prediction Result
          </h2>
          
          <div className="bg-white rounded-xl shadow-lg p-6">
            {/* Match Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600">Custom Match</span>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getBettingValueColor(prediction.betting_value)}`}>
                {prediction.betting_value} VALUE
              </span>
            </div>

            {/* Teams */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <img 
                  src={prediction.home_team_logo} 
                  alt={prediction.home_team_short}
                  className="w-16 h-16 object-contain"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/64px-Association_football.svg.png';
                      }}
                />
                <div>
                  <p className="text-xl font-bold text-gray-900">{prediction.home_team_short}</p>
                  <p className="text-sm text-gray-500">Home</p>
                </div>
              </div>
              
              <div className="text-center">
                <p className="text-3xl font-bold text-gray-400">VS</p>
                <p className="text-sm text-gray-500">Fair Odds: {prediction.fair_odds.toFixed(2)}</p>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <p className="text-xl font-bold text-gray-900">{prediction.away_team_short}</p>
                  <p className="text-sm text-gray-500">Away</p>
                </div>
                <img 
                  src={prediction.away_team_logo} 
                  alt={prediction.away_team_short}
                  className="w-16 h-16 object-contain"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/64px-Association_football.svg.png';
                      }}
                />
              </div>
            </div>

            {/* Prediction */}
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <span className={`px-4 py-2 rounded-full text-lg font-medium ${getPredictionColor(prediction.prediction)}`}>
                  {prediction.prediction}
                </span>
                <span className="text-lg font-bold text-gray-700">
                  {(prediction.confidence * 100).toFixed(1)}% confidence
                </span>
              </div>
              
              {/* Probability Bars */}
              <div className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 font-medium">Home Win</span>
                  <span className="font-bold">{(prediction.home_prob * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-blue-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${prediction.home_prob * 100}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 font-medium">Draw</span>
                  <span className="font-bold">{(prediction.draw_prob * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-orange-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${prediction.draw_prob * 100}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 font-medium">Away Win</span>
                  <span className="font-bold">{(prediction.away_prob * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-purple-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${prediction.away_prob * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictPage;