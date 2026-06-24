--
-- PostgreSQL database dump
--

\restrict GUHEeqoD0ZljDOQ0NK72QzageOSI8qfeRsNtQOf2TYJ7Voi464CgoNr1CQH8J4Q

-- Dumped from database version 16.13
-- Dumped by pg_dump version 16.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: campaignsource; Type: TYPE; Schema: public; Owner: spine
--

CREATE TYPE public.campaignsource AS ENUM (
    'trade_show',
    'ride_along',
    'outreach'
);


ALTER TYPE public.campaignsource OWNER TO spine;

--
-- Name: chainlevel; Type: TYPE; Schema: public; Owner: spine
--

CREATE TYPE public.chainlevel AS ENUM (
    'distributor',
    'importer',
    'broker',
    'end_user',
    'other'
);


ALTER TYPE public.chainlevel OWNER TO spine;

--
-- Name: endusertype; Type: TYPE; Schema: public; Owner: spine
--

CREATE TYPE public.endusertype AS ENUM (
    'restaurant',
    'hotel',
    'franchise',
    'country_club',
    'catering',
    'institution',
    'retail',
    'other'
);


ALTER TYPE public.endusertype OWNER TO spine;

--
-- Name: prospectcanal; Type: TYPE; Schema: public; Owner: spine
--

CREATE TYPE public.prospectcanal AS ENUM (
    'trade_show',
    'linkedin',
    'referral',
    'emailing',
    'inbound',
    'other'
);


ALTER TYPE public.prospectcanal OWNER TO spine;

--
-- Name: prospectsource; Type: TYPE; Schema: public; Owner: spine
--

CREATE TYPE public.prospectsource AS ENUM (
    'trade_show',
    'ride_along',
    'referral',
    'cold_outreach',
    'inbound',
    'other'
);


ALTER TYPE public.prospectsource OWNER TO spine;

--
-- Name: prospectstatus; Type: TYPE; Schema: public; Owner: spine
--

CREATE TYPE public.prospectstatus AS ENUM (
    'new',
    'contacted',
    'oven',
    'fridge',
    'trash',
    'converted'
);


ALTER TYPE public.prospectstatus OWNER TO spine;

--
-- Name: tradeshowstatus; Type: TYPE; Schema: public; Owner: spine
--

CREATE TYPE public.tradeshowstatus AS ENUM (
    'UPCOMING',
    'ACTIVE',
    'COMPLETED',
    'ARCHIVED'
);


ALTER TYPE public.tradeshowstatus OWNER TO spine;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO spine;

--
-- Name: campaign_contacts; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.campaign_contacts (
    id integer NOT NULL,
    campaign_id integer NOT NULL,
    prospect_id integer NOT NULL,
    status character varying(50) NOT NULL,
    notes text,
    email_sequence_step integer NOT NULL,
    last_email_sent_at timestamp without time zone,
    email_thread_id character varying(255),
    email_message_id character varying(255),
    added_at timestamp without time zone NOT NULL,
    response_received_at timestamp without time zone,
    last_response_content character varying,
    next_follow_up_scheduled_at timestamp without time zone,
    custom_followup_delay_1 integer,
    custom_followup_delay_2 integer,
    custom_followup_delay_3 integer
);


ALTER TABLE public.campaign_contacts OWNER TO spine;

--
-- Name: campaign_contacts_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.campaign_contacts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.campaign_contacts_id_seq OWNER TO spine;

--
-- Name: campaign_contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.campaign_contacts_id_seq OWNED BY public.campaign_contacts.id;


--
-- Name: campaign_products; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.campaign_products (
    id integer NOT NULL,
    campaign_id integer NOT NULL,
    product_id integer NOT NULL,
    added_at timestamp without time zone NOT NULL
);


ALTER TABLE public.campaign_products OWNER TO spine;

--
-- Name: campaign_products_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.campaign_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.campaign_products_id_seq OWNER TO spine;

--
-- Name: campaign_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.campaign_products_id_seq OWNED BY public.campaign_products.id;


--
-- Name: campaigns; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.campaigns (
    id integer NOT NULL,
    user_id integer NOT NULL,
    name character varying(255) NOT NULL,
    event_date date NOT NULL,
    end_date date,
    location character varying(255),
    distributor_name character varying(255),
    description text,
    status public.tradeshowstatus NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    followup_delay_1 integer DEFAULT 7 NOT NULL,
    followup_delay_2 integer DEFAULT 14 NOT NULL,
    followup_delay_3 integer DEFAULT 21 NOT NULL,
    template_initial_id integer,
    template_followup_1_id integer,
    template_followup_2_id integer,
    template_followup_3_id integer,
    campaign_source public.campaignsource NOT NULL,
    is_distributor_show boolean NOT NULL,
    distributor_company_id integer,
    auto_cc_sales_rep boolean NOT NULL,
    company_intro_text text,
    catalog_pitch_text text,
    offer_samples boolean NOT NULL,
    samples_note text,
    segment_note_global text,
    segment_note_restaurant text,
    segment_note_industry text,
    segment_note_retail text,
    attachment_paths text
);


ALTER TABLE public.campaigns OWNER TO spine;

--
-- Name: campaigns_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.campaigns_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.campaigns_id_seq OWNER TO spine;

--
-- Name: campaigns_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.campaigns_id_seq OWNED BY public.campaigns.id;


--
-- Name: companies; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.companies (
    id integer NOT NULL,
    user_id integer NOT NULL,
    name character varying(255) NOT NULL,
    market character varying(100),
    website character varying(255),
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    chain_level public.chainlevel,
    end_user_type public.endusertype
);


ALTER TABLE public.companies OWNER TO spine;

--
-- Name: companies_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.companies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.companies_id_seq OWNER TO spine;

--
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.companies_id_seq OWNED BY public.companies.id;


