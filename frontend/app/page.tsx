'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useTheme } from 'next-themes';
import axios from 'axios';
import {
  Sun,
  Moon,
  Send,
  Loader2,
  Copy,
  Share2,
  Globe,
  ChevronRight,
  AlertCircle,
  Lightbulb,
  LogOut,
  ArrowLeft,
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

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
        `http://localhost:8000/auth/login`,
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
    sessionStorage.removeItem('authenticated');
    sessionStorage.removeItem('username');
    sessionStorage.removeItem('token');
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
        `/api/ask`,
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

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
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

            {/* Footer */}
            <p className="text-center text-xs text-foreground/50 mt-6">
              Demo Credentials:<br/>
              Username: <span className="font-mono">Muthu</span><br/>
              Password: <span className="font-mono">Amsterdam@2025</span>
            </p>

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
        {messages.length === 0 ? (
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
                        onClick={() => copyToClipboard(message.content)}
                        className="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-background/30 transition-colors"
                      >
                        <Copy size={14} />
                        <span>{t('copy')}</span>
                      </button>
                      <button
                        onClick={() => {
                          const text = `${message.content}\n\nSources: ${message.citations?.map((c) => c.doc).join(', ')}`;
                          navigator.share &&
                            navigator.share({ title: t('title'), text });
                        }}
                        className="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-background/30 transition-colors"
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
    </div>
  );
}
