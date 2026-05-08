import api from "./client";

export const getTemplates = () => api.get("/api/templates").then((r) => r.data);

export const createTemplate = (data: {
  name: string;
  category: string;
  subject_template: string;
  body_template: string;
}) => api.post("/api/templates", data).then((r) => r.data);

export const updateTemplate = (
  id: number,
  data: {
    name?: string;
    subject_template?: string;
    body_template?: string;
  },
) => api.put(`/api/templates/${id}`, data).then((r) => r.data);

export const deleteTemplate = (id: number) =>
  api.delete(`/api/templates/${id}`);
