'use client';

import Link from 'next/link';
import { Search, Upload, User, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import styles from './Header.module.css';

export default function Header() {
  const { user, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      window.location.href = `/?q=${encodeURIComponent(searchQuery)}`;
    }
  };

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        {/* Logo */}
        <Link href="/" className={styles.logo}>
          <span className={styles.logoIcon}>▶</span>
          <span className={styles.logoText}>VideoHub</span>
        </Link>

        {/* Search */}
        <form className={styles.searchForm} onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="動画を検索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
          <button type="submit" className={styles.searchBtn}>
            <Search size={20} />
          </button>
        </form>

        {/* Actions */}
        <div className={styles.actions}>
          {user ? (
            <>
              <Link href="/upload" className={styles.uploadBtn}>
                <Upload size={20} />
                <span>アップロード</span>
              </Link>
              <div className={styles.userMenu}>
                <button className={styles.avatarBtn}>
                  <div className={styles.avatar}>
                    {user.icon_url ? (
                      <img src={user.icon_url} alt={user.display_name} />
                    ) : (
                      <User size={20} />
                    )}
                  </div>
                </button>
                <div className={styles.dropdown}>
                  <div className={styles.dropdownUser}>
                    <strong>{user.display_name}</strong>
                    <span>{user.email}</span>
                  </div>
                  <hr />
                  <button onClick={logout}>ログアウト</button>
                </div>
              </div>
            </>
          ) : (
            <Link href="/auth/login" className="btn btn-primary">
              ログイン
            </Link>
          )}
          
          <button 
            className={styles.menuBtn} 
            onClick={() => setShowMobileMenu(!showMobileMenu)}
          >
            {showMobileMenu ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {showMobileMenu && (
        <div className={styles.mobileMenu}>
          <form onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="動画を検索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input"
            />
          </form>
          {user ? (
            <>
              <Link href="/upload">アップロード</Link>
              <button onClick={logout}>ログアウト</button>
            </>
          ) : (
            <Link href="/auth/login">ログイン</Link>
          )}
        </div>
      )}
    </header>
  );
}
