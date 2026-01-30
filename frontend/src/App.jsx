import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Sender from './pages/Sender';
import Receiver from './pages/Receiver';
import { User, Lock } from 'lucide-react';

const Home = () => (
  <div className="container-center">
    <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
      <h1 className="title-gradient" style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>
        FaceLock
      </h1>
      <p className="subtitle" style={{ fontSize: '1.25rem' }}>Secure Biometric Data Transmission</p>
    </div>

    <div className="grid-2" style={{ maxWidth: '800px', width: '100%' }}>
      <Link to="/sender" style={{ textDecoration: 'none' }}>
        <div className="home-card">
          <div className="icon-circle">
            <Lock size={48} />
          </div>
          <h2 style={{ color: 'white', fontSize: '1.5rem', fontWeight: 'bold' }}>Sender Mode</h2>
          <p style={{ color: '#94a3b8' }}>Enroll your face and encrypt confidential messages.</p>
        </div>
      </Link>

      <Link to="/receiver" style={{ textDecoration: 'none' }}>
        <div className="home-card">
          <div className="icon-circle" style={{ background: 'rgba(34, 211, 238, 0.2)', color: '#22d3ee' }}>
            <User size={48} />
          </div>
          <h2 style={{ color: 'white', fontSize: '1.5rem', fontWeight: 'bold' }}>Receiver Mode</h2>
          <p style={{ color: '#94a3b8' }}>Verify identity via webcam to decrypt content.</p>
        </div>
      </Link>
    </div>
  </div>
);

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/sender" element={<Sender />} />
        <Route path="/receiver" element={<Receiver />} />
      </Routes>
    </Router>
  );
}

export default App;
