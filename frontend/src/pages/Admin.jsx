import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Settings, RefreshCw, BarChart2, Shield, AlertCircle, Database, CheckCircle, DatabaseZap } from 'lucide-react';

const Admin = () => {
  const [token, setToken] = useState(localStorage.getItem('adminToken') || null);
  const [email, setEmail] = useState('admin@govscheme.in');
  const [password, setPassword] = useState('admin123');
  
  const [analytics, setAnalytics] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [scraping, setScraping] = useState(false);
  const [scrapeResult, setScrapeResult] = useState(null);
  const [error, setError] = useState('');

  // Login handler
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await axios.post('/api/auth/login', { email, password });
      setToken(response.data.access_token);
      localStorage.setItem('adminToken', response.data.access_token);
    } catch (err) {
      setError('Invalid admin credentials.');
    } finally {
      setLoading(false);
    }
  };

  // Logout handler
  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem('adminToken');
    setAnalytics(null);
  };

  // Fetch Analytics & Model Info
  const fetchData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [analyticsRes, modelRes] = await Promise.all([
        axios.get('/api/admin/analytics', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get('/api/admin/model-info', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setAnalytics(analyticsRes.data);
      setModelInfo(modelRes.data);
      setError('');
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout();
      } else {
        setError('Failed to fetch admin data.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token]);

  // Scraper Trigger
  const triggerScrape = async () => {
    setScraping(true);
    setScrapeResult(null);
    setError('');
    try {
      // Calls the backend scraper endpoint we built
      const res = await axios.post('/api/admin/scrape?max_pages=250&merge=true', null, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setScrapeResult(res.data);
      // Refresh the analytics to show new numbers
      fetchData();
    } catch (err) {
      setError('Failed to trigger scraper. See console for details.');
      console.error(err);
    } finally {
      setScraping(false);
    }
  };

  // Render Login Screen if no token
  if (!token) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center bg-slate-50">
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 max-w-md w-full">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 mb-4">
              <Shield className="w-8 h-8 text-primary-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">Admin Portal</h2>
            <p className="text-slate-500 mt-2">Login to manage the GovScheme database.</p>
          </div>
          
          {error && (
            <div className="mb-6 bg-red-50 text-red-600 p-4 rounded-xl flex items-center text-sm">
              <AlertCircle className="w-5 h-5 mr-2 shrink-0" /> {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Admin Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-primary-500 outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-primary-500 outline-none"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 text-white font-medium py-3 rounded-xl hover:bg-primary-700 transition-colors disabled:opacity-70 flex justify-center items-center"
            >
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Render Admin Dashboard
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center">
            <Settings className="w-8 h-8 mr-3 text-primary-600" />
            Admin Dashboard
          </h1>
          <p className="text-slate-500 mt-1">Manage database, models, and system scraping.</p>
        </div>
        <button 
          onClick={handleLogout}
          className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
        >
          Logout
        </button>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 text-red-600 p-4 rounded-xl flex items-center text-sm border border-red-200">
          <AlertCircle className="w-5 h-5 mr-2 shrink-0" /> {error}
        </div>
      )}

      {/* Database Operations Section */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-8">
        <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center">
          <DatabaseZap className="w-6 h-6 mr-2 text-blue-600" />
          Data Synchronization
        </h2>
        
        <div className="flex flex-col md:flex-row gap-6 items-start md:items-center justify-between bg-slate-50 rounded-xl p-5 border border-slate-100">
          <div>
            <h3 className="font-semibold text-slate-900">Wikipedia Scraper</h3>
            <p className="text-sm text-slate-600 max-w-2xl mt-1">
              Click this button to trigger the backend NLP scraper. It will scan Wikipedia for new government schemes, 
              auto-extract eligibility rules, and insert them into the MongoDB database automatically.
            </p>
          </div>
          <button
            onClick={triggerScrape}
            disabled={scraping}
            className={`shrink-0 flex items-center px-6 py-3 rounded-xl font-medium text-white shadow-sm transition-all ${
              scraping ? 'bg-slate-400 cursor-not-allowed' : 'bg-primary-600 hover:bg-primary-700 hover:shadow'
            }`}
          >
            <RefreshCw className={`w-5 h-5 mr-2 ${scraping ? 'animate-spin' : ''}`} />
            {scraping ? 'Scraping Wikipedia...' : 'Refresh Database'}
          </button>
        </div>

        {scrapeResult && (
          <div className="mt-4 bg-emerald-50 text-emerald-800 p-4 rounded-xl border border-emerald-200 flex items-start">
            <CheckCircle className="w-5 h-5 mr-2 shrink-0 mt-0.5 text-emerald-600" />
            <div>
              <p className="font-medium">{scrapeResult.message}</p>
              <p className="text-sm mt-1 opacity-90">
                New schemes inserted: {scrapeResult.inserted} | Skipped existing: {scrapeResult.skipped} | Total DB size: {scrapeResult.total_schemes_now}
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Analytics Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-slate-900 flex items-center">
              <BarChart2 className="w-6 h-6 mr-2 text-primary-600" />
              Database Analytics
            </h2>
            <button onClick={fetchData} className="text-slate-400 hover:text-primary-600" title="Refresh">
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
          
          {analytics ? (
            <>
              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                  <p className="text-sm text-slate-500 font-medium mb-1">Total Schemes</p>
                  <p className="text-3xl font-bold text-slate-900">{analytics.total_schemes}</p>
                </div>
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                  <p className="text-sm text-slate-500 font-medium mb-1">Registered Users</p>
                  <p className="text-3xl font-bold text-slate-900">{analytics.total_users}</p>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">Schemes by Category</h3>
                <div className="space-y-3">
                  {analytics.categories?.slice(0, 8).map((cat) => (
                    <div key={cat.category} className="flex items-center">
                      <span className="w-32 text-sm text-slate-600 capitalize truncate" title={cat.category}>
                        {cat.category.replace('_', ' ')}
                      </span>
                      <div className="flex-1 ml-4 relative">
                        <div className="w-full bg-slate-100 rounded-full h-2">
                          <div 
                            className="bg-primary-500 h-2 rounded-full" 
                            style={{ width: `${Math.max(2, (cat.count / analytics.total_schemes) * 100)}%` }}
                          ></div>
                        </div>
                      </div>
                      <span className="ml-4 text-sm font-medium text-slate-900 w-8 text-right">{cat.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="h-48 flex items-center justify-center">
              <RefreshCw className="w-6 h-6 animate-spin text-slate-300" />
            </div>
          )}
        </div>

        {/* NLP Model Status */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center">
            <Database className="w-6 h-6 mr-2 text-amber-600" />
            NLP Engine Status
          </h2>
          
          {modelInfo ? (
            <div className="space-y-6">
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-3 ${modelInfo.classifier_loaded ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                <div>
                  <p className="font-medium text-slate-900">
                    {modelInfo.classifier_loaded ? 'Machine Learning Classifier Active' : 'Fallback (TF-IDF) Mode Active'}
                  </p>
                  <p className="text-sm text-slate-500 mt-0.5">
                    {modelInfo.classifier_loaded ? 'Recommendations are boosted by the trained ML model.' : 'Model not found. Using default NLP rules.'}
                  </p>
                </div>
              </div>

              <div className="bg-slate-50 rounded-xl p-5 border border-slate-100 space-y-4 text-sm">
                <div className="flex justify-between border-b border-slate-200 pb-3">
                  <span className="text-slate-500">Model Status</span>
                  <span className="font-semibold text-slate-900 uppercase">{modelInfo.status}</span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-3">
                  <span className="text-slate-500">Trained Samples</span>
                  <span className="font-medium text-slate-900">{modelInfo.num_samples} profiles</span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-3">
                  <span className="text-slate-500">Macro F1 Score</span>
                  <span className="font-medium text-slate-900">{(modelInfo.f1_score_macro * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Last Trained</span>
                  <span className="font-medium text-slate-900">
                    {modelInfo.trained_at ? new Date(modelInfo.trained_at).toLocaleString() : 'N/A'}
                  </span>
                </div>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mt-6">
                <h4 className="text-sm font-semibold text-amber-900 mb-1">Need Retraining?</h4>
                <p className="text-sm text-amber-800">
                  When new schemes are added via the Wikipedia scraper, they immediately become available through the TF-IDF semantic engine. 
                  To boost their scores with the ML classifier, you should trigger a model retrain.
                </p>
              </div>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center">
              <RefreshCw className="w-6 h-6 animate-spin text-slate-300" />
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default Admin;
