import { useState, useMemo } from 'react';
import { Search, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatUrl } from './utils';

export default function CorpusView({ urnList, metadata }) {
  const [inputText, setInputText] = useState('');
  const [filterText, setFilterText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 100;

  // Derive and filter the list of books based on search text
  const filteredCorpus = useMemo(() => {
    let list = urnList.map(urn => ({
      urn,
      ...metadata[urn]
    }));

    if (filterText.trim()) {
      const q = filterText.toLowerCase();
      list = list.filter(item => {
        const title = (item.title || '').toLowerCase();
        const author = (item.authors || '').toLowerCase();
        const year = (item.year || '').toString();
        const subjects = (item.subjects || '').toLowerCase();
        const litform = (item.literaryform || '').toLowerCase();
        return title.includes(q) || author.includes(q) || year.includes(q) || subjects.includes(q) || litform.includes(q);
      });
    }

    // Sort by year, then author
    list.sort((a, b) => {
      const yearA = parseInt(a.year || 0);
      const yearB = parseInt(b.year || 0);
      if (yearA !== yearB) return yearA - yearB;
      return (a.authors || '').localeCompare(b.authors || '');
    });

    return list;
  }, [urnList, metadata, filterText]);

  // Calculate pagination
  const totalPages = Math.max(1, Math.ceil(filteredCorpus.length / itemsPerPage));
  
  // Safety check if current page exceeds total pages after a search filter
  if (currentPage > totalPages) {
    setCurrentPage(1);
  }

  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredCorpus.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredCorpus, currentPage]);

  return (
    <div className="flex flex-col gap-6">
      <div className="bg-[var(--panel-warm)] p-6 rounded-xl shadow-sm flex flex-col md:flex-row justify-between items-center gap-4">
        
        {/* Search Field */}
        <form 
          className="w-full md:w-1/2 lg:w-2/5 flex gap-2"
          onSubmit={e => {
            e.preventDefault();
            setFilterText(inputText);
            setCurrentPage(1);
          }}
        >
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
              <Search size={18} />
            </div>
            <input
              type="text"
              placeholder="Søk på forfatter, tittel, år, emner, skjønnlitteratur..."
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[var(--primary)] bg-white"
            />
          </div>
          <button 
            type="submit"
            className="bg-[var(--primary)] text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-800 transition-colors"
          >
            Søk
          </button>
        </form>

        {/* Stats */}
        <div className="text-sm font-medium text-gray-700">
          Viser <span className="font-bold">{filteredCorpus.length}</span> titler
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-700 font-semibold border-b">
              <tr>
                <th className="px-4 py-3 w-16">År</th>
                <th className="px-4 py-3 w-1/5">Forfatter</th>
                <th className="px-4 py-3 w-1/3">Tittel</th>
                <th className="px-4 py-3 w-20">Form</th>
                <th className="px-4 py-3 w-1/5">Emner</th>
                <th className="px-4 py-3">URN</th>
                <th className="px-4 py-3 text-center">nb.no</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {paginatedData.length > 0 ? (
                paginatedData.map((item, i) => (
                  <tr key={item.urn || i} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-gray-600">{item.year ? parseInt(item.year, 10) : ''}</td>
                    <td className="px-4 py-3 font-medium text-gray-800">{item.authors}</td>
                    <td className="px-4 py-3 text-gray-700">{item.title}</td>
                    <td className="px-4 py-3 text-xs">
                      {item.literaryform && (
                        <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-md whitespace-nowrap">
                          {item.literaryform}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-xs italic truncate max-w-[200px]" title={item.subjects}>{item.subjects}</td>
                    <td className="px-4 py-3 text-xs text-gray-400 font-mono truncate max-w-[150px]" title={item.urn}>{item.urn}</td>
                    <td className="px-4 py-3 text-center">
                      <a href={formatUrl(item.urn, '')} target="_blank" rel="noreferrer" className="inline-flex text-[var(--primary)] hover:text-blue-800">
                        <ExternalLink size={16} />
                      </a>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                    Ingen bøker matchet søket.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        {filteredCorpus.length > 0 && (
          <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-t border-gray-100">
            <div className="text-sm text-gray-600">
              Side <span className="font-semibold">{currentPage}</span> av <span className="font-semibold">{totalPages}</span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-1 rounded-md text-gray-600 hover:bg-gray-200 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
              >
                <ChevronLeft size={20} />
              </button>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-1 rounded-md text-gray-600 hover:bg-gray-200 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
              >
                <ChevronRight size={20} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
