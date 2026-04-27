--
-- PostgreSQL database dump
--

\restrict uMfyV15Rz4aElI9C2KRHadCFs4juRavymX0p5F13fRkaR9HO89ewRoV81KVrmhd

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

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

--
-- Name: a; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA a;


ALTER SCHEMA a OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: borehole_fields; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.borehole_fields (
    id integer NOT NULL,
    ep_id integer,
    zhole numeric,
    rhole numeric,
    rb numeric,
    rpipeearth numeric,
    rpipegrout numeric,
    rringearth numeric,
    rgroutearth numeric,
    rgroutgrout numeric,
    mir integer,
    rmax numeric,
    nring integer,
    nzhole integer,
    nlayt integer,
    n1 integer,
    n2 integer,
    n3 integer,
    toutput numeric,
    cpgrd numeric,
    lambgrd numeric,
    rhogrd numeric,
    cpgrout numeric,
    lambgrout numeric,
    rhogrout numeric,
    rpipe numeric,
    thickpipe numeric,
    cppipe numeric,
    lambpipe numeric,
    lcasting numeric,
    lambda numeric,
    rhosurface numeric,
    cpsurface numeric,
    liqtype integer,
    tfreeze numeric,
    lambliq numeric,
    tmean numeric,
    geotgrad numeric,
    CONSTRAINT borehole_fields_cpgrd_check CHECK ((cpgrd > (0)::numeric)),
    CONSTRAINT borehole_fields_cpgrout_check CHECK ((cpgrout > (0)::numeric)),
    CONSTRAINT borehole_fields_cppipe_check CHECK ((cppipe > (0)::numeric)),
    CONSTRAINT borehole_fields_cpsurface_check CHECK ((cpsurface > (0)::numeric)),
    CONSTRAINT borehole_fields_lambda_check CHECK ((lambda > (0)::numeric)),
    CONSTRAINT borehole_fields_lambgrd_check CHECK ((lambgrd > (0)::numeric)),
    CONSTRAINT borehole_fields_lambgrout_check CHECK ((lambgrout > (0)::numeric)),
    CONSTRAINT borehole_fields_lambliq_check CHECK ((lambliq > (0)::numeric)),
    CONSTRAINT borehole_fields_lambpipe_check CHECK ((lambpipe > (0)::numeric)),
    CONSTRAINT borehole_fields_lcasting_check CHECK ((lcasting > (0)::numeric)),
    CONSTRAINT borehole_fields_n1_check CHECK ((n1 >= 0)),
    CONSTRAINT borehole_fields_n2_check CHECK ((n2 >= 0)),
    CONSTRAINT borehole_fields_n3_check CHECK ((n3 >= 0)),
    CONSTRAINT borehole_fields_nlayt_check CHECK ((nlayt > 0)),
    CONSTRAINT borehole_fields_nring_check CHECK ((nring > 0)),
    CONSTRAINT borehole_fields_nzhole_check CHECK ((nzhole > 0)),
    CONSTRAINT borehole_fields_rb_check CHECK ((rb >= (0)::numeric)),
    CONSTRAINT borehole_fields_rgroutearth_check CHECK ((rgroutearth > (0)::numeric)),
    CONSTRAINT borehole_fields_rgroutgrout_check CHECK ((rgroutgrout > (0)::numeric)),
    CONSTRAINT borehole_fields_rhogrd_check CHECK ((rhogrd > (0)::numeric)),
    CONSTRAINT borehole_fields_rhogrout_check CHECK ((rhogrout > (0)::numeric)),
    CONSTRAINT borehole_fields_rhole_check CHECK ((rhole > (0)::numeric)),
    CONSTRAINT borehole_fields_rhosurface_check CHECK ((rhosurface > (0)::numeric)),
    CONSTRAINT borehole_fields_rmax_check CHECK ((rmax > (0)::numeric)),
    CONSTRAINT borehole_fields_rpipe_check CHECK ((rpipe > (0)::numeric)),
    CONSTRAINT borehole_fields_rpipeearth_check CHECK ((rpipeearth > (0)::numeric)),
    CONSTRAINT borehole_fields_rpipegrout_check CHECK ((rpipegrout > (0)::numeric)),
    CONSTRAINT borehole_fields_rringearth_check CHECK ((rringearth > (0)::numeric)),
    CONSTRAINT borehole_fields_thickpipe_check CHECK ((thickpipe > (0)::numeric)),
    CONSTRAINT borehole_fields_toutput_check CHECK ((toutput >= (0)::numeric)),
    CONSTRAINT borehole_fields_zhole_check CHECK ((zhole > (0)::numeric))
);


