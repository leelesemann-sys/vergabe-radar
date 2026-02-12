import React, { useState, useMemo } from 'react';

// Echte Daten aus unserem POC
const TENDERS_DATA = [
  {
    "title": "Depotinstandsetzung 2026 EGV Frankfurt am Main - AP07 Gerüstbau",
    "url": "https://www.evergabe-online.de/tenderdetails.html?id=827375",
    "id": "827375",
    "published_date": "31.12.25",
    "deadline": "29.01.26, 13:00",
    "search_keyword": "IT-Dienstleistungen"
  },
  {
    "title": "Kartierung von FFH-Lebensraumtypen (LRT), LRT-Verlustflächen, LRT-Entwicklungsflächen und gesetzlich geschützten Biotopen",
    "url": "https://www.evergabe-online.de/tenderdetails.html?id=826366",
    "id": "826366",
    "published_date": "31.12.25",
    "deadline": "02.02.26, 23:59",
    "search_keyword": "IT-Dienstleistungen"
  },
  {
    "title": "Depotinstandsetzung 2026 EGV Frankfurt am Main - AP01 Schiffbauliche Arbeiten",
    "url": "https://www.evergabe-online.de/tenderdetails.html?id=827332",
    "id": "827332",
    "published_date": "31.12.25",
    "deadline": "29.01.26, 13:00",
    "search_keyword": "IT-Dienstleistungen"
  },
  {
    "title": "Gelände- und Sensorpflege an DWD Standorten Lingen-Baccum und Hannover",
    "url": "https://www.evergabe-online.de/tenderdetails.html?id=827327",
    "id": "827327",
    "published_date": "31.12.25",
    "deadline": "04.02.26, 23:59",
    "search_keyword": "Facility Management"
  },
  {
    "title": "REZ NORD 45ind AA Osnabrück",
    "url": "https://www.evergabe-online.de/tenderdetails.html?id=827273",
    "id": "827273",
    "published_date": "31.12.25",
    "deadline": "03.02.26, 12:00",
    "search_keyword": "IT-Dienstleistungen"
  }
];

export default function VergabeRadar() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTender, setSelectedTender] = useState(null);

  // Filter Ausschreibungen basierend auf Suche
  const filteredTenders = useMemo(() => {
    if (!searchTerm) return TENDERS_DATA;
    
    const term = searchTerm.toLowerCase();
    return TENDERS_DATA.filter(tender => 
      tender.title.toLowerCase().includes(term) ||
      tender.search_keyword.toLowerCase().includes(term)
    );
  }, [searchTerm]);

  // Tage bis Frist
  const getDaysUntilDeadline = (deadlineStr) => {
    try {
      const [date, time] = deadlineStr.split(', ');
      const [day, month, year] = date.split('.');
      const fullYear = parseInt(year) < 100 ? 2000 + parseInt(year) : parseInt(year);
      const deadline = new Date(fullYear, parseInt(month) - 1, parseInt(day));
      const today = new Date();
      const diffTime = deadline - today;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return diffDays;
    } catch {
      return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl font-bold">V</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">VergabeRadar</h1>
                <p className="text-sm text-gray-500">Öffentliche Ausschreibungen</p>
              </div>
            </div>
            <div className="hidden sm:flex items-center space-x-4">
              <span className="text-sm text-gray-600">Demo Version</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600">Gesamt</p>
            <p className="text-3xl font-bold text-gray-900">{TENDERS_DATA.length}</p>
            <p className="text-xs text-gray-500 mt-1">Ausschreibungen</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600">Neu heute</p>
            <p className="text-3xl font-bold text-blue-600">5</p>
            <p className="text-xs text-gray-500 mt-1">Veröffentlicht 31.12.25</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600">Bald abgelaufen</p>
            <p className="text-3xl font-bold text-red-600">2</p>
            <p className="text-xs text-gray-500 mt-1">Frist &lt; 7 Tage</p>
          </div>
        </div>

        {/* Search */}
        <div className="bg-white rounded-lg shadow mb-6 p-6">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Suche nach Ausschreibungen... (z.B. IT, Software, Facility)"
              className="flex-1 outline-none text-gray-900 placeholder-gray-400"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button 
                onClick={() => setSearchTerm('')}
                className="text-gray-400 hover:text-gray-600 ml-2"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-sm text-gray-600">
            {filteredTenders.length} {filteredTenders.length === 1 ? 'Ergebnis' : 'Ergebnisse'}
            {searchTerm && ` für "${searchTerm}"`}
          </p>
        </div>

        {/* Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ausschreibung
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">
                    Kategorie
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden md:table-cell">
                    Veröffentlicht
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Frist
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Aktion
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredTenders.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                      Keine Ausschreibungen gefunden.
                      <br />
                      <span className="text-sm">Versuche einen anderen Suchbegriff.</span>
                    </td>
                  </tr>
                ) : (
                  filteredTenders.map((tender) => {
                    const daysLeft = getDaysUntilDeadline(tender.deadline);
                    const isUrgent = daysLeft !== null && daysLeft <= 7;
                    
                    return (
                      <tr key={tender.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedTender(tender)}>
                        <td className="px-6 py-4">
                          <div className="text-sm font-medium text-gray-900">
                            {tender.title.substring(0, 80)}...
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            ID: {tender.id}
                          </div>
                        </td>
                        <td className="px-6 py-4 hidden sm:table-cell">
                          <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                            {tender.search_keyword}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500 hidden md:table-cell">
                          {tender.published_date}
                        </td>
                        <td className="px-6 py-4">
                          <div className={`text-sm ${isUrgent ? 'text-red-600 font-semibold' : 'text-gray-900'}`}>
                            {tender.deadline}
                          </div>
                          {daysLeft !== null && (
                            <div className={`text-xs ${isUrgent ? 'text-red-500' : 'text-gray-500'}`}>
                              {daysLeft > 0 ? `${daysLeft} Tage` : 'Abgelaufen'}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedTender(tender);
                            }}
                            className="text-blue-600 hover:text-blue-800 font-medium"
                          >
                            Details →
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Modal */}
      {selectedTender && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedTender(null)}>
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-2xl font-bold text-gray-900 pr-8">
                  {selectedTender.title}
                </h2>
                <button 
                  onClick={() => setSelectedTender(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Ausschreibungs-ID</p>
                    <p className="text-lg font-semibold text-gray-900">{selectedTender.id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Kategorie</p>
                    <p className="text-lg font-semibold text-gray-900">{selectedTender.search_keyword}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Veröffentlicht</p>
                    <p className="text-lg font-semibold text-gray-900">{selectedTender.published_date}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Frist</p>
                    <p className="text-lg font-semibold text-red-600">{selectedTender.deadline}</p>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <a 
                    href={selectedTender.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-blue-600 hover:bg-blue-700 text-white text-center py-3 rounded-lg font-medium transition-colors"
                  >
                    Zur vollständigen Ausschreibung →
                  </a>
                  <p className="text-xs text-gray-500 text-center mt-2">
                    Öffnet evergabe-online.de in neuem Tab
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}