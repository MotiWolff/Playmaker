import React from 'react';
import { Link } from 'react-router-dom';
import { Trophy, Home, BarChart3, Target, Users, HelpCircle, Info } from 'lucide-react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  const footerLinks = [
    { path: '/about', label: 'About', icon: Info },
    { path: '/faq', label: 'FAQ', icon: HelpCircle },
  ];

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <p className="text-sm text-gray-600 mb-0">© {currentYear} Playmaker, Inc</p>

          <Link
            to="/"
            className="flex items-center justify-center space-x-2 text-gray-700 hover:text-primary-600 transition-colors"
            aria-label="Playmaker"
          >
            <Trophy className="w-8 h-8 text-primary-600" />
            <span className="text-lg font-bold">Playmaker</span>
          </Link>

          <ul className="flex flex-wrap justify-center md:justify-end space-x-6">
            {footerLinks.map(({ path, label, icon: Icon }) => (
              <li key={path}>
                <Link
                  to={path}
                  className="flex items-center space-x-1 text-sm text-gray-600 hover:text-primary-600 transition-colors"
                >
                  <Icon className="w-4 h-4" />
                  <span>{label}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </footer>
  );
};

export default Footer;


