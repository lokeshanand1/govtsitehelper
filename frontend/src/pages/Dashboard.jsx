import React, { useState } from 'react';
import { useLocation, Navigate, Link } from 'react-router-dom';
import { CheckCircle, AlertCircle, FileText, ExternalLink, ArrowLeft, Heart, GraduationCap, Briefcase, Landmark } from 'lucide-react';

const Dashboard = () => {
  const location = useLocation();
  const { results, profile } = location.state || {};
  const [activeTab, setActiveTab] = useState('all');

  if (!results || !profile) {
    return <Navigate to="/" />;
  }

  const tabs = [
    { id: 'all', name: 'All Eligible', count: results.all.length, icon: <CheckCircle className="w-4 h-4 mr-2" /> },
    { id: 'scholarship', name: 'Scholarships', count: results.scholarship?.length || 0, icon: <GraduationCap className="w-4 h-4 mr-2" /> },
    { id: 'pension', name: 'Pensions', count: results.pension?.length || 0, icon: <Heart className="w-4 h-4 mr-2" /> },
    { id: 'employment', name: 'Jobs & Loans', count: results.employment?.length || 0, icon: <Briefcase className="w-4 h-4 mr-2" /> },
    { id: 'farmer', name: 'Agriculture', count: results.farmer?.length || 0, icon: <Landmark className="w-4 h-4 mr-2" /> },
  ];

  const currentSchemes = activeTab === 'all' ? results.all : results[activeTab] || [];

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      {/* Header Profile Summary */}
      <div className="bg-white border-b border-slate-200 pt-8 pb-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Link to="/" className="inline-flex items-center text-sm font-medium text-primary-600 hover:text-primary-800 mb-6">
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to Profile Form
          </Link>
          
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 mb-2">
                Hello, {profile.full_name || 'Citizen'}
              </h1>
              <p className="text-slate-600 max-w-2xl">
                Based on your profile ({profile.age} years, {profile.gender || 'unspecified'}, {profile.state || 'India'}), 
                our NLP engine has found <strong className="text-primary-700">{results.total} schemes</strong> you are eligible for.
              </p>
            </div>
            
            <div className="flex flex-col gap-3 items-end">
              {/* NLP Model Status Badge */}
              <div className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold tracking-wide shadow-sm transition-colors ${
                results.classifier_used
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  : 'bg-amber-100 text-amber-800 border border-amber-200'
              }`}>
                <span className="mr-1.5">🧠</span>
                NLP Model: {results.classifier_used ? 'Active' : 'TF-IDF Only'}
                <span className={`ml-2 w-2 h-2 rounded-full ${
                  results.classifier_used ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                }`}></span>
              </div>

              <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex items-start max-w-sm">
                <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5 mr-3 shrink-0" />
                <p className="text-sm text-blue-800">
                  These recommendations are sorted by relevance using {results.classifier_used
                    ? 'semantic matching, rule-based filters, and a trained NLP classifier.'
                    : 'semantic matching and rule-based filters.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Tabs */}
        <div className="flex overflow-x-auto pb-4 mb-6 scrollbar-hide">
          <div className="flex space-x-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`inline-flex items-center px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? 'bg-slate-900 text-white shadow-md'
                    : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                {tab.icon}
                {tab.name}
                <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                  activeTab === tab.id ? 'bg-slate-700 text-white' : 'bg-slate-100 text-slate-600'
                }`}>
                  {tab.count}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Results Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main List */}
          <div className="lg:col-span-2 space-y-6">
            {currentSchemes.length === 0 ? (
              <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center">
                <AlertCircle className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900">No schemes found in this category</h3>
                <p className="mt-1 text-slate-500">Try checking the 'All Eligible' tab or updating your profile.</p>
              </div>
            ) : (
              currentSchemes.map((scheme, idx) => (
                <div key={idx} className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow relative">
                  
                  {/* Top Match Badge */}
                  {idx === 0 && activeTab === 'all' && (
                    <div className="absolute top-0 right-0 bg-yellow-400 text-yellow-900 text-xs font-bold px-3 py-1 rounded-bl-lg flex items-center">
                      <span className="mr-1">★</span> Top Match
                    </div>
                  )}
                  
                  <div className="p-6 md:p-8">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 uppercase tracking-wider">
                        {scheme.category.replace('_', ' ')}
                      </span>
                      <span className="text-xs font-medium text-slate-500 flex items-center">
                        <CheckCircle className="w-3.5 h-3.5 mr-1 text-green-500" />
                        Match Score: {scheme.total_score}%
                      </span>
                    </div>

                    <h2 className="text-2xl font-bold text-slate-900 mb-1">{scheme.name}</h2>
                    {scheme.name_hindi && <h3 className="text-sm font-medium text-slate-500 mb-4">{scheme.name_hindi}</h3>}

                    <p className="text-slate-600 mb-6 leading-relaxed">
                      {scheme.description}
                    </p>

                    {/* Eligibility Explanation */}
                    <div className="bg-green-50 border border-green-100 rounded-xl p-4 mb-6">
                      <h4 className="text-sm font-semibold text-green-900 mb-2 flex items-center">
                        <CheckCircle className="w-4 h-4 mr-1.5" /> Why you are eligible:
                      </h4>
                      <ul className="list-disc pl-5 text-sm text-green-800 space-y-1">
                        {scheme.why_eligible.split('; ').map((reason, i) => (
                          <li key={i}>{reason}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6 mb-8">
                      <div>
                        <h4 className="text-sm font-semibold text-slate-900 mb-2 flex items-center">
                          <Heart className="w-4 h-4 mr-1.5 text-rose-500" /> Key Benefits
                        </h4>
                        <p className="text-sm text-slate-600">{scheme.benefits}</p>
                      </div>
                      <div>
                        <h4 className="text-sm font-semibold text-slate-900 mb-2 flex items-center">
                          <FileText className="w-4 h-4 mr-1.5 text-blue-500" /> Documents Needed
                        </h4>
                        <ul className="list-disc pl-4 text-sm text-slate-600 space-y-1">
                          {scheme.documents_required?.slice(0, 4).map((doc, i) => (
                            <li key={i}>{doc}</li>
                          ))}
                          {scheme.documents_required?.length > 4 && (
                            <li className="text-slate-400 italic">+{scheme.documents_required.length - 4} more</li>
                          )}
                        </ul>
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-4 pt-6 border-t border-slate-100">
                      <a
                        href={scheme.apply_link || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border border-transparent text-sm font-medium rounded-xl text-white bg-primary-600 hover:bg-primary-700"
                      >
                        Apply on Official Portal <ExternalLink className="ml-2 w-4 h-4" />
                      </a>
                      <button className="flex-1 inline-flex justify-center items-center px-4 py-2.5 border-2 border-slate-200 text-sm font-medium rounded-xl text-slate-700 bg-white hover:bg-slate-50 hover:border-slate-300">
                        View Full Details
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Right Sidebar - Analytics & Actions */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sticky top-24">
              <h3 className="text-lg font-bold text-slate-900 mb-4">Your Profile Match</h3>
              
              <div className="space-y-4 mb-6">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-600">Overall Eligibility</span>
                    <span className="font-medium text-primary-700">High</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2">
                    <div className="bg-primary-500 h-2 rounded-full w-4/5"></div>
                  </div>
                </div>
              </div>

              <div className="bg-slate-50 rounded-xl p-4 mb-6">
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Profile Data Used</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Income:</span>
                    <span className="font-medium text-slate-900">₹{profile.annual_family_income || 0}/yr</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Caste:</span>
                    <span className="font-medium text-slate-900 uppercase">{profile.caste_category || 'General'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">State:</span>
                    <span className="font-medium text-slate-900">{profile.state || 'Any'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Student:</span>
                    <span className="font-medium text-slate-900">{profile.is_student ? 'Yes' : 'No'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Farmer:</span>
                    <span className="font-medium text-slate-900">{profile.is_farmer ? 'Yes' : 'No'}</span>
                  </div>
                </div>
              </div>

              <button 
                onClick={() => window.print()}
                className="w-full inline-flex justify-center items-center px-4 py-2 border border-slate-300 shadow-sm text-sm font-medium rounded-lg text-slate-700 bg-white hover:bg-slate-50"
              >
                <FileText className="w-4 h-4 mr-2" /> Download Report
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
