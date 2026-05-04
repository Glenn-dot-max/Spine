import api from "./client";
import type { Campaign, CampaignContact } from "../types";

export const getCampaigns = async (): Promise<Campaign[]> => {
  const res = await api.get("/api/campaigns/");
  return res.data;
};

export const getCampaign = async (id: number): Promise<Campaign> => {
  const res = await api.get(`/api/campaigns/${id}/`);
  return res.data;
};

export const createCampaign = async (
  data: Partial<Campaign>,
): Promise<Campaign> => {
  const res = await api.post("/api/campaigns/", data);
  return res.data;
};

export const updateCampaign = async (
  id: number,
  data: Partial<Campaign>,
): Promise<Campaign> => {
  const res = await api.put(`/api/campaigns/${id}/`, data);
  return res.data;
};

export const deleteCampaign = async (id: number): Promise<void> => {
  await api.delete(`/api/campaigns/${id}/`);
};

export const getCampaignContacts = async (
  id: number,
): Promise<CampaignContact[]> => {
  const res = await api.get(`/api/campaigns/${id}/contacts/`);
  return res.data;
};

export const addContactToCampaign = async (
  campaignId: number,
  prospectId: number,
): Promise<void> => {
  await api.post(
    `/api/campaigns/${campaignId}/contacts?prospect_id=${prospectId}`,
  );
};

export const sendInitialEmails = async (campaignId: number): Promise<void> => {
  await api.post(`/api/campaigns/${campaignId}/emails/send-initial`);
};

export const getScheduledFollowups = async (campaignId: number) => {
  const res = await api.get(`/api/campaigns/${campaignId}/followups/scheduled`);
  return res.data;
};

export const sendDueFollowups = async (campaignId: number): Promise<void> => {
  await api.post(`/api/campaigns/${campaignId}/followups/send-due`);
};
