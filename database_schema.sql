--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2
-- Dumped by pg_dump version 17.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: benchmark_historical; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.benchmark_historical (
    benchmark_name character varying(50) NOT NULL,
    market_date date NOT NULL,
    closing_price numeric,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.benchmark_historical OWNER TO postgres;

--
-- Name: benchmark_metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.benchmark_metrics (
    benchmark_name character varying(50) NOT NULL,
    xirr_pct numeric,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.benchmark_metrics OWNER TO postgres;

--
-- Name: folio_metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.folio_metrics (
    folio_id integer NOT NULL,
    total_invested numeric,
    current_value numeric,
    overall_xirr_pct numeric,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.folio_metrics OWNER TO postgres;

--
-- Name: folios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.folios (
    folio_id integer NOT NULL,
    investor_id integer,
    amc_name character varying(255) NOT NULL,
    folio_number character varying(100) NOT NULL
);


ALTER TABLE public.folios OWNER TO postgres;

--
-- Name: folios_folio_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.folios_folio_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.folios_folio_id_seq OWNER TO postgres;

--
-- Name: folios_folio_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.folios_folio_id_seq OWNED BY public.folios.folio_id;


--
-- Name: historical_navs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.historical_navs (
    amfi_code character varying(50) NOT NULL,
    nav_date date NOT NULL,
    nav numeric
);


ALTER TABLE public.historical_navs OWNER TO postgres;

--
-- Name: investors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.investors (
    investor_id integer NOT NULL,
    name character varying(255) NOT NULL,
    email character varying(255),
    mobile character varying(20),
    address text
);


ALTER TABLE public.investors OWNER TO postgres;

--
-- Name: investors_investor_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.investors_investor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.investors_investor_id_seq OWNER TO postgres;

--
-- Name: investors_investor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.investors_investor_id_seq OWNED BY public.investors.investor_id;


--
-- Name: live_navs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.live_navs (
    amfi_code text,
    live_nav double precision,
    nav_date date
);


ALTER TABLE public.live_navs OWNER TO postgres;

--
-- Name: portfolio_history_daily; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.portfolio_history_daily (
    market_date date NOT NULL,
    investor_id character varying(50) NOT NULL,
    portfolio_value numeric(15,2) NOT NULL
);


ALTER TABLE public.portfolio_history_daily OWNER TO postgres;

--
-- Name: portfolio_metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.portfolio_metrics (
    investor_id integer NOT NULL,
    total_invested numeric,
    current_value numeric,
    overall_xirr_pct numeric,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.portfolio_metrics OWNER TO postgres;

--
-- Name: shadow_benchmark_values; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shadow_benchmark_values (
    market_date date NOT NULL,
    benchmark_name character varying(50) NOT NULL,
    shadow_value numeric(15,2) NOT NULL
);


ALTER TABLE public.shadow_benchmark_values OWNER TO postgres;

--
-- Name: transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transactions (
    transaction_id integer NOT NULL,
    folio_id integer,
    scheme_name character varying(255) NOT NULL,
    isin character varying(50),
    amfi_code character varying(20),
    transaction_date date NOT NULL,
    description text,
    amount numeric(15,4),
    units numeric(15,4),
    nav numeric(15,4),
    balance numeric(15,4),
    transaction_type character varying(50)
);


ALTER TABLE public.transactions OWNER TO postgres;

--
-- Name: transactions_transaction_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transactions_transaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transactions_transaction_id_seq OWNER TO postgres;

--
-- Name: transactions_transaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transactions_transaction_id_seq OWNED BY public.transactions.transaction_id;


--
-- Name: folios folio_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.folios ALTER COLUMN folio_id SET DEFAULT nextval('public.folios_folio_id_seq'::regclass);


--
-- Name: investors investor_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.investors ALTER COLUMN investor_id SET DEFAULT nextval('public.investors_investor_id_seq'::regclass);


--
-- Name: transactions transaction_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions ALTER COLUMN transaction_id SET DEFAULT nextval('public.transactions_transaction_id_seq'::regclass);


--
-- Name: benchmark_historical benchmark_historical_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.benchmark_historical
    ADD CONSTRAINT benchmark_historical_pkey PRIMARY KEY (benchmark_name, market_date);


--
-- Name: benchmark_metrics benchmark_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.benchmark_metrics
    ADD CONSTRAINT benchmark_metrics_pkey PRIMARY KEY (benchmark_name);


--
-- Name: folio_metrics folio_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.folio_metrics
    ADD CONSTRAINT folio_metrics_pkey PRIMARY KEY (folio_id);


--
-- Name: folios folios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.folios
    ADD CONSTRAINT folios_pkey PRIMARY KEY (folio_id);


--
-- Name: historical_navs historical_navs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historical_navs
    ADD CONSTRAINT historical_navs_pkey PRIMARY KEY (amfi_code, nav_date);


--
-- Name: investors investors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.investors
    ADD CONSTRAINT investors_pkey PRIMARY KEY (investor_id);


--
-- Name: portfolio_history_daily portfolio_history_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.portfolio_history_daily
    ADD CONSTRAINT portfolio_history_daily_pkey PRIMARY KEY (market_date, investor_id);


--
-- Name: portfolio_metrics portfolio_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.portfolio_metrics
    ADD CONSTRAINT portfolio_metrics_pkey PRIMARY KEY (investor_id);


--
-- Name: shadow_benchmark_values shadow_benchmark_values_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadow_benchmark_values
    ADD CONSTRAINT shadow_benchmark_values_pkey PRIMARY KEY (market_date, benchmark_name);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (transaction_id);


--
-- Name: folios unique_folio; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.folios
    ADD CONSTRAINT unique_folio UNIQUE (folio_number, investor_id);


--
-- Name: investors unique_investor; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.investors
    ADD CONSTRAINT unique_investor UNIQUE (email);


--
-- Name: transactions unique_transaction; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT unique_transaction UNIQUE (folio_id, transaction_date, description, amount, units);


--
-- Name: folio_metrics folio_metrics_folio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.folio_metrics
    ADD CONSTRAINT folio_metrics_folio_id_fkey FOREIGN KEY (folio_id) REFERENCES public.folios(folio_id);


--
-- Name: folios folios_investor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.folios
    ADD CONSTRAINT folios_investor_id_fkey FOREIGN KEY (investor_id) REFERENCES public.investors(investor_id) ON DELETE CASCADE;


--
-- Name: transactions transactions_folio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_folio_id_fkey FOREIGN KEY (folio_id) REFERENCES public.folios(folio_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

