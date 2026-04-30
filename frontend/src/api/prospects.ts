import api from "./client";
import type { Prospect } from "../types";

export const getProspects = async (): Promise<Prospect[]> => {
  const res = await api.get("/api/prospects/");
  return res.data;
};

export const createProspect = async (
  data: Partial<Prospect>,
): Promise<Prospect> => {
  const res = await api.post("/api/prospects/", data);
  return res.data;
};

export const deleteProspect = async (id: number): Promise<void> => {
  await api.delete(`/api/prospects/${id}/`);
};