ALTER TABLE a.borehole_fields OWNER TO postgres;

--
-- Name: borehole_fields_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.borehole_fields_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.borehole_fields_id_seq OWNER TO postgres;

--
-- Name: borehole_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.borehole_fields_id_seq OWNED BY a.borehole_fields.id;


--
-- Name: boreholes; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.boreholes (
    id integer NOT NULL,
    geom public.geometry(PointZ,25832),
    plant_id integer DEFAULT 1,
    "group" integer DEFAULT 1,
    mir boolean DEFAULT false
);


ALTER TABLE a.boreholes OWNER TO postgres;

--
-- Name: boreholes_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.boreholes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.boreholes_id_seq OWNER TO postgres;

--
-- Name: boreholes_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.boreholes_id_seq OWNED BY a.boreholes.id;


--
-- Name: buildings; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.buildings (
    id integer NOT NULL,
    b_id integer,
    z_id integer,
    substation_id integer,
    submodel integer DEFAULT 1,
    geom public.geometry(MultiPolygon,25832),
    z_bh_m numeric,
    z_height_m numeric
);


ALTER TABLE a.buildings OWNER TO postgres;

--
-- Name: buildings_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.buildings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.buildings_id_seq OWNER TO postgres;

--
-- Name: buildings_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.buildings_id_seq OWNED BY a.buildings.id;


--
-- Name: climate; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.climate (
    id integer NOT NULL,
    name text DEFAULT 'Graz'::text,
    file_name text DEFAULT 'C:\Users/peter.nageler/AppData/Roaming/QGIS/QGIS3\profiles\default/python/plugins\districts\Samples\climate\Graz-hour_std.prn'::text,
    latitude numeric DEFAULT 59.366,
    longitude numeric DEFAULT '-17.9999'::numeric,
    timezone integer DEFAULT '-1'::integer,
    height numeric DEFAULT 27
);


ALTER TABLE a.climate OWNER TO postgres;

--
-- Name: climate_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.climate_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.climate_id_seq OWNER TO postgres;

--
-- Name: climate_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.climate_id_seq OWNED BY a.climate.id;


--
-- Name: customer_connections; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.customer_connections (
    id integer NOT NULL,
    cid integer,
    c_seq integer,
    lid integer
);


ALTER TABLE a.customer_connections OWNER TO postgres;

--
-- Name: customer_connections_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.customer_connections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.customer_connections_id_seq OWNER TO postgres;

--
-- Name: customer_connections_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.customer_connections_id_seq OWNED BY a.customer_connections.id;


--
-- Name: customers; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.customers (
    id integer NOT NULL,
    geom public.geometry(PointZ,25832),
    template integer DEFAULT 1,
    network integer[] DEFAULT ARRAY[1],
    submodel integer DEFAULT 1
);


ALTER TABLE a.customers OWNER TO postgres;

--
-- Name: customers_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.customers_id_seq OWNER TO postgres;

--
-- Name: customers_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.customers_id_seq OWNED BY a.customers.id;


--
-- Name: energy_plant_connections; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.energy_plant_connections (
    id integer NOT NULL,
    epid integer,
    ep_seq integer,
    lid integer
);


