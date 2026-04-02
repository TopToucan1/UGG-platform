import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Cpu, Eye, EyeSlash } from '@phosphor-icons/react';

function formatError(detail) {
  if (!detail) return 'Something went wrong.';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(e => e?.msg || JSON.stringify(e)).join(' ');
  return String(detail);
}

export default function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('operator');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, password, name, role);
      } else {
        await login(email, password);
      }
      navigate('/');
    } catch (err) {
      setError(formatError(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#0A0C10' }}>
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: 'url(https://images.pexels.com/photos/13156181/pexels-photo-13156181.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      />
      <div className="relative z-10 w-full max-w-md px-6" data-testid="login-page">
        <div className="mb-10 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ background: '#00D4AA' }}>
              <Cpu size={28} weight="bold" color="#0A0C10" />
            </div>
            <h1 className="font-heading text-3xl font-bold tracking-tight" style={{ color: '#E8ECF1' }}>
              UGG
            </h1>
          </div>
          <p className="text-sm" style={{ color: '#6B7A90' }}>
            Universal Gaming Gateway
          </p>
        </div>

        <div className="rounded-lg border p-8" style={{ background: '#12151C', borderColor: '#272E3B' }}>
          <h2 className="font-heading text-xl font-semibold mb-6" style={{ color: '#E8ECF1' }}>
            {isRegister ? 'Create Account' : 'Sign In'}
          </h2>

          {error && (
            <div className="mb-4 p-3 rounded text-sm" style={{ background: 'rgba(255,59,48,0.1)', color: '#FF3B30', border: '1px solid rgba(255,59,48,0.2)' }} data-testid="auth-error">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-xs font-medium mb-1.5 uppercase tracking-wider" style={{ color: '#6B7A90' }}>Name</label>
                <input
                  data-testid="register-name-input"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2.5 rounded text-sm outline-none transition-colors"
                  style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}
                  placeholder="Full Name"
                  required
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-medium mb-1.5 uppercase tracking-wider" style={{ color: '#6B7A90' }}>Email</label>
              <input
                data-testid="login-email-input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2.5 rounded text-sm outline-none transition-colors"
                style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}
                placeholder="you@example.com"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1.5 uppercase tracking-wider" style={{ color: '#6B7A90' }}>Password</label>
              <div className="relative">
                <input
                  data-testid="login-password-input"
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2.5 rounded text-sm outline-none transition-colors pr-10"
                  style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}
                  placeholder="Password"
                  required
                />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2" style={{ color: '#6B7A90' }}>
                  {showPw ? <EyeSlash size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
            {isRegister && (
              <div>
                <label className="block text-xs font-medium mb-1.5 uppercase tracking-wider" style={{ color: '#6B7A90' }}>Role</label>
                <select
                  data-testid="register-role-select"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-3 py-2.5 rounded text-sm outline-none"
                  style={{ background: '#1A1E2A', border: '1px solid #272E3B', color: '#E8ECF1' }}
                >
                  <option value="operator">Operator</option>
                  <option value="engineer">Engineer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            )}
            <button
              data-testid="login-submit-btn"
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded text-sm font-semibold transition-all duration-150 hover:brightness-110 disabled:opacity-50"
              style={{ background: '#00D4AA', color: '#0A0C10' }}
            >
              {loading ? 'Processing...' : isRegister ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              data-testid="toggle-auth-mode-btn"
              onClick={() => { setIsRegister(!isRegister); setError(''); }}
              className="text-sm transition-colors hover:underline"
              style={{ color: '#00D4AA' }}
            >
              {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Register"}
            </button>
          </div>
        </div>

        <p className="mt-6 text-center text-xs" style={{ color: '#6B7A90' }}>
          Protocol-Agnostic Gaming Interoperability Platform
        </p>
      </div>
    </div>
  );
}
