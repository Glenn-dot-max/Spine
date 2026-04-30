import api from "./client";
import type { User } from "../types";

export const login = async (
  email: string,
  password: string,
): Promise<string> => {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const res = await api.post("/api/auth/login", formData, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data.access_token;
};

export const getMe = async (): Promise<User> => {
  const res = await api.get("/api/auth/me");
  return res.data;
};
