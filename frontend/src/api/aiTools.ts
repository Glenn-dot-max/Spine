/**
 * SPINE V1 - aiTools API client
 * Role: On-demand AI calls from the frontend
 * Dependencies: api client
 * Last modified: 2024-06-22 - creation
 */
import api from "./client";

export const improveEmail = async (body: string): Promise<string> => {
  const res = await api.post("/api/ai/improve-email", { body });
  return res.data.improved_body;
};
