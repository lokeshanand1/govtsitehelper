import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Landmark, CheckCircle2, FileText, Globe } from 'lucide-react';
import { recommend } from '../engine/recommend.js';

const Home = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    // Personal Details
    full_name: '',
    gender: '',
    age: '',
    marital_status: '',
    disability_status: false,

    // Social Category
    caste_category: '',
    minority_status: false,
    bpl_status: false,

    // Education
    highest_qualification: '',
    is_student: false,
    current_course: '',

    // Employment
    occupation: '',
    employment_status: '',
    monthly_income: '',
    annual_family_income: '',

    // Agriculture
    is_farmer: false,
    land_ownership: '',

    // Location
    state: '',
    district: '',
    area_type: '',

    // Other
    is_widow: false,
    is_senior_citizen: false,
    is_single_mother: false,
    is_orphan: false,
    special_category: ''
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSubmit = async (e) => {
    e.NLPpreventDefault?.() || e.preventDefault();
    setLoading(true);
    try {
      // Parse numbers
      const payload = {
        ...formData,
        age: parseInt(formData.age) || 0,
        monthly_income: parseInt(formData.monthly_income) || 0,
        annual_family_income: parseInt(formData.annual_family_income) || 0,
      };

      let data;
      const isStaticHost = window.location.hostname.includes('github.io') || !window.location.port;

      if (!isStaticHost) {
        try {
          // Try backend API when running locally
          const response = await axios.post('/api/recommend', payload, { timeout: 3000 });
          data = response.data;
        } catch {
          // Fallback if backend not available
          data = null;
        }
      }

      if (!data) {
        // Client-side recommendation engine (for GitHub Pages / no backend)
        const results = recommend(payload, 30);
        data = {
          total: results.length,
          classifier_used: false,
          all: results,
          scholarship: results.filter(r => r.category === 'scholarship'),
          pension: results.filter(r => r.category === 'pension'),
          women: results.filter(r => r.category === 'women'),
          student: results.filter(r => ['scholarship', 'student'].includes(r.category)),
          farmer: results.filter(r => r.category === 'farmer'),
          employment: results.filter(r => ['employment', 'startup'].includes(r.category)),
          health: results.filter(r => ['health', 'insurance'].includes(r.category)),
        };
      }
      navigate('/dashboard', { state: { results: data, profile: payload } });
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      alert('Failed to fetch recommendations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-50 min-h-screen">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-primary-900 via-primary-800 to-primary-600 text-white pb-20 pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-6">
            Find the Right Government Schemes for You
          </h1>
          <p className="text-xl text-primary-100 max-w-3xl mx-auto mb-10">
            Our AI-powered engine analyzes your profile against thousands of official policies to recommend benefits you're eligible for.
          </p>
          
          <div className="flex flex-wrap justify-center gap-6 text-sm font-medium text-primary-100">
            <div className="flex items-center"><CheckCircle2 className="w-5 h-5 mr-2 text-green-400" /> AI Matched</div>
            <div className="flex items-center"><FileText className="w-5 h-5 mr-2 text-blue-300" /> Rule Checked</div>
            <div className="flex items-center"><Globe className="w-5 h-5 mr-2 text-indigo-300" /> Pan-India Coverage</div>
          </div>
        </div>
      </div>

      {/* Main Form Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-12 pb-24">
        <div className="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
          <div className="px-6 py-8 md:p-10">
            <div className="text-center mb-10">
              <h2 className="text-2xl font-bold text-slate-900">Enter Your Details</h2>
              <p className="text-slate-500 mt-2">Fill the form below accurately to get the best matching schemes.</p>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-10">
                
                {/* 1. Personal Details */}
                <div className="space-y-6">
                  <div className="flex items-center mb-4 border-b pb-2">
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold mr-3">1</div>
                    <h3 className="text-lg font-semibold text-slate-800">Personal</h3>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                    <input type="text" name="full_name" value={formData.full_name} onChange={handleChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors" placeholder="Enter full name" />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Age</label>
                      <input type="number" name="age" value={formData.age} onChange={handleChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500" placeholder="e.g. 25" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Gender</label>
                      <select name="gender" value={formData.gender} onChange={handleChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white">
                        <option value="">Select</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                  </div>

                  <div className="flex items-center mt-4">
                    <input type="checkbox" id="disability_status" name="disability_status" checked={formData.disability_status} onChange={handleChange} className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded" />
                    <label htmlFor="disability_status" className="ml-2 block text-sm text-slate-700">Person with Disability (Divyang)</label>
                  </div>
                </div>

                {/* 2. Social & Location */}
                <div className="space-y-6">
                  <div className="flex items-center mb-4 border-b pb-2">
                    <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center font-bold mr-3">2</div>
                    <h3 className="text-lg font-semibold text-slate-800">Social & Location</h3>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Caste Category</label>
                      <select name="caste_category" value={formData.caste_category} onChange={handleChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white">
                        <option value="">Select</option>
                        <option value="general">General</option>
                        <option value="sc">SC</option>
                        <option value="st">ST</option>
                        <option value="obc">OBC</option>
                        <option value="ews">EWS</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">State</label>
                      <input type="text" name="state" value={formData.state} onChange={handleChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500" placeholder="e.g. Maharashtra" />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Area Type</label>
                    <select name="area_type" value={formData.area_type} onChange={handleChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white">
                      <option value="">Select</option>
                      <option value="rural">Rural</option>
                      <option value="urban">Urban</option>
                    </select>
                  </div>

                  <div className="space-y-3 mt-4">
                    <div className="flex items-center">
                      <input type="checkbox" id="bpl_status" name="bpl_status" checked={formData.bpl_status} onChange={handleChange} className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded" />
                      <label htmlFor="bpl_status" className="ml-2 block text-sm text-slate-700">Below Poverty Line (BPL)</label>
                    </div>
                    <div className="flex items-center">
                      <input type="checkbox" id="minority_status" name="minority_status" checked={formData.minority_status} onChange={handleChange} className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded" />
                      <label htmlFor="minority_status" className="ml-2 block text-sm text-slate-700">Minority Community</label>
                    </div>
                  </div>
                </div>

                {/* 3. Occupation & Finance */}
                <div className="space-y-6">
                  <div className="flex items-center mb-4 border-b pb-2">
                    <div className="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center font-bold mr-3">3</div>
                    <h3 className="text-lg font-semibold text-slate-800">Finance & Work</h3>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Annual Family Income (₹)</label>
                    <input type="number" name="annual_family_income" value={formData.annual_family_income} onChange={handleChange} className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500" placeholder="e.g. 250000" />
                  </div>

                  <div className="space-y-3 mt-6">
                    <div className="flex items-center">
                      <input type="checkbox" id="is_student" name="is_student" checked={formData.is_student} onChange={handleChange} className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded" />
                      <label htmlFor="is_student" className="ml-2 block text-sm text-slate-700">I am a Student</label>
                    </div>
                    <div className="flex items-center">
                      <input type="checkbox" id="is_farmer" name="is_farmer" checked={formData.is_farmer} onChange={handleChange} className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded" />
                      <label htmlFor="is_farmer" className="ml-2 block text-sm text-slate-700">I am a Farmer</label>
                    </div>
                    <div className="flex items-center">
                      <input type="checkbox" id="is_widow" name="is_widow" checked={formData.is_widow} onChange={handleChange} className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded" />
                      <label htmlFor="is_widow" className="ml-2 block text-sm text-slate-700">Widow</label>
                    </div>
                  </div>
                </div>

              </div>

              <div className="mt-12 pt-8 border-t border-slate-200 text-center">
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex items-center px-8 py-4 border border-transparent text-lg font-medium rounded-xl shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-70 transition-all hover:scale-105 transform duration-200"
                >
                  {loading ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Analyzing via NLP...
                    </span>
                  ) : (
                    'Find Eligible Schemes'
                  )}
                </button>
                <p className="mt-4 text-sm text-slate-500">
                  We use Natural Language Processing to match your profile against eligibility criteria of thousands of schemes.
                </p>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
