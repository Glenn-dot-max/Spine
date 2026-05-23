export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  gmail_connected: boolean;
  outlook_connected: boolean;
}

export interface Campaign {
  id: number;
  name: string;
  event_date: string;
  end_date?: string;
  location?: string;
  distributor_name?: string;
  description?: string;
  status: "upcoming" | "active" | "completed";
  followup_delay_1: number;
  followup_delay_2: number;
  followup_delay_3: number;
  contact_count: number;
  product_count: number;
}

export interface Prospect {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  company_name?: string;
  position?: string;
  phone_number?: string;
  source: string;
  status: string;
}

export interface CampaignContact {
  prospect_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string;
  company_name?: string;
  position?: string;
  status: string;
  email_sequence_step: number;
  last_email_sent_at?: string;
  next_followup_scheduled_at?: string;
  notes?: string;
}

export interface Product {
  id: number;
  item_number: string;
  name: string;
  short_description?: string;
}

export interface Company {
  id: number;
  user_id: number;
  name: string;
  market?: string;
  website?: string;
  notes?: string;
  type_structure?: "retail" | "foodservice" | "industry" | "other";
  type_contact?:
    | "distributor"
    | "restaurant"
    | "factory"
    | "consultant"
    | "retailer"
    | "other";
  created_at: string;
  updated_at: string;
}
