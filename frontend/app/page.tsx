'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useTheme } from 'next-themes';
import axios from 'axios';
import {
  Sun,
  Moon,
  Send,
  Loader2,
  Copy,
  Share2,
  ChevronRight,
  AlertCircle,
  Lightbulb,
  LogOut,
  ArrowLeft,
  X,
  BarChart3,
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

type Message = {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  citations?: Array<{ doc: string; section: string }>;
  scores?: number[];
  timestamp: Date;
};

type Translations = {
  [key: string]: string | Record<string, string>;
};

// Simple SHA256 hash function using Web Crypto API
const hashPassword = async (password: string, modKey: string = 'Handbook'): Promise<string> => {
  const combined = password + modKey;
  const encoder = new TextEncoder();
  const data = encoder.encode(combined);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex;
};

export default function Home() {
  const { theme, setTheme } = useTheme();
  const [language, setLanguage] = useState('en');
  const [translations, setTranslations] = useState<Translations>({});
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [authenticatedUser, setAuthenticatedUser] = useState('');
  const [showAbout, setShowAbout] = useState(false);
  const [showDashboard, setShowDashboard] = useState(false);
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load translations
  useEffect(() => {
    const loadTranslations = async () => {
      try {
        const response = await fetch(`/locales/${language}.json`);
        const data = await response.json();
        setTranslations(data);
      } catch (error) {
        console.error('Error loading translations:', error);
      }
    };
    loadTranslations();
  }, [language]);

  // Mount check
  useEffect(() => {
    setMounted(true);
    // Check if user is already authenticated in session
    const stored = sessionStorage.getItem('authenticated');
    const storedUser = sessionStorage.getItem('username');
    if (stored) {
      setIsAuthenticated(true);
      setAuthenticatedUser(storedUser || '');
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');

    if (!username || !password) {
      setLoginError('Please enter both username and password');
      return;
    }

    try {
      // Hash password with SHA256 and mod key (async)
      const hashedPassword = await hashPassword(password);

      const response = await axios.post(
        `${API_URL}/auth/login`,
        {
          username,
          password_hash: hashedPassword,
        }
      );

      if (response.data.success) {
        setIsAuthenticated(true);
        setAuthenticatedUser(username);
        setUsername('');
        setPassword('');
        // Store in session
        sessionStorage.setItem('authenticated', 'true');
        sessionStorage.setItem('username', username);
        sessionStorage.setItem('token', response.data.token || '');
      }
    } catch (error: any) {
      console.error('Login error:', error);
      setLoginError(error.response?.data?.detail || 'Authentication failed. Please check your credentials.');
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setAuthenticatedUser('');
    setMessages([]);
    setInput('');
    setShowDashboard(false);
    sessionStorage.removeItem('authenticated');
    sessionStorage.removeItem('username');
    sessionStorage.removeItem('token');
  };

  const fetchAnalytics = async () => {
    try {
      setAnalyticsLoading(true);
      const token = sessionStorage.getItem('token');
      const response = await axios.get(`${API_URL}/analytics`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setAnalyticsData(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const handleDashboard = () => {
    setShowDashboard(true);
    setMessages([]); // Clear chat messages when viewing dashboard
    fetchAnalytics();
  };

  const handleBack = () => {
    setMessages([]);
    setInput('');
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const t = (key: string): string => {
    const keys = key.split('.');
    let value: any = translations;
    for (const k of keys) {
      value = value?.[k];
    }
    return value || key;
  };

  const examples = [
    { key: 'examples.gdpr', icon: '📋' },
    { key: 'examples.psd2', icon: '💳' },
    { key: 'examples.aml', icon: '🔍' },
    { key: 'examples.mifid', icon: '📊' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      console.log('[API] Starting request...');
      console.log('[API] API_URL:', API_URL);
      console.log('[API] Full URL:', `/api/ask`);
      console.log('[API] Question:', input);
      
      const token = sessionStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/ask`,
        {
          question: input,
          top_k: 3,
        },
        { 
          timeout: 60000,
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          }
        }
      );

      console.log('[API] Response received:', response.status);
      console.log('[API] Response data:', response.data);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.data.answer,
        citations: response.data.citations || [],
        scores: response.data.scores || [],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('[API ERROR]', error);
      console.error('[API ERROR] message:', error.message);
      console.error('[API ERROR] code:', error.code);
      console.error('[API ERROR] response status:', error.response?.status);
      console.error('[API ERROR] response data:', error.response?.data);
      console.error('[API ERROR] request URL:', error.config?.url);
      
      let errorDetails = error.message || 'Unknown error';
      if (error.response?.status === 422) {
        errorDetails = 'Question validation failed - please use at least 5 characters';
        if (error.response?.data?.detail) {
          errorDetails = error.response.data.detail[0]?.msg || errorDetails;
        }
      } else if (error.response) {
        errorDetails = `Server error (${error.response.status}): ${error.response.statusText}`;
        if (error.response.data?.detail) {
          errorDetails = error.response.data.detail;
        }
      } else if (error.request) {
        errorDetails = 'No response from server - check if backend is running';
      } else if (error.code === 'ECONNABORTED') {
        errorDetails = 'Request timeout - backend took too long to respond';
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `${t('error')}: ${errorDetails}. ${t('tryAgain')}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleExampleClick = (text: string) => {
    setInput(text);
    inputRef.current?.focus();
  };

  const copyToClipboard = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // Show success feedback
      setCopiedMessageId(messageId);
      // Reset feedback after 2 seconds
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      // Fallback method for older browsers
      try {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        // Show success feedback
        setCopiedMessageId(messageId);
        setTimeout(() => setCopiedMessageId(null), 2000);
      } catch (fallbackError) {
        console.error('Fallback copy method also failed:', fallbackError);
        alert('Failed to copy to clipboard. Please try again.');
      }
    }
  };

  if (!mounted) {
    return null;
  }

  // Login Screen
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-secondary flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="rounded-lg border border-border bg-background p-8 shadow-lg">
            {/* Logo */}
            <div className="flex justify-center mb-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Lightbulb size={24} />
              </div>
            </div>

            {/* Title */}
            <h1 className="text-2xl font-bold text-center mb-2">
              Regulation Navigator
            </h1>
            <p className="text-center text-foreground/60 mb-6">
              Please login to continue
            </p>

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-4">
              {loginError && (
                <div className="rounded-lg bg-destructive/10 border border-destructive/30 p-3 flex gap-2">
                  <AlertCircle size={18} className="text-destructive flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-destructive">{loginError}</p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium mb-2">
                  Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username"
                  className="w-full rounded-lg border border-border bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:bg-secondary"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full rounded-lg border border-border bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:bg-secondary"
                />
              </div>

              <button
                type="submit"
                className="w-full rounded-lg bg-primary text-primary-foreground py-2 font-medium transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                Login
              </button>
            </form>

            {/* Theme Toggle */}
            <div className="flex justify-center mt-6 pt-6 border-t border-border">
              <button
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                className="rounded-lg border border-border p-2 transition-colors hover:bg-secondary"
              >
                {theme === 'dark' ? (
                  <Sun size={18} />
                ) : (
                  <Moon size={18} />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4 sm:py-6">
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Back Button - Show only when messages exist */}
            {messages.length > 0 && (
              <button
                onClick={handleBack}
                className="rounded-lg border border-border p-2 transition-colors hover:bg-secondary"
                title="Back to chat"
              >
                <ArrowLeft size={20} />
              </button>
            )}
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground sm:h-10 sm:w-10">
              <Lightbulb size={20} className="sm:w-6 sm:h-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold sm:text-2xl">
                {t('title')}
              </h1>
              {authenticatedUser && (
                <p className="text-xs sm:text-sm text-foreground/60">
                  Welcome, {authenticatedUser}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            {/* Language Selector */}
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="rounded-md border border-border bg-background px-2 py-2 text-sm sm:px-3 dark:bg-secondary"
            >
              <option value="en">🇬🇧 English</option>
              <option value="de">🇩🇪 Deutsch</option>
              <option value="es">🇪🇸 Español</option>
              <option value="pt">🇵🇹 Português</option>
              <option value="fr">🇫🇷 Français</option>
              <option value="nl">🇳🇱 Nederlands</option>
            </select>

            {/* Theme Toggle */}
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="rounded-lg border border-border p-2 transition-colors hover:bg-secondary"
              title={t('themeToggle')}
            >
              {theme === 'dark' ? (
                <Sun size={20} />
              ) : (
                <Moon size={20} />
              )}
            </button>

            {/* About Button */}
            <button
              onClick={() => setShowAbout(true)}
              className="rounded-lg border border-border p-2 transition-colors hover:bg-secondary"
              title={t('about')}
            >
              <AlertCircle size={20} />
            </button>

            {/* Dashboard Button */}
            <button
              onClick={handleDashboard}
              className="rounded-lg border border-border p-2 transition-colors hover:bg-secondary"
              title="Dashboard"
            >
              <BarChart3 size={20} />
            </button>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="rounded-lg border border-border p-2 transition-colors hover:bg-secondary text-destructive hover:border-destructive"
              title="Logout"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto flex max-w-4xl flex-col px-4 py-8 sm:py-12">
        {/* Dashboard View */}
        {showDashboard ? (
          <div className="space-y-8">
            {/* Back Button */}
            <button
              onClick={() => setShowDashboard(false)}
              className="flex items-center gap-2 text-primary hover:underline"
            >
              <ArrowLeft size={20} />
              Back to Chat
            </button>

            {/* Dashboard Title */}
            <div>
              <h1 className="text-4xl font-bold mb-2">Analytics Dashboard</h1>
              <p className="text-foreground/60">System metrics and EU regulatory intelligence</p>
            </div>

            {/* Loading State */}
            {analyticsLoading ? (
              <div className="flex justify-center items-center py-12">
                <Loader2 size={32} className="animate-spin" />
              </div>
            ) : analyticsData ? (
              <div className="space-y-6">
                {/* Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Total Queries */}
                  <div className="rounded-lg border border-border bg-secondary/50 p-6">
                    <div className="text-sm text-foreground/60 mb-2">Total Queries</div>
                    <div className="text-3xl font-bold">{analyticsData.total_queries || 0}</div>
                    <div className="text-xs text-foreground/50 mt-2">
                      Success Rate: {analyticsData.success_rate}%
                    </div>
                  </div>

                  {/* Successful Queries */}
                  <div className="rounded-lg border border-border bg-secondary/50 p-6">
                    <div className="text-sm text-foreground/60 mb-2">✓ Successful</div>
                    <div className="text-3xl font-bold text-green-600">{analyticsData.successful_queries || 0}</div>
                    <div className="text-xs text-foreground/50 mt-2">
                      Failed: {analyticsData.failed_queries || 0}
                    </div>
                  </div>

                  {/* Total Logins */}
                  <div className="rounded-lg border border-border bg-secondary/50 p-6">
                    <div className="text-sm text-foreground/60 mb-2">Total Logins</div>
                    <div className="text-3xl font-bold">{analyticsData.total_logins || 0}</div>
                    <div className="text-xs text-foreground/50 mt-2">
                      Uptime: {analyticsData.uptime_formatted}
                    </div>
                  </div>

                  {/* Avg Response Time */}
                  <div className="rounded-lg border border-border bg-secondary/50 p-6">
                    <div className="text-sm text-foreground/60 mb-2">Avg Response</div>
                    <div className="text-3xl font-bold">{analyticsData.avg_response_time_ms?.toFixed(0)}ms</div>
                    <div className="text-xs text-foreground/50 mt-2">
                      Last Hour: {analyticsData.query_distribution?.last_hour}
                    </div>
                  </div>
                </div>

                {/* Top Regulations */}
                {analyticsData.top_regulations && analyticsData.top_regulations.length > 0 && (
                  <div className="rounded-lg border border-border bg-secondary/50 p-6">
                    <h3 className="text-lg font-bold mb-4">Most Queried Regulations</h3>
                    <div className="space-y-2">
                      {analyticsData.top_regulations.slice(0, 5).map((reg: any, idx: number) => (
                        <div key={idx} className="flex justify-between items-center">
                          <span className="text-foreground/80">{reg.regulation}</span>
                          <span className="font-bold">{reg.queries}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* EU Regulatory Coverage */}
                {analyticsData.eu_regulatory_coverage && (
                  <div className="rounded-lg border border-border bg-secondary/50 p-6">
                    <h3 className="text-lg font-bold mb-4">EU Regulatory Directives Coverage</h3>
                    <p className="text-sm text-foreground/60 mb-4">Coverage Years: {analyticsData.coverage_years}</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.entries(analyticsData.eu_regulatory_coverage).map(([key, value]: [string, any]) => (
                        <div key={key} className="flex justify-between items-center p-3 bg-primary/5 rounded">
                          <span className="text-sm">{key}</span>
                          <span className="font-bold text-primary">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Latest Regulations */}
                {analyticsData.latest_regulations && (
                  <div className="rounded-lg border border-border bg-secondary/50 p-6">
                    <h3 className="text-lg font-bold mb-4">Latest Regulations (2023-2026)</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {analyticsData.latest_regulations.map((reg: string, idx: number) => (
                        <div key={idx} className="p-3 bg-primary/10 rounded text-sm text-center font-medium">
                          {reg}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Languages Used */}
                {analyticsData.languages_used && Object.keys(analyticsData.languages_used).length > 0 && (
                  <div className="rounded-lg border border-border bg-secondary/50 p-6">
                    <h3 className="text-lg font-bold mb-4">Language Distribution</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {Object.entries(analyticsData.languages_used).map(([lang, count]: [string, any]) => (
                        <div key={lang} className="p-3 bg-secondary rounded">
                          <div className="text-sm text-foreground/60 mb-1 capitalize">{lang}</div>
                          <div className="text-2xl font-bold">{count}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-foreground/60">Failed to load analytics data</p>
              </div>
            )}
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center space-y-8 py-12">
            {/* Welcome Section */}
            <div className="text-center animate-fade-in">
              <h2 className="text-3xl font-bold sm:text-4xl mb-3">
                {t('welcome')}
              </h2>
              <p className="text-lg text-foreground/60 max-w-md">
                {t('description')}
              </p>
            </div>

            {/* Examples Grid */}
            <div className="grid w-full grid-cols-1 gap-3 sm:grid-cols-2 md:gap-4">
              {examples.map((example) => (
                <button
                  key={example.key}
                  onClick={() => handleExampleClick(t(example.key))}
                  className="group flex items-center gap-3 rounded-lg border border-border p-4 transition-all hover:border-primary hover:bg-secondary"
                >
                  <span className="text-2xl">{example.icon}</span>
                  <div className="flex-1 text-left">
                    <p className="font-medium group-hover:text-primary">
                      {t(example.key)}
                    </p>
                  </div>
                  <ChevronRight size={20} className="text-foreground/40" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Messages Section */
          <div className="space-y-4 mb-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`animate-slide-up flex ${
                  message.type === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-xs sm:max-w-lg lg:max-w-2xl rounded-lg p-4 ${
                    message.type === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-foreground border border-border'
                  }`}
                >
                  <p className="text-sm sm:text-base">{message.content}</p>

                  {/* Citations */}
                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-3 space-y-2 border-t border-border pt-3">
                      <p className="text-xs font-semibold opacity-70">
                        {t('sources')}:
                      </p>
                      {message.citations.map((citation, idx) => (
                        <div
                          key={idx}
                          className="text-xs p-2 rounded bg-background/50 break-words"
                        >
                          <p className="font-medium">{citation.doc}</p>
                          <p className="opacity-70">{citation.section}</p>
                          {message.scores && message.scores[idx] !== undefined && (
                            <p className="text-xs opacity-50 mt-1">
                              {t('relevance')}: {(message.scores[idx] * 100).toFixed(0)}%
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Action Buttons */}
                  {message.type === 'assistant' && (
                    <div className="mt-3 flex gap-2 flex-wrap">
                      <button
                        onClick={() => copyToClipboard(message.content, message.id)}
                        className={`flex items-center gap-1 rounded px-2 py-1 text-xs transition-colors ${
                          copiedMessageId === message.id
                            ? 'bg-green-600/30 text-green-600 border border-green-600'
                            : 'hover:bg-background/30'
                        }`}
                        title="Copy message to clipboard"
                      >
                        <Copy size={14} />
                        <span>{copiedMessageId === message.id ? 'Copied!' : t('copy')}</span>
                      </button>
                      <button
                        onClick={async () => {
                          const text = `${message.content}\n\nSources: ${message.citations?.map((c) => c.doc).join(', ')}`;
                          if (navigator.share) {
                            try {
                              await navigator.share({ title: t('title'), text });
                            } catch (error: any) {
                              if (error.name !== 'AbortError') {
                                console.error('Share failed:', error);
                                // Fallback to copy if share fails
                                copyToClipboard(text, message.id);
                              }
                            }
                          } else {
                            // Fallback to copy if native share is not available
                            copyToClipboard(text, message.id);
                          }
                        }}
                        className="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-background/30 transition-colors"
                        title="Share message or copy if sharing is not available"
                      >
                        <Share2 size={14} />
                        <span>{t('share')}</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start animate-slide-up">
                <div className="flex gap-2 rounded-lg bg-secondary border border-border p-4">
                  <Loader2 size={20} className="animate-spin" />
                  <p className="text-sm">{t('loading')}</p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Input Section */}
      <footer className="sticky bottom-0 border-t border-border bg-background/95 backdrop-blur">
        <div className="mx-auto max-w-4xl px-4 py-4 sm:py-6">
          <form onSubmit={handleSubmit} className="flex gap-2 sm:gap-3">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t('placeholder')}
              disabled={loading}
              autoFocus
              className="flex-1 rounded-lg border border-border bg-background px-4 py-3 text-sm sm:text-base placeholder-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 dark:bg-secondary"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="rounded-lg bg-primary text-primary-foreground px-4 py-3 transition-opacity hover:opacity-90 disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <Send size={20} />
              )}
              <span className="hidden sm:inline">{t('askButton')}</span>
            </button>
          </form>

          {/* Footer Text */}
          <p className="mt-3 text-center text-xs sm:text-sm text-foreground/50">
            {t('footer')}
          </p>
        </div>
      </footer>

      {/* About Modal */}
      {showAbout && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background border border-border rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 flex items-center justify-between p-6 border-b border-border bg-background">
              <h2 className="text-2xl font-bold">{t('aboutModal.title')}</h2>
              <button
                onClick={() => setShowAbout(false)}
                className="rounded-lg border border-border p-2 transition-colors hover:bg-secondary"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Why Section */}
              <div>
                <h3 className="text-lg font-semibold mb-3 text-primary">{t('aboutModal.why')}</h3>
                <p className="text-foreground/80 whitespace-pre-wrap">{t('aboutModal.whyText')}</p>
              </div>

              {/* How It Works Section */}
              <div>
                <h3 className="text-lg font-semibold mb-3 text-primary">{t('aboutModal.how')}</h3>
                
                <div className="space-y-4">
                  {/* Functional */}
                  <div>
                    <h4 className="font-medium mb-2">{t('aboutModal.functional')}</h4>
                    <p className="text-sm text-foreground/80 whitespace-pre-wrap bg-secondary p-3 rounded-lg">{t('aboutModal.functionalText')}</p>
                  </div>

                  {/* Technical */}
                  <div>
                    <h4 className="font-medium mb-2">{t('aboutModal.technical')}</h4>
                    <p className="text-sm text-foreground/80 whitespace-pre-wrap bg-secondary p-3 rounded-lg">{t('aboutModal.technicalText')}</p>
                  </div>
                </div>
              </div>

              {/* For Whom Section */}
              <div>
                <h3 className="text-lg font-semibold mb-3 text-primary">{t('aboutModal.forWhom')}</h3>
                <p className="text-sm text-foreground/80 whitespace-pre-wrap bg-secondary p-3 rounded-lg">{t('aboutModal.forWhomText')}</p>
              </div>

              {/* Features Section */}
              <div>
                <h3 className="text-lg font-semibold mb-3 text-primary">{t('aboutModal.features')}</h3>
                <p className="text-sm text-foreground/80 whitespace-pre-wrap bg-secondary p-3 rounded-lg">{t('aboutModal.featuresText')}</p>
              </div>

              {/* Coverage Section */}
              <div>
                <h3 className="text-lg font-semibold mb-3 text-primary">{t('aboutModal.coverage')}</h3>
                <p className="text-sm text-foreground/80 whitespace-pre-wrap bg-secondary p-3 rounded-lg">{t('aboutModal.coverageText')}</p>
              </div>

              {/* Close Button */}
              <button
                onClick={() => setShowAbout(false)}
                className="w-full rounded-lg bg-primary text-primary-foreground py-2 font-medium transition-opacity hover:opacity-90 mt-4"
              >
                {t('close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