ALTER TABLE a.energy_plant_connections OWNER TO postgres;

--
-- Name: energy_plant_connections_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.energy_plant_connections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.energy_plant_connections_id_seq OWNER TO postgres;

--
-- Name: energy_plant_connections_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.energy_plant_connections_id_seq OWNED BY a.energy_plant_connections.id;


--
-- Name: energy_plants; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.energy_plants (
    id integer NOT NULL,
    geom public.geometry(PointZ,25832),
    template integer DEFAULT 1,
    network integer[] DEFAULT ARRAY[1],
    submodel integer DEFAULT 1
);


ALTER TABLE a.energy_plants OWNER TO postgres;

--
-- Name: energy_plants_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.energy_plants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.energy_plants_id_seq OWNER TO postgres;

--
-- Name: energy_plants_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.energy_plants_id_seq OWNED BY a.energy_plants.id;


--
-- Name: invoked_sf; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.invoked_sf (
    id integer NOT NULL,
    sf text,
    type text,
    vars text[]
);


ALTER TABLE a.invoked_sf OWNER TO postgres;

--
-- Name: invoked_sf_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.invoked_sf_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.invoked_sf_id_seq OWNER TO postgres;

--
-- Name: invoked_sf_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.invoked_sf_id_seq OWNED BY a.invoked_sf.id;


--
-- Name: junction_connections; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.junction_connections (
    id integer NOT NULL,
    jid integer,
    lid integer
);


ALTER TABLE a.junction_connections OWNER TO postgres;

--
-- Name: junction_connections_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.junction_connections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.junction_connections_id_seq OWNER TO postgres;

--
-- Name: junction_connections_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.junction_connections_id_seq OWNED BY a.junction_connections.id;


--
-- Name: junctions; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.junctions (
    id integer NOT NULL,
    geom public.geometry(PointZ,25832),
    type integer,
    n_connections integer,
    submodel integer DEFAULT 1,
    network integer DEFAULT 1,
    zeta numeric DEFAULT 0,
    CONSTRAINT junctions_n_connections_check CHECK ((n_connections >= 1))
);


ALTER TABLE a.junctions OWNER TO postgres;

--
-- Name: junctions_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.junctions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.junctions_id_seq OWNER TO postgres;

--
-- Name: junctions_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.junctions_id_seq OWNED BY a.junctions.id;


--
-- Name: kpi; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.kpi (
    id integer NOT NULL,
    tsup_mean_ep numeric,
    tsup_max_ep numeric,
    tsup_min_ep numeric,
    tret_mean_ep numeric,
    tret_max_ep numeric,
    tret_min_ep numeric,
    qsup_heat_ep numeric,
    qsup_cold_ep numeric,
    qsup_ep numeric,
    tsup_mean_c numeric,
    tsup_max_c numeric,
    tsup_min_c numeric,
    tret_mean_c numeric,
    tret_max_c numeric,
    tret_min_c numeric,
    qsup_heat_c numeric,
    qsup_cold_c numeric,
    qsup_c numeric,
    qamb numeric
);


ALTER TABLE a.kpi OWNER TO postgres;

--
-- Name: kpi_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.kpi_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.kpi_id_seq OWNER TO postgres;

--
-- Name: kpi_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.kpi_id_seq OWNED BY a.kpi.id;


--
-- Name: lines; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.lines (
    id integer NOT NULL,
    geom public.geometry(LineStringZ,25832),
    network integer DEFAULT 1,
    type integer DEFAULT 0,
    pipe_bundle_type_id integer DEFAULT 1,
    zeta numeric DEFAULT 0,
    submodel integer[] DEFAULT ARRAY[1]
);


ALTER TABLE a.lines OWNER TO postgres;

--
-- Name: lines_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.lines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.lines_id_seq OWNER TO postgres;

--
-- Name: lines_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.lines_id_seq OWNED BY a.lines.id;


--
-- Name: network; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.network (
    id integer NOT NULL,
    description text
);


