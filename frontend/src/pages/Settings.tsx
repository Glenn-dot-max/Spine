import { useState, useEffect } from "react";
import api from "../services/api";

interface OAuthStatus {
  gmail: {
    connected: boolean;
    email: string | null;
  };
  outlook: {
    connected: boolean;
    email: string | null;
  };
  default_provider: string | null;
}

const Settings = () => {
  const [status, setStatus] = useState<OAuthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const loadStatus = async () => {
    try {
      const response = await api.get("/oauth/status");
      setStatus(response.data);
    } catch (error) {
      console.error("Failed to load OAuth status:", error);
      setMessage({
        type: "error",
        text: "Failed to load settings. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const oauth = params.get("oauth");
    const statusParam = params.get("status");

    if (oauth && statusParam) {
      if (statusParam === "success") {
        setMessage({
          type: "success",
          text: `${oauth.toUpperCase()} connected successfully! ✅`,
        });
      } else {
        const errorMsg = params.get("message") || "Unknown error";
        setMessage({
          type: "error",
          text: `${oauth.toUpperCase()} connection failed: ${errorMsg} ❌`,
        });
      }
      window.history.replaceState({}, "", "/settings");
    }

    loadStatus();
  }, []);

  const connectGmail = async () => {
    try {
      const response = await api.get("/oauth/gmail/connect");
      window.location.href = response.data.auth_url;
    } catch (error) {
      setMessage({ type: "error", text: "Error connecting Gmail ❌" });
    }
  };

  const connectOutlook = async () => {
    try {
      const response = await api.get("/oauth/outlook/connect");
      window.location.href = response.data.auth_url;
    } catch (error) {
      setMessage({ type: "error", text: "Error connecting Outlook ❌" });
    }
  };

  const disconnect = async (provider: "gmail" | "outlook") => {
    if (!window.confirm(`Disconnect ${provider.toUpperCase()}?`)) return;

    try {
      await api.post(`/oauth/disconnect/${provider}`);
      setMessage({
        type: "success",
        text: `${provider.toUpperCase()} disconnected successfully! ✅`,
      });
      loadStatus();
    } catch (error) {
      setMessage({ type: "error", text: `Error disconnecting ❌` });
    }
  };

  if (loading) {
    return <div className="container mx-auto p-8">Loading...</div>;
  }

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">Email Settings</h1>

      {message && (
        <div
          className={`mb-6 p-4 rounded ${
            message.type === "success"
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Gmail */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-red-500 text-white rounded-full flex items-center justify-center font-bold">
              G
            </div>
            <div>
              <h2 className="text-xl font-semibold">Gmail</h2>
              {status?.gmail.connected ? (
                <p className="text-sm text-gray-600">
                  Connected:{" "}
                  <span className="font-medium">{status.gmail.email}</span>
                  {status.default_provider === "gmail" && (
                    <span className="m1-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      Default
                    </span>
                  )}
                </p>
              ) : (
                <p className="text-sm text-gray-500">Not connected</p>
              )}
            </div>
          </div>
          <div>
            {status?.gmail.connected ? (
              <button
                onClick={() => disconnect("gmail")}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
              >
                Disconnect
              </button>
            ) : (
              <button
                onClick={connectGmail}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition"
              >
                Connect Gmail
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Outlook */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">
              O
            </div>
            <div>
              <h2 className="text-xl font-semibold">Outlook</h2>
              {status?.outlook.connected ? (
                <p className="text-sm text-gray-600">
                  Connected:{" "}
                  <span className="font-medium">{status.outlook.email}</span>
                  {status.default_provider === "outlook" && (
                    <span className="m1-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      Default
                    </span>
                  )}
                </p>
              ) : (
                <p className="text-sm text-gray-500">Not connected</p>
              )}
            </div>
          </div>
          <div>
            {status?.outlook.connected ? (
              <button
                onClick={() => disconnect("outlook")}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
              >
                Disconnect
              </button>
            ) : (
              <button
                onClick={connectOutlook}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
              >
                Connect Outlook
              </button>
            )}
          </div>
        </div>
      </div>

      {!status?.gmail.connected && !status?.outlook.connected && (
        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-yellow-800">
            ⚠️ You must connext at least one email account to send emails.
          </p>
        </div>
      )}
    </div>
  );
};

export default Settings;
