import { useState, useEffect } from "react";
import api from "../api/client";

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
    } catch {
      setMessage({ type: "error", text: "Error connecting Gmail ❌" });
    }
  };

  const connectOutlook = async () => {
    try {
      const response = await api.get("/oauth/outlook/connect");
      window.location.href = response.data.auth_url;
    } catch {
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
    } catch {
      setMessage({ type: "error", text: "Error disconnecting ❌" });
    }
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <h2 className="text-2xl font-bold text-gray-800">Email Settings</h2>

      {/* Message */}
      {message && (
        <div
          className={`px-4 py-3 rounded text-sm ${
            message.type === "success"
              ? "bg-green-50 text-green-700"
              : "bg-red-50 text-red-700"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Gmail */}
      <div className="bg-white shadow-sm rounded-lg p-6 border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-red-500 text-white rounded-full flex items-center justify-center font-bold text-lg">
              G
            </div>
            <div>
              <h3 className="text-lg font-semibold">Gmail</h3>
              {status?.gmail.connected ? (
                <p className="text-sm text-gray-600">
                  Connected:{" "}
                  <span className="font-medium">{status.gmail.email}</span>
                  {status.default_provider === "gmail" && (
                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      Default
                    </span>
                  )}
                </p>
              ) : (
                <p className="text-sm text-gray-500">Not connected</p>
              )}
            </div>
          </div>
          {status?.gmail.connected ? (
            <button
              onClick={() => disconnect("gmail")}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm"
            >
              Disconnect
            </button>
          ) : (
            <button
              onClick={connectGmail}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition text-sm"
            >
              Connect Gmail
            </button>
          )}
        </div>
      </div>

      {/* Outlook */}
      <div className="bg-white shadow-sm rounded-lg p-6 border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold text-lg">
              O
            </div>
            <div>
              <h3 className="text-lg font-semibold">Outlook</h3>
              {status?.outlook.connected ? (
                <p className="text-sm text-gray-600">
                  Connected:{" "}
                  <span className="font-medium">{status.outlook.email}</span>
                  {status.default_provider === "outlook" && (
                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      Default
                    </span>
                  )}
                </p>
              ) : (
                <p className="text-sm text-gray-500">Not connected</p>
              )}
            </div>
          </div>
          {status?.outlook.connected ? (
            <button
              onClick={() => disconnect("outlook")}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm"
            >
              Disconnect
            </button>
          ) : (
            <button
              onClick={connectOutlook}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm"
            >
              Connect Outlook
            </button>
          )}
        </div>
      </div>

      {/* Warning */}
      {!status?.gmail.connected && !status?.outlook.connected && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-yellow-800 text-sm">
            ⚠️ You must connect at least one email account to send emails.
          </p>
        </div>
      )}
    </div>
  );
};

export default Settings;