ALTER TABLE a.network OWNER TO postgres;

--
-- Name: network_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.network_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.network_id_seq OWNER TO postgres;

--
-- Name: network_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.network_id_seq OWNED BY a.network.id;


--
-- Name: pipes_model; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.pipes_model (
    id integer NOT NULL,
    sim_model integer,
    pid integer,
    co_sim integer
);


ALTER TABLE a.pipes_model OWNER TO postgres;

--
-- Name: pipes_model_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.pipes_model_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.pipes_model_id_seq OWNER TO postgres;

--
-- Name: pipes_model_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.pipes_model_id_seq OWNED BY a.pipes_model.id;


--
-- Name: segment_lines_00; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.segment_lines_00 (
    lines_id integer,
    rc_split_multi public.geometry
);


ALTER TABLE a.segment_lines_00 OWNER TO postgres;

--
-- Name: streets; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.streets (
    id integer NOT NULL,
    geom public.geometry(LineString,25832),
    costs_eur7m numeric DEFAULT 100,
    source integer,
    target integer
);


ALTER TABLE a.streets OWNER TO postgres;

--
-- Name: streets_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.streets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.streets_id_seq OWNER TO postgres;

--
-- Name: streets_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.streets_id_seq OWNED BY a.streets.id;


--
-- Name: submodels; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.submodels (
    id integer NOT NULL,
    submodel text,
    geom public.geometry(MultiPolygon,25832)
);


ALTER TABLE a.submodels OWNER TO postgres;

--
-- Name: submodels_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.submodels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.submodels_id_seq OWNER TO postgres;

--
-- Name: submodels_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.submodels_id_seq OWNED BY a.submodels.id;


--
-- Name: time_manager_tair; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.time_manager_tair (
    id integer NOT NULL,
    b_id integer NOT NULL,
    the_geom public.geometry(MultiPolygon,25832),
    time_h text,
    time_stamp timestamp without time zone,
    t_air_c numeric
);


ALTER TABLE a.time_manager_tair OWNER TO postgres;

--
-- Name: time_manager_tair_b_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.time_manager_tair_b_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.time_manager_tair_b_id_seq OWNER TO postgres;

--
-- Name: time_manager_tair_b_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.time_manager_tair_b_id_seq OWNED BY a.time_manager_tair.b_id;


--
-- Name: time_manager_tair_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.time_manager_tair_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.time_manager_tair_id_seq OWNER TO postgres;

--
-- Name: time_manager_tair_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.time_manager_tair_id_seq OWNED BY a.time_manager_tair.id;


--
-- Name: borehole_fields id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.borehole_fields ALTER COLUMN id SET DEFAULT nextval('a.borehole_fields_id_seq'::regclass);


--
-- Name: boreholes id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.boreholes ALTER COLUMN id SET DEFAULT nextval('a.boreholes_id_seq'::regclass);


--
-- Name: buildings id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.buildings ALTER COLUMN id SET DEFAULT nextval('a.buildings_id_seq'::regclass);


--
-- Name: climate id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.climate ALTER COLUMN id SET DEFAULT nextval('a.climate_id_seq'::regclass);


--
-- Name: customer_connections id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.customer_connections ALTER COLUMN id SET DEFAULT nextval('a.customer_connections_id_seq'::regclass);


--
-- Name: customers id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.customers ALTER COLUMN id SET DEFAULT nextval('a.customers_id_seq'::regclass);


--
-- Name: energy_plant_connections id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.energy_plant_connections ALTER COLUMN id SET DEFAULT nextval('a.energy_plant_connections_id_seq'::regclass);


--
-- Name: energy_plants id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.energy_plants ALTER COLUMN id SET DEFAULT nextval('a.energy_plants_id_seq'::regclass);


--
-- Name: invoked_sf id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.invoked_sf ALTER COLUMN id SET DEFAULT nextval('a.invoked_sf_id_seq'::regclass);


