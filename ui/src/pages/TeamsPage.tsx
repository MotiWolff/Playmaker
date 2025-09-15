import React, { useState, useEffect } from 'react';
import { Team, League } from '../types';
import apiService from '../services/api';
import { Users, Search, Trophy, Globe } from 'lucide-react';

const TeamsPage: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [filteredTeams, setFilteredTeams] = useState<Team[]>([]);
  const [leagues, setLeagues] = useState<Record<string, League>>({});
  const [selectedLeague, setSelectedLeague] = useState<string>('PL');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadTeams();
  }, [selectedLeague]);

  useEffect(() => {
    const filtered = teams.filter(team =>
      team.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      team.short_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredTeams(filtered);
  }, [teams, searchTerm]);

  const loadData = async () => {
    try {
      const leaguesData = await apiService.getLeagues();
      setLeagues(leaguesData);
    } catch (error) {
      console.error('Error loading leagues:', error);
    }
  };

  const loadTeams = async () => {
    try {
      setLoading(true);
      const data = await apiService.getTeams(selectedLeague);
      setTeams(data);
      setFilteredTeams(data);
    } catch (error) {
      console.error('Error loading teams:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading teams...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center space-x-2 mb-4">
          <Users className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900">Premier League Teams</h1>
        </div>
        <p className="text-lg text-gray-600">
          {leagues[selectedLeague]?.name || 'Premier League'} teams with logos and information
        </p>
      </div>

      {/* League Selector and Search */}
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

          {/* Search */}
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <Search className="w-5 h-5 mr-2" />
              Search Teams
            </h2>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search teams..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Teams Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredTeams.map((team) => (
          <div key={team.id} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <img 
                  src={team.logo_url} 
                  alt={team.short_name}
                  className="w-16 h-16 object-contain"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/64px-Association_football.svg.png';
                  }}
                />
              </div>
              
              <h3 className="text-lg font-bold text-gray-900 mb-1">{team.short_name}</h3>
              <p className="text-sm text-gray-600 mb-4">{team.name}</p>
              
              <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
                <Trophy className="w-4 h-4" />
                <span>Premier League</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredTeams.length === 0 && (
        <div className="text-center py-12">
          <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No teams found matching your search</p>
        </div>
      )}

      {/* Stats */}
      <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-6">
        <div className="text-center">
          <h2 className="text-xl font-bold text-gray-900 mb-2">Premier League Overview</h2>
          <p className="text-gray-600 mb-4">
            {teams.length} teams competing in the world's most competitive football league
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white rounded-lg p-4">
              <p className="font-semibold text-gray-900">Total Teams</p>
              <p className="text-2xl font-bold text-primary-600">{teams.length}</p>
            </div>
            <div className="bg-white rounded-lg p-4">
              <p className="font-semibold text-gray-900">Seasons</p>
              <p className="text-2xl font-bold text-primary-600">32+</p>
            </div>
            <div className="bg-white rounded-lg p-4">
              <p className="font-semibold text-gray-900">Matches/Season</p>
              <p className="text-2xl font-bold text-primary-600">380</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamsPage;