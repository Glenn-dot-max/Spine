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

  // Source
  campaign_source: "trade_show" | "ride_along" | "outreach";

  // Distributor context
  is_distributor_show: boolean;
  distributor_company_id?: number;
  auto_cc_sales_rep: boolean;

  // Content blocks
  company_intro_text?: string;
  catalog_pitch_text?: string;
  offer_samples: boolean;
  samples_note?: string;

  // Segment notes
  segment_note_global?: string;
  segment_note_restaurant?: string;
  segment_note_industry?: string;
  segment_note_retail?: string;

  // Sequence
  followup_delay_1: number;
  followup_delay_2: number;
  followup_delay_3: number;

  // Computed
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

export interface Product {
  id: number;
  item_number: string;
  name: string;
  brand?: string;
  short_description?: string;
  category?: string;
  formats?: string;
  price_range?: string;
  certifications?: string;
  segment?: string;
  is_active: boolean;
}

export interface DistributorCatalogItem {
  id: number;
  catalog_id: number;
  product_id: number;
  notes?: string;
  is_active: boolean;
  product_name?: string;
  product_item_number?: string;
  product_brand?: string;
  product_category?: string;
}

export interface DistributorCatalog {
  id: number;
  company_id?: number;
  name: string;
  notes?: string;
  item_count?: number;
  items?: DistributorCatalogItem[];
  pdf_filename?: string;
  has_pdf?: boolean;
}
