import { Clock, AlertTriangle, XCircle } from 'lucide-react';
import { useTrialStatus } from '@/hooks/useTrialStatus';

export default function TrialBanner() {
  const { trial_disabled, days_remaining, expired, isLoading } = useTrialStatus();

  if (isLoading || trial_disabled) return null;

  // ── Expired: full-screen block ─────────────────────────────────────────────
  if (expired) {
    return (
      <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/90 backdrop-blur-sm print:hidden">
        <div className="bg-white rounded-2xl shadow-2xl p-10 max-w-md w-full mx-4 text-center space-y-5">
          <XCircle size={56} className="text-red-500 mx-auto" />
          <h2 className="text-2xl font-bold text-slate-800">Trial Period Expired</h2>
          <p className="text-slate-600 text-sm leading-relaxed">
            The 30-day trial for this COPS installation has ended. Please contact your system
            administrator to extend or activate the software.
          </p>
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 text-left space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Admin Action Required</p>
            <p className="text-xs text-slate-600">
              In the Admin Panel → Backup &amp; System Settings → scroll to
              <strong> Trial / License</strong>, then click <strong>Reset Trial</strong> or
              <strong> Activate Permanent License</strong>.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── Active: countdown banner ───────────────────────────────────────────────
  const d = days_remaining ?? 30;
  const color =
    d <= 3  ? 'bg-red-600 text-white'    :
    d <= 7  ? 'bg-orange-500 text-white' :
    d <= 14 ? 'bg-amber-400 text-amber-900' :
              'bg-blue-600 text-white';

  const Icon = d <= 7 ? AlertTriangle : Clock;

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-[9998] flex items-center justify-center gap-2 text-xs font-semibold py-1 px-4 print:hidden ${color}`}
      style={{ height: '26px' }}
    >
      <Icon size={13} />
      <span>
        {d === 0
          ? 'Trial expires TODAY — contact admin'
          : `Trial: ${d} day${d === 1 ? '' : 's'} remaining`}
      </span>
    </div>
  );
}
