import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import MapView from './pages/MapView';
import LocationDetail from './pages/LocationDetail';
import LocationsList from './pages/LocationsList';
import TrendsPage from './pages/TrendsPage';
import './index.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/map" element={<MapView />} />
          <Route path="/locations" element={<LocationsList />} />
          <Route path="/location/:id" element={<LocationDetail />} />
          <Route path="/trends" element={<TrendsPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