--
-- Name: junction_connections id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.junction_connections ALTER COLUMN id SET DEFAULT nextval('a.junction_connections_id_seq'::regclass);


--
-- Name: junctions id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.junctions ALTER COLUMN id SET DEFAULT nextval('a.junctions_id_seq'::regclass);


--
-- Name: kpi id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.kpi ALTER COLUMN id SET DEFAULT nextval('a.kpi_id_seq'::regclass);


--
-- Name: lines id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.lines ALTER COLUMN id SET DEFAULT nextval('a.lines_id_seq'::regclass);


--
-- Name: network id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.network ALTER COLUMN id SET DEFAULT nextval('a.network_id_seq'::regclass);


--
-- Name: pipes_model id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.pipes_model ALTER COLUMN id SET DEFAULT nextval('a.pipes_model_id_seq'::regclass);


--
-- Name: streets id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.streets ALTER COLUMN id SET DEFAULT nextval('a.streets_id_seq'::regclass);


--
-- Name: submodels id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.submodels ALTER COLUMN id SET DEFAULT nextval('a.submodels_id_seq'::regclass);


--
-- Name: time_manager_tair id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.time_manager_tair ALTER COLUMN id SET DEFAULT nextval('a.time_manager_tair_id_seq'::regclass);


--
-- Name: time_manager_tair b_id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.time_manager_tair ALTER COLUMN b_id SET DEFAULT nextval('a.time_manager_tair_b_id_seq'::regclass);


--
-- Data for Name: borehole_fields; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.borehole_fields (id, ep_id, zhole, rhole, rb, rpipeearth, rpipegrout, rringearth, rgroutearth, rgroutgrout, mir, rmax, nring, nzhole, nlayt, n1, n2, n3, toutput, cpgrd, lambgrd, rhogrd, cpgrout, lambgrout, rhogrout, rpipe, thickpipe, cppipe, lambpipe, lcasting, lambda, rhosurface, cpsurface, liqtype, tfreeze, lambliq, tmean, geotgrad) FROM stdin;
\.


--
-- Data for Name: boreholes; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.boreholes (id, geom, plant_id, "group", mir) FROM stdin;
\.


--
-- Data for Name: buildings; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.buildings (id, b_id, z_id, substation_id, submodel, geom, z_bh_m, z_height_m) FROM stdin;
\.


--
-- Data for Name: climate; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.climate (id, name, file_name, latitude, longitude, timezone, height) FROM stdin;
1	Graz	C:\\Users/peter.nageler/AppData/Roaming/QGIS/QGIS3\\profiles\\default/python/plugins\\districts\\Samples\\climate\\Graz-hour_std.prn	59.366	-17.9999	-1	27
\.


--
-- Data for Name: customer_connections; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.customer_connections (id, cid, c_seq, lid) FROM stdin;
\.


--
-- Data for Name: customers; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.customers (id, geom, template, network, submodel) FROM stdin;
\.


--
-- Data for Name: energy_plant_connections; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.energy_plant_connections (id, epid, ep_seq, lid) FROM stdin;
\.


--
-- Data for Name: energy_plants; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.energy_plants (id, geom, template, network, submodel) FROM stdin;
\.


--
-- Data for Name: invoked_sf; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.invoked_sf (id, sf, type, vars) FROM stdin;
\.


--
-- Data for Name: junction_connections; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.junction_connections (id, jid, lid) FROM stdin;
\.


--
-- Data for Name: junctions; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.junctions (id, geom, type, n_connections, submodel, network, zeta) FROM stdin;
\.


--
-- Data for Name: kpi; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.kpi (id, tsup_mean_ep, tsup_max_ep, tsup_min_ep, tret_mean_ep, tret_max_ep, tret_min_ep, qsup_heat_ep, qsup_cold_ep, qsup_ep, tsup_mean_c, tsup_max_c, tsup_min_c, tret_mean_c, tret_max_c, tret_min_c, qsup_heat_c, qsup_cold_c, qsup_c, qamb) FROM stdin;
\.


