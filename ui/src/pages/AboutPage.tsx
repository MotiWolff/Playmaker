import React from 'react';
import { Target, BarChart3, Users, Trophy } from 'lucide-react';

const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center mb-8">
          <Trophy className="w-16 h-16 text-primary-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 mb-4">About Playmaker</h1>
          <p className="text-lg text-gray-600">
            Advanced football analytics and prediction platform powered by machine learning
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-8">
          <div className="space-y-6">
            <div className="flex items-start space-x-4">
              <Target className="w-6 h-6 text-primary-600 mt-1" />
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Predictions</h3>
                <p className="text-gray-600">
                  Get accurate match predictions using advanced ML models trained on historical data
                  from major European leagues.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <BarChart3 className="w-6 h-6 text-primary-600 mt-1" />
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Analytics</h3>
                <p className="text-gray-600">
                  Deep dive into team performance metrics, player statistics, and league standings
                  with interactive visualizations.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <Users className="w-6 h-6 text-primary-600 mt-1" />
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Team Insights</h3>
                <p className="text-gray-600">
                  Comprehensive team profiles with current form, head-to-head records, and
                  tactical analysis.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Our Mission</h3>
            <p className="text-gray-600 mb-4">
              To revolutionize football analysis by providing data-driven insights that help fans,
              analysts, and professionals understand the beautiful game at a deeper level.
            </p>
            <h4 className="text-lg font-semibold text-gray-900 mb-2">Data Sources</h4>
            <ul className="text-gray-600 space-y-1">
              <li>• Football-Data.org API</li>
              <li>• Real-time match data</li>
              <li>• Historical performance metrics</li>
              <li>• League standings and fixtures</li>
            </ul>
          </div>
        </div>

        <div className="border-t pt-8">
          <h3 className="text-2xl font-semibold text-gray-900 mb-4">Technology Stack</h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="bg-primary-100 rounded-lg p-4 mb-3">
                <span className="text-2xl font-bold text-primary-600">ML</span>
              </div>
              <h4 className="font-semibold text-gray-900">Machine Learning</h4>
              <p className="text-sm text-gray-600">Advanced prediction models</p>
            </div>
            <div className="text-center">
              <div className="bg-primary-100 rounded-lg p-4 mb-3">
                <span className="text-2xl font-bold text-primary-600">API</span>
              </div>
              <h4 className="font-semibold text-gray-900">Real-time Data</h4>
              <p className="text-sm text-gray-600">Live football statistics</p>
            </div>
            <div className="text-center">
              <div className="bg-primary-100 rounded-lg p-4 mb-3">
                <span className="text-2xl font-bold text-primary-600">UI</span>
              </div>
              <h4 className="font-semibold text-gray-900">Modern Interface</h4>
              <p className="text-sm text-gray-600">Intuitive user experience</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;


