import React, { useEffect, useMemo, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, Outlet } from 'react-router-dom';
import './App.css';
import Dashboard from './pages/Dashboard';
import AdminsPage from './pages/AdminsPage';
import CategoriesPage from './pages/CategoriesPage';
import SubscriptionsPage from './pages/SubscriptionsPage';
import CustomersPage from './pages/CustomersPage';
import ProductsPage from './pages/ProductsPage';
import AuthPage from './pages/AuthPage';
import UserDashboard from './pages/UserDashboard';
import LandingPage from './pages/LandingPage';
import UserDeliveryPage from './pages/UserDeliveryPage';
import UserOrdersPage from './pages/UserOrdersPage';
import UserNotificationsPage from './pages/UserNotificationsPage';
import UserSupportPage from './pages/UserSupportPage';
import UserProfilePage from './pages/UserProfilePage';
import UserOffersPage from './pages/UserOffersPage';
import { authService } from './services/api';

const getDashboardPath = (role) => (role === 'admin' ? '/admin/dashboard' : '/user/dashboard');

function ProtectedRoute({ authUser }) {
  if (!authUser) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}

function RoleRoute({ authUser, allowedRole, children }) {
  if (!authUser) {
    return <Navigate to="/" replace />;
  }
  if (authUser.role !== allowedRole) {
    return <Navigate to={getDashboardPath(authUser.role)} replace />;
  }
  return children;
}

function MainLayout({ authUser, onLogout, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navItems = useMemo(() => {
    if (authUser?.role === 'admin') {
      return [
        { to: '/admin/dashboard', label: 'Dashboard', icon: 'DB' },
        { to: '/admins', label: 'Admins', icon: 'AD' },
        { to: '/categories', label: 'Categories', icon: 'CT' },
        { to: '/subscriptions', label: 'Subscriptions', icon: 'SB' },
        { to: '/customers', label: 'Customers', icon: 'CU' },
        { to: '/products', label: 'Products', icon: 'PD' },
      ];
    }

    return [
      { to: '/user/dashboard', label: 'Dashboard', icon: 'DB' },
      { to: '/user/delivery', label: 'Delivery', icon: 'DL' },
      { to: '/user/orders', label: 'Orders', icon: 'OR' },
      { to: '/user/notifications', label: 'Alerts', icon: 'NT' },
      { to: '/user/support', label: 'Support', icon: 'SP' },
      { to: '/user/profile', label: 'Profile', icon: 'PR' },
      { to: '/user/offers', label: 'Offers', icon: 'OF' },
    ];
  }, [authUser]);

  return (
    <div className="app-container">
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>MilkMan</h2>
          <button
            type="button"
            className="toggle-btn"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            III
          </button>
        </div>

        <div className="sidebar-user">
          <div>{authUser?.first_name} {authUser?.last_name}</div>
          <small>{authUser?.role === 'admin' ? 'Admin' : 'User'}</small>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <Link key={item.to} to={item.to} className="nav-item">
              <span className="icon">{item.icon}</span>
              {sidebarOpen && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>

        <button type="button" className="logout-btn" onClick={onLogout}>
          Logout
        </button>
      </aside>

      <main className="main-content">{children}</main>
    </div>
  );
}

function App() {
  const [authUser, setAuthUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    const bootstrapAuth = async () => {
      try {
        const response = await authService.me();
        setAuthUser(response.data.user || null);
      } catch (error) {
        setAuthUser(null);
      } finally {
        setAuthLoading(false);
      }
    };

    bootstrapAuth();
  }, []);

  const handleLogin = async (payload) => {
    const response = await authService.login(payload);
    setAuthUser(response.data.user);
  };

  const handleSignup = async (payload) => {
    const response = await authService.signup(payload);
    setAuthUser(response.data.user);
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      // Ignore API errors during logout and still clear client auth state.
    } finally {
      setAuthUser(null);
    }
  };

  if (authLoading) {
    return <div className="app-loading">Loading...</div>;
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            authUser
              ? <Navigate to={getDashboardPath(authUser.role)} replace />
              : <LandingPage onLogin={handleLogin} onSignup={handleSignup} />
          }
        />

        <Route
          path="/auth"
          element={
            authUser
              ? <Navigate to={getDashboardPath(authUser.role)} replace />
              : <AuthPage onLogin={handleLogin} onSignup={handleSignup} />
          }
        />

        <Route element={<ProtectedRoute authUser={authUser} />}>
          <Route
            path="/admin/dashboard"
            element={(
              <RoleRoute authUser={authUser} allowedRole="admin">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <Dashboard />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/admins"
            element={(
              <RoleRoute authUser={authUser} allowedRole="admin">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <AdminsPage />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/categories"
            element={(
              <RoleRoute authUser={authUser} allowedRole="admin">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <CategoriesPage />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/subscriptions"
            element={(
              <RoleRoute authUser={authUser} allowedRole="admin">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <SubscriptionsPage />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/customers"
            element={(
              <RoleRoute authUser={authUser} allowedRole="admin">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <CustomersPage />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/products"
            element={(
              <RoleRoute authUser={authUser} allowedRole="admin">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <ProductsPage />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/user/dashboard"
            element={(
              <RoleRoute authUser={authUser} allowedRole="user">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <UserDashboard authUser={authUser} />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/user/delivery"
            element={(
              <RoleRoute authUser={authUser} allowedRole="user">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <UserDeliveryPage authUser={authUser} />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/user/orders"
            element={(
              <RoleRoute authUser={authUser} allowedRole="user">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <UserOrdersPage authUser={authUser} />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/user/reorder"
            element={<Navigate to="/user/orders" replace />}
          />
          <Route
            path="/user/notifications"
            element={(
              <RoleRoute authUser={authUser} allowedRole="user">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <UserNotificationsPage authUser={authUser} />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/user/support"
            element={(
              <RoleRoute authUser={authUser} allowedRole="user">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <UserSupportPage authUser={authUser} />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/user/profile"
            element={(
              <RoleRoute authUser={authUser} allowedRole="user">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <UserProfilePage authUser={authUser} />
                </MainLayout>
              </RoleRoute>
            )}
          />
          <Route
            path="/user/offers"
            element={(
              <RoleRoute authUser={authUser} allowedRole="user">
                <MainLayout authUser={authUser} onLogout={handleLogout}>
                  <UserOffersPage authUser={authUser} />
                </MainLayout>
              </RoleRoute>
            )}
          />
        </Route>

        <Route
          path="*"
          element={<Navigate to={authUser ? getDashboardPath(authUser.role) : '/'} replace />}
        />
      </Routes>
    </Router>
  );
}

export default App;