--
-- Data for Name: lines; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.lines (id, geom, network, type, pipe_bundle_type_id, zeta, submodel) FROM stdin;
\.


--
-- Data for Name: network; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.network (id, description) FROM stdin;
1	This is the main network.
\.


--
-- Data for Name: pipes_model; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.pipes_model (id, sim_model, pid, co_sim) FROM stdin;
\.


--
-- Data for Name: segment_lines_00; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.segment_lines_00 (lines_id, rc_split_multi) FROM stdin;
\.


--
-- Data for Name: streets; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.streets (id, geom, costs_eur7m, source, target) FROM stdin;
\.


--
-- Data for Name: submodels; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.submodels (id, submodel, geom) FROM stdin;
\.


--
-- Data for Name: time_manager_tair; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.time_manager_tair (id, b_id, the_geom, time_h, time_stamp, t_air_c) FROM stdin;
\.


--
-- Name: borehole_fields_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.borehole_fields_id_seq', 1, false);


--
-- Name: boreholes_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.boreholes_id_seq', 1, false);


--
-- Name: buildings_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.buildings_id_seq', 1, false);


--
-- Name: climate_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.climate_id_seq', 1, false);


--
-- Name: customer_connections_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.customer_connections_id_seq', 1, false);


--
-- Name: customers_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.customers_id_seq', 1, false);


--
-- Name: energy_plant_connections_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.energy_plant_connections_id_seq', 1, false);


--
-- Name: energy_plants_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.energy_plants_id_seq', 1, false);


--
-- Name: invoked_sf_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.invoked_sf_id_seq', 1, false);


--
-- Name: junction_connections_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.junction_connections_id_seq', 1, false);


--
-- Name: junctions_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.junctions_id_seq', 1, false);


--
-- Name: kpi_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.kpi_id_seq', 1, false);


--
-- Name: lines_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.lines_id_seq', 1, false);


--
-- Name: network_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.network_id_seq', 1, false);


--
-- Name: pipes_model_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.pipes_model_id_seq', 1, false);


--
-- Name: streets_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.streets_id_seq', 1, false);


--
-- Name: submodels_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.submodels_id_seq', 1, false);


--
-- Name: time_manager_tair_b_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.time_manager_tair_b_id_seq', 1, false);


--
-- Name: time_manager_tair_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.time_manager_tair_id_seq', 1, false);


--
-- Name: borehole_fields borehole_fields_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.borehole_fields
    ADD CONSTRAINT borehole_fields_pkey PRIMARY KEY (id);


--
-- Name: boreholes boreholes_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.boreholes
    ADD CONSTRAINT boreholes_pkey PRIMARY KEY (id);


--
-- Name: buildings buildings_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.buildings
    ADD CONSTRAINT buildings_pkey PRIMARY KEY (id);


--
-- Name: climate climate_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.climate
    ADD CONSTRAINT climate_pkey PRIMARY KEY (id);


