import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import Navbar from './components/Layout/Navbar';
import Dashboard from './pages/Dashboard';
import Scanner from './pages/Scanner';
import Profile from './pages/Profile';
import ProductAnalysis from './pages/ProductAnalysis';
import History from './pages/History';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import './App.css';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  
  if (loading) return <div className="loading-spinner">Loading...</div>;
  
  return user ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Router>
          <div className="App">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/*" element={
                <ProtectedRoute>
                  <Navbar />
                  <main className="main-content">
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/scanner" element={<Scanner />} />
                      <Route path="/profile" element={<Profile />} />
                      <Route path="/analysis/:scanId" element={<ProductAnalysis />} />
                      <Route path="/history" element={<History />} />
                    </Routes>
                  </main>
                </ProtectedRoute>
              } />
            </Routes>
          </div>
        </Router>
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;