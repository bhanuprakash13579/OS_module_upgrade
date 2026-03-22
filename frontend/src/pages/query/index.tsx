import { useState } from 'react';
import { Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import { FileSearch, LogOut, Menu, ChevronLeft, Download, FileText } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import OSQueryPage from './OSQueryPage';
import OSPrintView from './OSPrintView';
import ExportData from './ExportData';
import CustomReport from './CustomReport';

export default function QueryModule() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [isCollapsed, setIsCollapsed] = useState(true);

  const handleLogout = () => {
    logout();
    navigate('/modules');
  };

  return (
    <div className="flex h-screen w-full bg-slate-50 min-h-screen overflow-hidden text-slate-800 print:h-auto print:min-h-0 print:overflow-visible print:block print-layout-root">
      {/* Sidebar - hidden when printing */}
      <aside className={`${isCollapsed ? 'w-16' : 'w-64'} flex flex-col h-full bg-slate-900 border-r border-slate-700 shadow-xl shadow-slate-900/20 transition-[width] duration-200 print:hidden shrink-0 z-50`}>
        <div className="p-3 border-b border-slate-700/50 flex items-center justify-between min-h-[72px] shrink-0">
            {!isCollapsed && (
              <div className="flex items-center gap-3">
                <div className="bg-gradient-to-br from-emerald-500 to-emerald-700 p-2 rounded-lg shrink-0">
                  <FileSearch className="text-white w-6 h-6" />
                </div>
                <div className="flex-1 min-w-0">
                  <h1 className="text-white font-bold text-base tracking-wide leading-tight">Query Module</h1>
                  <p className="text-emerald-400 text-xs">COPS</p>
                </div>
              </div>
            )}
            
            <button
              type="button"
              onClick={() => setIsCollapsed(v => !v)}
              className={`text-slate-400 hover:text-white hover:bg-slate-800 p-2 rounded-lg transition-colors ${isCollapsed ? 'mx-auto' : 'ml-1 shrink-0'}`}
              title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              <Menu size={26} />
            </button>
          </div>
        
        <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
          <nav className="p-3 space-y-1 mt-2">
            {!isCollapsed && <p className="text-emerald-500/70 text-xs uppercase tracking-widest font-semibold px-3 mb-3">Search & Reports</p>}
            
            <button
              onClick={() => navigate('/query/os')}
              className={`w-full flex items-center ${isCollapsed ? 'justify-center py-3' : 'gap-3 px-4 py-3'} rounded-lg text-base transition-colors text-emerald-400 bg-emerald-500/15 border border-emerald-500/20 hover:bg-emerald-500/25`}
              title={isCollapsed ? 'OS Query' : undefined}
            >
              <FileSearch className="w-6 h-6 shrink-0 opacity-90" />
              {!isCollapsed && <span className="font-medium leading-tight">OS Query</span>}
            </button>

            <button
              onClick={() => navigate('/query/report')}
              className={`mt-2 w-full flex items-center ${isCollapsed ? 'justify-center py-3' : 'gap-3 px-4 py-3'} rounded-lg text-base transition-colors text-emerald-200 bg-slate-900/40 border border-slate-700/60 hover:bg-slate-800/70`}
              title={isCollapsed ? 'Custom Report' : undefined}
            >
              <FileText className="w-5 h-5 shrink-0 opacity-90" />
              {!isCollapsed && <span className="font-medium leading-tight">Custom Report</span>}
            </button>

            <button
              onClick={() => navigate('/query/export')}
              className={`mt-2 w-full flex items-center ${isCollapsed ? 'justify-center py-3' : 'gap-3 px-4 py-3'} rounded-lg text-base transition-colors text-emerald-200 bg-slate-900/40 border border-slate-700/60 hover:bg-slate-800/70`}
              title={isCollapsed ? 'Download Backup' : undefined}
            >
              <Download className="w-5 h-5 shrink-0 opacity-90" />
              {!isCollapsed && <span className="font-medium leading-tight">Download Backup</span>}
            </button>
          </nav>
        </div>
        
        <div className={`border-t border-slate-700/50 space-y-3 shrink-0 ${isCollapsed ? 'p-2' : 'p-4'}`}>
          {!isCollapsed && (
            <div className="bg-slate-800 rounded-lg p-3 border border-slate-700/50">
              <div className="flex items-center gap-2 mb-1">
                <FileSearch size={18} className="text-emerald-400" />
                <p className="text-emerald-300 text-xs uppercase tracking-wider font-semibold">Logged in as</p>
              </div>
              <p className="text-white font-semibold text-sm truncate">{user?.user_name}</p>
              <p className="text-emerald-400 text-xs">{user?.user_desig || user?.user_role}</p>
            </div>
          )}
          
          <button
            onClick={() => navigate('/modules')}
            className={`flex w-full items-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors text-base ${isCollapsed ? 'justify-center py-3' : 'gap-2 px-4 py-3'}`}
            title="Module Selection"
          >
            <ChevronLeft size={22} />
            {!isCollapsed && 'Module Selection'}
          </button>
          
          <button
            onClick={handleLogout}
            className={`flex w-full items-center rounded-lg text-slate-400 hover:bg-rose-500/10 hover:text-rose-400 transition-colors text-base border border-transparent hover:border-rose-500/20 ${isCollapsed ? 'justify-center py-3' : 'gap-2 px-4 py-3'}`}
            title="Sign Out"
          >
            <LogOut size={22} />
            {!isCollapsed && 'Sign Out'}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50/50 print:bg-white relative print:h-auto print:min-h-0 print:overflow-visible print:block">
        <div className="h-[2px] w-full bg-gradient-to-r from-emerald-500 via-emerald-400 to-transparent fixed top-0 z-50 print:hidden print-hide-bar" data-print-hide="true"></div>
        <div className="flex-1 overflow-auto p-4 md:p-8 pt-10 print:p-0 print:overflow-visible print-content-wrap">
          <Routes>
            <Route path="/" element={<Navigate to="/query/os" replace />} />
            <Route path="os" element={<OSQueryPage />} />
            <Route path="os/print/:os_no/:os_year" element={<OSPrintView />} />
            <Route path="report" element={<CustomReport />} />
            <Route path="export" element={<ExportData />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