--
-- Name: distributor_catalog_items; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.distributor_catalog_items (
    id integer NOT NULL,
    catalog_id integer NOT NULL,
    product_id integer NOT NULL,
    notes text,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.distributor_catalog_items OWNER TO spine;

--
-- Name: distributor_catalog_items_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.distributor_catalog_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.distributor_catalog_items_id_seq OWNER TO spine;

--
-- Name: distributor_catalog_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.distributor_catalog_items_id_seq OWNED BY public.distributor_catalog_items.id;


--
-- Name: distributor_catalogs; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.distributor_catalogs (
    id integer NOT NULL,
    user_id integer NOT NULL,
    company_id integer,
    name character varying(255) NOT NULL,
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    pdf_path text,
    pdf_filename character varying(255)
);


ALTER TABLE public.distributor_catalogs OWNER TO spine;

--
-- Name: distributor_catalogs_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.distributor_catalogs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.distributor_catalogs_id_seq OWNER TO spine;

--
-- Name: distributor_catalogs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.distributor_catalogs_id_seq OWNED BY public.distributor_catalogs.id;


--
-- Name: email_templates; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.email_templates (
    id integer NOT NULL,
    user_id integer,
    name character varying(100) NOT NULL,
    category character varying(50) NOT NULL,
    subject_template character varying(500) NOT NULL,
    body_template text NOT NULL,
    variables json,
    is_active boolean DEFAULT true NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.email_templates OWNER TO spine;

--
-- Name: email_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.email_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.email_templates_id_seq OWNER TO spine;

--
-- Name: email_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.email_templates_id_seq OWNED BY public.email_templates.id;


--
-- Name: oauth_states; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.oauth_states (
    id integer NOT NULL,
    state character varying(64) NOT NULL,
    user_id integer NOT NULL,
    expires_at timestamp without time zone NOT NULL
);


ALTER TABLE public.oauth_states OWNER TO spine;

--
-- Name: oauth_states_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.oauth_states_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.oauth_states_id_seq OWNER TO spine;

--
-- Name: oauth_states_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.oauth_states_id_seq OWNED BY public.oauth_states.id;


--
-- Name: products; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.products (
    id integer NOT NULL,
    item_number character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    short_description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    user_id integer NOT NULL,
    brand character varying(255),
    category character varying(100),
    formats character varying(500),
    price_range character varying(100),
    certifications character varying(500),
    segments character varying(255),
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE public.products OWNER TO spine;

--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.products_id_seq OWNER TO spine;

--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- Name: prospect_products; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.prospect_products (
    id integer NOT NULL,
    prospect_id integer NOT NULL,
    product_id integer NOT NULL,
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.prospect_products OWNER TO spine;

--
-- Name: prospect_products_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.prospect_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.prospect_products_id_seq OWNER TO spine;

--
-- Name: prospect_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.prospect_products_id_seq OWNED BY public.prospect_products.id;


--
-- Name: prospects; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.prospects (
    id integer NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    phone_number character varying(20),
    "position" character varying(100),
    company_name character varying(255),
    company_size character varying(50),
    market character varying(100),
    source public.prospectsource NOT NULL,
    source_notes text,
    status public.prospectstatus DEFAULT 'new'::public.prospectstatus NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    user_id integer,
    company_id integer,
    source_detail character varying(255),
    canal public.prospectcanal,
    canal_detail character varying(255)
);


ALTER TABLE public.prospects OWNER TO spine;

--
-- Name: prospects_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.prospects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.prospects_id_seq OWNER TO spine;

--
-- Name: prospects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.prospects_id_seq OWNED BY public.prospects.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: spine
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255),
    first_name character varying(100),
    last_name character varying(100),
    is_active boolean NOT NULL,
    is_superuser boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    gmail_connected boolean DEFAULT false NOT NULL,
    gmail_email character varying,
    gmail_access_token character varying,
    gmail_refresh_token character varying,
    outlook_connected boolean DEFAULT false NOT NULL,
    outlook_email character varying,
    outlook_access_token character varying,
    outlook_refresh_token character varying,
    default_email_provider character varying
);


ALTER TABLE public.users OWNER TO spine;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: spine
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO spine;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: spine
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: campaign_contacts id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaign_contacts ALTER COLUMN id SET DEFAULT nextval('public.campaign_contacts_id_seq'::regclass);


--
-- Name: campaign_products id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaign_products ALTER COLUMN id SET DEFAULT nextval('public.campaign_products_id_seq'::regclass);


--
-- Name: campaigns id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaigns ALTER COLUMN id SET DEFAULT nextval('public.campaigns_id_seq'::regclass);


--
-- Name: companies id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.companies ALTER COLUMN id SET DEFAULT nextval('public.companies_id_seq'::regclass);


--
-- Name: distributor_catalog_items id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.distributor_catalog_items ALTER COLUMN id SET DEFAULT nextval('public.distributor_catalog_items_id_seq'::regclass);


--
-- Name: distributor_catalogs id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.distributor_catalogs ALTER COLUMN id SET DEFAULT nextval('public.distributor_catalogs_id_seq'::regclass);


--
-- Name: email_templates id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.email_templates ALTER COLUMN id SET DEFAULT nextval('public.email_templates_id_seq'::regclass);


--
-- Name: oauth_states id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.oauth_states ALTER COLUMN id SET DEFAULT nextval('public.oauth_states_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- Name: prospect_products id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.prospect_products ALTER COLUMN id SET DEFAULT nextval('public.prospect_products_id_seq'::regclass);


--
-- Name: prospects id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.prospects ALTER COLUMN id SET DEFAULT nextval('public.prospects_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.alembic_version (version_num) FROM stdin;
b2c3d4e5f6a7
\.


--
-- Data for Name: campaign_contacts; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.campaign_contacts (id, campaign_id, prospect_id, status, notes, email_sequence_step, last_email_sent_at, email_thread_id, email_message_id, added_at, response_received_at, last_response_content, next_follow_up_scheduled_at, custom_followup_delay_1, custom_followup_delay_2, custom_followup_delay_3) FROM stdin;
74	40	61	contacted	\N	4	2026-05-14 03:34:48.913926	19e248ca3bc60abc	<CAAXD9vTNVnnOByXPqzhmH2ASM=yPUdnTc0G9Unavk_fkbWKtxQ@mail.gmail.com>	2026-05-14 03:34:08.318151	\N	\N	\N	\N	\N	\N
76	31	61	contacted	\N	3	2026-06-06 15:57:43.999238	AQQkADAwATM0MDAAMi05Y2UwLTQzNGYtMDACLTAwCgAQAND1bZFKXeFOsxwvXyTYdXI=	AQMkADAwATM0MDAAMi05Y2UwLTQzNGYtMDACLTAwCgBGAAADkVDyFF_WkkSSamO7YVnCDwcActmHrreF_0aE5vSwIt09OwAAAgEJAAAActmHrreF_0aE5vSwIt09OwAAAII32D8AAAA=	2026-05-14 12:20:50.458601	\N	\N	2026-06-27 15:57:44.025314	\N	\N	\N
75	32	61	contacted	\N	3	2026-06-06 15:57:47.887936	AQQkADAwATM0MDAAMi05Y2UwLTQzNGYtMDACLTAwCgAQAEbp0l2VXsNHhIlSUgDw4FxS	AQMkADAwATM0MDAAMi05Y2UwLTQzNGYtMDACLTAwCgBGAAADkVDyFF_WkkSSamO7YVnCDwcActmHrreF_0aE5vSwIt09OwAAAgEJAAAActmHrreF_0aE5vSwIt09OwAAAII32EAAAAA=	2026-05-14 03:38:32.770636	\N	\N	2026-06-27 15:57:47.907986	\N	\N	\N
101	61	83	contacted	\N	2	2026-06-18 03:08:26.911099	AQQkADAwATM0MDAAMi05Y2UwLTQzNGYtMDACLTAwCgAQAGnN9n3GeAJCpbg9XGZ8nAo=	AQMkADAwATM0MDAAMi05Y2UwLTQzNGYtMDACLTAwCgBGAAADkVDyFF_WkkSSamO7YVnCDwcActmHrreF_0aE5vSwIt09OwAAAgEJAAAActmHrreF_0aE5vSwIt09OwAAAIk1hlgAAAA=	2026-06-04 21:56:04.430925	\N	\N	2026-07-02 03:08:26.915524	\N	\N	\N
77	41	62	oven	interesse	0	\N	\N	\N	2026-05-28 20:52:29.729297	\N	\N	\N	\N	\N	\N
102	61	84	contacted	\N	2	2026-06-18 03:08:37.827398	AQQkADAwATM0MDAAMi05Y2UwLTQzNGYtMDACLTAwCgAQACSlQ08YbLhPqXyrcPDH8JQ=	AQMkADAwATM0MDAAMi05Y2UwLTQzNGYtMDACLTAwCgBGAAADkVDyFF_WkkSSamO7YVnCDwcActmHrreF_0aE5vSwIt09OwAAAgEJAAAActmHrreF_0aE5vSwIt09OwAAAIk1hlkAAAA=	2026-06-04 21:56:04.430932	\N	\N	2026-07-02 03:08:37.828261	\N	\N	\N
103	61	85	responded	\N	2	2026-06-18 03:08:37.826556	AQQkADAwATM0MDAAMi05Y2UwLTQzNGYtMDACLTAwCgAQANe85Suc71VDlYE0tHYn2Xc=	AQMkADAwATM0MDAAMi05Y2UwLTQzNGYtMDACLTAwCgBGAAADkVDyFF_WkkSSamO7YVnCDwcActmHrreF_0aE5vSwIt09OwAAAgEJAAAActmHrreF_0aE5vSwIt09OwAAAIk1hloAAAA=	2026-06-04 21:56:04.430933	2026-06-20 07:17:17.48425	<html><head>\r\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head><body>Hi Kristine,<br><br>I wanted to follow up on my previous email regarding cdsx.<br><br>Did you get a chance to review our discussion?<br><br>Looking forward to hearing from you!<br><br>Best regards,<br>Test User </body></html>	\N	\N	\N	\N
8	3	3	pending	\N	0	\N	\N	\N	2026-04-28 15:22:37.142402	\N	\N	\N	\N	\N	\N
104	62	86	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.271391	\N	\N	\N	\N	\N	\N
105	62	87	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.271399	\N	\N	\N	\N	\N	\N
106	62	88	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.2714	\N	\N	\N	\N	\N	\N
107	62	89	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.271401	\N	\N	\N	\N	\N	\N
108	62	90	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.271402	\N	\N	\N	\N	\N	\N
109	62	91	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.271403	\N	\N	\N	\N	\N	\N
71	37	61	contacted	\N	4	2026-05-08 19:10:25.215578	19e08fed9f6e101b	<CAAXD9vQnFKuvZVNFGvam+3PDEf2-SCCE6_mnVOJZ8MZEUyWT9g@mail.gmail.com>	2026-05-08 19:09:35.146442	\N	\N	\N	\N	\N	\N
110	62	92	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.271405	\N	\N	\N	\N	\N	\N
111	62	93	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.271406	\N	\N	\N	\N	\N	\N
112	62	94	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.271407	\N	\N	\N	\N	\N	\N
72	38	61	contacted	\N	4	2026-05-09 12:14:06.715249	19e0ca87b248b42b	<CAAXD9vRDbpRUWNbyB0o65Xi6nE6jpda1oitqO2dLubD1y_vP-g@mail.gmail.com>	2026-05-09 12:13:43.266773	\N	\N	\N	\N	\N	\N
73	39	61	contacted	\N	4	2026-05-14 03:29:03.299372	19e24879fd3607fd	<CAAXD9vSTwMSQu8vaPQN7AN7q8--uuxJop5MHx6Ff0BO_uaZ91w@mail.gmail.com>	2026-05-14 03:09:24.135648	\N	\N	\N	\N	\N	\N
113	62	95	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.271408	\N	\N	\N	\N	\N	\N
114	62	96	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.271409	\N	\N	\N	\N	\N	\N
115	62	97	pending	\N	0	\N	\N	\N	2026-06-22 09:55:04.27141	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: campaign_products; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.campaign_products (id, campaign_id, product_id, added_at) FROM stdin;
\.


--
-- Data for Name: campaigns; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.campaigns (id, user_id, name, event_date, end_date, location, distributor_name, description, status, created_at, updated_at, followup_delay_1, followup_delay_2, followup_delay_3, template_initial_id, template_followup_1_id, template_followup_2_id, template_followup_3_id, campaign_source, is_distributor_show, distributor_company_id, auto_cc_sales_rep, company_intro_text, catalog_pitch_text, offer_samples, samples_note, segment_note_global, segment_note_restaurant, segment_note_industry, segment_note_retail, attachment_paths) FROM stdin;
1	1	Test Campaign Email 2026	2026-04-15	\N	Montreal	\N	\N	UPCOMING	2026-03-17 19:36:05.172715	2026-03-17 19:36:05.172719	7	14	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
2	1	test	2026-03-19	2026-03-19	LA	LA	LA	UPCOMING	2026-03-19 19:07:44.511556	2026-03-19 19:07:44.511563	7	14	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
3	3	Test Campagne Outlook	2026-06-01	\N	Paris	\N	\N	ACTIVE	2026-04-28 15:09:35.116431	2026-04-28 15:09:35.11644	7	14	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
61	5	cdsx	2026-06-19	\N	edscqx	\N	\N	ACTIVE	2026-06-04 21:56:04.284383	2026-06-04 21:56:43.013366	5	14	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	["/tmp/spine_attachments/61/Clovis_Flyer.pdf"]
62	5	zds	2026-06-24	\N	\N	\N	\N	UPCOMING	2026-06-22 09:55:04.155086	2026-06-22 09:55:04.386286	5	14	21	\N	\N	\N	\N	trade_show	t	\N	f	\N	\N	f	\N	\N	\N	\N	\N	["/tmp/spine_attachments/62/Clovis_Flyer.pdf"]
33	4	test3	2026-05-06	\N	d	\N	\N	COMPLETED	2026-05-04 17:09:19.809856	2026-05-05 22:47:05.918795	7	14	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
35	4	test56	2026-05-14	\N	fre	red	\N	COMPLETED	2026-05-05 22:17:35.038298	2026-05-05 22:49:49.556405	1	4	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
37	4	iddb	2026-05-24	\N	\N	\N	\N	COMPLETED	2026-05-08 19:09:28.457487	2026-05-08 19:10:25.21889	1	10	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
38	4	testttt	2026-05-21	\N	\N	\N	\N	COMPLETED	2026-05-09 12:13:34.772157	2026-05-09 12:14:06.719956	7	14	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
39	4	test90	2026-05-20	\N	\N	fcxw	\N	COMPLETED	2026-05-14 03:09:18.182158	2026-05-14 03:29:03.304816	7	14	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
40	4	test102	2026-05-15	\N	\N	\N	\N	COMPLETED	2026-05-14 03:34:02.292881	2026-05-14 03:34:48.919835	7	14	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
31	4	test	2026-12-05	\N	\N	\N	\N	ACTIVE	2026-05-04 15:20:39.777618	2026-05-14 12:25:32.504666	7	14	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
32	4	test2	2026-04-22	\N	\N	\N	\N	ACTIVE	2026-05-04 15:24:08.928602	2026-05-14 13:00:00.474801	7	14	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
41	7	test	2026-05-28	2026-05-28	string	string	string	UPCOMING	2026-05-28 20:51:25.513361	2026-05-28 20:51:25.513369	7	14	21	\N	\N	\N	\N	trade_show	f	\N	f	\N	\N	f	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.companies (id, user_id, name, market, website, notes, created_at, updated_at, chain_level, end_user_type) FROM stdin;
1	5	test	string	string	string	2026-06-02 21:39:13.30557	2026-06-02 21:39:13.305575	\N	\N
2	5	gge				2026-06-02 23:46:27.677962	2026-06-02 23:46:27.677968	\N	\N
3	5	dcs	doc	dsc	\N	2026-06-21 21:37:15.333897	2026-06-21 21:37:15.333899	distributor	\N
4	5	efzdscogyoofzbd	\N	\N	\N	2026-06-22 15:19:40.365116	2026-06-22 15:19:40.36512	distributor	\N
5	5	feds	ezfds	efzds	\N	2026-06-22 15:22:46.339226	2026-06-22 15:22:46.339231	distributor	\N
\.


--
-- Data for Name: distributor_catalog_items; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.distributor_catalog_items (id, catalog_id, product_id, notes, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: distributor_catalogs; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.distributor_catalogs (id, user_id, company_id, name, notes, created_at, updated_at, pdf_path, pdf_filename) FROM stdin;
\.


--
-- Data for Name: email_templates; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.email_templates (id, user_id, name, category, subject_template, body_template, variables, is_active, is_default, created_at, updated_at) FROM stdin;
21	4	test	initial	Great meeting you at {{campaign.name}}!	Hi {{prospect.first_name}},\n\nIt was great meeting you at {{campaign.name}} in {{campaign.location}}!\n\nI wanted to follow up on our conversation about {{prospect.company_name}}.\n\nWould you be available for a quick call this week?\n\nBest regards,\n{{user.first_name}} {{user.last_name}}	{"used_variables": ["campaign.name", "user.last_name", "campaign.location", "prospect.first_name", "user.first_name", "prospect.company_name"]}	t	f	2026-05-14 02:14:32.828201	2026-05-14 02:14:32.828212
23	4	test	followup_2	Re: Great meeting you at {{campaign.name}}	Hi {{prospect.first_name}},\n\nJust checking in one more time about {{campaign.name}}.\n\nI'd love to connect and explore how we can help {{prospect.company_name}}.\n\nBest regards,\n{{user.first_name}} {{user.last_name}}	{"used_variables": ["campaign.name", "user.last_name", "prospect.first_name", "user.first_name", "prospect.company_name"]}	t	f	2026-05-14 02:14:35.14441	2026-05-14 02:14:35.144418
24	4	test	followup_3	Re: Great meeting you at {{campaign.name}}	Hi {{prospect.first_name}},\n\nThis will be my last follow-up regarding our meeting at {{campaign.name}}.\n\nIf the timing isn't right, no worries at all — feel free to reach out whenever you're ready.\n\nBest regards,\n{{user.first_name}} {{user.last_name}}	{"used_variables": ["campaign.name", "prospect.first_name", "user.last_name", "user.first_name"]}	t	f	2026-05-14 02:14:36.008104	2026-05-14 02:14:36.008109
22	4	test	followup_1	Re: Great meeting you at {{campaign.name}}	Hi {{prospect.first_name}},\n\nI wanted to follow up on my previous email regarding {{campaign.name}}.\n\nDid you get a chance to review our discusdddddsion?\n\nLooking forward to hearing from you!\n\nBest regards,\n{{user.first_name}} {{user.last_name}}	{"used_variables": ["campaign.name", "prospect.first_name", "user.last_name", "user.first_name"]}	t	f	2026-05-14 02:14:33.880954	2026-05-14 02:14:47.541061
25	5	tets	initial	Great meeting you at {{campaign.name}}!	Hi {{prospect.first_name}},\n\nIt was great meeting you at {{campaign.name}} in {{campaign.location}}!\n\nI wanted to follow up on our conversation about {{prospect.company_name}}.\n\nWould you be available for a quick call this week?\n\nBest regards,\n{{user.first_name}} {{user.last_name}}	{"used_variables": ["prospect.company_name", "prospect.first_name", "user.first_name", "campaign.name", "user.last_name", "campaign.location"]}	t	f	2026-05-28 22:45:41.012908	2026-05-28 22:45:41.012914
26	5	tets	followup_1	Re: Great meeting you at {{campaign.name}}	Hi {{prospect.first_name}},\n\nI wanted to follow up on my previous email regarding {{campaign.name}}.\n\nDid you get a chance to review our discussion?\n\nLooking forward to hearing from you!\n\nBest regards,\n{{user.first_name}} {{user.last_name}}	{"used_variables": ["campaign.name", "user.last_name", "prospect.first_name", "user.first_name"]}	t	f	2026-05-28 22:45:43.52311	2026-05-28 22:45:43.523118
27	5	tets	followup_2	Re: Great meeting you at {{campaign.name}}	Hi {{prospect.first_name}},\n\nJust checking in one more time about {{campaign.name}}.\n\nI'd love to connect and explore how we can help {{prospect.company_name}}.\n\nBest regards,\n{{user.first_name}} {{user.last_name}}	{"used_variables": ["prospect.company_name", "prospect.first_name", "user.first_name", "campaign.name", "user.last_name"]}	t	f	2026-05-28 22:45:44.008276	2026-05-28 22:45:44.008287
28	5	tets	followup_3	Re: Great meeting you at {{campaign.name}}	Hi {{prospect.first_name}},\n\nThis will be my last follow-up regarding our meeting at {{campaign.name}}.\n\nIf the timing isn't right, no worries at all — feel free to reach out whenever you're ready.\n\nBest regards,\n{{user.first_name}} {{user.last_name}}	{"used_variables": ["campaign.name", "user.last_name", "prospect.first_name", "user.first_name"]}	t	f	2026-05-28 22:45:44.239426	2026-05-28 22:45:44.239432
\.


--
-- Data for Name: oauth_states; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.oauth_states (id, state, user_id, expires_at) FROM stdin;
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.products (id, item_number, name, short_description, created_at, updated_at, user_id, brand, category, formats, price_range, certifications, segments, is_active) FROM stdin;
1	TEST-001	Updated Test Product	Test description	2026-03-18 21:37:48.477283	2026-03-18 21:37:48.501457	2	\N	\N	\N	\N	\N	\N	t
50	11201	Clovis Vinegar Aged Sherry	\N	2026-06-05 21:30:14.21235	2026-06-05 21:30:14.212355	5	Clovis	Vinegars	2 x 5L	\N	\N	\N	t
51	11101	Clovis Vinegar Balsamic Modena	\N	2026-06-05 21:30:14.220513	2026-06-05 21:30:14.220518	5	Clovis	Vinegars	2 x 5L	\N	\N	\N	t
52	11107	Balsamic Glaze	\N	2026-06-05 21:30:14.225891	2026-06-05 21:30:14.225894	5	Clovis	Vinegars	6 x 16.9 fl.oz.	\N	\N	\N	t
39	10301	Whole Grain Mustard Mini Jar	\N	2026-06-05 21:30:14.127631	2026-06-05 21:34:42.222703	5	Clovis	Condiments	60 x 1.2 oz	\N	\N	\N	t
40	10302	Mayonnaise Mini Jar	\N	2026-06-05 21:30:14.139332	2026-06-05 21:34:50.797037	5	Clovis	Condiments	60 x 1.2 oz	\N	\N	\N	t
41	10303	Ketchup Mini Jar	\N	2026-06-05 21:30:14.146357	2026-06-05 21:34:57.914364	5	Clovis	Condiments	60 x 1.2 oz	\N	\N	\N	t
53	10202	Clovis French Cornichons 6/9.5lb	\N	2026-06-22 22:20:34.241656	2026-06-22 22:20:34.241664	5	Clovis	Condiments	6/9.5lb	\N	\N	\N	t
54	10209	Clovis French Cornichons 3/9.5lb	\N	2026-06-22 22:20:34.249389	2026-06-22 22:20:34.249394	5	Clovis	Condiments	3/9.5lb	\N	\N	\N	t
55	16010	Grilled Caramelized Onions 10/28oz	\N	2026-06-22 22:20:34.280472	2026-06-22 22:20:34.28048	5	white-toque	Vegetable Retort Pouch	10/28oz	\N	\N	\N	t
56	16014	Fully Cooked Organic White Quinoa 12/2lb	\N	2026-06-22 22:20:34.285464	2026-06-22 22:20:34.285468	5	white-toque	Vegetables	12/2lb	\N	\N	\N	t
57	16015	Fully Cooked Organic Red Quinoa 12/2lb	\N	2026-06-22 22:20:34.292456	2026-06-22 22:20:34.292462	5	white-toque	Vegetables	12/2lb	\N	\N	\N	t
58	16016	Fully Ckd Organic Tricolor Quinoa 12/2lb	\N	2026-06-22 22:20:34.297597	2026-06-22 22:20:34.2976	5	white-toque	Vegetables	12/2lb	\N	\N	\N	t
59	20000	BM Hazelnut Chocolate Spread 48/0.88oz	\N	2026-06-22 22:20:34.306012	2026-06-22 22:20:34.306017	5	Bonne Maman	Preserves	48/0.88oz	\N	\N	\N	t
38	10300	Original Dijon Mustard Mini Jar	\N	2026-06-05 21:30:14.117983	2026-06-05 21:30:14.117992	5	Clovis	Condiments	60 x 1.2oz	\N	\N	\N	t
42	10009	Clovis Original Dijon Mustard	\N	2026-06-05 21:30:14.155	2026-06-05 21:30:14.155007	5	Clovis	Mustards	2 x 8.6lbs	\N	\N	\N	t
43	10008	All Natural Dijon Mustard - No Sulfites	\N	2026-06-05 21:30:14.163043	2026-06-05 21:30:14.163048	5	Clovis	Mustards	2 x 8.6lb	\N	No Sulfites	\N	t
44	10102	Clovis Mustard Whole Grain	\N	2026-06-05 21:30:14.172579	2026-06-05 21:30:14.172585	5	Clovis	Mustards	2 x 8.16 Lb	\N	\N	\N	t
60	20001	BM Mini Strawberry Preserves 60/1oz	\N	2026-06-22 22:20:34.31598	2026-06-22 22:20:34.315984	5	Bonne Maman	Preserves	60/1oz	\N	\N	\N	t
61	20003	BM Mini Apricot Preserves 60/1oz	\N	2026-06-22 22:20:34.322658	2026-06-22 22:20:34.322661	5	Bonne Maman	Preserves	60/1oz	\N	\N	\N	t
62	20005	BM Mini Orange Marmalade 60/1oz	\N	2026-06-22 22:20:34.329233	2026-06-22 22:20:34.329234	5	Bonne Maman	Preserves	60/1oz	\N	\N	\N	t
63	20007	BM Mini Wild Blueberry Preserves 60/1oz	\N	2026-06-22 22:20:34.332318	2026-06-22 22:20:34.332319	5	Bonne Maman	Preserves	60/1oz	\N	\N	\N	t
64	20008	BM Mini Raspberry Preserves 60/1oz	\N	2026-06-22 22:20:34.336746	2026-06-22 22:20:34.336749	5	Bonne Maman	Preserves	60/1oz	\N	\N	\N	t
65	20009	BM Mini Cherry Preserves 60/1oz	\N	2026-06-22 22:20:34.340312	2026-06-22 22:20:34.340314	5	Bonne Maman	Preserves	60/1oz	\N	\N	\N	t
66	20012	BM Mini Guava Preserves 60/1oz	\N	2026-06-22 22:20:34.343855	2026-06-22 22:20:34.343856	5	Bonne Maman	Preserves	60/1oz	\N	\N	\N	t
67	20030	BM Strawberry Sticks 100/0.5oz	\N	2026-06-22 22:20:34.346789	2026-06-22 22:20:34.346791	5	Bonne Maman	Preserves	100/0.5oz	\N	\N	\N	t
68	20031	BM Apricot Preserves Sticks 100/0.5oz	\N	2026-06-22 22:20:34.350906	2026-06-22 22:20:34.350907	5	Bonne Maman	Preserves	100/0.5oz	\N	\N	\N	t
69	20032	BM Raspberry Mix Sticks 100/0.5oz	\N	2026-06-22 22:20:34.354362	2026-06-22 22:20:34.354365	5	Bonne Maman	Preserves	100/0.5oz	\N	\N	\N	t
70	20040	BM Strawberry Preserves 6/13oz	\N	2026-06-22 22:20:34.35924	2026-06-22 22:20:34.359242	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
71	20041	BM Apricot Preserves 6/13oz	\N	2026-06-22 22:20:34.362227	2026-06-22 22:20:34.362229	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
72	20042	BM Orange Marmalade 6/13oz	\N	2026-06-22 22:20:34.367689	2026-06-22 22:20:34.367692	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
73	20043	BM Wild Blueberry Preserves 6/13oz	\N	2026-06-22 22:20:34.37383	2026-06-22 22:20:34.373836	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
74	20101	BM Mini Honey 60/1oz	\N	2026-06-22 22:20:34.379695	2026-06-22 22:20:34.379699	5	Bonne Maman	Preserves	60/1oz	\N	\N	\N	t
75	20102	BM Fig Preserves Sticks 100/0.5oz	\N	2026-06-22 22:20:34.385415	2026-06-22 22:20:34.38542	5	Bonne Maman	Preserves	100/0.5oz	\N	\N	\N	t
76	20104	BM Honey Sticks 100/0.5oz	\N	2026-06-22 22:20:34.402471	2026-06-22 22:20:34.402479	5	Bonne Maman	Preserves	100/0.5oz	\N	\N	\N	t
77	20201	BM Raspberry Preserves 6/13oz	\N	2026-06-22 22:20:34.407429	2026-06-22 22:20:34.407433	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
78	20202	BM Fig Preserves 6/13oz	\N	2026-06-22 22:20:34.411652	2026-06-22 22:20:34.411655	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
79	20203	BM Peach Preserves 6/13oz	\N	2026-06-22 22:20:34.415903	2026-06-22 22:20:34.415905	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
80	20206	BM Blackberry Preserves 6/13oz	\N	2026-06-22 22:20:34.419894	2026-06-22 22:20:34.419896	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
81	20207	BM Redcurrant Jelly 6/13oz	\N	2026-06-22 22:20:34.425392	2026-06-22 22:20:34.425394	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
82	20208	BM Plum Preserves 6/13oz	\N	2026-06-22 22:20:34.429814	2026-06-22 22:20:34.429817	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
83	20216	BM Blackcurrant Jelly 6/13oz	\N	2026-06-22 22:20:34.433923	2026-06-22 22:20:34.433925	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
84	20217	BM Hazelnut Chocolate Spread 6/12.7oz	\N	2026-06-22 22:20:34.438506	2026-06-22 22:20:34.438508	5	Bonne Maman	Preserves	6/12.7oz	\N	\N	\N	t
85	20218	BM Guava Jelly 6/13oz	\N	2026-06-22 22:20:34.443105	2026-06-22 22:20:34.443107	5	Bonne Maman	Preserves	6/13oz	\N	\N	\N	t
86	26001	Ind. Wrap Sugar Cubes 2/5.5lb	\N	2026-06-22 22:20:34.447621	2026-06-22 22:20:34.447623	5	white-toque	Sugars	2/5.5lb	\N	\N	\N	t
87	26009	Caramel Shards 2/2.48lb	\N	2026-06-22 22:20:34.451768	2026-06-22 22:20:34.451771	5	white-toque	Sugars	2/2.48lb	\N	\N	\N	t
88	26124	50% Bake Stable Filling Strawberry 6/2.2lbs	\N	2026-06-22 22:20:34.456743	2026-06-22 22:20:34.456747	5	Andros	Filling	6/2.2lbs	\N	\N	\N	t
89	26125	50% Bake Stable Filling Apple Cinnamon 6/2.2lbs	\N	2026-06-22 22:20:34.461098	2026-06-22 22:20:34.4611	5	Andros	Filling	6/2.2lbs	\N	\N	\N	t
90	26126	50% Bake Stable Filling Blueberry 6/2.2lbs	\N	2026-06-22 22:20:34.466036	2026-06-22 22:20:34.466038	5	Andros	Filling	6/2.2lbs	\N	\N	\N	t
91	26127	50% Bake Stable Filling Apricot 6/2.2lbs	\N	2026-06-22 22:20:34.470594	2026-06-22 22:20:34.470596	5	Andros	Filling	6/2.2lbs	\N	\N	\N	t
92	26128	50% Bake Stable Filling Raspberry 6/2.2lbs	\N	2026-06-22 22:20:34.476085	2026-06-22 22:20:34.476086	5	Andros	Filling	6/2.2lbs	\N	\N	\N	t
93	26129	50% Bake Stable Filling Cherry 6/2.2lbs	\N	2026-06-22 22:20:34.481396	2026-06-22 22:20:34.481398	5	Andros	Filling	6/2.2lbs	\N	\N	\N	t
94	26109	50% Fruit Spread Blackberry 6/2.2lbs	\N	2026-06-22 22:20:34.486433	2026-06-22 22:20:34.486437	5	Andros	Fruit Spreads	6/2.2lbs	\N	\N	\N	t
95	26132	50% Fruit Spread Apricot 6/2.2lbs	\N	2026-06-22 22:20:34.493137	2026-06-22 22:20:34.493141	5	Andros	Fruit Spreads	6/2.2lbs	\N	\N	\N	t
96	26140	50% Fruit Spread Blueberry 6/2.2lbs	\N	2026-06-22 22:20:34.49765	2026-06-22 22:20:34.497653	5	Andros	Fruit Spreads	6/2.2lbs	\N	\N	\N	t
97	26141	50% Fruit Spread Raspberry 6/2.2lbs	\N	2026-06-22 22:20:34.5031	2026-06-22 22:20:34.503103	5	Andros	Fruit Spreads	6/2.2lbs	\N	\N	\N	t
98	26160	Fruit&Chunks Mango Passion Fruit 6/2.2lbs	\N	2026-06-22 22:20:34.508776	2026-06-22 22:20:34.508779	5	Andros	Fruit & Chunks	6/2.2lbs	\N	\N	\N	t
99	26161	Fruit&Chunks Mango 6/2.2lbs	\N	2026-06-22 22:20:34.51346	2026-06-22 22:20:34.513462	5	Andros	Fruit & Chunks	6/2.2lbs	\N	\N	\N	t
100	26162	Fruit&Chunks Mixed Berry 6/2.2lbs	\N	2026-06-22 22:20:34.517388	2026-06-22 22:20:34.51739	5	Andros	Fruit & Chunks	6/2.2lbs	\N	\N	\N	t
101	26163	Fruit&Chunks Guava 6/2.2lbs	\N	2026-06-22 22:20:34.522854	2026-06-22 22:20:34.522857	5	Andros	Fruit & Chunks	6/2.2lbs	\N	\N	\N	t
102	26164	Fruit&Chunks Peach 6/2.2lbs	\N	2026-06-22 22:20:34.528013	2026-06-22 22:20:34.528016	5	Andros	Fruit & Chunks	6/2.2lbs	\N	\N	\N	t
103	26165	Fruit&Chunks Pineapple Yuzu 6/2.2lbs	\N	2026-06-22 22:20:34.533108	2026-06-22 22:20:34.53311	5	Andros	Fruit & Chunks	6/2.2lbs	\N	\N	\N	t
104	26166	Fruit&Chunks Raspberry 6/2.2lbs	\N	2026-06-22 22:20:34.538946	2026-06-22 22:20:34.538949	5	Andros	Fruit & Chunks	6/2.2lbs	\N	\N	\N	t
\.


--
-- Data for Name: prospect_products; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.prospect_products (id, prospect_id, product_id, notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: prospects; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.prospects (id, first_name, last_name, email, phone_number, "position", company_name, company_size, market, source, source_notes, status, created_at, updated_at, user_id, company_id, source_detail, canal, canal_detail) FROM stdin;
3	Glenn	Test	glenn.duval4cd@gmail.com	\N	CEO	Oh My Brunch	\N	\N	trade_show	\N	new	2026-04-28 15:20:51.21971	2026-04-28 15:20:51.219717	3	\N	\N	\N	\N
61	Glenn	Duval	gduval@charbonneaux.com				\N	\N	trade_show	\N	new	2026-05-05 22:35:42.186405	2026-05-05 22:35:42.18641	4	\N	\N	\N	\N
62	test	test	user@example.com	string	string	string	string	string	trade_show	string	oven	2026-05-28 20:50:58.090804	2026-05-28 20:55:37.924291	7	\N	\N	\N	\N
84	Theodore	Scott	glenn.duval14cd@gmail.com	+1 530-328-6826	catering chef	HEAVENLY RESORT	\N	\N	other	mustard, butter	converted	2026-06-04 21:56:04.348919	2026-06-05 21:50:55.9277	5	\N	\N	\N	\N
83	Joeric	Cruz	gduval@charbonneaux.com	+1 916-801-5500	Hospitality Manager	TT&CO	\N	\N	other	escargot	converted	2026-06-04 21:56:04.345582	2026-06-05 21:50:57.521938	5	\N	\N	\N	\N
85	Kristine	Bertram	glenn_duval@outlook.com	+1 916-878-6868	Sous Chef	Esplanade at Turkey Creek	\N	\N	other	escargots, butter	converted	2026-06-04 21:56:04.351233	2026-06-05 21:50:59.298914	5	\N	\N	\N	\N
86	Anthony	Giallanza	agiallanza@comcast.net	\N	\N	Maggiano's Little Italy	\N	\N	trade_show	Alex LONDONO	new	2026-06-22 09:55:04.190064	2026-06-22 09:55:04.190073	5	\N	\N	trade_show	Trade Show
87	Paul	Nazario	pnazario@gourmetculinaryllc.com	\N	\N	Gourmet Culinary Partners	\N	\N	trade_show	Alex LONDONO	new	2026-06-22 09:55:04.19829	2026-06-22 09:55:04.198297	5	\N	\N	trade_show	Trade Show
88	Eric	Slaymaker	eric@wingerbros.com	\N	\N	WINGERS Alehouse	\N	\N	trade_show	Didier HEVIN	new	2026-06-22 09:55:04.202219	2026-06-22 09:55:04.202226	5	\N	\N	trade_show	Trade Show
89	James	Hunt	jameshunt8878@gmail.com	\N	\N	Compass -UChicago	\N	\N	trade_show	Lena WILLENS	new	2026-06-22 09:55:04.206469	2026-06-22 09:55:04.206475	5	\N	\N	trade_show	Trade Show
90	Nicholas	Thiakos	nicholas.thiakos@usfoods.com	\N	\N	US Foods	\N	\N	trade_show	Lena WILLENS	new	2026-06-22 09:55:04.210968	2026-06-22 09:55:04.210979	5	\N	\N	trade_show	Trade Show
91	Jax	Sperling	jax@craveworthybrands.com	\N	\N	Craveworthy Brands	\N	\N	trade_show	Lena WILLENS	new	2026-06-22 09:55:04.216487	2026-06-22 09:55:04.216492	5	\N	\N	trade_show	Trade Show
92	David	Horner	davidh@warmel.com	\N	\N	Warmel Management Co.	\N	\N	trade_show	Marjorie CACHOT	new	2026-06-22 09:55:04.220463	2026-06-22 09:55:04.220467	5	\N	\N	trade_show	Trade Show
93	Andre	Pinto	apinto@pechanga.com	\N	\N	Pechanga Resort Casino	\N	\N	trade_show	Marjorie CACHOT	new	2026-06-22 09:55:04.223759	2026-06-22 09:55:04.223764	5	\N	\N	trade_show	Trade Show
94	Masahiko	Tajima	tajima@afcsushi.com	\N	\N	AFC Franchise Corp.	\N	\N	trade_show	Marjorie CACHOT	new	2026-06-22 09:55:04.227585	2026-06-22 09:55:04.227589	5	\N	\N	trade_show	Trade Show
95	Caitlin	Barrett	cbarrett@crispellis.com	\N	\N	Crispelli's Pizzeria	\N	\N	trade_show	Marnie  Whitelaw	new	2026-06-22 09:55:04.230717	2026-06-22 09:55:04.230721	5	\N	\N	trade_show	Trade Show
96	Vincent	Pike	vpike@thelastpagerestaurant.com	\N	\N	The Last Page	\N	\N	trade_show	Marnie  Whitelaw	new	2026-06-22 09:55:04.233724	2026-06-22 09:55:04.233727	5	\N	\N	trade_show	Trade Show
97	Brian	Curry	briancurry@culvers.com	\N	\N	Culver Franchising System, LLC	\N	\N	trade_show	Marnie  Whitelaw	new	2026-06-22 09:55:04.237456	2026-06-22 09:55:04.237459	5	\N	\N	trade_show	Trade Show
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: spine
--

COPY public.users (id, email, hashed_password, first_name, last_name, is_active, is_superuser, created_at, updated_at, gmail_connected, gmail_email, gmail_access_token, gmail_refresh_token, outlook_connected, outlook_email, outlook_access_token, outlook_refresh_token, default_email_provider) FROM stdin;
2	test_api@test.com	$2b$12$HeUrJV3JoHgVWxd.2r1zke4rklpWlshflicTlNMTfuTw55YC3TWQ.	Test	API	t	f	2026-03-18 21:37:48.26597	2026-03-18 21:37:48.265973	f	\N	\N	\N	f	\N	\N	\N	\N
1	test@test.com	$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5kosgAb9Q/TU.	Glenn	Duval	t	f	2026-03-17 19:16:45.765306	2026-05-25 23:36:35.291293	f	\N	\N	\N	t	glenn_duval@outlook.com	gAAAAABqFN0Dd9GRQ0tDJYSsQKstZDI3sH3IKtdKqK_-NutQxg38JWz555RWZiY6_EkXu0h1y8Mm5AYtFawQFzsbsf_vBU8mjbAT8XQ3FL_Ytonc3jknZxTObojQ6Gd2KbDYGFS89ETAhjc9q_Z-8yJaK_MHcGqHlBUccXAnnCiAGkMB7oSNeWAh_xIv1Q65bzAMXtiXx0XN8u037nr7JxnQ9tt_SnTefCiWVCbi8j_49F5u7RTHyfR0g9rEwqYnpZaSRVQXJxikXXBILcrEvH8egPsX1GZefee2AWrJcEINWVi98KtogBt0dLlp3QiGyENETPMVISJveTg0IFWXBvPnYsAG51nj8Zh1N8dtbgXsiwbFom4B_RAVVoZ0pot1urY7ePoHIEjHvkKnJ6E_rf-_S4_tgxYiTvFyBtX0e8xeGo2IOg_4YXt4u5ICny_dQnQ9Ct_6WSttBj5F0ixUdpiQJn1HQ1jw8gc3mhnkrbDLW8-6ERWCOBmssPhN1mGvdHFVO08PQewLDReoMW-E-bN_gfD2IpW9JLfluf1k4OuCbcFxesSOWQl6jb9a1Ry4kRinwBRwuHrp7HxMB96Xqo667X-gFvAPngzyQ5Y9LJwkySJ14QLMw1Z72T1bS7smCTpylfa6cW1JWJ3D0ff813QEPpNtUbe2WcuP5Mj8SMSV4igO3tTLEUbttzSEBm6cJSJCKA6mnbplYHtIdqsETOgBoi3MKktqKaikQIgW4KdRGGQlB2ItQO4mCi08kFbTO36Y6f5Mqs1GqFeOfxA9xvhgi6cWclvR8GwzjhMOLre4V5SAWKgVM8NIJyIluFj50F1LMYJBLLMInEwmWmrRgQiLhR3FWchbEv5wpoE-B-D07vFN_8pfw57oRd2e3jR-FYMR8O7JtvqrXFDJ-OOsreFGulovG8dXGXQ1XCXXcpF4kAOb03yhEZIdTW4KCKE29hsoBGS_MCe4dXPyvrK-Y3Yhk_JRpgJKYAib5Vaojw_oJM1hmaFcWeutJYsdJUfeq16sAa-Gz2IB58sXrN9hEcG74KX9qmo-mDQsLHVmd7EE3SRqVIk0VH0tugtKHkAbdEM4kxY1Zrbf2m29Q8dsg5--d2mRNZqauUB6CVWZPfT7ytb1KDeuXTmaX5ozBBUIkVdqYqowMksnYX5d8j_GVnEIklB0tueoS6cjsCqo4JIRL3MD3q0GNB5mX4fFI0QwcyB3S_nJgvy9tEcOQozyzrqqKJWBzEmB6vf1G2fpCvQP_dVa0Ryt8A4L9k9YOrvW6oU7N4YsTvff7oMZKrPNE7CV9eXCaNS6YlATdvbftRlCUv8waqfWLR6ecv3Wyeq9rywyKQYci9AKZxLK2-PW_BDcHLnzkR2X-zJ3-3cOaAleZ6vLkSXv8_VwQobDxTzAWe8wLFE68spO43Jv1AnJns4ftuNhxpC7RAencPBxvAG6huQOq6JYsXpFdxJIoCQY3zqf0OsDT74-yUIiK3BjK2pyp8PU0gecJCWqLTTAJzMCH5RDrzctvNSoeT0tWOUAG7X6uvyxNiN9oQV7I9h5J0MhvTTgiBgUbxo0a4aqmfFuB42TIXQbqxD9vwVStzgu1TxcNA_sg3LfvrIkTbwBHJgNnEbq_cgQy5_xJRteLluQ2srP_V_o5v7SP_Oatd-ny57AgorufVsXUeHgjUUlIH6Ihah0lPvHfFGGvaGdN6qd-UdZRzMoVjIzYu3dshCJJm6MpUWw2sY4pNY1FpEM-fSbSX2j_TXls4JtS7rVAzndjnWVaESeyYpjKFcmGc43qxvUVrb64D4ZEhLwhsw3wKKzOFVHJUduzWQ2VfGUojnbZ29cg40rCeKMFAooAl5fQ7v860i63GmYb2VtNXjgDU__yq8GEfzBZ9lULzz14fRZSOZ4UNzh7URKTmY6-T721H8S-NKFDWYZD0BD0z7Uabgryz_24k0gN-lPSlJeSVWxZf4JH2vlTO0U11Wdyjrm_KDmTF-SkOrJEYmGNvHVw686VbZhFBy7ulMWLPZCtpxIWL8sg50rGyI=	gAAAAABqFN0DFT6Y4xPpU_g-eQCJUTQnX08xBuNvC3tXwKsYmDnj3vGumn-60n_j_mmAz1tOZ3J4IpQbOccofdGsIZp2eiKOgpfWbhnZZFN63ya-XlEFNBaW-UXa6IX3MCzlU9W_e0o2iRQblH0CQZvi3dLX4U8VkHLZ7MBcIq-29OUN4Byb18ouqEYV5OcBB6Eqgen1VPz-Vz0iu1v-ByoPV6FHtp1yktT3i-omwjPANaqMcmEi_gOtS56HVGNyTJKZ48bfRsViiPNBfgaN5ahI1692LkxDowtWk9cUY7C4bXvQ2DWjyYiGNK5MnEOSQ44eYiHYb6J5rHAV7jDV6u87HyU5Zq6iynxjzS7WlHOlx-YDbFQLJ7Td8hDObHeZMX4k2GzYt8bNnmKwVJQFm0UQn6_5COpQEN9ddPVdiTwV872fkDSd3eYZUDi1XbVW4G1T1tydrtdkNHJyuHStyp1rpzZk-IuEJaJ5WB_0oLX6IeJd8_VyyI9p8inHFCP-Es9cdc1jW7BZBWC7S63PGFKxuBjH2D84XCPhjjNEB_4RBdhNzuYYCidz8Auycgg05TPGwVTjopf2epPFRMXGl2V6iffoqmocXI1lbuTDNsbI5GGsuYHpKQnPch6LCprpUhacBHJRH8P_Pn3ck6l1GXnbxX-ajG-HU91b3320M1fmLXJBUEHYemQHixfR8ngFDxt7p78byPnQGOmkFsB50Sq2fvLS_oP_xQ==	outlook
3	glenn_duval@outlook.com	$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5kosgAb9Q/TU.	Glenn	Duval	t	f	2026-04-28 14:58:35.339068	2026-05-25 23:36:35.291296	f	\N	\N	\N	t	glenn_duval@outlook.com	gAAAAABqFN0DZYey4OCku9M3mXVqshcHdPkeQYDDDx4Cc4fvPh0WTQQDzGAFR3Jbl9m073y7UzQVpwXXDtB8OIQAFXmQmQvV89blqBu3aXYjTTU7Q4lOIQNRnp5LSIfmeQQRHA0gg4cw28FDvGQ4PHnzX7Rsa-i5jYjMRTT4Vni85Usqz3Ly4kSFtDls1o5K1sc8Lo65RqSaDN-txWdNnmELCOaeBFTf8F-NopNpiZeiiXd05SWgoXKle6umRbyrRvQqKQpQKX1qjp1YWrfXiECl7O2AOPdwIGWZ48P2RoC_xjjo7o3mSrvXIFfp-f3OTWaJZq3moZ-0_S4u7l9dBxs-qun6Fd7x2WctYPSkps5kZny7CyYHmHbUyoalPUa_uRYfDKmtSLXYkmYmkweGBkE8jWXl9S5a-22y5INFTGt-Q1APA2UgNFQpir_jyulZKxjlG5xBRNtfo0eWxKzVlLpmWt3dH720cdsFi6h2wpQ273xI0Z9RgGpcTfmX-5mR9DydycJ81lYIpOz0BxxD8Jyo9D2_mAV4n5bqZIX6K7fw_W0bxko8dBOKrJAjUdpUo0t3VhiYsZU1-WgtEwaEaMD0LGzKuPd80ZWx8_fxNvCtI-dLPm3bFaql588R5q0rzJP7RkI0cginjS_Q1Jl3ShBySOwKX1TKvD2py3IgUlPqUv-ArPQS7TeLO4Sh2vFdCVwboPxblvmnIz1KmQSdJceykm-JGqrkfuOufGycvSiHgcGq_HuiZjA8Rr7oH8fWInJYu1wvIx1tA8ZI4x5IC0w3kdbBFI9bD2WKU93cZmUz1t3lHx8BDazmdo0jaYhrQLXk-sgW_IwwWI5z8SI8L9q4BCK7CpJUHo_cKvZGaHh7I6Ip69576wxzgMO5kpql31M669-CN_0iiRnLnySwWxitVnj7B86pqce6-cZkrCrQAM2Njj-NNglz1CtU4YmlfJZA1J9BML7i4wBYBNhT8li6EE7NYnvlE9yNTVSs-QjYeR2jnRnUULs7cJZWZoHnrm_WAXPrEugltfek0ghDs5WCnSjUvV827VZAPr6xq20E1gMy8b9CwDfiQm3Y8dbTjWJiLRE36ZrFCTdr_vtjlSJZWDA5ttcO7aqfTv4DjoybyRwr9ku2H4M4o2VUl7xOkE675WwpYF-sALkXrkJd4AH49b2UjAWcBMIsoVQVMw8SPU4y73Om_FYp7B3Kp9AzhVglGQyfQEwyM3nZEVWRSYFLB8oQuuKnyhixZVHPGgcYt7FdClsG_-2WTK5aw05_uZPGjdybdJbSbEIlkLN8iwa4EuYdGuhSw26kQrInycncJ8RdSNGY9--S127mpqHW8gWmurgfpoIH5_Fd4JlDUzUGkk3ddg4FJNE7VGQ2PXdFRHBseYfWp7tczIR8wWz8CEib2q_W7bfGfSgirjynf67gCaMrSjUVtc5bwsyHtKMd1KlUCy24Z7LxR0EVOYqgCiZ3sZsadvB_niYNE_Jsb3u--aV_JTnelJ_LMLUskLBjQS_T36ytEGDTXxZQ-X_iYqih3lm_pZ9JVtqYIhx9MraAinjWqzTNa7MYFkrWUv-03pyKysUdCX6YDdBDkflQ6SoiJ48Bg7UJPXKZAAYuU1kVlrSa_4Xi2zOe5wJtLrAYm7eSKzIZ12OMge09glHEpluRWTEGyCb-6wa9ITcHOR_kw87DnMMTcqRZr8eMNr26_c4mXHAhFmaFSnQuLa6z6M7TLN5Owa27XDLuhTxu-TnQFJmIkEX0b5wP_mPW4ZsX1C4m-YyqSR36q0iRJs58mMQi9N5pLDZlYA4R6kFLMQpX07TkeMgkfA9lw_WuoHMiT0y_1x9Ntzeq3z0dUiGW8BTgdX-Ku0s0GADr2urfauCqGSTHxzHwnWB3xDtIwdoXKK_ea2Hl1PnqTjAgWgqJWaoPwjkOwFba7IYljW-mL1DDClpEc3sy-26VZN4Thn4U9DUWzE1djSi7jltsxu6sZKWXR2_aoSVCJOBGc_2LYkDJsSMCOeHaNvybfiwP0EnE-F-WnF9ETRA=	gAAAAABqFN0DBxA_y6J4vAOGJAqdAA3ZAN8zgG8VOhdyjXjnNNIsm_xfpMtSdWUoxwaXDyVBuQ0KDbR8-QnjW_dfEncBcDsNwgQG8s3Wpqe7tPn6NxGhz1j3GiCVUkK9f4dIXdxHlxuDaVzX07oDvmtDKI6hzHJknyqiL6YKpACy5mUs4N9zliNZSREMPBu-8qM5489KSstyH6Sj1nWh7r9_ppFp4XoqpfyPpZJaGnQ_0MFQcxnNozeiF84GLOEa86PrDCyV9mAIt5qrgFrJfXx40o2vVHnhVF8IGhv-ErFWSjQVdL-2qESBIgz6w4M9cWv_5KX-uzXcPZwhtiXM0Ti_H8gQb5Wg8lCNMi16DdUAOWOKfKG8fxf_jxV_f1bJhq8h-1Q1M5t7SHlySnC2-lFjwFHlZSFG_PBABCEhxlQqUGDlE5JRHxhjWdX8wF-KJv-AYMKONigV8mTk94_VWlD5UyFKbbooAeITTDmoAcrl3IqRcioteMZ71BYIcXRNsI2v3reJsGN6MBaH6riAvOBCvcdh_wI1HtrN94ShX2j04AtwmQdU9Hu9HD6PkN4SJUk__i4ulTt3ZuTbdZK17QqCgv3_c0aPgJXQGDiztCSXJ6_8_FyfU67UmmHcKankeloFZeR81awIijITSqrNSgq4gfQkoTerTW9DrzXxbETmKDyoeM9Kdxqg3zwlcJgkR5gG3K3ucQGWKoUxr0pIzVKUWRuJIK9JNg==	outlook
5	test_quali_28@test.com	$2b$12$ozdUBnBouVfwaDQLzjGTJ.xWyd.UipO1JYore2jgvh5CythoM5NZC	Test	User	t	f	2026-05-28 20:20:23.994013	2026-06-21 18:56:40.724255	f	\N	\N	\N	f	\N	\N	\N	\N
4	test_flow@spine.com	$2b$12$6lbiddCr5ltOvMGCD8xZEO9dKlCaC/FnkfGDjxtAs63pFSykjVX3m	Test	Flow	t	f	2026-04-29 15:49:33.177163	2026-06-22 11:52:21.719213	f	\N	\N	\N	t	glenn_duval@outlook.com	gAAAAABqOSH10gZZBOd9Yyd-VLLAVTp5o8SZVg4j6GKLKghUIgZI0woFUsLQ5a002r2jmbVAZivAhzoWztQ5QapiSizbfxs-ZwJAxS7qpRURX1uuZgg4AJsGDcs-5XI3BC6Os2GQbgC_ds__IzkQwwmsMRjQYoOpxP-WNnXHAt5z9ImygH2XbLaq2V1I6R8Ru78mikIGR-avOopJv2B9ZJ_gy9QFxr8XKsMmLMVelzZ8QC1UYD8tR2xgIstv8DDriPzeiBY32LwZ1sQ9pMZ4i2u9O_HLgRqQ54N94I6TcjQGUAXLQuRfSN-OSiXpoVjRUYcLfuY2smDSNTs15ZeSJOACsPFlJSVTkr4jxtgmNOXcgMN6RZigtAz-SOrSw_D0NPfy_ucRe4NdE9Em3kXGiTwwk8LbiqHBQB7LHWofm1Fce_S1BeLDHzQXOHwkWcA5JjgHhvE6qmoZKXJlQIeoYQOgMHuhoasTned8htjOWuuGtHucFJDF9fh5z_ZlNntg6518Y68dn0p2SAOjWakJB_TsgxglKrp_696P0R_5SNEJ6hAwLyyqFPsAPx1izIoXkpizgSK8_LBjcH1bwE7mjpLRFGaUzFgCWKizaSFyR1aRguO5eUdSDQ0FIEUlUQvpASgod-QUoMc-ngjPR4oOWk4yzcUitoD3dFXBSvIEOt-q_BYCbp-AiE0CybOl2EGbv6qj58Y5aJRPFubSwsddKz6__eGPndGgK2WQ07RLXAyWUbaQknbvCvACBAxp4RHJDRrRVZyVdePKZ62mD9EFd0-V3a_3EiQS_7jXq3jOqrKjogLh-U6M8aNbTR_LCQzGHHk53zMuNhd1zfnjJgIqK8pney-1OhzJP4zbXIZNtNPbcEkBibLmwB5b-SrZi2SntJr2OQBYWbn2Bq2y4qP8ez64a8fsZJCUmW4ZmBafGg6VJuQ8SogzygZv8FiftHW2gofz1aLOm-xxqATSVMSq9VSfXAE7OhzPfAtX2P5JomApNErvWjcDSV0I68Xulq6mDL9IBgotuS-h96Ifm-k9KwxO9l3y5Qu4gsl4FF1GSwnCixk-qLjAkZDINPCrvaLmUB4m-8GPKU1s3JzFyBeKxbqh-0eJ8W13tRfWim7pMhRZX7eyV_5Ise7BDojuwD78d-qorpsrrTfYbiIa_PtxzzoOOhRyDsULXnI2naRp8Ezh6Y1BnlXa0U_jZnnbVY42w4IUOSYmmrVbxfGLtVRGMQWa7LQPGYSCdzLfdjnIwsp6IilqsVic_Ajpuo7WVt2NFgOJ9RC1acG2mtbTda1QWjorJ5mWxS1FNLS7vj3H3huO6NIezmMgZEJSZnfYss9mvEF6n4lR0JZXupMFX5iPtSBIdx68JLxZwV1uVTRO9lIsd5AitrrAznwfXW732qBH53E2GwAWGexbkNaKVEcqSm79LigdoVOpgHuxQHCGiMnD_Uf9eIqVYK55qYiTmZHJR9fqQNCaARWzjmxK-RH1wtpzeYheeRlPUyszmd7Y0T18EJy5_-vWAMkxvswNlaahFCYed2dRtdqVOmiaVB3UarVY_5cONFpGo-5JZIQvBQ8tx9spY8IlDEdSYAtyN7oKjF9J6-gwqunayLibYJ5TFNxsSfBtHSfPxJ40S9D22H1AeYifR5XJ4j8Qpp4ayv4bLC8AZTgfOp-USVu_-2SKJtD52SF-3KADxHdOh6IFvkPo_xi8ZW7X5LBcV2TVQXUlXNBuvqGTCkLNVHxKkz9vhWR-5aaCs5Kekw7Qh7HQuJ6W3OSSxBwMoBJV5bBXAJMdhsBuVBHUO1LQET4YiKscYB8qjLwHdblxE8XoCo55NG976SJIBgaN_pWs_Wks7uktvTb5VyqntnuRe1-600-beo9gc_inTMyCNX3ir7rktunEbXxJJa4dI3faQ3z-APZRtQfX4SkRQ57pdeKnbSxbBaEyewyB0A2gjgrpFl-RuDjPLFfLhnEgFTVcBIh37xZDHXbvUnDKp90OiUhjTUeDkubScXEWlGFDFq_73iNKrPsvyWWvPWa9CbY=	gAAAAABqOSH1PBz5yE6T08pxTDTpZYaBF59jc3zqltFnAeI5JwdPx3SxP8kJsVVVRlhMqFgRczfZdAhIPF9kwDly9FiyNlJma2K0f1C_EtJVqe9FN8GuU5euIA0GXuUAHmdFcaeQ6dfftX7rbEv79yympmlSqBfoNv2MRVCFin3Y03iXr6Xb8GlxwAVHdC9jEcEX6IMfexcdYDRPcNwqepR3a_Ev2cSKkDnOKDieCsy5h9VDJUYyS_DIY07AZ6GaSE1VfmD1pUUMm46HD9xTh8_nPmIgpRlQ0qPULsWW8fXliF8rWRtHJSjlORGB4Sr9Qg7oV87cEpVuxFiffP03oCvfs2xxWaElJ-6FGEuA007wejTFaczqpBr3iaVQnAmb06uuB1mtaRrtaSmKOf4ye-3Taa74yw1wgOLdW3mqFcts1PgeW4jb1tBhioAu7E3K2eqiGKQEKt0171YHLoby4zJuFX6vFVuDgVALRP85Z9uOHN1aAuHeJdLV4OGXcKHB_6pzQOw_pfuw3rxk6jl0OqxC4VCri5x3FqN_ZEEIgl52l_2n0IwBd7De_lv2-mjkWGjyp2yRibSkFOc2nI-JVXS4IBFdqv_xddW2NrsJ9p9Kq5ffpxzkxfkssvfJL9WesP3HI-4X9XbCme2dkAcnzQ7avXelJVPJtlYHytkefv_onwp7gioEr78Z0NRN_s0PhirqSoLZV_sVEqcdVOZcr6zYm1JADaYuDx39Oz5XtWPq6QBcYYjFAXM=	outlook
6	test_final_28@test.com	$2b$12$HTKqws6NkU5UAOWSOSMOx.gqofAoYW0qpWFFTiY5zuW9TlcIEy2mC	Final	Test	t	f	2026-05-28 20:32:45.150735	2026-05-28 20:32:45.150739	f	\N	\N	\N	f	\N	\N	\N	\N
7	test_final_29@test.com	$2b$12$dNH3Tt7T29ULV/1Mk.WeAOJUuYr0B7/zJOJnLesHqCizSTaalHOra	Test	Duval	t	f	2026-05-28 20:35:30.837834	2026-05-28 20:35:30.83784	f	\N	\N	\N	f	\N	\N	\N	\N
8	user2_test@test.com	$2b$12$3crheAvqU2tfk5j16gWcguzFIlKuzxBwOw56DhzUFyQ.jxtdrlVoa	User	Two	t	f	2026-05-28 21:01:06.130726	2026-05-28 21:01:06.130733	f	\N	\N	\N	f	\N	\N	\N	\N
\.


--
-- Name: campaign_contacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.campaign_contacts_id_seq', 115, true);


--
-- Name: campaign_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.campaign_products_id_seq', 18, true);


--
-- Name: campaigns_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.campaigns_id_seq', 62, true);


--
-- Name: companies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.companies_id_seq', 5, true);


--
-- Name: distributor_catalog_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.distributor_catalog_items_id_seq', 71, true);


--
-- Name: distributor_catalogs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.distributor_catalogs_id_seq', 4, true);


--
-- Name: email_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.email_templates_id_seq', 28, true);


--
-- Name: oauth_states_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.oauth_states_id_seq', 8, true);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.products_id_seq', 104, true);


--
-- Name: prospect_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.prospect_products_id_seq', 47, true);


--
-- Name: prospects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.prospects_id_seq', 97, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: spine
--

SELECT pg_catalog.setval('public.users_id_seq', 8, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: campaign_contacts campaign_contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaign_contacts
    ADD CONSTRAINT campaign_contacts_pkey PRIMARY KEY (id);


--
-- Name: campaign_products campaign_products_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaign_products
    ADD CONSTRAINT campaign_products_pkey PRIMARY KEY (id);


--
-- Name: campaigns campaigns_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT campaigns_pkey PRIMARY KEY (id);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: distributor_catalog_items distributor_catalog_items_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.distributor_catalog_items
    ADD CONSTRAINT distributor_catalog_items_pkey PRIMARY KEY (id);


--
-- Name: distributor_catalogs distributor_catalogs_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.distributor_catalogs
    ADD CONSTRAINT distributor_catalogs_pkey PRIMARY KEY (id);


--
-- Name: email_templates email_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT email_templates_pkey PRIMARY KEY (id);


--
-- Name: oauth_states oauth_states_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.oauth_states
    ADD CONSTRAINT oauth_states_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: prospect_products prospect_products_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.prospect_products
    ADD CONSTRAINT prospect_products_pkey PRIMARY KEY (id);


--
-- Name: prospects prospects_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.prospects
    ADD CONSTRAINT prospects_pkey PRIMARY KEY (id);


--
-- Name: distributor_catalog_items uq_catalog_item_product; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.distributor_catalog_items
    ADD CONSTRAINT uq_catalog_item_product UNIQUE (catalog_id, product_id);


--
-- Name: prospects uq_prospects_email_user; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.prospects
    ADD CONSTRAINT uq_prospects_email_user UNIQUE (email, user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_campaign_contacts_campaign_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_campaign_contacts_campaign_id ON public.campaign_contacts USING btree (campaign_id);


--
-- Name: ix_campaign_contacts_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_campaign_contacts_id ON public.campaign_contacts USING btree (id);


--
-- Name: ix_campaign_contacts_prospect_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_campaign_contacts_prospect_id ON public.campaign_contacts USING btree (prospect_id);


--
-- Name: ix_campaign_products_campaign_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_campaign_products_campaign_id ON public.campaign_products USING btree (campaign_id);


--
-- Name: ix_campaign_products_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_campaign_products_id ON public.campaign_products USING btree (id);


--
-- Name: ix_campaign_products_product_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_campaign_products_product_id ON public.campaign_products USING btree (product_id);


--
-- Name: ix_campaigns_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_campaigns_id ON public.campaigns USING btree (id);


--
-- Name: ix_campaigns_user_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_campaigns_user_id ON public.campaigns USING btree (user_id);


--
-- Name: ix_companies_user_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_companies_user_id ON public.companies USING btree (user_id);


--
-- Name: ix_companies_user_id_name; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_companies_user_id_name ON public.companies USING btree (user_id, name);


--
-- Name: ix_distributor_catalog_items_catalog_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_distributor_catalog_items_catalog_id ON public.distributor_catalog_items USING btree (catalog_id);


--
-- Name: ix_distributor_catalog_items_product_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_distributor_catalog_items_product_id ON public.distributor_catalog_items USING btree (product_id);


--
-- Name: ix_distributor_catalogs_company_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_distributor_catalogs_company_id ON public.distributor_catalogs USING btree (company_id);


--
-- Name: ix_distributor_catalogs_user_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_distributor_catalogs_user_id ON public.distributor_catalogs USING btree (user_id);


--
-- Name: ix_email_templates_category; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_email_templates_category ON public.email_templates USING btree (category);


--
-- Name: ix_email_templates_name; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_email_templates_name ON public.email_templates USING btree (name);


--
-- Name: ix_email_templates_user_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_email_templates_user_id ON public.email_templates USING btree (user_id);


--
-- Name: ix_email_templates_user_id_name_category; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_email_templates_user_id_name_category ON public.email_templates USING btree (user_id, name, category);


--
-- Name: ix_oauth_states_state; Type: INDEX; Schema: public; Owner: spine
--

CREATE UNIQUE INDEX ix_oauth_states_state ON public.oauth_states USING btree (state);


--
-- Name: ix_products_user_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_products_user_id ON public.products USING btree (user_id);


--
-- Name: ix_products_user_item; Type: INDEX; Schema: public; Owner: spine
--

CREATE UNIQUE INDEX ix_products_user_item ON public.products USING btree (user_id, item_number);


--
-- Name: ix_prospects_company_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_prospects_company_id ON public.prospects USING btree (company_id);


--
-- Name: ix_prospects_user_canal; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_prospects_user_canal ON public.prospects USING btree (user_id, canal);


--
-- Name: ix_prospects_user_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_prospects_user_id ON public.prospects USING btree (user_id);


--
-- Name: ix_prospects_user_source; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_prospects_user_source ON public.prospects USING btree (user_id, source);


--
-- Name: ix_prospects_user_status; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_prospects_user_status ON public.prospects USING btree (user_id, status);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: spine
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: spine
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: campaign_contacts campaign_contacts_campaign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaign_contacts
    ADD CONSTRAINT campaign_contacts_campaign_id_fkey FOREIGN KEY (campaign_id) REFERENCES public.campaigns(id);


--
-- Name: campaign_contacts campaign_contacts_prospect_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaign_contacts
    ADD CONSTRAINT campaign_contacts_prospect_id_fkey FOREIGN KEY (prospect_id) REFERENCES public.prospects(id);


--
-- Name: campaign_products campaign_products_campaign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaign_products
    ADD CONSTRAINT campaign_products_campaign_id_fkey FOREIGN KEY (campaign_id) REFERENCES public.campaigns(id);


--
-- Name: campaign_products campaign_products_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaign_products
    ADD CONSTRAINT campaign_products_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: campaigns campaigns_template_followup_1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT campaigns_template_followup_1_id_fkey FOREIGN KEY (template_followup_1_id) REFERENCES public.email_templates(id);


--
-- Name: campaigns campaigns_template_followup_2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT campaigns_template_followup_2_id_fkey FOREIGN KEY (template_followup_2_id) REFERENCES public.email_templates(id);


--
-- Name: campaigns campaigns_template_followup_3_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT campaigns_template_followup_3_id_fkey FOREIGN KEY (template_followup_3_id) REFERENCES public.email_templates(id);


--
-- Name: campaigns campaigns_template_initial_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT campaigns_template_initial_id_fkey FOREIGN KEY (template_initial_id) REFERENCES public.email_templates(id);


--
-- Name: campaigns campaigns_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT campaigns_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: companies companies_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: distributor_catalog_items distributor_catalog_items_catalog_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.distributor_catalog_items
    ADD CONSTRAINT distributor_catalog_items_catalog_id_fkey FOREIGN KEY (catalog_id) REFERENCES public.distributor_catalogs(id) ON DELETE CASCADE;


--
-- Name: distributor_catalog_items distributor_catalog_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.distributor_catalog_items
    ADD CONSTRAINT distributor_catalog_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;


--
-- Name: distributor_catalogs distributor_catalogs_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.distributor_catalogs
    ADD CONSTRAINT distributor_catalogs_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: distributor_catalogs distributor_catalogs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.distributor_catalogs
    ADD CONSTRAINT distributor_catalogs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: email_templates email_templates_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT email_templates_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: campaigns fk_campaigns_distributor_company_id; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT fk_campaigns_distributor_company_id FOREIGN KEY (distributor_company_id) REFERENCES public.companies(id) ON DELETE SET NULL;


--
-- Name: oauth_states oauth_states_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.oauth_states
    ADD CONSTRAINT oauth_states_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: products products_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: prospect_products prospect_products_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.prospect_products
    ADD CONSTRAINT prospect_products_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;


--
-- Name: prospect_products prospect_products_prospect_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.prospect_products
    ADD CONSTRAINT prospect_products_prospect_id_fkey FOREIGN KEY (prospect_id) REFERENCES public.prospects(id) ON DELETE CASCADE;


--
-- Name: prospects prospects_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.prospects
    ADD CONSTRAINT prospects_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE SET NULL;


--
-- Name: prospects prospects_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: spine
--

ALTER TABLE ONLY public.prospects
    ADD CONSTRAINT prospects_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict GUHEeqoD0ZljDOQ0NK72QzageOSI8qfeRsNtQOf2TYJ7Voi464CgoNr1CQH8J4Q