--
-- Name: customer_connections customer_connections_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.customer_connections
    ADD CONSTRAINT customer_connections_pkey PRIMARY KEY (id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: energy_plant_connections energy_plant_connections_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.energy_plant_connections
    ADD CONSTRAINT energy_plant_connections_pkey PRIMARY KEY (id);


--
-- Name: energy_plants energy_plants_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.energy_plants
    ADD CONSTRAINT energy_plants_pkey PRIMARY KEY (id);


--
-- Name: pipes_model id_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.pipes_model
    ADD CONSTRAINT id_pkey PRIMARY KEY (id);


--
-- Name: invoked_sf invoked_sf_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.invoked_sf
    ADD CONSTRAINT invoked_sf_pkey PRIMARY KEY (id);


--
-- Name: junction_connections junction_connections_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.junction_connections
    ADD CONSTRAINT junction_connections_pkey PRIMARY KEY (id);


--
-- Name: junctions junctions_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.junctions
    ADD CONSTRAINT junctions_pkey PRIMARY KEY (id);


--
-- Name: kpi kpi_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.kpi
    ADD CONSTRAINT kpi_pkey PRIMARY KEY (id);


--
-- Name: lines lines_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.lines
    ADD CONSTRAINT lines_pkey PRIMARY KEY (id);


--
-- Name: network network_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.network
    ADD CONSTRAINT network_pkey PRIMARY KEY (id);


--
-- Name: streets streets_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.streets
    ADD CONSTRAINT streets_pkey PRIMARY KEY (id);


--
-- Name: submodels submodel_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.submodels
    ADD CONSTRAINT submodel_pkey PRIMARY KEY (id);


--
-- Name: time_manager_tair time_manager_tair_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.time_manager_tair
    ADD CONSTRAINT time_manager_tair_pkey PRIMARY KEY (id);


--
-- Name: segment_lines_00_rc_split_multi_idx; Type: INDEX; Schema: a; Owner: postgres
--

CREATE INDEX segment_lines_00_rc_split_multi_idx ON a.segment_lines_00 USING gist (rc_split_multi);


--
-- Name: borehole_fields column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.borehole_fields FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: boreholes column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.boreholes FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: buildings column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.buildings FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: climate column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.climate FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: customer_connections column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.customer_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: customers column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.customers FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: energy_plant_connections column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.energy_plant_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: energy_plants column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.energy_plants FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: junction_connections column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.junction_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: junctions column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.junctions FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: kpi column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.kpi FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: lines column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.lines FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: network column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.network FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: pipes_model column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.pipes_model FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: segment_lines_00 column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.segment_lines_00 FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: streets column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.streets FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: submodels column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.submodels FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: time_manager_tair column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.time_manager_tair FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: borehole_fields my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.borehole_fields FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: boreholes my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.boreholes FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: buildings my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.buildings FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: climate my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.climate FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: customer_connections my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.customer_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: customers my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.customers FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: energy_plant_connections my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.energy_plant_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: energy_plants my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.energy_plants FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: junction_connections my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.junction_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: junctions my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.junctions FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: kpi my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.kpi FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: lines my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.lines FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: network my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.network FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: pipes_model my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.pipes_model FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: segment_lines_00 my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.segment_lines_00 FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: streets my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.streets FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: submodels my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.submodels FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: time_manager_tair my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.time_manager_tair FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: borehole_fields my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.borehole_fields FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: boreholes my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.boreholes FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: buildings my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.buildings FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: climate my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.climate FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: customer_connections my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.customer_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: customers my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.customers FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: energy_plant_connections my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.energy_plant_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: energy_plants my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.energy_plants FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: junction_connections my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.junction_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: junctions my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.junctions FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: kpi my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.kpi FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: lines my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.lines FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: network my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.network FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: pipes_model my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.pipes_model FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: segment_lines_00 my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.segment_lines_00 FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: streets my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.streets FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: submodels my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.submodels FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: time_manager_tair my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.time_manager_tair FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: borehole_fields my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.borehole_fields FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: boreholes my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.boreholes FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: buildings my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.buildings FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: climate my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.climate FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: customer_connections my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.customer_connections FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: customers my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.customers FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: energy_plant_connections my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.energy_plant_connections FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: energy_plants my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.energy_plants FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: junction_connections my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.junction_connections FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: junctions my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.junctions FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: kpi my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.kpi FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: lines my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.lines FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: network my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.network FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: pipes_model my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.pipes_model FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: segment_lines_00 my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.segment_lines_00 FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: streets my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.streets FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: submodels my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.submodels FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: time_manager_tair my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.time_manager_tair FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- PostgreSQL database dump complete
--

\unrestrict uMfyV15Rz4aElI9C2KRHadCFs4juRavymX0p5F13fRkaR9HO89ewRoV81KVrmhd

