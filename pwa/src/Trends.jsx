import { useState, useMemo } from 'react';
import { Loader2, TrendingUp } from 'lucide-react';
import { fetchFrequencies } from './utils';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export default function Trends({ urnList, metadata, corpusMinYear, corpusMaxYear }) {
  const [search, setSearch] = useState('barn, skole, leke');
  const [startYear, setStartYear] = useState(corpusMinYear || 1800);
  const [endYear, setEndYear] = useState(corpusMaxYear || new Date().getFullYear());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [displayMode, setDisplayMode] = useState('absolute');
  const [timeResolution, setTimeResolution] = useState('1');
  const [rawData, setRawData] = useState([]);
  const [wordsUsed, setWordsUsed] = useState([]);
  const [hiddenLines, setHiddenLines] = useState({});

  const toggleLine = (e) => {
    const dataKey = e.dataKey;
    setHiddenLines(prev => ({ ...prev, [dataKey]: !prev[dataKey] }));
  };

  const chartData = useMemo(() => {
    if (!rawData.length) return [];
    
    const rawYearStats = {};
    let minYear = 9999;
    let maxYear = 0;

    rawData.forEach(row => {
      if (!Array.isArray(row) || row.length < 4) return;
      const dhlabid = row[0].toString();
      const word = row[1];
      const count = row[2];
      const urnTotalWords = row[3];
      
      const meta = metadata[dhlabid];
      if (!meta || !meta.year) return;
      
      const year = parseInt(meta.year);
      if (year < minYear) minYear = year;
      if (year > maxYear) maxYear = year;
      
      if (!rawYearStats[year]) {
        rawYearStats[year] = { year, counts: {}, seenDhlabIds: new Set(), totalWords: 0 };
      }
      
      rawYearStats[year].counts[word] = (rawYearStats[year].counts[word] || 0) + count;
      
      if (!rawYearStats[year].seenDhlabIds.has(dhlabid)) {
        rawYearStats[year].seenDhlabIds.add(dhlabid);
        rawYearStats[year].totalWords += urnTotalWords;
      }
    });

    if (minYear === 9999) return [];

    // Fill in missing years with 0s for proper smoothing
    for (let y = minYear; y <= maxYear; y++) {
      if (!rawYearStats[y]) {
        rawYearStats[y] = { year: y, counts: {}, totalWords: 0 };
      }
    }

    const windowSize = parseInt(timeResolution);
    const halfWindowLeft = Math.floor((windowSize - 1) / 2);
    const halfWindowRight = Math.floor(windowSize / 2);

    const smoothedData = [];

    for (let y = minYear; y <= maxYear; y++) {
      const dataPoint = { year: y };
      
      let windowTotalWords = 0;
      let windowCounts = {};
      let yearsInWindow = 0;

      for (let wy = y - halfWindowLeft; wy <= y + halfWindowRight; wy++) {
        if (rawYearStats[wy]) {
          yearsInWindow++;
          windowTotalWords += rawYearStats[wy].totalWords || 0;
          wordsUsed.forEach(w => {
            windowCounts[w] = (windowCounts[w] || 0) + (rawYearStats[wy].counts[w] || 0);
          });
        }
      }

      let cohortTotal = 0;
      if (displayMode === 'relative_cohort') {
        wordsUsed.forEach(w => {
          cohortTotal += windowCounts[w] || 0;
        });
      }

      wordsUsed.forEach(w => {
        if (displayMode === 'relative_corpus' && windowTotalWords > 0) {
          dataPoint[w] = (windowCounts[w] / windowTotalWords) * 100000;
        } else if (displayMode === 'relative_cohort') {
          dataPoint[w] = cohortTotal > 0 ? (windowCounts[w] / cohortTotal) * 100 : 0;
        } else {
          // Average absolute count across the window to keep Y-axis scale intact
          dataPoint[w] = windowCounts[w] / yearsInWindow;
        }
      });

      smoothedData.push(dataPoint);
    }

    return smoothedData;
  }, [rawData, wordsUsed, metadata, displayMode, timeResolution]);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!search.trim()) {
      setError("Skriv inn minst ett ord (separert med komma).");
      return;
    }
    setError('');
    setLoading(true);

    try {
      // 1. Filter URNs by year
      const filteredUrns = urnList.filter(urn => {
        const meta = metadata[urn];
        if (!meta || !meta.year) return false;
        const year = parseInt(meta.year);
        return year >= startYear && year <= endYear;
      });

      if (filteredUrns.length === 0) {
        setError('Ingen bøker i den valgte perioden.');
        setLoading(false);
        return;
      }

      const words = search.split(',').map(w => w.trim()).filter(w => w.length > 0);
      setWordsUsed(words);

      // 2. Fetch frequencies
      const freqData = await fetchFrequencies(filteredUrns, words);
      if (Array.isArray(freqData)) {
        setRawData(freqData);
      } else {
        setRawData([]);
      }
    } catch (err) {
      console.error(err);
      setError('Feil ved henting av trender. Prøv igjen.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8">
      <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 bg-[var(--panel-warm)] p-6 rounded-xl shadow-sm">
        
        {/* Søkefelt */}
        <div className="flex flex-col gap-2">
          <label className="font-semibold text-sm">Ord (komma-separert)</label>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
            title="Skriv inn ord adskilt med komma."
          />
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

        {/* Action knapper */}
        <div className="flex items-end gap-3">
          <button 
            type="submit" 
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-[var(--primary)] text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-800 transition-colors disabled:opacity-50"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <TrendingUp size={20} />}
            Generer Trendlinjer
          </button>
        </div>
      </form>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {chartData.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex flex-wrap justify-between items-center mb-6 gap-4">
            <h3 className="text-lg font-semibold">Ordfrekvenser over tid</h3>
            
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700">Oppløsning:</span>
                <select
                  value={timeResolution}
                  onChange={(e) => setTimeResolution(e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] bg-white"
                >
                  <option value="1">Ingen glatting (1 år)</option>
                  <option value="5">5-års glidende gjennomsnitt</option>
                  <option value="10">10-års glidende gjennomsnitt</option>
                </select>
              </label>

              <label className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700">Visning:</span>
                <select
                  value={displayMode}
                  onChange={(e) => setDisplayMode(e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] bg-white"
                >
                  <option value="absolute">Absolutte tall</option>
                  <option value="relative_corpus">Relativ til korpus (pr. 100 000 ord)</option>
                  <option value="relative_cohort">Relativ til søkegruppe (andel i %)</option>
                </select>
              </label>
            </div>
          </div>
          <div className="h-[500px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartData}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                <XAxis 
                  dataKey="year" 
                  type="number" 
                  domain={['dataMin', 'dataMax']} 
                  tickCount={10} 
                  tickFormatter={(val) => Math.round(val)} 
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(val) => `År: ${val}`}
                />
                <Legend 
                  onClick={toggleLine} 
                  wrapperStyle={{ cursor: 'pointer' }}
                />
                {wordsUsed.map((word, idx) => (
                  <Line 
                    key={word} 
                    type="monotone" 
                    dataKey={word} 
                    stroke={COLORS[idx % COLORS.length]} 
                    strokeWidth={4}
                    dot={false}
                    activeDot={{ r: 6 }}
                    hide={hiddenLines[word] === true}
                    strokeOpacity={hiddenLines[word] ? 0.3 : 1}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
