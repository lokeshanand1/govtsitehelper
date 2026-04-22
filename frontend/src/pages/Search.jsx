import React, { useState } from 'react';
import axios from 'axios';
import { Search as SearchIcon, ExternalLink, ShieldCheck, ArrowRight } from 'lucide-react';
import { semanticSearch } from '../engine/recommend.js';

const Search = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      let data;
      const isStaticHost = window.location.hostname.includes('github.io') || !window.location.port;

      if (!isStaticHost) {
        try {
          const response = await axios.post('/api/search', { query, language: 'en' }, { timeout: 3000 });
          data = response.data;
        } catch {
          data = null;
        }
      }

      if (!data) {
        // Client-side search fallback
        const searchResults = semanticSearch(query, 15);
        data = {
          query,
          total: searchResults.length,
          results: searchResults.map(({ scheme, score }) => ({
            name: scheme.name,
            name_hindi: scheme.name_hindi || "",
            description: scheme.description,
            category: scheme.category,
            relevance_score: Math.round(score * 1000) / 10,
            benefits: scheme.benefits,
            apply_link: scheme.apply_link,
            eligibility_text: scheme.eligibility_text,
          }))
        };
      }
      setResults(data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-slate-900 mb-4">Intelligent Scheme Search</h1>
        <p className="text-slate-600 max-w-2xl mx-auto">
          Use natural language to search. For example: "scholarship for girls", "startup loan for youth", or "pension for widow".
        </p>
      </div>

      <form onSubmit={handleSearch} className="mb-12 relative max-w-3xl mx-auto">
        <div className="relative flex items-center">
          <SearchIcon className="absolute left-4 w-6 h-6 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What are you looking for?"
            className="w-full pl-14 pr-32 py-5 text-lg rounded-2xl border-2 border-primary-100 shadow-lg focus:border-primary-500 focus:ring-0 outline-none transition-all"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-3 bg-primary-600 hover:bg-primary-700 text-white px-6 py-2.5 rounded-xl font-medium transition-colors"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {loading && (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
        </div>
      )}

      {results && !loading && (
        <div className="space-y-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-slate-800">
              Found {results.total} results for "{results.query}"
            </h2>
          </div>

          <div className="grid gap-6">
            {results.results.map((scheme, idx) => (
              <div key={idx} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-3 uppercase tracking-wider">
                        {scheme.category}
                      </span>
                      <span className="flex items-center text-sm text-green-600 font-medium">
                        <ShieldCheck className="w-4 h-4 mr-1" />
                        Relevance: {scheme.relevance_score}%
                      </span>
                    </div>
                    
                    <h3 className="text-xl font-bold text-slate-900 mb-2">{scheme.name}</h3>
                    {scheme.name_hindi && <p className="text-sm text-slate-500 mb-3">{scheme.name_hindi}</p>}
                    
                    <p className="text-slate-600 mb-4 line-clamp-2">{scheme.description}</p>
                    
                    {scheme.benefits && (
                      <div className="bg-slate-50 p-4 rounded-lg mb-4">
                        <h4 className="text-sm font-semibold text-slate-900 mb-1">Key Benefits:</h4>
                        <p className="text-sm text-slate-700">{scheme.benefits}</p>
                      </div>
                    )}
                  </div>
                  
                  <div className="md:ml-6 flex flex-col items-start md:items-end md:w-48 shrink-0">
                    <a
                      href={scheme.apply_link || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center w-full px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-primary-600 hover:bg-primary-700"
                    >
                      Apply Now
                      <ExternalLink className="ml-2 w-4 h-4" />
                    </a>
                    
                    <button className="mt-3 inline-flex items-center text-sm font-medium text-primary-600 hover:text-primary-800">
                      View Details
                      <ArrowRight className="ml-1 w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
            
            {results.results.length === 0 && (
              <div className="text-center py-16 bg-white rounded-xl border border-dashed border-slate-300">
                <SearchIcon className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                <h3 className="text-lg font-medium text-slate-900">No matching schemes found</h3>
                <p className="mt-1 text-slate-500">Try using different keywords or broadening your search.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Search;
