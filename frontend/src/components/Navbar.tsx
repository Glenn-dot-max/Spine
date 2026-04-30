import { Link, useLocation, useNavigate } from "react-router-dom";

function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  const isActive = (path: string) =>
    location.pathname === path
      ? "text-blue-600 font-semibold border-b-2 border-blue-600"
      : "text-gray-600 hover:text-gray-900";

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-8">
            <h1 className="text-xl font-bold text-blue-800">🦴 Spine CRM</h1>

            {/* Liens de navigation */}
            <div className="flex space-x-6">
              <Link to="/" className={`px-2 py-2 ${isActive("/")}`}>
                Dashboard
              </Link>
              <Link
                to="/campaigns"
                className={`px-2 py-2 ${isActive("/campaigns")}`}
              >
                Campagnes
              </Link>
              <Link
                to="/prospects"
                className={`px-2 py-2 ${isActive("/prospects")}`}
              >
                Prospects
              </Link>
              <Link
                to="/settings"
                className={`px-2 py-2 ${isActive("/settings")}`}
              >
                ⚙️ Paramètres
              </Link>
            </div>
          </div>

          {/* Bouton de déconnexion */}
          <button
            onClick={handleLogout}
            className="text-sm text-red-500 hover:text-red-700 font-medium"
          >
            Déconnexion
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
