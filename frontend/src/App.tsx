import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Settings from "./pages/Settings";
import Prospects from "./pages/Prospects";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm border-b">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-8">
                <h1 className="text-xl font-bold text-gray-800">Spine CRM</h1>
                <div className="flex space-x-4">
                  <Link
                    to="/"
                    className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md"
                  >
                    Prospects
                  </Link>
                  <Link
                    to="/settings"
                    className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md"
                  >
                    ⚙️ Settings
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </nav>

        {/* Content */}
        <Routes>
          <Route path="/" element={<Prospects />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
