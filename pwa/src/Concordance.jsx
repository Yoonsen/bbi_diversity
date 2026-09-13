import { useState } from 'react';
import { Search, Download, ExternalLink, Loader2 } from 'lucide-react';
import { fetchConcordances, formatConcordance, formatUrl, exportToExcel } from './utils';

export default function Concordance({ urnList, metadata, corpusMinYear, corpusMaxYear }) {
  const [search, setSearch] = useState('leksikografi');
  const [startYear, setStartYear] = useState(corpusMinYear || 1800);
  const [endYear, setEndYear] = useState(corpusMaxYear || new Date().getFullYear());
  const [sampleSize, setSampleSize] = useState(150);
  const [splitContext, setSplitContext] = useState(false);
  const [strictMode, setStrictMode] = useState(true);
  const [filename, setFilename] = useState('konkordanser.xlsx');
  
  const [results, setResults] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [error, setError] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const [searchHistory, setSearchHistory] = useState(() => {
    try {
      const saved = localStorage.getItem('bbi_concordance_history');
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });

  const addToHistory = (term) => {
    const cleanTerm = term.trim();
    if (!cleanTerm) return;
    setSearchHistory(prev => {
      const updated = [cleanTerm, ...prev.filter(t => t !== cleanTerm)].slice(0, 10);
      localStorage.setItem('bbi_concordance_history', JSON.stringify(updated));
      return updated;
    });
  };

  const removeFromHistory = (term, e) => {
    e.stopPropagation();
    setSearchHistory(prev => {
      const updated = prev.filter(t => t !== term);
      localStorage.setItem('bbi_concordance_history', JSON.stringify(updated));
      return updated;
    });
  };

  const isStrictMatch = (target, query) => {
    const cleanQuery = query.replace(/["']/g, '').trim();
    const regexStr = '^' + cleanQuery.replace(/\*/g, '.*') + '$';
    try {
      const regex = new RegExp(regexStr, 'i');
      return regex.test(target);
    } catch(e) {
      return target.toLowerCase() === cleanQuery.toLowerCase();
    }
  };

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!search.trim() || search.match(/^[.,\/#!$%\^&\*;:{}=\-_`~()]+$/g)) {
      setError("Ugyldig søk. Skriv inn et ord eller en frase i søkefeltet.");
      return;
    }
    setError('');
    setLoadingSearch(true);
    addToHistory(search);

    try {
      // 1. Filter URNs by year
      const filteredUrns = urnList.filter(urn => {
        const meta = metadata[urn];
        if (!meta || !meta.year) return false;
        const year = parseInt(meta.year);
        return year >= startYear && year <= endYear;
      });

      // 2. Fetch from DHlab API
      const rawConc = await fetchConcordances(filteredUrns, search, sampleSize);
      
      // 3. Format and merge with metadata
      const formatted = rawConc.reduce((acc, item) => {
        const meta = metadata[item.urn] || {};
        const { left_context, target, right_context, raw } = formatConcordance(item.concordance);
        
        if (strictMode && target && !isStrictMatch(target, search)) {
          return acc;
        }

        acc.push({
          concordance: raw,
          left_context,
          target,
          right_context,
          year: meta.year || '',
          url: formatUrl(item.urn, search),
          authors: meta.authors || '',
          title: meta.title || '',
          kristin: meta.kristin || '',
          urn: item.urn
        });
        return acc;
      }, []);
      
      // Sort by year
      formatted.sort((a, b) => parseInt(a.year || 0) - parseInt(b.year || 0));
      
      setResults(formatted);
    } catch (err) {
      console.error(err);
      setError('Kunne ikke laste konkordanser for dette søket. Prøv igjen.');
    } finally {
      setLoadingSearch(false);
    }
  };

  const handleExport = () => {
    const exportData = results.map(r => {
      if (splitContext) {
        return {
          "Venstre kontekst": r.left_context,
          "Søkeord": r.target,
          "Høyre kontekst": r.right_context,
          "Årstall": r.year,
          "Forfatter": r.authors,
          "Tittel": r.title,
          "Kristin": r.kristin,
          "URL": r.url
        };
      } else {
        return {
          "Konkordans": r.concordance,
          "Årstall": r.year,
          "Forfatter": r.authors,
          "Tittel": r.title,
          "Kristin": r.kristin,
          "URL": r.url
        };
      }
    });
    exportToExcel(exportData, filename);
  };

  return (
    <div className="flex flex-col gap-8">
      <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 bg-[var(--panel-warm)] p-6 rounded-xl shadow-sm">
        
        {/* Søkefelt */}
        <div className="flex flex-col gap-2 relative">
          <label className="font-semibold text-sm">Ord og fraser</label>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => setIsDropdownOpen(true)}
            onBlur={() => setIsDropdownOpen(false)}
            className="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
            title="Skriv inn ord for å finne match i avsnitt."
          />
          {isDropdownOpen && searchHistory.length > 0 && (
            <div 
              className="absolute top-[100%] left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 max-h-60 overflow-y-auto"
              onMouseDown={(e) => e.preventDefault()}
            >
              {searchHistory.map(term => (
                <div 
                  key={term} 
                  className="flex justify-between items-center px-4 py-2 hover:bg-gray-100 cursor-pointer transition-colors"
                  onClick={() => { setSearch(term); setIsDropdownOpen(false); }}
                >
                  <span className="font-medium text-gray-700 truncate">{term}</span>
                  <button 
                    type="button" 
                    onClick={(e) => removeFromHistory(term, e)} 
                    className="text-gray-400 hover:text-red-500 px-2 py-1 leading-none rounded text-lg font-bold"
                    title="Slett fra historikk"
                  >&times;</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Periode */}
        <div className="flex flex-col gap-2">
          <label className="font-semibold text-sm">Velg en periode</label>
          <div className="flex items-center gap-2">
            <input 
              type="number" min={corpusMinYear} max={corpusMaxYear} 
              value={startYear} onChange={e => setStartYear(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
            />
            <span>-</span>
            <input 
              type="number" min={corpusMinYear} max={corpusMaxYear}
              value={endYear} onChange={e => setEndYear(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
            />
          </div>
        </div>

        {/* Max results */}
        <div className="flex flex-col gap-2">
          <label className="font-semibold text-sm">Maks antall treff</label>
          <input
            type="number"
            value={sampleSize}
            onChange={(e) => setSampleSize(e.target.value === '' ? '' : Number(e.target.value))}
            className="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
          />
        </div>

        {/* Action knapper */}
        <div className="flex items-end gap-3 lg:justify-end">
          <button 
            type="submit" 
            disabled={loadingSearch}
            className="flex-1 lg:flex-none flex items-center justify-center gap-2 bg-[var(--primary)] text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-800 transition-colors disabled:opacity-50"
          >
            {loadingSearch ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
            Søk
          </button>
        </div>
      </form>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {/* Resultater */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
          <div className="font-medium text-gray-700">
            Antall konkordanser totalt: <span className="font-bold text-black">{results.length}</span>
          </div>
          
          <div className="flex flex-wrap items-center gap-6">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={strictMode}
                onChange={(e) => setStrictMode(e.target.checked)}
                className="w-4 h-4 text-[var(--primary)] rounded border-gray-300 focus:ring-[var(--primary)]"
              />
              <span className="text-sm font-medium">Strengt søk (skiller a/å)</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={splitContext}
                onChange={(e) => setSplitContext(e.target.checked)}
                className="w-4 h-4 text-[var(--primary)] rounded border-gray-300 focus:ring-[var(--primary)]"
              />
              <span className="text-sm font-medium">Del opp i flere kolonner</span>
            </label>

            <div className="flex items-center gap-2">
              <input 
                type="text" 
                value={filename}
                onChange={e => setFilename(e.target.value)}
                className="px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none"
              />
              <button
                onClick={handleExport}
                disabled={results.length === 0}
                className="flex items-center gap-2 text-sm bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                <Download size={16} /> Last ned
              </button>
            </div>
          </div>
        </div>

        {/* Tabell */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-x-auto">
          {results.length > 0 ? (
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 text-gray-700 font-semibold border-b">
                <tr>
                  {splitContext ? (
                    <>
                      <th className="px-4 py-3 text-right">Venstre kontekst</th>
                      <th className="px-4 py-3 text-center">Søkeord</th>
                      <th className="px-4 py-3">Høyre kontekst</th>
                    </>
                  ) : (
                    <th className="px-4 py-3">Konkordans</th>
                  )}
                  <th className="px-4 py-3">Årstall</th>
                  <th className="px-4 py-3 max-w-[150px]">Forfatter</th>
                  <th className="px-4 py-3 max-w-[200px]">Tittel</th>
                  <th className="px-4 py-3">Kristin</th>
                  <th className="px-4 py-3 text-center">nb.no</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {results.map((r, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    {splitContext ? (
                      <>
                        <td className="px-4 py-3 text-right text-gray-600">{r.left_context}</td>
                        <td className="px-4 py-3 text-center font-bold text-[var(--primary)]">{r.target}</td>
                        <td className="px-4 py-3 text-gray-600">{r.right_context}</td>
                      </>
                    ) : (
                      <td className="px-4 py-3 text-gray-800">
                        {r.left_context} <span className="font-bold text-[var(--primary)]">{r.target}</span> {r.right_context}
                      </td>
                    )}
                    <td className="px-4 py-3">{r.year}</td>
                    <td className="px-4 py-3 truncate max-w-[150px]" title={r.authors}>{r.authors}</td>
                    <td className="px-4 py-3 truncate max-w-[200px]" title={r.title}>{r.title}</td>
                    <td className="px-4 py-3">{r.kristin}</td>
                    <td className="px-4 py-3 text-center">
                      <a href={r.url} target="_blank" rel="noreferrer" className="inline-flex text-[var(--primary)] hover:text-blue-800">
                        <ExternalLink size={16} />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : !loadingSearch ? (
            <div className="p-8 text-center text-gray-500">
              Ingen resultater å vise. Prøv et nytt søk.
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
