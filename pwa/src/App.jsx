import { useState, useEffect } from 'react';
import { Loader2, BookOpen } from 'lucide-react';
import { loadMetadata } from './utils';
import Concordance from './Concordance';
import Trends from './Trends';
import CorpusView from './CorpusView';
import './index.css';

export default function App() {
  const [metadata, setMetadata] = useState({});
  const [urnList, setUrnList] = useState([]);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [corpusMinYear, setCorpusMinYear] = useState(1800);
  const [corpusMaxYear, setCorpusMaxYear] = useState(new Date().getFullYear());
  
  const [activeTab, setActiveTab] = useState('konkordans');

  useEffect(() => {
    loadMetadata().then(({ metaMap, urnList }) => {
      setMetadata(metaMap);
      setUrnList(urnList);
      
      const urns = urnList;
      
      let min = 9999;
      let max = 0;
      for (const urn of urns) {
        const year = parseInt(metaMap[urn].year);
        if (!isNaN(year)) {
          if (year < min) min = year;
          if (year > max) max = year;
        }
      }
      if (min !== 9999) {
        setCorpusMinYear(min);
      }
      if (max !== 0) {
        setCorpusMaxYear(max);
      }
      
      setLoadingMeta(false);
    });
  }, []);

  if (loadingMeta) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--bg-warm)]">
        <div className="flex flex-col items-center gap-4 text-[var(--primary)]">
          <Loader2 className="h-10 w-10 animate-spin" />
          <h2 className="text-xl font-medium">Laster BBI-korpus...</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto">
      <header className="flex justify-between items-center mb-6 pb-4 border-b border-gray-200">
        <div className="flex items-center gap-3 text-[var(--primary)]">
          <BookOpen size={32} />
          <h1 className="text-3xl font-bold">Barnebokkorpuset (BBI)</h1>
        </div>
        <div className="text-sm text-gray-500 font-medium">
          {urnList.length} titler i korpuset
        </div>
      </header>

      {/* Tabs */}
      <div className="flex gap-4 mb-8">
        <button 
          onClick={() => setActiveTab('konkordans')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'konkordans' 
              ? 'bg-[var(--primary)] text-white' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Konkordans
        </button>
        <button 
          onClick={() => setActiveTab('trender')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'trender' 
              ? 'bg-[var(--primary)] text-white' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Trender (N-gram)
        </button>
        <button 
          onClick={() => setActiveTab('korpus')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'korpus' 
              ? 'bg-[var(--primary)] text-white' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Korpus
        </button>
      </div>

      <div className={activeTab === 'konkordans' ? 'block' : 'hidden'}>
        <Concordance 
          urnList={urnList} 
          metadata={metadata} 
          corpusMinYear={corpusMinYear} 
          corpusMaxYear={corpusMaxYear} 
        />
      </div>

      <div className={activeTab === 'trender' ? 'block' : 'hidden'}>
        <Trends 
          urnList={urnList} 
          metadata={metadata} 
          corpusMinYear={corpusMinYear} 
          corpusMaxYear={corpusMaxYear} 
        />
      </div>

      <div className={activeTab === 'korpus' ? 'block' : 'hidden'}>
        <CorpusView 
          urnList={urnList} 
          metadata={metadata} 
        />
      </div>
    </div>
  );
}
