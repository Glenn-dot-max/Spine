import api from "./client";
import type { Company } from "../types";

export const getCompanies = async (): Promise<Company[]> => {
  const res = await api.get("/api/companies");
  return res.data;
};

export const createCompany = async (
  data: Partial<Company>,
): Promise<Company> => {
  const res = await api.post("/api/companies", data);
  return res.data;
};

export const updateCompany = async (
  id: number,
  data: Partial<Company>,
): Promise<Company> => {
  const res = await api.put(`/api/companies/${id}`, data);
  return res.data;
};

export const deleteCompany = async (id: number): Promise<void> => {
  await api.delete(`/api/companies/${id}`);
};

export interface CompanyContact {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  position: string;
}

/** Retourne uniquement les companies qualifiées comme distributor */
export const getDistributors = async (): Promise<Company[]> => {
  const res = await api.get("/api/companies/", {
    params: { chain_level: "distributor" },
  });
  return res.data;
};

/** Retourne les contacts (prospects) rattachés à une company */
export const getCompanyContacts = async (
  companyId: number,
): Promise<CompanyContact[]> => {
  const res = await api.get(`/api/companies/${companyId}/contacts`);
  return res.data;
};
