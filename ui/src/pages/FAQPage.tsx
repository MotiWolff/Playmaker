import React, { useState } from 'react';
import { ChevronDown, ChevronUp, HelpCircle } from 'lucide-react';

const FAQPage: React.FC = () => {
  const [openItems, setOpenItems] = useState<number[]>([]);

  const toggleItem = (index: number) => {
    setOpenItems(prev => prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]);
  };

  const faqs = [
    {
      question: 'How accurate are the match predictions?',
      answer:
        "Our ML models achieve an accuracy rate of 75-80% on average. Accuracy varies by league and match type.",
    },
    {
      question: 'What data sources do you use?',
      answer:
        'We use the Football-Data.org API with comprehensive data from major European leagues and historical metrics.',
    },
    {
      question: 'How often is the data updated?',
      answer:
        'Match data is near real-time. Team statistics and standings are refreshed daily; models retrain weekly.',
    },
    {
      question: 'Can I see predictions for specific leagues?',
      answer:
        'Yes. You can filter predictions by league, team, or date range across major European competitions.',
    },
  ];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center mb-8">
          <HelpCircle className="w-16 h-16 text-primary-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Frequently Asked Questions</h1>
          <p className="text-lg text-gray-600">Find answers to common questions about Playmaker</p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div key={index} className="border border-gray-200 rounded-lg">
              <button
                onClick={() => toggleItem(index)}
                className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-gray-50 transition-colors"
              >
                <span className="font-semibold text-gray-900">{faq.question}</span>
                {openItems.includes(index) ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>
              {openItems.includes(index) && (
                <div className="px-6 pb-4">
                  <p className="text-gray-600 leading-relaxed">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FAQPage;


