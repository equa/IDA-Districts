--
-- PostgreSQL database dump
--

\restrict OkOYMcyewFknCYjiNHBlzyOSjsZEgAWqpvijZt51AIefjMOrPg3mhOK5oIQLJtQ

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
    geom public.geometry(PointZ,31256),
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
    geom public.geometry(MultiPolygon,31256),
    z_bh_m numeric,
    z_height_m numeric,
    z_template integer,
    z_construction integer,
    room_unit integer,
    win_facade_ratio numeric DEFAULT 30
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
    file_name text DEFAULT 'C:\Users\peter.nageler\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\ida_districts_data_center\Samples\climate\Graz-hour_std.prn'::text,
    latitude numeric DEFAULT 47.4,
    longitude numeric DEFAULT '-15.26'::numeric,
    timezone integer DEFAULT '-1'::integer,
    height numeric DEFAULT 353
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
    geom public.geometry(PointZ,31256),
    template integer DEFAULT 0,
    network integer[] DEFAULT ARRAY[1],
    load_w numeric DEFAULT 10000,
    submodel integer DEFAULT 1,
    dhw_id integer,
    internal_load_id integer,
    gfa numeric DEFAULT 100
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
    geom public.geometry(PointZ,31256),
    template integer DEFAULT 0,
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
-- Name: feature_decoupling; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.feature_decoupling (
    id integer NOT NULL,
    template integer,
    comp_name text,
    type text
);


ALTER TABLE a.feature_decoupling OWNER TO postgres;

--
-- Name: feature_decoupling_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.feature_decoupling_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.feature_decoupling_id_seq OWNER TO postgres;

--
-- Name: feature_decoupling_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.feature_decoupling_id_seq OWNED BY a.feature_decoupling.id;


--
-- Name: invoked_sensor_source_signals; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.invoked_sensor_source_signals (
    id integer NOT NULL,
    type integer,
    sensor_id integer,
    templates integer[],
    multi_signal boolean,
    test_value numeric,
    description text
);


ALTER TABLE a.invoked_sensor_source_signals OWNER TO postgres;

--
-- Name: invoked_sensor_source_signals_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.invoked_sensor_source_signals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.invoked_sensor_source_signals_id_seq OWNER TO postgres;

--
-- Name: invoked_sensor_source_signals_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.invoked_sensor_source_signals_id_seq OWNED BY a.invoked_sensor_source_signals.id;


--
-- Name: invoked_sensor_target_signals; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.invoked_sensor_target_signals (
    id integer NOT NULL,
    type integer,
    sensor_id integer,
    templates integer[],
    target integer,
    multi_signal boolean,
    test_value numeric,
    description text
);


ALTER TABLE a.invoked_sensor_target_signals OWNER TO postgres;

--
-- Name: invoked_sensor_target_signals_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.invoked_sensor_target_signals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.invoked_sensor_target_signals_id_seq OWNER TO postgres;

--
-- Name: invoked_sensor_target_signals_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.invoked_sensor_target_signals_id_seq OWNED BY a.invoked_sensor_target_signals.id;


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
    geom public.geometry(PointZ,31256),
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
-- Name: lines; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.lines (
    id integer NOT NULL,
    geom public.geometry(LineStringZ,31256),
    network integer DEFAULT 1,
    type integer,
    pipe_bundle_type_id integer DEFAULT 1,
    length numeric,
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
-- Name: model_parms; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.model_parms (
    id integer NOT NULL,
    type integer,
    parm_name text,
    model_name text,
    mapping_expression text,
    macro_name text,
    mapping_direction text DEFAULT 'ToIDA'::text
);


ALTER TABLE a.model_parms OWNER TO postgres;

--
-- Name: model_parms_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.model_parms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.model_parms_id_seq OWNER TO postgres;

--
-- Name: model_parms_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.model_parms_id_seq OWNED BY a.model_parms.id;


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
-- Name: sensor_source; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.sensor_source (
    id integer NOT NULL,
    sensor_id integer,
    type integer,
    template integer,
    measure integer,
    function integer,
    conn_type integer,
    conns integer,
    ids integer,
    test_value numeric DEFAULT 1,
    description text
);


ALTER TABLE a.sensor_source OWNER TO postgres;

--
-- Name: sensor_source_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.sensor_source_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.sensor_source_id_seq OWNER TO postgres;

--
-- Name: sensor_source_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.sensor_source_id_seq OWNED BY a.sensor_source.id;


--
-- Name: sensor_target; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.sensor_target (
    id integer NOT NULL,
    sensor_id integer,
    type integer,
    template integer,
    ids integer,
    target integer,
    test_value numeric,
    description text
);


ALTER TABLE a.sensor_target OWNER TO postgres;

--
-- Name: sensor_target_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.sensor_target_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.sensor_target_id_seq OWNER TO postgres;

--
-- Name: sensor_target_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.sensor_target_id_seq OWNED BY a.sensor_target.id;


--
-- Name: sensors; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.sensors (
    id integer NOT NULL
);


ALTER TABLE a.sensors OWNER TO postgres;

--
-- Name: sensors_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.sensors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.sensors_id_seq OWNER TO postgres;

--
-- Name: sensors_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.sensors_id_seq OWNED BY a.sensors.id;


--
-- Name: source_conn_type; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.source_conn_type (
    id integer NOT NULL,
    source_id integer,
    conn_type integer,
    active boolean DEFAULT false
);


ALTER TABLE a.source_conn_type OWNER TO postgres;

--
-- Name: source_conn_type_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.source_conn_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.source_conn_type_id_seq OWNER TO postgres;

--
-- Name: source_conn_type_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.source_conn_type_id_seq OWNED BY a.source_conn_type.id;


--
-- Name: source_conns; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.source_conns (
    id integer NOT NULL,
    source_id integer,
    connection_id integer,
    active boolean DEFAULT false
);


ALTER TABLE a.source_conns OWNER TO postgres;

--
-- Name: source_conns_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.source_conns_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.source_conns_id_seq OWNER TO postgres;

--
-- Name: source_conns_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.source_conns_id_seq OWNED BY a.source_conns.id;


--
-- Name: source_ids; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.source_ids (
    id integer NOT NULL,
    source_id integer,
    feature_id integer,
    active boolean DEFAULT false
);


ALTER TABLE a.source_ids OWNER TO postgres;

--
-- Name: source_ids_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.source_ids_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.source_ids_id_seq OWNER TO postgres;

--
-- Name: source_ids_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.source_ids_id_seq OWNED BY a.source_ids.id;


--
-- Name: source_template; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.source_template (
    id integer NOT NULL,
    source_id integer,
    template integer,
    active boolean DEFAULT false
);


ALTER TABLE a.source_template OWNER TO postgres;

--
-- Name: source_template_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.source_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.source_template_id_seq OWNER TO postgres;

--
-- Name: source_template_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.source_template_id_seq OWNED BY a.source_template.id;


--
-- Name: streets; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.streets (
    id integer NOT NULL,
    geom public.geometry(LineString,31256),
    length_m double precision,
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
    geom public.geometry(MultiPolygon,31256)
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
-- Name: supervisory_ctrl; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.supervisory_ctrl (
    id integer NOT NULL,
    submodel integer
);


ALTER TABLE a.supervisory_ctrl OWNER TO postgres;

--
-- Name: supervisory_ctrl_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.supervisory_ctrl_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.supervisory_ctrl_id_seq OWNER TO postgres;

--
-- Name: supervisory_ctrl_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.supervisory_ctrl_id_seq OWNED BY a.supervisory_ctrl.id;


--
-- Name: target_ids; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.target_ids (
    id integer NOT NULL,
    target_id integer,
    feature_id integer,
    active boolean DEFAULT false
);


ALTER TABLE a.target_ids OWNER TO postgres;

--
-- Name: target_ids_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.target_ids_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.target_ids_id_seq OWNER TO postgres;

--
-- Name: target_ids_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.target_ids_id_seq OWNED BY a.target_ids.id;


--
-- Name: target_template; Type: TABLE; Schema: a; Owner: postgres
--

CREATE TABLE a.target_template (
    id integer NOT NULL,
    target_id integer,
    template integer,
    active boolean DEFAULT false
);


ALTER TABLE a.target_template OWNER TO postgres;

--
-- Name: target_template_id_seq; Type: SEQUENCE; Schema: a; Owner: postgres
--

CREATE SEQUENCE a.target_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE a.target_template_id_seq OWNER TO postgres;

--
-- Name: target_template_id_seq; Type: SEQUENCE OWNED BY; Schema: a; Owner: postgres
--

ALTER SEQUENCE a.target_template_id_seq OWNED BY a.target_template.id;


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
-- Name: feature_decoupling id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.feature_decoupling ALTER COLUMN id SET DEFAULT nextval('a.feature_decoupling_id_seq'::regclass);


--
-- Name: invoked_sensor_source_signals id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.invoked_sensor_source_signals ALTER COLUMN id SET DEFAULT nextval('a.invoked_sensor_source_signals_id_seq'::regclass);


--
-- Name: invoked_sensor_target_signals id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.invoked_sensor_target_signals ALTER COLUMN id SET DEFAULT nextval('a.invoked_sensor_target_signals_id_seq'::regclass);


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
-- Name: lines id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.lines ALTER COLUMN id SET DEFAULT nextval('a.lines_id_seq'::regclass);


--
-- Name: model_parms id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.model_parms ALTER COLUMN id SET DEFAULT nextval('a.model_parms_id_seq'::regclass);


--
-- Name: network id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.network ALTER COLUMN id SET DEFAULT nextval('a.network_id_seq'::regclass);


--
-- Name: pipes_model id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.pipes_model ALTER COLUMN id SET DEFAULT nextval('a.pipes_model_id_seq'::regclass);


--
-- Name: sensor_source id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.sensor_source ALTER COLUMN id SET DEFAULT nextval('a.sensor_source_id_seq'::regclass);


--
-- Name: sensor_target id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.sensor_target ALTER COLUMN id SET DEFAULT nextval('a.sensor_target_id_seq'::regclass);


--
-- Name: sensors id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.sensors ALTER COLUMN id SET DEFAULT nextval('a.sensors_id_seq'::regclass);


--
-- Name: source_conn_type id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_conn_type ALTER COLUMN id SET DEFAULT nextval('a.source_conn_type_id_seq'::regclass);


--
-- Name: source_conns id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_conns ALTER COLUMN id SET DEFAULT nextval('a.source_conns_id_seq'::regclass);


--
-- Name: source_ids id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_ids ALTER COLUMN id SET DEFAULT nextval('a.source_ids_id_seq'::regclass);


--
-- Name: source_template id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_template ALTER COLUMN id SET DEFAULT nextval('a.source_template_id_seq'::regclass);


--
-- Name: streets id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.streets ALTER COLUMN id SET DEFAULT nextval('a.streets_id_seq'::regclass);


--
-- Name: submodels id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.submodels ALTER COLUMN id SET DEFAULT nextval('a.submodels_id_seq'::regclass);


--
-- Name: supervisory_ctrl id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.supervisory_ctrl ALTER COLUMN id SET DEFAULT nextval('a.supervisory_ctrl_id_seq'::regclass);


--
-- Name: target_ids id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.target_ids ALTER COLUMN id SET DEFAULT nextval('a.target_ids_id_seq'::regclass);


--
-- Name: target_template id; Type: DEFAULT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.target_template ALTER COLUMN id SET DEFAULT nextval('a.target_template_id_seq'::regclass);


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

COPY a.buildings (id, b_id, z_id, substation_id, submodel, geom, z_bh_m, z_height_m, z_template, z_construction, room_unit, win_facade_ratio) FROM stdin;
\.


--
-- Data for Name: climate; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.climate (id, name, file_name, latitude, longitude, timezone, height) FROM stdin;
\.


--
-- Data for Name: customer_connections; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.customer_connections (id, cid, c_seq, lid) FROM stdin;
\.


--
-- Data for Name: customers; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.customers (id, geom, template, network, load_w, submodel, dhw_id, internal_load_id, gfa) FROM stdin;
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
1	01010000A0187A000068DAC236073EE2C0035C0AD59DA215410000000000000000	1	{1}	1
2	01010000A0187A00007055766AFCB3E2C02DD53924259815410000000000000000	1	{1}	1
\.


--
-- Data for Name: feature_decoupling; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.feature_decoupling (id, template, comp_name, type) FROM stdin;
\.


--
-- Data for Name: invoked_sensor_source_signals; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.invoked_sensor_source_signals (id, type, sensor_id, templates, multi_signal, test_value, description) FROM stdin;
\.


--
-- Data for Name: invoked_sensor_target_signals; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.invoked_sensor_target_signals (id, type, sensor_id, templates, target, multi_signal, test_value, description) FROM stdin;
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
-- Data for Name: lines; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.lines (id, geom, network, type, pipe_bundle_type_id, length, zeta, submodel) FROM stdin;
1	01020000A0187A0000840000003C04BDAFBD9EE2C0A84695253A93154100000000000000009C2414BC9F9DE2C0DDFE35644D9315410000000000000000C11E93189F9DE2C0A4775D6F4D9315410000000000000000158218769E9DE2C0CC3CC07A4D9315410000000000000000ECAEA9D49D9DE2C0E4ED5D864D9315410000000000000000BAFC4B349D9DE2C0852836924D9315410000000000000000EBB904959C9DE2C05C88489E4D9315410000000000000000B42BD9F69B9DE2C026A794AA4D9315410000000000000000E68DCE599B9DE2C0B81C1AB74D9315410000000000000000C312EABD9A9DE2C0017FD8C34D9315410000000000000000D3E230239A9DE2C00F62CFD04D9315410000000000000000B31CA889999DE2C01158FEDD4D9315410000000000000000F2D454F1989DE2C059F164EB4D9315410000000000000000DE153C5A989DE2C064BC02F94D93154100000000000000005EDF62C4979DE2C0DB45D7064E9315410000000000000000C626CE2F979DE2C09718E2144E9315410000000000000000ADD6829C969DE2C0A5BD22234E9315410000000000000000C5CE850A969DE2C04ABC98314E9315410000000000000000AEE3DB79959DE2C0089A43404E9315410000000000000000D2DE89EA949DE2C0A0DA224F4E9315410000000000000000397E945C949DE2C01800365E4E9315410000000000000000607400D0939DE2C0BE8A7C6D4E93154100000000000000001668D244939DE2C02CF9F57C4E931541000000000000000050F40EBB929DE2C04FC8A18C4E931541000000000000000003A8BA32929DE2C068737F9C4E9315410000000000000000FF05DAAB919DE2C010748EAC4E9315410000000000000000C7847126919DE2C04242CEBC4E93154100000000000000006C8E85A2909DE2C058543ECD4E931541000000000000000068801A20909DE2C0141FDEDD4E931541000000000000000079AB349F8F9DE2C0A615ADEE4E93154100000000000000007953D81F8F9DE2C0ABA9AAFF4E931541000000000000000041AF09A28E9DE2C0384BD6104F93154100000000000000007FE8CC258E9DE2C0DA682F224F9315410000000000000000951B26AB8D9DE2C09E6FB5334F9315410000000000000000755719328D9DE2C013CB67454F9315410000000000000000839DAABA8C9DE2C053E545574F93154100000000000000006DE1DD448C9DE2C002274F694F93154100000000000000000C09B7D08B9DE2C05BF7827B4F931541000000000000000046EC395E8B9DE2C02CBCE08D4F9315410000000000000000E8546AED8A9DE2C0E1D967A04F931541000000000000000089FE4B7E8A9DE2C08AB317B34F93154100000000000000006C96E2108A9DE2C0DCAAEFC54F93154100000000000000005DBB31A5899DE2C03720EFD84F931541000000000000000095FD3C3B899DE2C0AF7215EC4F93154100000000000000009ADE07D3889DE2C00E0062FF4F931541000000000000000024D1956C889DE2C0D824D412509315410000000000000000FD38EA07889DE2C0573C6B26509315410000000000000000E66A08A5879DE2C097A0263A50931541000000000000000078ACF343879DE2C075AA054E5093154100000000000000000F34AFE4869DE2C09DB10762509315410000000000000000A5283E87869DE2C0930C2C76509315410000000000000000C0A1A32B869DE2C0BA10728A50931541000000000000000054A7E2D1859DE2C05612D99E509315410000000000000000A931FE79859DE2C0946460B35093154100000000000000004229F923859DE2C0915907C8509315410000000000000000C666D6CF849DE2C05A42CDDC509315410000000000000000E7B2987D849DE2C0FB6EB1F150931541000000000000000048C6422D849DE2C07C2EB3065193154100000000000000006B49D7DE839DE2C0EACED11B51931541000000000000000096D45892839DE2C0619D0C31519315410000000000000000BEEFC947839DE2C00BE6624651931541000000000000000075122DFF829DE2C02BF4D35B519315410000000000000000CFA384B8829DE2C020125F7151931541000000000000000054FAD273829DE2C06D890387519315410000000000000000E65B1A31829DE2C0BEA2C09C519315410000000000000000B4FD5CF0819DE2C0EFA595B25193154100000000000000005C82921B2A9DE2C052826BD76F9315410000000000000000D3BA91CC299DE2C04F3CF6F16F9315410000000000000000723FA37A299DE2C0E45A5D0C709315410000000000000000EC12CB25299DE2C037939F26709315410000000000000000765C0DCE289DE2C03A9CBB407093154100000000000000008E676E73289DE2C0BE2EB05A709315410000000000000000CBA3F215289DE2C082057C74709315410000000000000000A3A49EB5279DE2C045DD1D8E7093154100000000000000002F217752279DE2C0D47494A7709315410000000000000000F7F380EC269DE2C0188DDEC0709315410000000000000000AC1AC183269DE2C029E9FAD9709315410000000000000000F1B53C18269DE2C05D4EE8F27093154100000000000000001709F9A9259DE2C05584A50B719315410000000000000000DD79FB38259DE2C00F553124719315410000000000000000299049C5249DE2C0F28C8A3C719315410000000000000000C8F5E84E249DE2C0E1FAAF547193154100000000000000002176DFD5239DE2C04870A06C719315410000000000000000F2FD325A239DE2C02AC15A84719315410000000000000000029BE9DB229DE2C031C4DD9B719315410000000000000000D57B095B229DE2C0BA5228B371931541000000000000000063EF98D7219DE2C0E94839CA719315410000000000000000C4649E51219DE2C0B1850FE1719315410000000000000000E06A20C9209DE2C0E5EAA9F771931541000000000000000020B0253E209DE2C0485D070E7293154100000000000000001702B5B01F9DE2C097C42624729315410000000000000000304DD5201F9DE2C0990B073A729315410000000000000000529C8D8E1E9DE2C02B20A74F7293154100000000000000008E18E5F91D9DE2C050F30565729315410000000000000000C008E3621D9DE2C03C79227A72931541000000000000000039D18EC91C9DE2C063A9FB8E7293154100000000000000005CF3EF2D1C9DE2C0827E90A3729315410000000000000000460D0E901B9DE2C0B1F6DFB77293154100000000000000006AD9F0EF1A9DE2C06C13E9CB729315410000000000000000342EA04D1A9DE2C0A3D9AADF729315410000000000000000A4FD23A9199DE2C0C05124F3729315410000000000000000EB548402199DE2C0BA875406739315410000000000000000075CC959189DE2C01D8B3A197393154100000000000000005C55FBAE179DE2C0186FD52B7393154100000000000000004D9D2202179DE2C0854A243E739315410000000000000000D3A94753169DE2C0F9372650739315410000000000000000110A73A2159DE2C0CB55DA61739315410000000000000000EF65ADEF149DE2C024C63F73739315410000000000000000A47DFF3A149DE2C004AF558473931541000000000000000052297284139DE2C0513A1B957393154100000000000000008F580ECC129DE2C0DF958FA5739315410000000000000000FD11DD11129DE2C07EF3B1B5739315410000000000000000D072E755119DE2C0FE8881C573931541000000000000000064AE3698109DE2C03F90FDD4739315410000000000000000C40DD4D80F9DE2C0364725E473931541000000000000000039EFC8170F9DE2C0FBEFF7F2739315410000000000000000D3C51E550E9DE2C0CDD07401749315410000000000000000F218DF900D9DE2C020349B0F749315410000000000000000D28313CB0C9DE2C0A3686A1D7493154100000000000000000EB5C5030C9DE2C04BC1E12A749315410000000000000000296EFF3A0B9DE2C0579500387493154100000000000000001583CA700A9DE2C05D40C644749315410000000000000000B5D930A5099DE2C05222325174931541000000000000000063693CD8089DE2C08C9F435D749315410000000000000000743AF709089DE2C0D120FA68749315410000000000000000B5656B3A079DE2C05B135574749315410000000000000000F413A369069DE2C0DDE8537F7493154100000000000000007B7DA897059DE2C08F17F68974931541000000000000000093E985C4049DE2C0301A3B9474931541000000000000000001AE45F0039DE2C01070229E749315410000000000000000882EF21A039DE2C0159DABA7749315410000000000000000BCCB0D47E09CE2C016448C2D769315410000000000000000	1	1	14	\N	0	{1}
2	01020000A0187A00000200000090986773A06FE2C0A2F64D59B49915410000000000000000B8A6F9E67B6FE2C09F8F451A5F9915410000000000000000	1	1	14	\N	0	{1}
3	01020000A0187A000002000000B8A6F9E67B6FE2C09F8F451A5F9915410000000000000000B4B503A5476FE2C020BC6037E59815410000000000000000	1	1	14	\N	0	{1}
4	01020000A0187A000002000000B4B503A5476FE2C020BC6037E59815410000000000000000B00E46001A6FE2C04A7FC4C17A9815410000000000000000	1	1	14	\N	0	{1}
5	01020000A0187A0000020000003452C62DC871E2C0723D78DF3499154100000000000000007C5C7AA1BD71E2C02F49A835179915410000000000000000	1	1	14	\N	0	{1}
6	01020000A0187A000002000000B00E46001A6FE2C04A7FC4C17A981541000000000000000020A4B97F916EE2C097CCBD603C9715410000000000000000	1	1	14	\N	0	{1}
7	01020000A0187A00000200000020A4B97F916EE2C097CCBD603C9715410000000000000000F88D96F1696EE2C043210E72D89615410000000000000000	1	1	14	\N	0	{1}
8	01020000A0187A000002000000F88D96F1696EE2C043210E72D89615410000000000000000A487749C7E71E2C038876700D99615410000000000000000	1	1	14	\N	0	{1}
9	01020000A0187A00000200000088197076FE72E2C086493AA7D79615410000000000000000C8FDA4C6897BE2C079B250A7B69615410000000000000000	1	1	14	\N	0	{1}
10	01020000A0187A000002000000C8FDA4C6897BE2C079B250A7B6961541000000000000000098A7806E6E81E2C05D886B27929615410000000000000000	1	1	14	\N	0	{1}
11	01020000A0187A00000200000090DEE3894287E2C0D08D5CA36C9615410000000000000000741FCF256D88E2C0D46C690C659615410000000000000000	1	1	14	\N	0	{1}
12	01020000A0187A000002000000E80D3FE17B82E2C04146DE8BD69315410000000000000000E8AB3632E582E2C0C4389819E59315410000000000000000	1	1	14	\N	0	{1}
13	01020000A0187A000002000000247C70BA5B83E2C00E17824AF99315410000000000000000F8C0E3E88083E2C0E27174DC059415410000000000000000	1	1	14	\N	0	{1}
14	01020000A0187A0000020000004CBD859E2483E2C04DCB378283941541000000000000000024A64C596781E2C0ECD4DCBD869415410000000000000000	1	1	14	\N	0	{1}
15	01020000A0187A0000020000001CD2D794D490E2C02CA69DB53D9615410000000000000000509932EB7192E2C0D9E2E0422F9615410000000000000000	1	1	14	\N	0	{1}
16	01020000A0187A0000020000003CFE936D6F9AE2C0EF24E3A6C295154100000000000000003CBE7949869CE2C0E7CB21FFAD9515410000000000000000	1	1	14	\N	0	{1}
17	01020000A0187A0000020000003CBE7949869CE2C0E7CB21FFAD951541000000000000000080B70863529EE2C00732E555909515410000000000000000	1	1	14	\N	0	{1}
18	01020000A0187A000002000000802449A07BA2E2C063723F28D495154100000000000000007092FA3B5FA2E2C0D8884CBDD79515410000000000000000	1	1	14	\N	0	{1}
19	01020000A0187A0000020000001C3FA7DEFC6FE2C0D336C568E6991541000000000000000014D206C3CF6EE2C00FBCB235129A15410000000000000000	1	1	14	\N	0	{1}
20	01020000A0187A00000200000014D206C3CF6EE2C00FBCB235129A15410000000000000000D82CDB17E368E2C076D448DFDC9A15410000000000000000	1	1	14	\N	0	{1}
21	01020000A0187A000002000000D82CDB17E368E2C076D448DFDC9A15410000000000000000F82570711266E2C095D9E0EA3E9B15410000000000000000	1	1	14	\N	0	{1}
22	01020000A0187A000002000000202870711266E2C048D9E0EA3E9B15410000000000000000FCA5927BBF5EE2C0BDAA0F023E9C15410000000000000000	1	1	14	\N	0	{1}
23	01020000A0187A000002000000FCA5927BBF5EE2C0BDAA0F023E9C1541000000000000000050736A07055BE2C018F81896D89C15410000000000000000	1	1	14	\N	0	{1}
24	01020000A0187A00000200000050736A07055BE2C018F81896D89C15410000000000000000388D29CF8E57E2C06993A7D5979D15410000000000000000	1	1	14	\N	0	{1}
25	01020000A0187A000002000000388D29CF8E57E2C06993A7D5979D154100000000000000004C156F871755E2C061C459274B9E15410000000000000000	1	1	14	\N	0	{1}
26	01020000A0187A0000020000004C156F871755E2C061C459274B9E154100000000000000009C8DCAE1C952E2C0476F43EA329F15410000000000000000	1	1	14	\N	0	{1}
27	01020000A0187A000002000000B80C63CDC952E2C0B7B696F2329F15410000000000000000645444488E52E2C08E5A07304C9F15410000000000000000	1	1	14	\N	0	{1}
28	01020000A0187A000002000000AC706C488E52E2C08E59F62F4C9F15410000000000000000B44710B9734FE2C010ECF8EA9CA015410000000000000000	1	1	14	\N	0	{1}
29	01020000A0187A000002000000604310B9734FE2C0E6EDF8EA9CA01541000000000000000088DD7C70644FE2C02D461A65A3A015410000000000000000	1	1	14	\N	0	{1}
30	01020000A0187A00000200000088DD7C70644FE2C02D461A65A3A01541000000000000000098F24452A24CE2C0A03FCBDEA5A115410000000000000000	1	1	14	\N	0	{1}
31	01020000A0187A00000200000098F24452A24CE2C0A03FCBDEA5A115410000000000000000403EFA92BD49E2C0743029E4A6A215410000000000000000	1	1	14	\N	0	{1}
32	01020000A0187A000002000000ECF2208C7272E2C091E8F9A20E99154100000000000000001421C3150372E2C0ECC9D9660F9915410000000000000000	1	1	14	\N	0	{1}
33	01020000A0187A0000020000003C7465FE8F72E2C0FCCEAF6D0A991541000000000000000094CA1FAF8D72E2C043B1C2C3069915410000000000000000	1	1	14	\N	0	{1}
34	01020000A0187A000002000000B8FD728A5787E2C043A1EBC773951541000000000000000090C552C4AA86E2C0639AE6D57B9515410000000000000000	1	1	14	\N	0	{1}
35	01020000A0187A00000200000090C552C4AA86E2C0639AE6D57B951541000000000000000098EE80364886E2C0F91EBB92819515410000000000000000	1	1	14	\N	0	{1}
36	01020000A0187A00000200000098EE80364886E2C0F91EBB9281951541000000000000000090E90746D085E2C093C0CB24899515410000000000000000	1	1	14	\N	0	{1}
37	01020000A0187A00000200000090E90746D085E2C093C0CB24899515410000000000000000249973FB8C85E2C059D2F240909515410000000000000000	1	1	14	\N	0	{1}
38	01020000A0187A000002000000E8AB3632E582E2C0C4389819E59315410000000000000000247C70BA5B83E2C00E17824AF99315410000000000000000	1	1	14	\N	0	{1}
39	01020000A0187A000002000000B8057C333688E2C0EC1B161BD3931541000000000000000078054C063E87E2C09FC89366AC9315410000000000000000	1	1	14	\N	0	{1}
40	01020000A0187A0000020000007437B2EC6270E2C02A800077FC97154100000000000000001452CFE0E26EE2C0EF210B30FA9715410000000000000000	1	1	14	\N	0	{1}
41	01020000A0187A000002000000243FA7DEFC6FE2C0D536C568E6991541000000000000000080CF02B0EF6FE2C02528B1C3E29915410000000000000000	1	1	14	\N	0	{1}
56	01020000A0187A000002000000608DE72CD073E2C04CCE9686D49615410000000000000000BC5D32147273E2C0D70A3C45669615410000000000000000	1	1	14	\N	0	{1}
57	01020000A0187A00000200000038FEA7AAC888E2C036E98547639615410000000000000000D45BC828A689E2C0BF87A9EA5C9615410000000000000000	1	1	14	\N	0	{1}
58	01020000A0187A000002000000100B8F3C868CE2C0FA8197D84C96154100000000000000001CD2D794D490E2C02CA69DB53D9615410000000000000000	1	1	14	\N	0	{1}
42	01020000A0187A00004100000044CA63AFEF6FE2C032D9E5C3E29915410000000000000000647D8804ED6FE2C05F330318E29915410000000000000000603FA464EA6FE2C05A0B746BE199154100000000000000002CF5C1CFE76FE2C0682D3BBEE09915410000000000000000FC55EC45E56FE2C08D685B10E0991541000000000000000034EB2DC7E26FE2C0828ED761DF991541000000000000000020109153E06FE2C0AC73B2B2DE9915410000000000000000F0F11FEBDD6FE2C00AEFEE02DE9915410000000000000000588FE48DDB6FE2C02DDA8F52DD991541000000000000000098B8E83BD96FE2C02E1198A1DC99154100000000000000003C0F36F5D66FE2C09F720AF0DB9915410000000000000000F005D6B9D46FE2C07CDFE93DDB991541000000000000000068E0D189D26FE2C0293B398BDA991541000000000000000038B33265D06FE2C05E6BFBD7D999154100000000000000009063014CCE6FE2C019583324D999154100000000000000004CA7463ECC6FE2C09BEBE36FD899154100000000000000009C040B3CCA6FE2C0551210BBD7991541000000000000000008D25645C86FE2C0DFBABA05D799154100000000000000003436325AC66FE2C0E7D5E64FD69915410000000000000000C827A57AC46FE2C02A569799D59915410000000000000000546DB7A6C26FE2C06930CFE2D49915410000000000000000249D70DEC06FE2C0555B912BD49915410000000000000000241DD821BF6FE2C08BCFE073D39915410000000000000000C822F570BD6FE2C08387C0BBD29915410000000000000000ECB2CECBBB6FE2C0847F3303D29915410000000000000000B4A16B32BA6FE2C09BB53C4AD199154100000000000000006C92D2A4B86FE2C08829DF90D0991541000000000000000070F70923B76FE2C0B8DC1DD7CF9915410000000000000000181218ADB56FE2C037D2FB1CCF991541000000000000000094F20243B46FE2C09F0E7C62CE9915410000000000000000D877D0E4B26FE2C01598A1A7CD99154100000000000000007C4F8692B16FE2C02F766FECCC9915410000000000000000B8F5294CB06FE2C0F5B1E830CC991541000000000000000038B5C011AF6FE2C0CC551075CB99154100000000000000000CA74FE3AD6FE2C06A6DE9B8CA99154100000000000000009CB2DBC0AC6FE2C0CE0577FCC99915410000000000000000848D69AAAB6FE2C02F2DBC3FC9991541000000000000000090BBFD9FAA6FE2C0F2F2BB82C89915410000000000000000A48E9CA1A96FE2C0986779C5C799154100000000000000009C264AAFA86FE2C0BB9CF707C7991541000000000000000058710AC9A76FE2C0F6A4394AC699154100000000000000008C2AE1EEA66FE2C0E293428CC59915410000000000000000C4DBD120A66FE2C0037E15CEC499154100000000000000005CDCDF5EA56FE2C0BE78B50FC499154100000000000000005C510EA9A46FE2C04A9A2551C39915410000000000000000742D60FFA36FE2C0A6F96892C29915410000000000000000F430D861A36FE2C08CAE82D3C19915410000000000000000C4E978D0A26FE2C060D17514C1991541000000000000000050B3444BA26FE2C0267B4555C099154100000000000000007CB63DD2A16FE2C079C5F495BF9915410000000000000000A4E96565A16FE2C078CA86D6BE99154100000000000000009C10BF04A16FE2C0BCA4FE16BE991541000000000000000090BC4AB0A06FE2C0476F5F57BD9915410000000000000000084C0A68A06FE2C08145AC97BC9915410000000000000000F0EAFE2BA06FE2C02243E8D7BB99154100000000000000008C9229FC9F6FE2C026841618BB99154100000000000000005C098BD89F6FE2C0C5243A58BA991541000000000000000044E323C19F6FE2C061415698B999154100000000000000006481F4B59F6FE2C07BF66DD8B899154100000000000000002812FDB69F6FE2C0A9608418B8991541000000000000000048913DC49F6FE2C0869C9C58B79915410000000000000000C0C7B5DD9F6FE2C0A0C6B998B69915410000000000000000DC4B6503A06FE2C078FBDED8B599154100000000000000002C814B35A06FE2C06A570F19B5991541000000000000000090986773A06FE2C0A2F64D59B49915410000000000000000	1	1	14	\N	0	{1}
43	01020000A0187A00000200000068DAC236073EE2C0035C0AD59DA215410000000000000000E0398D4AEF3DE2C0E94E245D9DA215410000000000000000	1	1	14	\N	0	{1}
44	01020000A0187A00000200000024916A9D223EE2C0963E87BB65A215410000000000000000E0398D4AEF3DE2C0E94E245D9DA215410000000000000000	1	1	14	\N	0	{1}
45	01020000A0187A000002000000CC006F4F7D41E2C061D07ADA72A21541000000000000000024916A9D223EE2C0963E87BB65A215410000000000000000	1	1	14	\N	0	{1}
46	01020000A0187A000002000000CC006F4F7D41E2C061D07ADA72A2154100000000000000007CA6BF4B4F44E2C0376203FD80A215410000000000000000	1	1	14	\N	0	{1}
47	01020000A0187A0000020000007CA6BF4B4F44E2C0376203FD80A215410000000000000000B07203595747E2C0A3FCF68092A215410000000000000000	1	1	14	\N	0	{1}
48	01020000A0187A00000200000040C30E01A948E2C0A40FCC9E9CA215410000000000000000FC4DD013D447E2C00BF0788795A215410000000000000000	1	1	14	\N	0	{1}
49	01020000A0187A000002000000FC4DD013D447E2C00BF0788795A215410000000000000000B07203595747E2C0A3FCF68092A215410000000000000000	1	1	14	\N	0	{1}
50	01020000A0187A000002000000CCB040F4C671E2C034374825179915410000000000000000D4D1CDD95E6FE2C0D9E6635F1B9915410000000000000000	1	1	14	\N	0	{1}
51	01020000A0187A000041000000286B48E3E471E2C052AA759D139915410000000000000000402D78C6E471E2C09E6340B3139915410000000000000000C09A09A6E471E2C08DBCF6C8139915410000000000000000984A0082E471E2C0EC4D96DE139915410000000000000000C439605AE471E2C013B31CF413991541000000000000000010CB2D2FE471E2C01E8A870914991541000000000000000060C66D00E471E2C03A74D41E149915410000000000000000505825CEE371E2C0E015013414991541000000000000000094115A98E371E2C01E170B4914991541000000000000000058E6115FE371E2C0D823F05D149915410000000000000000A42D5322E371E2C007ECAD7214991541000000000000000094A024E2E271E2C0FC234287149915410000000000000000A8598D9EE271E2C0A684AA9B14991541000000000000000000D49457E271E2C0C9CBE4AF14991541000000000000000070EA420DE271E2C045BCEEC3149915410000000000000000C4D69FBFE171E2C0551EC6D7149915410000000000000000B430B46EE171E2C0CCBF68EB14991541000000000000000004ED881AE171E2C05274D4FE149915410000000000000000905C27C3E071E2C0A41507121599154100000000000000001C2B9968E071E2C0D283FE241599154100000000000000007C5EE80AE071E2C077A5B83715991541000000000000000040551FAADF71E2C0F767334A159915410000000000000000B4C54846DF71E2C0BBBF6C5C159915410000000000000000A0BC6FDFDE71E2C068A8626E159915410000000000000000109C9F75DE71E2C01B251380159915410000000000000000181AE408DE71E2C0A0407C91159915410000000000000000843F4999DD71E2C0A70D9CA21599154100000000000000008066DB26DD71E2C000A770B31599154100000000000000003839A7B1DC71E2C0CD2FF8C315991541000000000000000084B0B939DC71E2C0B6D330D4159915410000000000000000601220BFDB71E2C01FC718E415991541000000000000000088F0E741DB71E2C05D47AEF3159915410000000000000000E0261FC2DA71E2C0E09AEF0216991541000000000000000004DAD33FDA71E2C06D11DB11169915410000000000000000AC7514BBD971E2C049046F2016991541000000000000000010ABEF33D971E2C069D6A92E169915410000000000000000506F74AAD871E2C09CF4893C169915410000000000000000C4F9B11ED871E2C0BFD50D4A16991541000000000000000054C2B790D771E2C0E3FA3357169915410000000000000000C07F9500D771E2C078EFFA63169915410000000000000000E4255B6ED671E2C078496170169915410000000000000000E0E318DAD571E2C08FA9657C1699154100000000000000007022DF43D571E2C03FBB06881699154100000000000000000C82BEABD471E2C00935439316991541000000000000000000D9C711D471E2C08FD8199E169915410000000000000000AC310C76D371E2C0BA7289A81699154100000000000000008CC89CD8D271E2C0DADB90B2169915410000000000000000540A8B39D271E2C0C7F72EBC1699154100000000000000000C92E898D171E2C000B662C51699154100000000000000001427C7F6D071E2C0CA112BCE1699154100000000000000002CBB3853D071E2C04D1287D616991541000000000000000078684FAECF71E2C0AECA75DE169915410000000000000000806F1D08CF71E2C02C5AF6E51699154100000000000000003C35B560CE71E2C038EC07ED169915410000000000000000E44029B8CD71E2C088B8A9F31699154100000000000000000C3A8C0ECD71E2C03303DBF916991541000000000000000070E6F063CC71E2C0C51C9BFF16991541000000000000000004286AB8CB71E2C04F62E904179915410000000000000000B8FA0A0CCB71E2C07E3DC5091799154100000000000000008072E65ECA71E2C0A5242E0E1799154100000000000000001CB90FB1C971E2C0D49A23121799154100000000000000000C0C9A02C971E2C0DE2FA51517991541000000000000000064BA9853C871E2C06C80B218179915410000000000000000B4221FA4C771E2C004364B1B179915410000000000000000CCB040F4C671E2C016076F1D179915410000000000000000	1	1	14	\N	0	{1}
52	01020000A0187A0000410000002C6B48E3E471E2C052AA759D13991541000000000000000058FEB8DAE471E2C0DAAD5984139915410000000000000000E83B18D7E471E2C009E8386B13991541000000000000000004B366D8E471E2C0D23817521399154100000000000000002030A4DEE471E2C05280F838139915410000000000000000E4BCCFE9E471E2C02F9EE01F1399154100000000000000005CA0E7F9E471E2C00271D3061399154100000000000000003C5FE90EE571E2C0BBD5D4ED12991541000000000000000034BCD128E571E2C00CA7E8D412991541000000000000000094B89C47E571E2C0CFBC12BC129915410000000000000000B494456BE571E2C073EB56A3129915410000000000000000E8D0C693E571E2C05C03B98A129915410000000000000000302E1AC1E571E2C051D03C7212991541000000000000000044AF38F3E571E2C0EA18E65912991541000000000000000098991A2AE671E2C0F69DB841129915410000000000000000A076B765E671E2C0E619B8291299154100000000000000000C1506A6E671E2C03F40E811129915410000000000000000408AFCEAE671E2C002BD4CFA119915410000000000000000D8339034E771E2C02134E9E211991541000000000000000044B9B582E771E2C0E940C1CB1199154100000000000000008C0D61D5E771E2C07975D8B41199154100000000000000004071852CE871E2C0345A329E11991541000000000000000044741588E871E2C02E6DD28711991541000000000000000010F802E8E871E2C0B321BC71119915410000000000000000BC313F4CE971E2C0A8DFF25B1199154100000000000000005CACBAB4E971E2C01D037A46119915410000000000000000584B6521EA71E2C0B4DB5431119915410000000000000000EC4C2E92EA71E2C027AC861C119915410000000000000000C04C0407EB71E2C0CDA912081199154100000000000000008C46D57FEB71E2C00FFCFBF3109915410000000000000000E4988EFCEB71E2C0F2BB45E010991541000000000000000030081D7DEC71E2C0A0F3F2CC10991541000000000000000070C16C01ED71E2C0EB9D06BA1099154100000000000000007C5D6989ED71E2C0D5A583A71099154100000000000000000CE4FD14EE71E2C027E66C95109915410000000000000000FCCE14A4EE71E2C0F528C583109915410000000000000000A80D9836EF71E2C036278F72109915410000000000000000400871CCEF71E2C05788CD6110991541000000000000000054A38865F071E2C0D4E182511099154100000000000000005843C701F171E2C0CFB6B14110991541000000000000000050D014A1F171E2C0AF775C3210991541000000000000000088B95843F271E2C0BE8185231099154100000000000000005CF979E8F271E2C0CE1E2F1510991541000000000000000004195F90F371E2C0DD845B07109915410000000000000000A834EE3AF471E2C0BDD50CFA0F991541000000000000000030FF0CE8F471E2C0C31E45ED0F99154100000000000000006CC6A097F571E2C0715806E10F991541000000000000000040778E49F671E2C02D6652D50F9915410000000000000000A0A1BAFDF671E2C0F7152BCA0F9915410000000000000000087D09B4F771E2C0192092BF0F991541000000000000000094EC5E6CF871E2C0EF2689B50F991541000000000000000068839E26F971E2C09EB611AC0F99154100000000000000001C89ABE2F971E2C0DC442DA30F991541000000000000000020FE68A0FA71E2C0B130DD9A0F99154100000000000000002CA0B95FFB71E2C047C222930F9915410000000000000000D0EE7F20FC71E2C0B42AFF8B0F991541000000000000000004309EE2FC71E2C0CA8373850F9915410000000000000000AC74F6A5FD71E2C0EECF807F0F9915410000000000000000409D6A6AFE71E2C0EFF9277A0F99154100000000000000007C5EDC2FFF71E2C0E2D469750F9915410000000000000000F4452DF6FF71E2C0001C47710F9915410000000000000000DCBE3EBD0072E2C08D72C06D0F9915410000000000000000B416F2840172E2C0BA63D66A0F99154100000000000000000082284D0272E2C0936289680F99154100000000000000001421C3150372E2C0EBC9D9660F9915410000000000000000	1	1	14	\N	0	{1}
53	01020000A0187A000041000000AC8F17EF8F72E2C0AEE968550A9915410000000000000000B0EF96FC8F72E2C087D1DD6E0A9915410000000000000000B06902059072E2C038765B880A99154100000000000000002CA758089072E2C0C6CADDA10A9915410000000000000000542099069072E2C078C160BB0A9915410000000000000000541CC4FF8F72E2C07C4CE0D40A991541000000000000000018B1DAF38F72E2C08A5E58EE0A991541000000000000000038C3DEE28F72E2C089EBC4070B99154100000000000000009405D3CC8F72E2C037E921210B99154100000000000000000CF9BAB18F72E2C0C84F6B3A0B9915410000000000000000D4EB9A918F72E2C0911A9D530B9915410000000000000000C4F8776C8F72E2C0A348B36C0B9915410000000000000000980658428F72E2C077DDA9850B9915410000000000000000F8C641138F72E2C087E17C9E0B991541000000000000000070B53CDF8E72E2C0F46228B70B99154100000000000000002C1651A68E72E2C02B76A8CF0B9915410000000000000000B8F487688E72E2C07C36F9E70B99154100000000000000009022EB258E72E2C0BCC616000C9915410000000000000000883585DE8D72E2C0E451FD170C9915410000000000000000248661928D72E2C0AA0BA92F0C9915410000000000000000C82D8C418D72E2C01E3116470C9915410000000000000000D00412EC8C72E2C04009415E0C991541000000000000000078A000928C72E2C09AE525750C9915410000000000000000C05066338C72E2C0D522C18B0C99154100000000000000002C1E52D08B72E2C04F290FA20C991541000000000000000050C7D3688B72E2C0A86D0CB80C991541000000000000000054BEFBFC8A72E2C05771B5CD0C99154100000000000000006026DB8C8A72E2C035C306E30C9915410000000000000000DCD083188A72E2C00C00FDF70C9915410000000000000000943A08A08972E2C01ED3940C0D9915410000000000000000D4887B238972E2C0AEF6CA200D99154100000000000000006086F1A28872E2C089349C340D991541000000000000000040A07E1E8872E2C07C6605480D99154100000000000000008CE237968772E2C0E576035B0D991541000000000000000004F5320A8772E2C02261936D0D9915410000000000000000C417867A8672E2C01732B27F0D9915410000000000000000901F48E78572E2C09E085D910D9915410000000000000000447290508572E2C0FF1591A20D9915410000000000000000300377B68472E2C0639E4BB30D99154100000000000000001C4F14198472E2C043F989C30D9915410000000000000000A05881788372E2C0D19149D30D9915410000000000000000ECA3D7D48272E2C069E787E20D9915410000000000000000E432312E8272E2C0EB8D42F10D9915410000000000000000FC80A8848172E2C0272E77FF0D9915410000000000000000E47E58D88072E2C03C86230D0E9915410000000000000000688E5C298072E2C0EC69451A0E9915410000000000000000FC7DD0777F72E2C0FBC2DA260E99154100000000000000004884D0C37E72E2C08491E1320E9915410000000000000000D83B790D7E72E2C049EC573E0E9915410000000000000000589EE7547D72E2C0FC003C490E99154100000000000000002C00399A7C72E2C092148C530E9915410000000000000000A80B8BDD7B72E2C08383465D0E99154100000000000000005CBCFB1E7B72E2C00FC269660E99154100000000000000005C5AA95E7A72E2C07C5CF46E0E99154100000000000000006875B29C7972E2C053F7E4760E991541000000000000000014E035D97872E2C0944F3A7E0E9915410000000000000000DCAA52147872E2C0EA3AF3840E9915410000000000000000441F284E7772E2C0DFA70E8B0E9915410000000000000000C4BAD5867672E2C0019E8B900E9915410000000000000000E8297BBE7572E2C00F3E69950E99154100000000000000002C4338F57472E2C017C2A6990E9915410000000000000000F4012D2B7472E2C09A7D439D0E9915410000000000000000888179607372E2C0A5DD3EA00E9915410000000000000000E8F73D957272E2C0EA6898A20E9915410000000000000000A4B09AC97172E2C0D1BF4FA40E9915410000000000000000	1	1	14	\N	0	{1}
54	01020000A0187A000002000000D89B49C2A180E2C0FC3FA867B79615410000000000000000A87E5C406C80E2C0D62D7766989615410000000000000000	1	1	14	\N	0	{1}
55	01020000A0187A000002000000C04197326F81E2C0CDE87E249296154100000000000000008CDEE3894287E2C0D08D5CA36C9615410000000000000000	1	1	14	\N	0	{1}
59	01020000A0187A000002000000509932EB7192E2C0D9E2E0422F9615410000000000000000C8BEA0104994E2C0B5CCF069169615410000000000000000	1	1	14	\N	0	{1}
60	01020000A0187A000002000000C8BEA0104994E2C0B5CCF069169615410000000000000000BC4E10851C97E2C0559F1BC1ED9515410000000000000000	1	1	14	\N	0	{1}
61	01020000A0187A0000020000003CCD6877948CE2C0791D92A64C961541000000000000000030996977948CE2C0D30A93A64C9615410000000000000000	1	1	14	\N	0	{1}
62	01020000A0187A000002000000705441696B71E2C038876700D9961541000000000000000088197076FE72E2C086493AA7D79615410000000000000000	1	1	14	\N	0	{1}
63	01020000A0187A000002000000802449A07BA2E2C063723F28D495154100000000000000004CF2D17336A1E2C05129E6D5AB9515410000000000000000	1	1	14	\N	0	{1}
64	01020000A0187A0000020000004CF2D17336A1E2C05129E6D5AB951541000000000000000070585B5B7FA0E2C08AF61C359D9515410000000000000000	1	1	14	\N	0	{1}
65	01020000A0187A00000200000070585B5B7FA0E2C08AF61C359D95154100000000000000002C73E230D49FE2C0398B0853959515410000000000000000	1	1	14	\N	0	{1}
66	01020000A0187A0000020000002C73E230D49FE2C0398B0853959515410000000000000000241F30B6D09EE2C02907485F8E9515410000000000000000	1	1	14	\N	0	{1}
67	01020000A0187A00000200000078585B5B7FA0E2C089F61C359D951541000000000000000048255C5B7FA0E2C0DCE31D359D9515410000000000000000	1	1	14	\N	0	{1}
68	01020000A0187A0000020000007C585B5B7FA0E2C089F61C359D9515410000000000000000B4F3BC52B7A0E2C0F38F2EFD969515410000000000000000	1	1	14	\N	0	{1}
69	01020000A0187A000002000000B4F3BC52B7A0E2C0F38F2EFD969515410000000000000000ACF0434C96A1E2C00B7E5104889515410000000000000000	1	1	14	\N	0	{1}
70	01020000A0187A000002000000ACF0434C96A1E2C00B7E51048895154100000000000000006CF75C638BA2E2C02D7F95A07D9515410000000000000000	1	1	14	\N	0	{1}
71	01020000A0187A00000200000080B70863529EE2C00732E555909515410000000000000000241F30B6D09EE2C02907485F8E9515410000000000000000	1	1	14	\N	0	{1}
72	01020000A0187A0000020000003CFE936D6F9AE2C0EF24E3A6C29515410000000000000000BC4E10851C97E2C0559F1BC1ED9515410000000000000000	1	1	14	\N	0	{1}
73	01020000A0187A000002000000ACE99B63788BE2C0ED907AB97A9615410000000000000000A07A8111938AE2C0C652E6947E9615410000000000000000	1	1	14	\N	0	{1}
74	01020000A0187A000002000000A07A8111938AE2C0C652E6947E96154100000000000000005C8FC2F5488AE2C0BA1E85EB6E9615410000000000000000	1	1	14	\N	0	{1}
75	01020000A0187A0000020000005C8FC2F5488AE2C0BA1E85EB6E9615410000000000000000103F8E04DF89E2C041B3EC475F9615410000000000000000	1	1	14	\N	0	{1}
76	01020000A0187A000041000000D05BC828A689E2C0BE87A9EA5C96154100000000000000002426EC1EA789E2C0E227DEE35C96154100000000000000005498F415A889E2C0FAAC99DD5C96154100000000000000006437CF0DA989E2C00F8FDCD75C96154100000000000000009C786906AA89E2C0093CA7D25C9615410000000000000000E8C2B0FFAA89E2C0A417FACD5C96154100000000000000004C7092F9AB89E2C0727BD5C95C961541000000000000000040CFFBF3AC89E2C0C9B639C65C96154100000000000000000C24DAEEAD89E2C0C60E27C35C961541000000000000000038AA1AEAAE89E2C041BE9DC05C96154100000000000000000496AAE5AF89E2C0CDF59DBE5C9615410000000000000000A81577E1B089E2C0B6DB27BD5C9615410000000000000000E4526DDDB189E2C0F48B3BBC5C961541000000000000000058747AD9B289E2C03918D9BB5C9615410000000000000000E89E8BD5B389E2C0E18700BC5C961541000000000000000028F78DD1B489E2C0F7D7B1BC5C9615410000000000000000D0A26ECDB589E2C03AFBECBD5C961541000000000000000018CA1AC9B689E2C015DAB1BF5C96154100000000000000002C997FC4B789E2C0A65200C25C96154100000000000000007C418ABFB889E2C0C438D8C45C961541000000000000000054FB27BAB989E2C0F85539C85C96154100000000000000000C0746B4BA89E2C08C6923CC5C961541000000000000000098AED1ADBB89E2C0872896D05C9615410000000000000000D846B8A6BC89E2C0B93D91D55C96154100000000000000000831E79EBD89E2C0BF4914DB5C961541000000000000000024DC4B96BE89E2C00AE31EE15C961541000000000000000044C6D38CBF89E2C0E695B0E75C96154100000000000000000C7E6C82C089E2C084E4C8EE5C9615410000000000000000F8A30377C189E2C0064767F65C9615410000000000000000D4EB866AC289E2C07F2B8BFE5C96154100000000000000000C1EE45CC389E2C00FF633075D96154100000000000000000C19094EC489E2C0DC0061105D96154100000000000000009CD2E33DC589E2C02B9C111A5D96154100000000000000003459622CC689E2C06C0E45245D961541000000000000000060D57219C789E2C03F94FA2E5D9615410000000000000000048B0305C889E2C08F60313A5D9615410000000000000000CCDA02EFC889E2C0989CE8455D961541000000000000000054435FD7C989E2C0F9671F525D9615410000000000000000A06207BECA89E2C0CBD8D45E5D961541000000000000000050F7E9A2CB89E2C0A8FB076C5D9615410000000000000000F4E1F585CC89E2C0C6D3B7795D96154100000000000000004C261A67CD89E2C0075BE3875D9615410000000000000000A0EC4546CE89E2C0098289965D9615410000000000000000E8826823CF89E2C04230A9A55D9615410000000000000000285E71FECF89E2C00D4441B55D96154100000000000000008C1B50D7D089E2C0C59250C55D9615410000000000000000BC81F4ADD189E2C0D9E8D5D55D961541000000000000000018824E82D289E2C0E509D0E65D9615410000000000000000C8394E54D389E2C0C6B03DF85D961541000000000000000014F3E323D489E2C0B68F1D0A5E9615410000000000000000782600F1D489E2C064506E1C5E9615410000000000000000D07B93BBD589E2C00B942E2F5E961541000000000000000088CB8E83D689E2C090F35C425E9615410000000000000000C01FE348D789E2C09CFFF7555E961541000000000000000058B5810BD889E2C0B640FE695E961541000000000000000014FD5BCBD889E2C05F376E7E5E9615410000000000000000C49C6388D989E2C02F5C46935E96154100000000000000003C708A42DA89E2C0F71F85A85E9615410000000000000000708AC2F9DA89E2C0D6EB28BE5E96154100000000000000008436FEADDB89E2C05F2130D45E9615410000000000000000C0F82F5FDC89E2C0B31A99EA5E9615410000000000000000A88F4A0DDD89E2C0A22A62015F9615410000000000000000ECF440B8DD89E2C0D19C89185F9615410000000000000000645E0660DE89E2C0CFB50D305F9615410000000000000000103F8E04DF89E2C042B3EC475F9615410000000000000000	1	1	14	\N	0	{1}
77	01020000A0187A000002000000D4650318608CE2C04504D66B4F9615410000000000000000E03A5E0F1B8CE2C05F3DB0E1599615410000000000000000	1	1	14	\N	0	{1}
78	01020000A0187A000002000000E03A5E0F1B8CE2C05F3DB0E15996154100000000000000005CF539AABD8BE2C0DD527C676A9615410000000000000000	1	1	14	\N	0	{1}
79	01020000A0187A0000020000005CF539AABD8BE2C0DD527C676A9615410000000000000000ACE99B63788BE2C0ED907AB97A9615410000000000000000	1	1	14	\N	0	{1}
80	01020000A0187A000041000000D8650318608CE2C04604D66B4F96154100000000000000007824F889608CE2C0FF7FC75A4F9615410000000000000000ACEA8FFD608CE2C0C943E5494F9615410000000000000000486BC672618CE2C07BF02F394F9615410000000000000000B44997E9618CE2C04025A8284F96154100000000000000001C1AFE61628CE2C0917F4E184F96154100000000000000008061F6DB628CE2C02D9B23084F9615410000000000000000FC957B57638CE2C01A1228F84E9615410000000000000000E01E89D4638CE2C0987C5CE84E9615410000000000000000E4541A53648CE2C01F71C1D84E961541000000000000000058822AD3648CE2C0588457C94E96154100000000000000004CE3B454658CE2C01A491FBA4E9615410000000000000000B0A5B4D7658CE2C0605019AB4E96154100000000000000009CE9245C668CE2C04729469C4E961541000000000000000070C100E2668CE2C00A61A68D4E961541000000000000000000324369678CE2C0F7823A7F4E9615410000000000000000CC32E7F1678CE2C0711803714E961541000000000000000028AEE77B688CE2C0E5A800634E961541000000000000000074813F07698CE2C0C7B933554E9615410000000000000000487DE993698CE2C091CE9C474E9615410000000000000000A465E0216A8CE2C0B5683C3A4E96154100000000000000002CF21EB16A8CE2C0A207132D4E96154100000000000000004CCE9F416B8CE2C0B92821204E961541000000000000000070995DD36B8CE2C04B4767134E961541000000000000000040E752666C8CE2C092DCE5064E9615410000000000000000C43F7AFA6C8CE2C0B15F9DFA4D9615410000000000000000AC1FCE8F6D8CE2C0A8458EEE4D96154100000000000000006CF848266E8CE2C05A01B9E24D96154100000000000000008C30E5BD6E8CE2C07F031ED74D9615410000000000000000BC239D566F8CE2C0A7BABDCB4D961541000000000000000038236BF06F8CE2C02F9398C04D9615410000000000000000C875498B708CE2C043F7AEB54D961541000000000000000024583227718CE2C0D84E01AB4D961541000000000000000010FD1FC4718CE2C0A7FF8FA04D9615410000000000000000A48D0C62728CE2C02A6D5B964D96154100000000000000007029F200738CE2C09AF8638C4D9615410000000000000000C8E6CAA0738CE2C0E800AA824D9615410000000000000000F0D29041748CE2C0BCE22D794D96154100000000000000005CF23DE3748CE2C06FF8EF6F4D9615410000000000000000E440CC85758CE2C00E9AF0664D961541000000000000000004B23529768CE2C04D1D305E4D9615410000000000000000003174CD768CE2C08DD5AE554D961541000000000000000040A18172778CE2C0D1136D4D4D961541000000000000000070DE5718788CE2C0C4266B454D9615410000000000000000CCBCF0BE788CE2C0AB5AA93D4D961541000000000000000044094666798CE2C06DF927364D9615410000000000000000C889510E7A8CE2C0894AE72E4D961541000000000000000090FD0CB77A8CE2C01593E7274D96154100000000000000003C1D72607B8CE2C0BF1529214D96154100000000000000000C9B7A0A7C8CE2C0C512AC1A4D9615410000000000000000502320B57C8CE2C0F5C770144D9615410000000000000000605C5C607D8CE2C0AE70770E4D961541000000000000000004E7280C7E8CE2C0D745C0084D9615410000000000000000B05E7FB87E8CE2C0E57D4B034D96154100000000000000009C5959657F8CE2C0CE4C19FE4C96154100000000000000003C69B012808CE2C016E429F94C9615410000000000000000381A7EC0808CE2C0BD727DF44C9615410000000000000000F0F4BB6E818CE2C04A2514F04C9615410000000000000000847D631D828CE2C0C325EEEB4C96154100000000000000002C346ECC828CE2C0AC9B0BE84C96154100000000000000006895D57B838CE2C00AAC6CE44C96154100000000000000004C1A932B848CE2C0567911E14C9615410000000000000000BC38A0DB848CE2C08E23FADD4C96154100000000000000009863F68B858CE2C021C826DB4C9615410000000000000000100B8F3C868CE2C0FB8197D84C9615410000000000000000	1	1	14	\N	0	{1}
81	01020000A0187A000002000000F0F9EF03089DE2C057F24675979515410000000000000000E4B79436369DE2C093FABDA7A29515410000000000000000	1	1	14	\N	0	{1}
82	01020000A0187A000002000000586846493B88E2C0AA3A9597419615410000000000000000741FCF256D88E2C0D46C690C659615410000000000000000	1	1	14	\N	0	{1}
83	01020000A0187A000002000000B46746493B88E2C0AE3A9597419615410000000000000000D46478CF5A88E2C07EA0A6E7409615410000000000000000	1	1	14	\N	0	{1}
84	01020000A0187A000002000000D46478CF5A88E2C07EA0A6E7409615410000000000000000980417098388E2C0725243825D9615410000000000000000	1	1	14	\N	0	{1}
115	01020000A0187A00000D000000802449A07BA2E2C063723F28D49515410000000000000000D0FB942936A4E2C060F1F8D20D9615410000000000000000709E5BE48DA5E2C09E074D1C3C9615410000000000000000585F817F19A8E2C05D289F978D96154100000000000000003CF419D894AAE2C0E3BA59B0DC961541000000000000000048E0F2A2FAABE2C0BC714A3508971541000000000000000070063DDB29AEE2C0319AB58E49971541000000000000000068881D04F8AEE2C07A9B1479609715410000000000000000805943E7C7B0E2C0D7B122F9999715410000000000000000849A356C0DB3E2C0FEBC59CAD897154100000000000000002C407FC5E1B3E2C05375A10BF09715410000000000000000D86B4AADA4B4E2C0F1FC7C60049815410000000000000000644497322BB4E2C047C37768189815410000000000000000	1	1	14	\N	0	{1}
116	01020000A0187A00000A000000A84FABB4A1B3E2C09B12F53F299815410000000000000000B8D9860235B3E2C06F6EAC3D3A9815410000000000000000047236789CB1E2C0C19316DB1598154100000000000000008830A787BAAFE2C038290B0CEC9715410000000000000000C8C6248A4BAEE2C06A41CE26CE971541000000000000000004FE91F6F9ACE2C0E8DF97ADB5971541000000000000000098646115D3ABE2C073022757A29715410000000000000000C8B6751152AAE2C086776718A19715410000000000000000E838F82384A8E2C086776718A1971541000000000000000054107AB16EA6E2C086776718A19715410000000000000000	1	1	14	\N	0	{1}
117	01020000A0187A00000900000054107AB16EA6E2C086776718A1971541000000000000000054107AB16EA6E2C0B7B9FE0DB69715410000000000000000B4338CEC60A6E2C0BD8CE9A9CC9715410000000000000000D4BDF6AF3EA6E2C0C8424F55ED971541000000000000000014C74049FFA5E2C0E49127842898154100000000000000004C2D8B1DA6A5E2C0EA619DA7729815410000000000000000C4FAD54F30A5E2C05A5EAEE4CE981541000000000000000000A66924CEA4E2C0708EBFD01C99154100000000000000003C841A7386A4E2C0141FCB0D569915410000000000000000	1	1	14	\N	0	{1}
118	01020000A0187A0000060000003C841A7386A4E2C0141FCB0D569915410000000000000000988146B368A4E2C02D212CCE6D9915410000000000000000F4BDB5B6FCA3E2C0A11D3D0BCA99154100000000000000006891938D52A3E2C036A596D2509A154100000000000000003C3088C8D3A2E2C09137DED3C69A15410000000000000000381B620BB8A2E2C023EE653EDE9A15410000000000000000	1	1	14	\N	0	{1}
85	01020000A0187A00004100000038FEA7AAC888E2C037E98547639615410000000000000000702C443DC788E2C01F6269516396154100000000000000008800FDCDC588E2C0449E235A639615410000000000000000DCEA0E5DC488E2C0FA2DB36163961541000000000000000074A1B6EAC288E2C0BED21668639615410000000000000000E4153177C188E2C0677F4D6D639615410000000000000000586BBB02C088E2C0515856716396154100000000000000007CEC928DBE88E2C088B330746396154100000000000000006C01F517BD88E2C0D918DC756396154100000000000000009C251FA2BB88E2C0F2415876639615410000000000000000B0DD4E2CBA88E2C0631AA5756396154100000000000000005CADC1B6B888E2C0A6BFC273639615410000000000000000500DB541B788E2C01E81B170639615410000000000000000106166CDB588E2C001E0716C639615410000000000000000E4EC125AB488E2C04C8F0467639615410000000000000000B8CBF7E7B288E2C09C736A6063961541000000000000000010E55177B188E2C013A3A45863961541000000000000000010E35D08B088E2C02165B44F6396154100000000000000006828589BAE88E2C053329B4563961541000000000000000078C67C30AD88E2C016B45A3A639615410000000000000000687307C8AB88E2C06BC4F42D6396154100000000000000004C803362AA88E2C0A06D6B2063961541000000000000000074CF3BFFA888E2C0F6E9C011639615410000000000000000ACCA5A9FA788E2C044A3F7016396154100000000000000009859CA42A688E2C0933212F16296154100000000000000004CD8C3E9A488E2C0AB5F13DF629615410000000000000000B40D8094A388E2C0A720FECB62961541000000000000000060223743A288E2C07099D5B76296154100000000000000002C9720F6A088E2C03C1B9DA2629615410000000000000000203C73AD9F88E2C00324588C629615410000000000000000882765699E88E2C0EC5D0A75629615410000000000000000E4AC2B2A9D88E2C0AE9EB75C6296154100000000000000004454FBEF9B88E2C0F7E663436296154100000000000000008CD107BB9A88E2C0BB611329629615410000000000000000F8FB838B9988E2C08863CA0D629615410000000000000000C8C5A1619888E2C0D0698DF1619615410000000000000000FC33923D9788E2C02D1A61D46196154100000000000000004856851F9688E2C099414AB6619615410000000000000000343FAA079588E2C0A8D34D976196154100000000000000003CFC2EF69388E2C0B5E97077619615410000000000000000688E40EB9288E2C00BC2B856619615410000000000000000D4E20AE79188E2C00ABF2A356196154100000000000000005CCBB8E99088E2C04466CC12619615410000000000000000B4F773F38F88E2C0945FA3EF60961541000000000000000080EE64048F88E2C02B74B5CB6096154100000000000000009806B31C8E88E2C0A68D08A7609615410000000000000000AC60843C8D88E2C00CB5A281609615410000000000000000E0E0FD638C88E2C0D4118A5B609615410000000000000000D42843938B88E2C0E4E8C434609615410000000000000000B89176CA8A88E2C0809B590D609615410000000000000000A826B9098A88E2C048A64EE55F96154100000000000000003C9F2A518988E2C01FA0AABC5F96154100000000000000004C5AE9A08888E2C01B3974935F9615410000000000000000FC5812F98788E2C06739B2695F9615410000000000000000F039C1598788E2C024806B3F5F9615410000000000000000B43410C38688E2C05002A7145F9615410000000000000000801518358688E2C098C96BE95E96154100000000000000001839F0AF8588E2C033F3C0BD5E9615410000000000000000F888AE338588E2C0B4AEAD915E9615410000000000000000B47767C08488E2C0E23C39655E9615410000000000000000A0FD2D568488E2C07DEE6A385E9615410000000000000000AC9513F58388E2C014234A0B5E9615410000000000000000883A289D8388E2C0C347DEDD5D961541000000000000000000647A4E8388E2C006D62EB05D9615410000000000000000980417098388E2C0725243825D9615410000000000000000	1	1	14	\N	0	{1}
86	01020000A0187A000059000000586846493B88E2C0AA3A95974196154100000000000000002C33D5B9DC87E2C01F1EAFDBE49515410000000000000000B0E19EA45687E2C0B2FD2BFBBF9515410000000000000000608FB92A6286E2C06C807977A8951541000000000000000080EB41188885E2C03549D7B28F95154100000000000000009CAFC7A4D584E2C0BB2B5B68799515410000000000000000BCB719E31F84E2C0207F27CC589515410000000000000000C0F889EB7882E2C0ECD75ACC119515410000000000000000C0A184DD5782E2C037579C69059515410000000000000000B09E59F30482E2C0CC3C9FDBDD941541000000000000000068225326B681E2C091EDB4D5BF9415410000000000000000BC1C7EFD7E81E2C01A0FBA45A4941541000000000000000024A64C596781E2C0ECD4DCBD86941541000000000000000098DEFA965781E2C02EDFEF5D5F941541000000000000000024A64C596781E2C0F14200A42E94154100000000000000008CF008B09281E2C092411A5C01941541000000000000000068225326B681E2C08128917EEC9315410000000000000000B8EB8D841982E2C02B9AA1A6DE93154100000000000000008C579A50BC82E2C0D6C1BB3CD193154100000000000000009453B4787A83E2C0AD404242CD931541000000000000000064D07CACDE85E2C01D052FBFCD9315410000000000000000D042383F3C87E2C03A2852DACF9315410000000000000000A8C8BF273089E2C09D0FDA5BD69315410000000000000000504053EE368AE2C0949955C7D993154100000000000000004F045481388AE2C06FA6E1CBD99315410000000000000000B3752D153A8AE2C03C680BCFD9931541000000000000000022BA91A93B8AE2C0DF42D2D0D993154100000000000000007CDC323E3D8AE2C0AADE35D1D99315410000000000000000E7DBC2D23E8AE2C0672836D0D99315410000000000000000D7BAF366408AE2C06351D3CDD99315410000000000000000148E77FA418AE2C060CF0DCAD99315410000000000000000C58B008D438AE2C07E5CE6C4D99315410000000000000000691A411E458AE2C019F75DBED99315410000000000000000D3DFEBAD468AE2C097E175B6D993154100000000000000000ED0B33B488AE2C02BA22FADD99315410000000000000000383C4CC7498AE2C089028DA2D993154100000000000000004EE168504B8AE2C08D0F9096D99315410000000000000000DCF6BDD64C8AE2C0D6183B89D993154100000000000000009A3D005A4E8AE2C055B0907AD99315410000000000000000EF0DE5D94F8AE2C0CEA9936AD9931541000000000000000052662256518AE2C04B1A4759D9931541000000000000000093F96ECE528AE2C08757AE46D99315410000000000000000F73C8242548AE2C046F7CC32D99315410000000000000000387614B2558AE2C0A5CEA61DD9931541000000000000000059C9DE1C578AE2C05EF13F07D993154100000000000000004B469B82588AE2C0FEB09CEFD893154100000000000000006CF604E3598AE2C0119CC1D6D89315410000000000000000D3E9D73D5B8AE2C03E7DB3BCD893154100000000000000006544D1925C8AE2C05F5A77A1D89315410000000000000000BD4AAFE15D8AE2C086731285D89315410000000000000000D46E312A5F8AE2C0F8418A67D89315410000000000000000765C186C608AE2C02677E448D89315410000000000000000750526A7618AE2C08DFB2629D89315410000000000000000A0AD1DDB628AE2C096ED5708D893154100000000000000007BF6C307648AE2C065A07DE6D79315410000000000000000ADEADE2C658AE2C0A59A9EC3D793154100000000000000002F09364A668AE2C04395C19FD793154100000000000000002E50925F678AE2C0247AED7AD79315410000000000000000A847BE6C688AE2C0CE622955D79315410000000000000000BC0B8671698AE2C00A977C2ED79315410000000000000000A556B76D6A8AE2C07E8BEE06D79315410000000000000000728A21616B8AE2C03DE086DED6931541000000000000000060BA954B6C8AE2C04C5F4DB5D69315410000000000000000E9B3E62C6D8AE2C025FB498BD693154100000000000000007A07E9046E8AE2C02ECD8460D69315410000000000000000CF1073D36E8AE2C025140635D6931541000000000000000001FF5C986F8AE2C09232D608D693154100000000000000002DDC8053708AE2C020ADFDDBD59315410000000000000000C794BA04718AE2C0FE2885AED5931541000000000000000090FEE7AB718AE2C0326A7580D5931541000000000000000029DFE848728AE2C0EC51D751D593154100000000000000004EF29EDB728AE2C0C9DCB322D59315410000000000000000A7EFED63738AE2C0202114F3D493154100000000000000003F90BBE1738AE2C0384D01C3D493154100000000000000009293EF54748AE2C08DA58492D493154100000000000000003EC473BD748AE2C0FF82A761D4931541000000000000000046FC331B758AE2C007517330D49315410000000000000000F9281E6E758AE2C0E98BF1FED393154100000000000000006A4E22B6758AE2C0DABE2BCDD39315410000000000000000888A32F3758AE2C030822B9BD39315410000000000000000C9174325768AE2C08279FA68D393154100000000000000006F4F4A4C768AE2C0D151A236D3931541000000000000000066AB4068768AE2C0A7BF2C04D39315410000000000000000B6C72079768AE2C03B7DA3D1D293154100000000000000008F63E77E768AE2C08F48109FD29315410000000000000000E4619379768AE2C091E17C6CD29315410000000000000000A9C92569768AE2C03708F339D293154100000000000000009CC5A14D768AE2C0A17A7C07D29315410000000000000000E8C254AB5D8AE2C0EE6D270EAC9315410000000000000000	1	1	14	\N	0	{1}
87	01020000A0187A000002000000EC432155F19BE2C038D6F62A939315410000000000000000A46717D6629CE2C0544FC2148E9315410000000000000000	1	1	14	\N	0	{1}
88	01020000A0187A00000200000084167CFA0D9DE2C0B9C14769869315410000000000000000BCCB0D47E09CE2C016448C2D769315410000000000000000	1	1	14	\N	0	{1}
89	01020000A0187A000002000000B8F76D2BC7A2E2C0CF00C8F71293154100000000000000002CF6D49C20A2E2C0DA6E69CFAB9215410000000000000000	1	1	14	\N	0	{1}
90	01020000A0187A0000020000007C0704F469A2E2C009C7E33BD99215410000000000000000A8F7B70B2FA2E2C00E8550A0DA9215410000000000000000	1	1	14	\N	0	{1}
91	01020000A0187A0000020000002CF6D49C20A2E2C0DA6E69CFAB9215410000000000000000584F5A2ACBA1E2C047561CAC899215410000000000000000	1	1	14	\N	0	{1}
92	01020000A0187A00000200000064A4ACAC0E79E2C040651E73A39615410000000000000000AC19AD6CB773E2C093B64486B79615410000000000000000	1	1	14	\N	0	{1}
93	01020000A0187A000002000000C4E625782479E2C002D6FA91699615410000000000000000E8343309DD78E2C0A8E27A9E6A9615410000000000000000	1	1	14	\N	0	{1}
94	01020000A0187A000002000000E8343309DD78E2C0A8E27A9E6A961541000000000000000064A4ACAC0E79E2C040651E73A39615410000000000000000	1	1	14	\N	0	{1}
95	01020000A0187A00000200000054DA32915E49E2C009B89B20A3A21541000000000000000040C30E01A948E2C0A40FCC9E9CA215410000000000000000	1	1	14	\N	0	{1}
96	01020000A0187A000002000000403EFA92BD49E2C0743029E4A6A21541000000000000000054DA32915E49E2C009B89B20A3A215410000000000000000	1	1	14	\N	0	{1}
97	01020000A0187A000043000000043FF53D8471E2C07FE84991219815410000000000000000A4BCBAC78371E2C0BBF694B81F98154100000000000000007BD8189D8371E2C0973713691F981541000000000000000008030A628371E2C0EF87BB191F9815410000000000000000575698168371E2C0067A9BCA1E9815410000000000000000F5B9D0BA8271E2C09D96C07B1E9815410000000000000000C0E0C24E8271E2C09E5A382D1E9815410000000000000000364681D28171E2C0D03410DF1D98154100000000000000004A2B21468171E2C08B8355911D9815410000000000000000C592BAA98071E2C06F9215441D9815410000000000000000273D68FD7F71E2C01B985DF71C981541000000000000000016A447417F71E2C0EFB33AAB1C981541000000000000000052F578757E71E2C0C8EBB95F1C9815410000000000000000350D1F9A7D71E2C0CB29E8141C9815410000000000000000BA705FAF7C71E2C02B3AD2CA1B9815410000000000000000174762B57B71E2C0FCC884811B9815410000000000000000DA5252AC7A71E2C006600C391B981541000000000000000099EA5C947971E2C0A16475F11A981541000000000000000036F1B16D7871E2C09615CCAA1A9815410000000000000000A6CD83387771E2C007891C651A9815410000000000000000596207F57571E2C05CAA72201A98154100000000000000002B0474A37471E2C03C38DADC199815410000000000000000ED7003447371E2C089C25E9A19981541000000000000000086C5F1D67171E2C067A80B59199815410000000000000000AA737D5C7071E2C04616EC181998154100000000000000002A37E7D46E71E2C0FF030BDA189815410000000000000000E50A72406D71E2C0EE32739C189815410000000000000000521D639F6B71E2C0202C2F60189815410000000000000000A7C401F26971E2C0823E4925189815410000000000000000AB7297386871E2C01E7DCBEB17981541000000000000000022A86F736671E2C063BDBFB3179815410000000000000000E3E7D7A26471E2C078952F7D1798154100000000000000009AA91FC76271E2C0945A2448179815410000000000000000294C98E06071E2C0691FA714179815410000000000000000C50795EF5E71E2C094B2C0E2169815410000000000000000B4DF6AF45C71E2C01F9D79B2169815410000000000000000C69370EF5A71E2C00621DA831698154100000000000000007B91FEE05871E2C0D337EA56169815410000000000000000E7E46EC95671E2C03D91B12B16981541000000000000000049291DA95471E2C0D89137021698154100000000000000005C7966805271E2C0D45183DA159815410000000000000000735FA94F5071E2C0C29B9BB415981541000000000000000044C545174E71E2C06EEB869015981541000000000000000086E39CD74B71E2C0C16C4B6E1598154100000000000000004E3111914971E2C0B5FAEE4D159815410000000000000000365306444771E2C0521E772F159815410000000000000000560AE1F04471E2C0BE0DE912159815410000000000000000022307984271E2C057AB49F81498154100000000000000006663DF394071E2C0DF849DDF149815410000000000000000F079D1D63D71E2C0B2D2E8C814981541000000000000000091EB456F3B71E2C00F772FB4149815410000000000000000E101A6033971E2C06EFD74A114981541000000000000000019B95B943671E2C0E599BC90149815410000000000000000F5ADD1213471E2C09A280982149815410000000000000000760B73AC3171E2C0472D5D751498154100000000000000008D78AB342F71E2C0CCD2BA6A149815410000000000000000B105E7BA2C71E2C0CFEA2362149815410000000000000000641A923F2A71E2C070ED995B149815410000000000000000AA6219C32771E2C003F91D571498154100000000000000006CBCE9452571E2C0E2D1B054149815410000000000000000E32470C82271E2C04EE25254149815410000000000000000E8A5194B2071E2C0563A0456149815410000000000000000564353CE1D71E2C0DC8FC45914981541000000000000000063E889521B71E2C09D3E935F149815410000000000000000FB542AD81871E2C04E486F67149815410000000000000000280BA15F1671E2C0C554577114981541000000000000000018D6DDBAEF6EE2C09045CE29189815410000000000000000	1	1	14	\N	0	{1}
119	01020000A0187A000002000000C45D3D027248E2C01C2C448AB4A21541000000000000000040C30E01A948E2C0A40FCC9E9CA215410000000000000000	1	1	14	\N	0	{1}
120	01020000A0187A0000020000001068C58D2BB4E2C047C37768189815410000000000000000A84FABB4A1B3E2C09B12F53F299815410000000000000000	1	1	14	\N	0	{1}
121	01020000A0187A000002000000A8243233E0B3E2C0154F519D2198154100000000000000007055766AFCB3E2C02DD53924259815410000000000000000	1	1	14	\N	0	{1}
122	01020000A0187A0000020000009C6637518DA5E2C0B34F44128698154100000000000000009C4E95D57BA2E2C0E2EB8265769815410000000000000000	1	1	14	\N	0	{1}
123	01020000A0187A0000020000009C4E95D57BA2E2C0E2EB82657698154100000000000000009C4E95D57BA2E2C0E66580825F9815410000000000000000	1	1	14	\N	0	{1}
124	01020000A0187A00000200000008F456534BA5E2C0F50CF0BDB998154100000000000000002863E71BECA6E2C0652E230FC29815410000000000000000	1	1	14	\N	0	{1}
125	01020000A0187A0000020000002863E71BECA6E2C0652E230FC298154100000000000000008030B6B500A7E2C08EC889F1B59815410000000000000000	1	1	14	\N	0	{1}
126	01020000A0187A000002000000A86D7606CAA4E2C0645A351A2099154100000000000000003430E1073CA4E2C0B942CD521D9915410000000000000000	1	1	14	\N	0	{1}
127	01020000A0187A0000020000003430E1073CA4E2C0B942CD521D99154100000000000000000C6AC8E0EA9FE2C0334EAE1EF99815410000000000000000	1	1	14	\N	0	{1}
128	01020000A0187A0000020000000C6AC8E0EA9FE2C0334EAE1EF99815410000000000000000D071A1750CA0E2C0DDB6060AE49815410000000000000000	1	1	14	\N	0	{1}
129	01020000A0187A000002000000300092B920A4E2C00FA5CB48AB99154100000000000000002CEFB332EBA0E2C07A2F29339F9915410000000000000000	1	1	14	\N	0	{1}
130	01020000A0187A0000020000002CEFB332EBA0E2C07A2F29339F991541000000000000000020CE57D5F1A0E2C06FA7C5EC949915410000000000000000	1	1	14	\N	0	{1}
131	01020000A0187A000002000000E0E05E0A4EA3E2C08CBAEC05559A15410000000000000000F0D66D03DDA2E2C0FB803C20539A15410000000000000000	1	1	14	\N	0	{1}
98	01020000A0187A000007010000C0856086B798E2C0D453EBC99894154100000000000000000CC51046849AE2C0BA8774EE67941541000000000000000066E43147859AE2C0844B9CD2679415410000000000000000C3CAA443869AE2C048C11AB6679415410000000000000000F29A4D3B879AE2C07D0EF3986794154100000000000000001AFF102E889AE2C0F26A287B679415410000000000000000B92BD41B899AE2C06F20BE5C6794154100000000000000009BE27C048A9AE2C05F8AB73D679415410000000000000000C175F1E78A9AE2C06A15181E67941541000000000000000031CA18C68B9AE2C0183FE3FD669415410000000000000000C55ADA9E8C9AE2C071951CDD669415410000000000000000D43A1E728D9AE2C091B6C7BB669415410000000000000000E018CD3F8E9AE2C04A50E8996694154100000000000000002541D0078F9AE2C0B51F827766941541000000000000000017A011CA8F9AE2C0CFF09854669415410000000000000000D9C47B86909AE2C0079E303166941541000000000000000096E3F93C919AE2C0D60F4D0D669415410000000000000000CCD777ED919AE2C0513CF2E86594154100000000000000008926E297929AE2C0B32624C46594154100000000000000008F00263C939AE2C0F3DEE69E659415410000000000000000654431DA939AE2C04C813E796594154100000000000000005E80F271949AE2C0CE352F5365941541000000000000000080F45803959AE2C0E02FBD2C6594154100000000000000005E94548E959AE2C0D3ADEC05659415410000000000000000E208D612969AE2C065F8C1DE649415410000000000000000F7B1CE90969AE2C0486241B76494154100000000000000002EA83008979AE2C0A8476F8F64941541000000000000000042BEEE78979AE2C0B10D50676494154100000000000000008D82FCE2979AE2C01322E83E64941541000000000000000068404E46989AE2C082FA3B166494154100000000000000007701D9A2989AE2C03D1450ED639415410000000000000000DE8E92F8989AE2C08AF328C463941541000000000000000061727147999AE2C03823CB9A6394154100000000000000006DF76C8F999AE2C021343B71639415410000000000000000152C7DD0999AE2C0A6BC7D47639415410000000000000000ECE19A0A9A9AE2C02F58971D639415410000000000000000D1AEBF3D9A9AE2C0A9A68CF3629415410000000000000000A8EDE5699A9AE2C0024C62C9629415410000000000000000F4BE088F9A9AE2C0A6EF1C9F629415410000000000000000670924AD9A9AE2C0FD3BC1746294154100000000000000004D7A34C49A9AE2C0E6DD534A629415410000000000000000F58537D49A9AE2C03484D91F629415410000000000000000F0672BDD9A9AE2C027DF56F561941541000000000000000046230FDF9A9AE2C0EC9FD0CA6194154100000000000000009482E2D99A9AE2C012784BA06194154100000000000000000D18A6CD9A9AE2C00D19CC756194154100000000000000006F3D5BBA9A9AE2C0AB33574B619415410000000000000000DB1304A09A9AE2C09477F1206194154100000000000000009683A37E9A9AE2C0C2929FF6609415410000000000000000BC3B3D569A9AE2C0FF3066CC609415410000000000000000D2B1D5269A9AE2C05FFB49A26094154100000000000000004F2172F0999AE2C0C2974F78609415410000000000000000028B18B3999AE2C046A87B4E6094154100000000000000006CB4CF6E999AE2C0D0CAD224609415410000000000000000FC269F23999AE2C0829859FB5F9415410000000000000000432F8FD1989AE2C03AA514D25F941541000000000000000000DCA878989AE2C0127F08A95F941541000000000000000024FDF518989AE2C0E2AD39805F9415410000000000000000BF2281B2979AE2C0B9B2AC575F9415410000000000000000D29B5545979AE2C06307662F5F941541000000000000000010757FD1969AE2C0EB1D6A075F94154100000000000000008C770B57969AE2C01A60BDDF5E94154100000000000000004D2707D6959AE2C0FC2E64B85E9415410000000000000000D1C1804E959AE2C065E262915E94154100000000000000007B3C87C0949AE2C075C8BD6A5E9415410000000000000000EC422A2C949AE2C01F2579445E9415410000000000000000781A3F221E9AE2C00729159C409415410000000000000000D06F4E320599E2C0ACF63F3401941541000000000000000003B372B30499E2C061FB1417019415410000000000000000FD8F63380499E2C02D2DA9F9009415410000000000000000184E29C10399E2C0C086FEDB009415410000000000000000B0F2CB4D0399E2C0080717BE0094154100000000000000009A4053DE0299E2C008B1F49F0094154100000000000000009FB7C6720299E2C0BC8B9981009415410000000000000000FA932D0B0299E2C0EEA10763009415410000000000000000D9CD8EA70199E2C01A024144009415410000000000000000EB18F1470199E2C047BE4725009415410000000000000000E8E35AEC0099E2C0E5EB1D060094154100000000000000002258D2940099E2C0A6A3C5E6FF93154100000000000000001D595D410099E2C0600141C7FF93154100000000000000002A8401F2FF98E2C0E12392A7FF93154100000000000000000330C4A6FF98E2C0CF2CBB87FF9315410000000000000000736CAA5FFF98E2C08640BE67FF9315410000000000000000FC01B91CFF98E2C0EB859D47FF93154100000000000000008571F4DDFE98E2C04E265B27FF931541000000000000000010F460A3FE98E2C0444DF906FF9315410000000000000000697A026DFE98E2C07C287AE6FE9315410000000000000000EDACDC3AFE98E2C0A1E7DFC5FE931541000000000000000042EBF20CFE98E2C030BC2CA5FE9315410000000000000000224C48E3FD98E2C053D96284FE9315410000000000000000239DDFBDFD98E2C0BA738463FE93154100000000000000008962BB9CFD98E2C078C19342FE931541000000000000000018D7DD7FFD98E2C0DAF99221FE9315410000000000000000F1EB4867FD98E2C044558400FE93154100000000000000006E48FE52FD98E2C0050D6ADFFD9315410000000000000000054AFF42FD98E2C0385B46BEFD931541000000000000000034044D37FD98E2C0997A1B9DFD93154100000000000000006940E82FFD98E2C05EA6EB7BFD9315410000000000000000FC7DD12CFD98E2C0151AB95AFD93154100000000000000001EF2082EFD98E2C07A118639FD9315410000000000000000DC878E33FD98E2C050C85418FD93154100000000000000001CE0613DFD98E2C03D7A27F7FC9315410000000000000000A751824BFD98E2C0A36200D6FC931541000000000000000031E9EE5DFD98E2C077BCE1B4FC93154100000000000000006E69A674FD98E2C01FC2CD93FC9315410000000000000000204BA78FFD98E2C047ADC672FC931541000000000000000039BDEFAEFD98E2C0BFB6CE51FC9315410000000000000000F7A47DD2FD98E2C05216E830FC9315410000000000000000059E4EFAFD98E2C09E021510FC9315410000000000000000ACFA5F26FE98E2C0F5B057EFFB9315410000000000000000FAC3AE56FE98E2C02E55B2CEFB9315410000000000000000F6B9378BFE98E2C0852127AEFB9315410000000000000000DE53F7C3FE98E2C07446B88DFB93154100000000000000005BC0E900FF98E2C08CF2676DFB9315410000000000000000CAE50A42FF98E2C05152384DFB93154100000000000000007F625687FF98E2C014902B2DFB9315410000000000000000118DC7D0FF98E2C0CBD3430DFB9315410000000000000000AA74591E0099E2C0F24283EDFA93154100000000000000005FE106700099E2C05F00ECCDFA93154100000000000000008554CAC50099E2C0242C80AEFA931541000000000000000014099E1F0199E2C065E3418FFA931541000000000000000007F47B7D0199E2C035403370FA9315410000000000000000C5C45DDF0199E2C074595651FA931541000000000000000092E53C450299E2C0A942AD32FA9315410000000000000000FA7B12AF0299E2C0DE0B3A14FA93154100000000000000004869D71C0399E2C07EC1FEF5F99315410000000000000000074B848E0399E2C0306CFDD7F99315410000000000000000797B11040499E2C0B61038BAF993154100000000000000002012777D0499E2C0C8AFB09CF9931541000000000000000043E4ACFA0499E2C0F445697FF993154100000000000000007E85AA7B0599E2C078CB6362F99315410000000000000000504867000699E2C02434A245F993154100000000000000000002A3AD9099E2C08882AAC8DB9315410000000000000000EE0318719199E2C0F4DEEF9DDB9315410000000000000000178F472C9299E2C09414A272DB93154100000000000000009EF515DF9299E2C0A98AC746DB9315410000000000000000DBC668899399E2C044BD661ADB931541000000000000000042D3262B9499E2C0513C86EDDA93154100000000000000001D3038C49499E2C09EAA2CC0DA9315410000000000000000143B86549599E2C0E0BC6092DA93154100000000000000008A9DFBDB9599E2C0B5382964DA9315410000000000000000C14F845A9699E2C0A3F38C35DA9315410000000000000000D09B0DD09699E2C018D29206DA93154100000000000000006920863C9799E2C060C641D7D993154100000000000000006CD3DD9F9799E2C0A5CFA0A7D99315410000000000000000420406FA9799E2C0DEF8B677D993154100000000000000000E5EF14A9899E2C0CC578B47D99315410000000000000000A1E993929899E2C0E90B2517D99315410000000000000000450FE3D09899E2C05C3D8BE6D893154100000000000000004698D5059999E2C0EA1BC5B5D8931541000000000000000055B063319999E2C0E6DDD984D89315410000000000000000B0E686539999E2C020BFD053D89315410000000000000000112F3A6C9999E2C0D2FFB022D8931541000000000000000073E2797B9999E2C090E381F1D7931541000000000000000098BF43819999E2C032B04AC0D7931541000000000000000060EB967D9999E2C0C4AC128FD79315410000000000000000EBF073709999E2C07020E15DD7931541000000000000000081C1DC599999E2C06A51BD2CD793154100000000000000004BB4D4399999E2C0E083AEFBD69315410000000000000000D38560109999E2C0E3F8BBCAD69315410000000000000000525786DD9899E2C058EDEC99D69315410000000000000000C9AD4DA19899E2C0E4984869D69315410000000000000000E070BF5B9899E2C0D82CD638D6931541000000000000000098E9E50C9899E2C028D39C08D69315410000000000000000C9C0CCB49799E2C055ADA3D8D5931541000000000000000061FD80539799E2C062D3F1A8D593154100000000000000007B0211E99699E2C0C8528E79D59315410000000000000000418D8C759699E2C06A2D804AD5931541000000000000000094B204F99599E2C08A58CE1BD5931541000000000000000086DC8B739599E2C0C6BB7FEDD49315410000000000000000A2C735E59499E2C00E309BBFD493154100000000000000000280174E9499E2C0A57E2792D49315410000000000000000305E47AE9399E2C01C602B65D49315410000000000000000D803DD059399E2C0567BAD38D493154100000000000000004C58F1549299E2C08D64B40CD49315410000000000000000D4849E9B9199E2C0569C46E1D39315410000000000000000CCF0FFD99099E2C0AF8E6AB6D393154100000000000000009F3D32109099E2C00692268CD393154100000000000000008342533E8F99E2C04FE68062D39315410000000000000000130882648E99E2C015B47F39D39315410000000000000000B8C3DE828D99E2C0910B2911D39315410000000000000000E7D28A998C99E2C0C2E382E9D293154100000000000000002EB6A8A88B99E2C0901993C2D293154100000000000000001F0C5CB08A99E2C0EB6E5F9CD29315410000000000000000078CC9B08999E2C0F189ED76D29315410000000000000000840017AA8899E2C01AF44252D29315410000000000000000EC416B9C8799E2C06419652ED293154100000000000000008F30EE878699E2C08747590BD29315410000000000000000D2AEC86C8599E2C02EAD24E9D19315410000000000000000239B244B8499E2C02E59CCC7D19315410000000000000000C7C92C238399E2C0CC3955A7D1931541000000000000000089FE0CF58199E2C0001CC487D193154100000000000000003AE6F1C08099E2C0BDAA1D69D193154100000000000000001E1009877F99E2C0446E664BD1931541000000000000000027E780477E99E2C078CBA22ED1931541000000000000000020AB88027D99E2C03303D712D19315410000000000000000AC6950B87B99E2C0AD3107F8D093154100000000000000001C446A7D5799E2C0EE329F1ACE931541000000000000000027C17D545799E2C0507EAE14CE93154100000000000000001CE3BF2B5799E2C04AC9B80ECE931541000000000000000019D130035799E2C09619BE08CE931541000000000000000011B2D0DA5699E2C0F074BE02CE9315410000000000000000C9AC9FB25699E2C01CE1B9FCCD9315410000000000000000D8E79D8A5699E2C0E163B0F6CD9315410000000000000000AA89CB625699E2C00A03A2F0CD93154100000000000000007AB8283B5699E2C06AC48EEACD9315410000000000000000599AB5135699E2C0D4AD76E4CD9315410000000000000000285572EC5599E2C023C559DECD93154100000000000000009B0E5FC55599E2C0361038D8CD931541000000000000000036EC7B9E5599E2C0F09411D2CD93154100000000000000005113C9775599E2C03959E6CBCD931541000000000000000016A946515599E2C0FD62B6C5CD93154100000000000000007DD2F42A5599E2C02EB881BFCD931541000000000000000054B4D3045599E2C0C05E48B9CD93154100000000000000003773E3DE5499E2C0AE5C0AB3CD9315410000000000000000943324B95499E2C0F6B7C7ACCD9315410000000000000000A91996935499E2C09B7680A6CD93154100000000000000008849396E5499E2C0A59E34A0CD93154100000000000000000FE70D495499E2C01F36E499CD9315410000000000000000F11514245499E2C019438F93CD9315410000000000000000AEF94BFF5399E2C0A8CB358DCD931541000000000000000099B5B5DA5399E2C0E5D5D786CD9315410000000000000000D26C51B65399E2C0EC677580CD93154100000000000000004C421F925399E2C0E0870E7ACD9315410000000000000000C9581F6E5399E2C0E53BA373CD9315410000000000000000D9D2514A5399E2C0278A336DCD9315410000000000000000DED2B6265399E2C0D278BF66CD9315410000000000000000097B4E035399E2C01A0E4760CD931541000000000000000058ED18E05299E2C03550CA59CD93154100000000000000009C4B16BD5299E2C05D454953CD931541000000000000000073B7469A5299E2C0D2F3C34CCD93154100000000000000004952AA775299E2C0D6613A46CD93154100000000000000005B3D41555299E2C0B095AC3FCD9315410000000000000000B3990B335299E2C0AC951A39CD93154100000000000000002C8809115299E2C019688432CD93154100000000000000006B293BEF5199E2C04913EA2BCD9315410000000000000000E99DA0CD5199E2C0949D4B25CD9315410000000000000000E9053AAC5199E2C0550DA91ECD93154100000000000000007E81078B5199E2C0EB680218CD93154100000000000000008930096A5199E2C0B9B65711CD9315410000000000000000B7323F495199E2C025FDA80ACD931541000000000000000085A7A9285199E2C09B42F603CD93154100000000000000003DAE48085199E2C0888D3FFDCC9315410000000000000000F6651CE85099E2C060E484F6CC931541000000000000000096ED24C85099E2C0984DC6EFCC9315410000000000000000CD6362A85099E2C0ABCF03E9CC93154100000000000000001BE7D4885099E2C015713DE2CC9315410000000000000000CC957C695099E2C0593873DBCC9315410000000000000000FA8D594A5099E2C0FB2BA5D4CC93154100000000000000008BED6B2B5099E2C08552D3CDCC931541000000000000000031D2B30C5099E2C082B2FDC6CC93154100000000000000006C5931EE4F99E2C0835224C0CC931541000000000000000087A0E4CF4F99E2C01B3947B9CC93154100000000000000009CC4CDB14F99E2C0E26C66B2CC93154100000000000000008DE2EC934F99E2C072F481ABCC93154100000000000000000D1742764F99E2C06AD699A4CC9315410000000000000000977ECD584F99E2C06B19AE9DCC931541000000000000000076358F3B4F99E2C01BC4BE96CC9315410000000000000000BC57871E4F99E2C023DDCB8FCC93154100000000000000004A01B6014F99E2C02E6BD588CC9315410000000000000000CD4D1BE54E99E2C0ED74DB81CC9315410000000000000000BC58B7C84E99E2C01101DE7ACC9315410000000000000000AC0F741F3D99E2C07C2D621CC89315410000000000000000	1	1	14	\N	0	{1}
99	01020000A0187A00004300000040719C0B399AE2C0240729E0B2931541000000000000000068287A8DA09BE2C0BF98900AA29315410000000000000000D6921170A29BE2C0A25A57F4A193154100000000000000003672CF4FA49BE2C0C1702CDDA193154100000000000000009385952CA69BE2C0205111C5A19315410000000000000000E2BB4506A89BE2C0E98007ACA19315410000000000000000EA35C2DCA99BE2C054941092A193154100000000000000002248EDAFAB9BE2C08E2E2E77A19315410000000000000000927CA97FAD9BE2C09B01625BA19315410000000000000000B094D94BAF9BE2C040CEAD3EA19315410000000000000000358B6014B19BE2C0E2631321A19315410000000000000000F29521D9B29BE2C06AA09402A19315410000000000000000A627009AB49BE2C02A7033E3A09315410000000000000000C2F1DF56B69BE2C0B9CDF1C2A093154100000000000000003AE6A40FB89BE2C0D6C1D1A1A09315410000000000000000443933C4B99BE2C04863D57FA093154100000000000000001F636F74BB9BE2C0B8D6FE5CA09315410000000000000000C9213E20BD9BE2C0954E5039A09315410000000000000000BA7A84C7BE9BE2C0EA0ACC14A0931541000000000000000099BC276AC09BE2C03D5974EF9F9315410000000000000000E8800D08C29BE2C06B944BC99F9315410000000000000000B0AD1BA1C39BE2C07E2454A29F931541000000000000000028773835C59BE2C08B7E907A9F93154100000000000000004F614AC4C69BE2C0842403529F93154100000000000000009141384EC89BE2C017A5AE289F93154100000000000000005340E9D2C99BE2C0809B95FE9E93154100000000000000008EDA4452CB9BE2C05FAFBAD39E931541000000000000000053E332CCCC9BE2C08E9420A89E931541000000000000000054859B40CE9BE2C0F70ACA7B9E9315410000000000000000664467AFCF9BE2C065DEB94E9E9315410000000000000000FCFE7E18D19BE2C058E6F2209E931541000000000000000099EFCB7BD29BE2C0D60578F29D931541000000000000000046AE37D9D39BE2C0412B4CC39D9315410000000000000000F331AC30D59BE2C0205072939D9315410000000000000000E3D11382D69BE2C0F478ED629D9315410000000000000000054759CDD79BE2C009B5C0319D93154100000000000000004EAD6712D99BE2C03F1EEFFF9C931541000000000000000009852A51DA9BE2C0DCD87BCD9C93154100000000000000001FB48D89DB9BE2C059136A9A9C931541000000000000000062877DBBDC9BE2C02C06BD669C9315410000000000000000C6B3E6E6DD9BE2C097F377329C93154100000000000000009B57B60BDF9BE2C073279EFD9B9315410000000000000000BBFBD929E09BE2C0F9F632C89B9315410000000000000000B8943F41E19BE2C08CC039929B9315410000000000000000FB83D551E29BE2C087EBB55B9B9315410000000000000000E6988A5BE39BE2C0FFE7AA249B9315410000000000000000E3114E5EE49BE2C0942E1CED9A9315410000000000000000779D0F5AE59BE2C02F400DB59A9315410000000000000000495BBF4EE69BE2C0D4A5817C9A93154100000000000000001FDD4D3CE79BE2C05FF07C439A9315410000000000000000DD27AC22E89BE2C053B8020A9A931541000000000000000070B4CB01E99BE2C09A9D16D0999315410000000000000000BF709ED9E99BE2C04C47BC959993154100000000000000008AC016AAEA9BE2C07763F75A999315410000000000000000467E2773EB9BE2C0E0A6CB1F999315410000000000000000F2FBC334EC9BE2C0C6CC3CE4989315410000000000000000E603E0EEEC9BE2C0AC964EA898931541000000000000000093D96FA1ED9BE2C017CC046C989315410000000000000000463A684CEE9BE2C0513A632F989315410000000000000000DA5DBEEFEE9BE2C030B46DF297931541000000000000000067F7678BEF9BE2C0D21128B5979315410000000000000000E9355B1FF09BE2C064309677979315410000000000000000DEC48EABF09BE2C0E3F1BB39979315410000000000000000DCCCF92FF19BE2C0DA3C9DFB96931541000000000000000020F493ACF19BE2C028FC3DBD969315410000000000000000185F5521F29BE2C0BB1EA27E969315410000000000000000EC432155F19BE2C038D6F62A939315410000000000000000	1	1	14	\N	0	{1}
100	01020000A0187A000002000000548CA8CB029CE2C06BDBD146A39315410000000000000000FC31AC30D59BE2C0205072939D9315410000000000000000	1	1	14	\N	0	{1}
101	01020000A0187A0000030000004487C011B17CE2C0DED5AB4886AA15410000000000000000F8B13C5AB27CE2C0164399F485AA154100000000000000008CF809881F7DE2C0FA0EC96467AA15410000000000000000	1	1	14	\N	0	{1}
102	01020000A0187A00000200000058ECBCD6539CE2C04F073411899315410000000000000000A46717D6629CE2C0544FC2148E9315410000000000000000	1	1	14	\N	0	{1}
103	01020000A0187A0000080000005C5E3CA4A887E2C0899A8688D69515410000000000000000142ACFFC8589E2C0BD04D463BC9515410000000000000000903D3A7A888AE2C0DD66591EAC9515410000000000000000F4BB6E08728BE2C0AE47638D9995154100000000000000002CEDBC29398CE2C04DF7D298879515410000000000000000406F365E288DE2C0B21B8E3273951541000000000000000028D20996808EE2C03FA2D17252951541000000000000000078048D30A590E2C06E24E20B279515410000000000000000	1	1	14	\N	0	{1}
104	01020000A0187A0000030000007C048D30A590E2C06E24E20B27951541000000000000000098713EAE8491E2C0E20AD10414951541000000000000000010FF0D969C94E2C0673E6933D89415410000000000000000	1	1	14	\N	0	{1}
105	01020000A0187A00000600000010FF0D969C94E2C0673E6933D8941541000000000000000028C71A673795E2C03D5041E6CF94154100000000000000002865BA05B595E2C0F1852056C9941541000000000000000054B230A43196E2C02C6B2B2DC0941541000000000000000088F173B60997E2C096AE035FB29415410000000000000000C0856086B798E2C0D453EBC9989415410000000000000000	1	1	14	\N	0	{1}
106	01020000A0187A000002000000BCF8EB3B4CA0E2C056FF83EB2593154100000000000000003C04BDAFBD9EE2C0A84695253A9315410000000000000000	1	1	14	\N	0	{1}
107	01020000A0187A000002000000BCF8EB3B4CA0E2C056FF83EB259315410000000000000000584591FCECA0E2C0B9BA8B53209315410000000000000000	1	1	14	\N	0	{1}
108	01020000A0187A000002000000584F5A2ACBA1E2C047561CAC89921541000000000000000044DD4FCBBDA1E2C02DEF807F749215410000000000000000	1	1	14	\N	0	{1}
109	01020000A0187A000002000000584591FCECA0E2C0B9BA8B53209315410000000000000000B8F76D2BC7A2E2C0CF00C8F7129315410000000000000000	1	1	14	\N	0	{1}
110	01020000A0187A00000200000044DD4FCBBDA1E2C02DEF807F749215410000000000000000F4964C808CA1E2C024060AA95E9215410000000000000000	1	1	14	\N	0	{1}
111	01020000A0187A00000200000044F6DE3757A1E2C0B29404DB4E9215410000000000000000F4964C808CA1E2C024060AA95E9215410000000000000000	1	1	14	\N	0	{1}
112	01020000A0187A0000020000003C719C0B399AE2C0240729E0B29315410000000000000000E822B05E2699E2C0E051128DBE9315410000000000000000	1	1	14	\N	0	{1}
113	01020000A0187A000002000000E822B05E2699E2C0E051128DBE9315410000000000000000D438E7B23E99E2C0CBAD3080C89315410000000000000000	1	1	14	\N	0	{1}
114	01020000A0187A000002000000984108B34F99E2C0D53796C9B0931541000000000000000040DD2EFA6C99E2C0CCD7BF8CBB9315410000000000000000	1	1	14	\N	0	{1}
132	01020000A0187A000002000000F0D66D03DDA2E2C0FB803C20539A15410000000000000000E0B32E1C4B9EE2C0E6A1B3BA1D9A15410000000000000000	1	1	14	\N	0	{1}
133	01020000A0187A000002000000E0B32E1C4B9EE2C0E6A1B3BA1D9A1541000000000000000034CAEB9B6D9EE2C02D080D28119A15410000000000000000	1	1	14	\N	0	{1}
134	01020000A0187A000002000000381B620BB8A2E2C023EE653EDE9A15410000000000000000001FA80C7B9FE2C04B9A47C7CD9A15410000000000000000	1	1	14	\N	0	{1}
135	01020000A0187A000002000000001FA80C7B9FE2C04B9A47C7CD9A154100000000000000009C12F8AF829FE2C016FA19E5C29A15410000000000000000	1	1	14	\N	0	{1}
136	01020000A0187A0000020000002CAEF119C17EE2C0ACCDFF2BFFAA15410000000000000000ECE4DC8EBA82E2C0F1EDC84D24AB15410000000000000000	1	1	14	\N	0	{1}
137	01020000A0187A000002000000ECE4DC8EBA82E2C0F1EDC84D24AB15410000000000000000BCEEFAAD9F82E2C0C5E204172FAB15410000000000000000	1	1	14	\N	0	{1}
138	01020000A0187A000002000000287C02E00275E2C0DC1629666DA615410000000000000000D449B63ADD77E2C0C2A6CEA385A615410000000000000000	1	1	14	\N	0	{1}
139	01020000A0187A000002000000D449B63ADD77E2C0C2A6CEA385A61541000000000000000018E059B0207AE2C0E3C1FE888EA615410000000000000000	1	1	14	\N	0	{1}
140	01020000A0187A000002000000FC357FA24D76E2C026F960B271AC154100000000000000004849186E4A76E2C03F50D9A573AC15410000000000000000	1	1	14	\N	0	{1}
141	01020000A0187A0000020000004849186E4A76E2C03F50D9A573AC15410000000000000000C4770E8F7F75E2C0D6AAD8B86EAC15410000000000000000	1	1	14	\N	0	{1}
142	01020000A0187A000002000000C4770E8F7F75E2C0D6AAD8B86EAC154100000000000000008C3F84799374E2C0FB337CC803AD15410000000000000000	1	1	14	\N	0	{1}
143	01020000A0187A0000020000008C3F84799374E2C0FB337CC803AD15410000000000000000345A0E74C975E2C08E4814DA0CAD15410000000000000000	1	1	14	\N	0	{1}
144	01020000A0187A00000200000090E9D069627BE2C05F6BEF5319AD1541000000000000000090551A993F7BE2C0C891398B31AD15410000000000000000	1	1	14	\N	0	{1}
145	01020000A0187A00000200000090551A993F7BE2C0C891398B31AD15410000000000000000345A0E74C975E2C08E4814DA0CAD15410000000000000000	1	1	14	\N	0	{1}
146	01020000A0187A000002000000345A0E74C975E2C08E4814DA0CAD15410000000000000000C4478BB36A74E2C0BF50C076D8AD15410000000000000000	1	1	14	\N	0	{1}
147	01020000A0187A000002000000C4478BB36A74E2C0BF50C076D8AD154100000000000000002CCC6B4DFD74E2C00FC83420DCAD15410000000000000000	1	1	14	\N	0	{1}
148	01020000A0187A00000200000090E9D069627BE2C05F6BEF5319AD15410000000000000000BC70E742B17BE2C094C9A91D1DAD15410000000000000000	1	1	14	\N	0	{1}
149	01020000A0187A000002000000BC70E742B17BE2C094C9A91D1DAD15410000000000000000ECCBCF79007CE2C059AC13992AAD15410000000000000000	1	1	14	\N	0	{1}
150	01020000A0187A000002000000ECCBCF79007CE2C059AC13992AAD15410000000000000000282D5CD6697CE2C0799ACCF838AD15410000000000000000	1	1	14	\N	0	{1}
151	01020000A0187A000002000000282D5CD6697CE2C0799ACCF838AD15410000000000000000CCC820F72D80E2C00B8849384CAD15410000000000000000	1	1	14	\N	0	{1}
152	01020000A0187A000002000000CCC820F72D80E2C00B8849384CAD1541000000000000000070395E01D186E2C0E456410C57AD15410000000000000000	1	1	14	\N	0	{1}
153	01020000A0187A00000200000070395E01D186E2C0E456410C57AD1541000000000000000014416C51E087E2C0FF1A7BEBB9AC15410000000000000000	1	1	14	\N	0	{1}
154	01020000A0187A00000200000014416C51E087E2C0FF1A7BEBB9AC15410000000000000000CCFAA9B63988E2C0D318247CBBAC15410000000000000000	1	1	14	\N	0	{1}
155	01020000A0187A000002000000C45D3D027248E2C01C2C448AB4A21541000000000000000048749F84834BE2C0CE12CFCED3A215410000000000000000	1	1	14	\N	0	{1}
156	01020000A0187A00000200000048749F84834BE2C0CE12CFCED3A215410000000000000000246E1EEF074BE2C04FA8125A01A315410000000000000000	1	1	14	\N	0	{1}
157	01020000A0187A000002000000246E1EEF074BE2C04FA8125A01A3154100000000000000002C836A038C4FE2C07319373521A315410000000000000000	1	1	14	\N	0	{1}
158	01020000A0187A0000020000002C836A038C4FE2C07319373521A315410000000000000000B0058D01DB79E2C0EFC241372BA415410000000000000000	1	1	14	\N	0	{1}
159	01020000A0187A000002000000B0058D01DB79E2C0EFC241372BA415410000000000000000287C02E00275E2C0DC1629666DA615410000000000000000	1	1	14	\N	0	{1}
160	01020000A0187A000002000000287C02E00275E2C0DC1629666DA6154100000000000000002858E3ECD66EE2C07F1B62BCFDA815410000000000000000	1	1	14	\N	0	{1}
161	01020000A0187A0000020000002858E3ECD66EE2C07F1B62BCFDA8154100000000000000004487C011D17AE2C0994A3F61A5A915410000000000000000	1	1	14	\N	0	{1}
162	01020000A0187A0000020000004487C011D17AE2C0994A3F61A5A915410000000000000000D4743D518678E2C07DF0DAA548AA15410000000000000000	1	1	14	\N	0	{1}
163	01020000A0187A000002000000D4743D518678E2C07DF0DAA548AA154100000000000000004487C011B17CE2C0DED5AB4886AA15410000000000000000	1	1	14	\N	0	{1}
164	01020000A0187A0000020000004487C011B17CE2C0DED5AB4886AA154100000000000000007064E517627FE2C0383AE727ADAA15410000000000000000	1	1	14	\N	0	{1}
165	01020000A0187A0000020000007064E517627FE2C0383AE727ADAA154100000000000000002CAEF119C17EE2C0ACCDFF2BFFAA15410000000000000000	1	1	14	\N	0	{1}
166	01020000A0187A0000020000002CAEF119C17EE2C0ACCDFF2BFFAA1541000000000000000090E9D069627BE2C05F6BEF5319AD15410000000000000000	1	1	14	\N	0	{1}
167	01020000A0187A000002000000A46717D6629CE2C0544FC2148E931541000000000000000084167CFA0D9DE2C0B9C14769869315410000000000000000	1	1	14	\N	0	{1}
168	01020000A0187A000004000000381B620BB8A2E2C023EE653EDE9A15410000000000000000BC2FF2F9B3A2E2C0611734EBE19A15410000000000000000884AD97A8AA8E2C062DB85C2FC9A15410000000000000000385B8530CCA8E2C0D66CF655E99A15410000000000000000	1	1	14	\N	0	{1}
169	01020000A0187A000004000000688E396843A3E2C0CC55DDEB5E9A15410000000000000000E4327FE4B0A4E2C02B1326EC649A15410000000000000000544B43F520A8E2C028770AAE6D9A15410000000000000000941B093239A8E2C004E3D8995D9A15410000000000000000	1	1	14	\N	0	{1}
170	01020000A0187A000002000000F002F54A3188E2C04229ADCA37961541000000000000000080DD80819288E2C0103AE281359615410000000000000000	1	1	14	\N	0	{1}
171	01020000A0187A000002000000E0398D4AEF3DE2C0E94E245D9DA215410000000000000000E0A0E3DC2139E2C01FD0D88882A415410000000000000000	1	1	14	\N	0	{1}
172	01020000A0187A000002000000E0A646E28F3AE2C0EE8B5C17F2A315410000000000000000E405B828EC38E2C0D8436B31EFA315410000000000000000	1	1	14	\N	0	{1}
173	01020000A0187A0000840000003C04BDAFBD9EE2C0A84695253A93154100000000000000009C2414BC9F9DE2C0DDFE35644D9315410000000000000000C11E93189F9DE2C0A4775D6F4D9315410000000000000000158218769E9DE2C0CC3CC07A4D9315410000000000000000ECAEA9D49D9DE2C0E4ED5D864D9315410000000000000000BAFC4B349D9DE2C0852836924D9315410000000000000000EBB904959C9DE2C05C88489E4D9315410000000000000000B42BD9F69B9DE2C026A794AA4D9315410000000000000000E68DCE599B9DE2C0B81C1AB74D9315410000000000000000C312EABD9A9DE2C0017FD8C34D9315410000000000000000D3E230239A9DE2C00F62CFD04D9315410000000000000000B31CA889999DE2C01158FEDD4D9315410000000000000000F2D454F1989DE2C059F164EB4D9315410000000000000000DE153C5A989DE2C064BC02F94D93154100000000000000005EDF62C4979DE2C0DB45D7064E9315410000000000000000C626CE2F979DE2C09718E2144E9315410000000000000000ADD6829C969DE2C0A5BD22234E9315410000000000000000C5CE850A969DE2C04ABC98314E9315410000000000000000AEE3DB79959DE2C0089A43404E9315410000000000000000D2DE89EA949DE2C0A0DA224F4E9315410000000000000000397E945C949DE2C01800365E4E9315410000000000000000607400D0939DE2C0BE8A7C6D4E93154100000000000000001668D244939DE2C02CF9F57C4E931541000000000000000050F40EBB929DE2C04FC8A18C4E931541000000000000000003A8BA32929DE2C068737F9C4E9315410000000000000000FF05DAAB919DE2C010748EAC4E9315410000000000000000C7847126919DE2C04242CEBC4E93154100000000000000006C8E85A2909DE2C058543ECD4E931541000000000000000068801A20909DE2C0141FDEDD4E931541000000000000000079AB349F8F9DE2C0A615ADEE4E93154100000000000000007953D81F8F9DE2C0ABA9AAFF4E931541000000000000000041AF09A28E9DE2C0384BD6104F93154100000000000000007FE8CC258E9DE2C0DA682F224F9315410000000000000000951B26AB8D9DE2C09E6FB5334F9315410000000000000000755719328D9DE2C013CB67454F9315410000000000000000839DAABA8C9DE2C053E545574F93154100000000000000006DE1DD448C9DE2C002274F694F93154100000000000000000C09B7D08B9DE2C05BF7827B4F931541000000000000000046EC395E8B9DE2C02CBCE08D4F9315410000000000000000E8546AED8A9DE2C0E1D967A04F931541000000000000000089FE4B7E8A9DE2C08AB317B34F93154100000000000000006C96E2108A9DE2C0DCAAEFC54F93154100000000000000005DBB31A5899DE2C03720EFD84F931541000000000000000095FD3C3B899DE2C0AF7215EC4F93154100000000000000009ADE07D3889DE2C00E0062FF4F931541000000000000000024D1956C889DE2C0D824D412509315410000000000000000FD38EA07889DE2C0573C6B26509315410000000000000000E66A08A5879DE2C097A0263A50931541000000000000000078ACF343879DE2C075AA054E5093154100000000000000000F34AFE4869DE2C09DB10762509315410000000000000000A5283E87869DE2C0930C2C76509315410000000000000000C0A1A32B869DE2C0BA10728A50931541000000000000000054A7E2D1859DE2C05612D99E509315410000000000000000A931FE79859DE2C0946460B35093154100000000000000004229F923859DE2C0915907C8509315410000000000000000C666D6CF849DE2C05A42CDDC509315410000000000000000E7B2987D849DE2C0FB6EB1F150931541000000000000000048C6422D849DE2C07C2EB3065193154100000000000000006B49D7DE839DE2C0EACED11B51931541000000000000000096D45892839DE2C0619D0C31519315410000000000000000BEEFC947839DE2C00BE6624651931541000000000000000075122DFF829DE2C02BF4D35B519315410000000000000000CFA384B8829DE2C020125F7151931541000000000000000054FAD273829DE2C06D890387519315410000000000000000E65B1A31829DE2C0BEA2C09C519315410000000000000000B4FD5CF0819DE2C0EFA595B25193154100000000000000005C82921B2A9DE2C052826BD76F9315410000000000000000D3BA91CC299DE2C04F3CF6F16F9315410000000000000000723FA37A299DE2C0E45A5D0C709315410000000000000000EC12CB25299DE2C037939F26709315410000000000000000765C0DCE289DE2C03A9CBB407093154100000000000000008E676E73289DE2C0BE2EB05A709315410000000000000000CBA3F215289DE2C082057C74709315410000000000000000A3A49EB5279DE2C045DD1D8E7093154100000000000000002F217752279DE2C0D47494A7709315410000000000000000F7F380EC269DE2C0188DDEC0709315410000000000000000AC1AC183269DE2C029E9FAD9709315410000000000000000F1B53C18269DE2C05D4EE8F27093154100000000000000001709F9A9259DE2C05584A50B719315410000000000000000DD79FB38259DE2C00F553124719315410000000000000000299049C5249DE2C0F28C8A3C719315410000000000000000C8F5E84E249DE2C0E1FAAF547193154100000000000000002176DFD5239DE2C04870A06C719315410000000000000000F2FD325A239DE2C02AC15A84719315410000000000000000029BE9DB229DE2C031C4DD9B719315410000000000000000D57B095B229DE2C0BA5228B371931541000000000000000063EF98D7219DE2C0E94839CA719315410000000000000000C4649E51219DE2C0B1850FE1719315410000000000000000E06A20C9209DE2C0E5EAA9F771931541000000000000000020B0253E209DE2C0485D070E7293154100000000000000001702B5B01F9DE2C097C42624729315410000000000000000304DD5201F9DE2C0990B073A729315410000000000000000529C8D8E1E9DE2C02B20A74F7293154100000000000000008E18E5F91D9DE2C050F30565729315410000000000000000C008E3621D9DE2C03C79227A72931541000000000000000039D18EC91C9DE2C063A9FB8E7293154100000000000000005CF3EF2D1C9DE2C0827E90A3729315410000000000000000460D0E901B9DE2C0B1F6DFB77293154100000000000000006AD9F0EF1A9DE2C06C13E9CB729315410000000000000000342EA04D1A9DE2C0A3D9AADF729315410000000000000000A4FD23A9199DE2C0C05124F3729315410000000000000000EB548402199DE2C0BA875406739315410000000000000000075CC959189DE2C01D8B3A197393154100000000000000005C55FBAE179DE2C0186FD52B7393154100000000000000004D9D2202179DE2C0854A243E739315410000000000000000D3A94753169DE2C0F9372650739315410000000000000000110A73A2159DE2C0CB55DA61739315410000000000000000EF65ADEF149DE2C024C63F73739315410000000000000000A47DFF3A149DE2C004AF558473931541000000000000000052297284139DE2C0513A1B957393154100000000000000008F580ECC129DE2C0DF958FA5739315410000000000000000FD11DD11129DE2C07EF3B1B5739315410000000000000000D072E755119DE2C0FE8881C573931541000000000000000064AE3698109DE2C03F90FDD4739315410000000000000000C40DD4D80F9DE2C0364725E473931541000000000000000039EFC8170F9DE2C0FBEFF7F2739315410000000000000000D3C51E550E9DE2C0CDD07401749315410000000000000000F218DF900D9DE2C020349B0F749315410000000000000000D28313CB0C9DE2C0A3686A1D7493154100000000000000000EB5C5030C9DE2C04BC1E12A749315410000000000000000296EFF3A0B9DE2C0579500387493154100000000000000001583CA700A9DE2C05D40C644749315410000000000000000B5D930A5099DE2C05222325174931541000000000000000063693CD8089DE2C08C9F435D749315410000000000000000743AF709089DE2C0D120FA68749315410000000000000000B5656B3A079DE2C05B135574749315410000000000000000F413A369069DE2C0DDE8537F7493154100000000000000007B7DA897059DE2C08F17F68974931541000000000000000093E985C4049DE2C0301A3B9474931541000000000000000001AE45F0039DE2C01070229E749315410000000000000000882EF21A039DE2C0159DABA7749315410000000000000000BCCB0D47E09CE2C016448C2D769315410000000000000000	1	\N	1	\N	0	{1}
174	01020000A0187A00000200000090986773A06FE2C0A2F64D59B49915410000000000000000B8A6F9E67B6FE2C09F8F451A5F9915410000000000000000	1	\N	1	\N	0	{1}
175	01020000A0187A000002000000B8A6F9E67B6FE2C09F8F451A5F9915410000000000000000B4B503A5476FE2C020BC6037E59815410000000000000000	1	\N	1	\N	0	{1}
176	01020000A0187A000002000000B4B503A5476FE2C020BC6037E59815410000000000000000B00E46001A6FE2C04A7FC4C17A9815410000000000000000	1	\N	1	\N	0	{1}
177	01020000A0187A0000020000003452C62DC871E2C0723D78DF3499154100000000000000007C5C7AA1BD71E2C02F49A835179915410000000000000000	1	\N	1	\N	0	{1}
178	01020000A0187A000002000000B00E46001A6FE2C04A7FC4C17A981541000000000000000020A4B97F916EE2C097CCBD603C9715410000000000000000	1	\N	1	\N	0	{1}
179	01020000A0187A00000200000020A4B97F916EE2C097CCBD603C9715410000000000000000F88D96F1696EE2C043210E72D89615410000000000000000	1	\N	1	\N	0	{1}
180	01020000A0187A000002000000F88D96F1696EE2C043210E72D89615410000000000000000A487749C7E71E2C038876700D99615410000000000000000	1	\N	1	\N	0	{1}
181	01020000A0187A00000200000088197076FE72E2C086493AA7D79615410000000000000000C8FDA4C6897BE2C079B250A7B69615410000000000000000	1	\N	1	\N	0	{1}
182	01020000A0187A000002000000C8FDA4C6897BE2C079B250A7B6961541000000000000000098A7806E6E81E2C05D886B27929615410000000000000000	1	\N	1	\N	0	{1}
183	01020000A0187A00000200000090DEE3894287E2C0D08D5CA36C9615410000000000000000741FCF256D88E2C0D46C690C659615410000000000000000	1	\N	1	\N	0	{1}
184	01020000A0187A000002000000E80D3FE17B82E2C04146DE8BD69315410000000000000000E8AB3632E582E2C0C4389819E59315410000000000000000	1	\N	1	\N	0	{1}
185	01020000A0187A000002000000247C70BA5B83E2C00E17824AF99315410000000000000000F8C0E3E88083E2C0E27174DC059415410000000000000000	1	\N	1	\N	0	{1}
186	01020000A0187A0000020000004CBD859E2483E2C04DCB378283941541000000000000000024A64C596781E2C0ECD4DCBD869415410000000000000000	1	\N	1	\N	0	{1}
187	01020000A0187A0000020000001CD2D794D490E2C02CA69DB53D9615410000000000000000509932EB7192E2C0D9E2E0422F9615410000000000000000	1	\N	1	\N	0	{1}
188	01020000A0187A0000020000003CFE936D6F9AE2C0EF24E3A6C295154100000000000000003CBE7949869CE2C0E7CB21FFAD9515410000000000000000	1	\N	1	\N	0	{1}
189	01020000A0187A0000020000003CBE7949869CE2C0E7CB21FFAD951541000000000000000080B70863529EE2C00732E555909515410000000000000000	1	\N	1	\N	0	{1}
190	01020000A0187A000002000000802449A07BA2E2C063723F28D495154100000000000000007092FA3B5FA2E2C0D8884CBDD79515410000000000000000	1	\N	1	\N	0	{1}
191	01020000A0187A0000020000001C3FA7DEFC6FE2C0D336C568E6991541000000000000000014D206C3CF6EE2C00FBCB235129A15410000000000000000	1	\N	1	\N	0	{1}
192	01020000A0187A00000200000014D206C3CF6EE2C00FBCB235129A15410000000000000000D82CDB17E368E2C076D448DFDC9A15410000000000000000	1	\N	1	\N	0	{1}
193	01020000A0187A000002000000D82CDB17E368E2C076D448DFDC9A15410000000000000000F82570711266E2C095D9E0EA3E9B15410000000000000000	1	\N	1	\N	0	{1}
194	01020000A0187A000002000000202870711266E2C048D9E0EA3E9B15410000000000000000FCA5927BBF5EE2C0BDAA0F023E9C15410000000000000000	1	\N	1	\N	0	{1}
195	01020000A0187A000002000000FCA5927BBF5EE2C0BDAA0F023E9C1541000000000000000050736A07055BE2C018F81896D89C15410000000000000000	1	\N	1	\N	0	{1}
196	01020000A0187A00000200000050736A07055BE2C018F81896D89C15410000000000000000388D29CF8E57E2C06993A7D5979D15410000000000000000	1	\N	1	\N	0	{1}
197	01020000A0187A000002000000388D29CF8E57E2C06993A7D5979D154100000000000000004C156F871755E2C061C459274B9E15410000000000000000	1	\N	1	\N	0	{1}
198	01020000A0187A0000020000004C156F871755E2C061C459274B9E154100000000000000009C8DCAE1C952E2C0476F43EA329F15410000000000000000	1	\N	1	\N	0	{1}
199	01020000A0187A000002000000B80C63CDC952E2C0B7B696F2329F15410000000000000000645444488E52E2C08E5A07304C9F15410000000000000000	1	\N	1	\N	0	{1}
200	01020000A0187A000002000000AC706C488E52E2C08E59F62F4C9F15410000000000000000B44710B9734FE2C010ECF8EA9CA015410000000000000000	1	\N	1	\N	0	{1}
201	01020000A0187A000002000000604310B9734FE2C0E6EDF8EA9CA01541000000000000000088DD7C70644FE2C02D461A65A3A015410000000000000000	1	\N	1	\N	0	{1}
202	01020000A0187A00000200000088DD7C70644FE2C02D461A65A3A01541000000000000000098F24452A24CE2C0A03FCBDEA5A115410000000000000000	1	\N	1	\N	0	{1}
203	01020000A0187A00000200000098F24452A24CE2C0A03FCBDEA5A115410000000000000000403EFA92BD49E2C0743029E4A6A215410000000000000000	1	\N	1	\N	0	{1}
204	01020000A0187A000002000000ECF2208C7272E2C091E8F9A20E99154100000000000000001421C3150372E2C0ECC9D9660F9915410000000000000000	1	\N	1	\N	0	{1}
205	01020000A0187A0000020000003C7465FE8F72E2C0FCCEAF6D0A991541000000000000000094CA1FAF8D72E2C043B1C2C3069915410000000000000000	1	\N	1	\N	0	{1}
206	01020000A0187A000002000000B8FD728A5787E2C043A1EBC773951541000000000000000090C552C4AA86E2C0639AE6D57B9515410000000000000000	1	\N	1	\N	0	{1}
207	01020000A0187A00000200000090C552C4AA86E2C0639AE6D57B951541000000000000000098EE80364886E2C0F91EBB92819515410000000000000000	1	\N	1	\N	0	{1}
208	01020000A0187A00000200000098EE80364886E2C0F91EBB9281951541000000000000000090E90746D085E2C093C0CB24899515410000000000000000	1	\N	1	\N	0	{1}
209	01020000A0187A00000200000090E90746D085E2C093C0CB24899515410000000000000000249973FB8C85E2C059D2F240909515410000000000000000	1	\N	1	\N	0	{1}
210	01020000A0187A000002000000E8AB3632E582E2C0C4389819E59315410000000000000000247C70BA5B83E2C00E17824AF99315410000000000000000	1	\N	1	\N	0	{1}
211	01020000A0187A000002000000B8057C333688E2C0EC1B161BD3931541000000000000000078054C063E87E2C09FC89366AC9315410000000000000000	1	\N	1	\N	0	{1}
212	01020000A0187A0000020000007437B2EC6270E2C02A800077FC97154100000000000000001452CFE0E26EE2C0EF210B30FA9715410000000000000000	1	\N	1	\N	0	{1}
213	01020000A0187A000002000000243FA7DEFC6FE2C0D536C568E6991541000000000000000080CF02B0EF6FE2C02528B1C3E29915410000000000000000	1	\N	1	\N	0	{1}
214	01020000A0187A00004100000044CA63AFEF6FE2C032D9E5C3E29915410000000000000000647D8804ED6FE2C05F330318E29915410000000000000000603FA464EA6FE2C05A0B746BE199154100000000000000002CF5C1CFE76FE2C0682D3BBEE09915410000000000000000FC55EC45E56FE2C08D685B10E0991541000000000000000034EB2DC7E26FE2C0828ED761DF991541000000000000000020109153E06FE2C0AC73B2B2DE9915410000000000000000F0F11FEBDD6FE2C00AEFEE02DE9915410000000000000000588FE48DDB6FE2C02DDA8F52DD991541000000000000000098B8E83BD96FE2C02E1198A1DC99154100000000000000003C0F36F5D66FE2C09F720AF0DB9915410000000000000000F005D6B9D46FE2C07CDFE93DDB991541000000000000000068E0D189D26FE2C0293B398BDA991541000000000000000038B33265D06FE2C05E6BFBD7D999154100000000000000009063014CCE6FE2C019583324D999154100000000000000004CA7463ECC6FE2C09BEBE36FD899154100000000000000009C040B3CCA6FE2C0551210BBD7991541000000000000000008D25645C86FE2C0DFBABA05D799154100000000000000003436325AC66FE2C0E7D5E64FD69915410000000000000000C827A57AC46FE2C02A569799D59915410000000000000000546DB7A6C26FE2C06930CFE2D49915410000000000000000249D70DEC06FE2C0555B912BD49915410000000000000000241DD821BF6FE2C08BCFE073D39915410000000000000000C822F570BD6FE2C08387C0BBD29915410000000000000000ECB2CECBBB6FE2C0847F3303D29915410000000000000000B4A16B32BA6FE2C09BB53C4AD199154100000000000000006C92D2A4B86FE2C08829DF90D0991541000000000000000070F70923B76FE2C0B8DC1DD7CF9915410000000000000000181218ADB56FE2C037D2FB1CCF991541000000000000000094F20243B46FE2C09F0E7C62CE9915410000000000000000D877D0E4B26FE2C01598A1A7CD99154100000000000000007C4F8692B16FE2C02F766FECCC9915410000000000000000B8F5294CB06FE2C0F5B1E830CC991541000000000000000038B5C011AF6FE2C0CC551075CB99154100000000000000000CA74FE3AD6FE2C06A6DE9B8CA99154100000000000000009CB2DBC0AC6FE2C0CE0577FCC99915410000000000000000848D69AAAB6FE2C02F2DBC3FC9991541000000000000000090BBFD9FAA6FE2C0F2F2BB82C89915410000000000000000A48E9CA1A96FE2C0986779C5C799154100000000000000009C264AAFA86FE2C0BB9CF707C7991541000000000000000058710AC9A76FE2C0F6A4394AC699154100000000000000008C2AE1EEA66FE2C0E293428CC59915410000000000000000C4DBD120A66FE2C0037E15CEC499154100000000000000005CDCDF5EA56FE2C0BE78B50FC499154100000000000000005C510EA9A46FE2C04A9A2551C39915410000000000000000742D60FFA36FE2C0A6F96892C29915410000000000000000F430D861A36FE2C08CAE82D3C19915410000000000000000C4E978D0A26FE2C060D17514C1991541000000000000000050B3444BA26FE2C0267B4555C099154100000000000000007CB63DD2A16FE2C079C5F495BF9915410000000000000000A4E96565A16FE2C078CA86D6BE99154100000000000000009C10BF04A16FE2C0BCA4FE16BE991541000000000000000090BC4AB0A06FE2C0476F5F57BD9915410000000000000000084C0A68A06FE2C08145AC97BC9915410000000000000000F0EAFE2BA06FE2C02243E8D7BB99154100000000000000008C9229FC9F6FE2C026841618BB99154100000000000000005C098BD89F6FE2C0C5243A58BA991541000000000000000044E323C19F6FE2C061415698B999154100000000000000006481F4B59F6FE2C07BF66DD8B899154100000000000000002812FDB69F6FE2C0A9608418B8991541000000000000000048913DC49F6FE2C0869C9C58B79915410000000000000000C0C7B5DD9F6FE2C0A0C6B998B69915410000000000000000DC4B6503A06FE2C078FBDED8B599154100000000000000002C814B35A06FE2C06A570F19B5991541000000000000000090986773A06FE2C0A2F64D59B49915410000000000000000	1	\N	1	\N	0	{1}
215	01020000A0187A00000200000068DAC236073EE2C0035C0AD59DA215410000000000000000E0398D4AEF3DE2C0E94E245D9DA215410000000000000000	1	\N	1	\N	0	{1}
216	01020000A0187A00000200000024916A9D223EE2C0963E87BB65A215410000000000000000E0398D4AEF3DE2C0E94E245D9DA215410000000000000000	1	\N	1	\N	0	{1}
217	01020000A0187A000002000000CC006F4F7D41E2C061D07ADA72A21541000000000000000024916A9D223EE2C0963E87BB65A215410000000000000000	1	\N	1	\N	0	{1}
218	01020000A0187A000002000000CC006F4F7D41E2C061D07ADA72A2154100000000000000007CA6BF4B4F44E2C0376203FD80A215410000000000000000	1	\N	1	\N	0	{1}
219	01020000A0187A0000020000007CA6BF4B4F44E2C0376203FD80A215410000000000000000B07203595747E2C0A3FCF68092A215410000000000000000	1	\N	1	\N	0	{1}
220	01020000A0187A00000200000040C30E01A948E2C0A40FCC9E9CA215410000000000000000FC4DD013D447E2C00BF0788795A215410000000000000000	1	\N	1	\N	0	{1}
221	01020000A0187A000002000000FC4DD013D447E2C00BF0788795A215410000000000000000B07203595747E2C0A3FCF68092A215410000000000000000	1	\N	1	\N	0	{1}
222	01020000A0187A000002000000CCB040F4C671E2C034374825179915410000000000000000D4D1CDD95E6FE2C0D9E6635F1B9915410000000000000000	1	\N	1	\N	0	{1}
264	01020000A0187A00000200000064A4ACAC0E79E2C040651E73A39615410000000000000000AC19AD6CB773E2C093B64486B79615410000000000000000	1	\N	1	\N	0	{1}
265	01020000A0187A000002000000C4E625782479E2C002D6FA91699615410000000000000000E8343309DD78E2C0A8E27A9E6A9615410000000000000000	1	\N	1	\N	0	{1}
266	01020000A0187A000002000000E8343309DD78E2C0A8E27A9E6A961541000000000000000064A4ACAC0E79E2C040651E73A39615410000000000000000	1	\N	1	\N	0	{1}
267	01020000A0187A00000200000054DA32915E49E2C009B89B20A3A21541000000000000000040C30E01A948E2C0A40FCC9E9CA215410000000000000000	1	\N	1	\N	0	{1}
223	01020000A0187A000041000000286B48E3E471E2C052AA759D139915410000000000000000402D78C6E471E2C09E6340B3139915410000000000000000C09A09A6E471E2C08DBCF6C8139915410000000000000000984A0082E471E2C0EC4D96DE139915410000000000000000C439605AE471E2C013B31CF413991541000000000000000010CB2D2FE471E2C01E8A870914991541000000000000000060C66D00E471E2C03A74D41E149915410000000000000000505825CEE371E2C0E015013414991541000000000000000094115A98E371E2C01E170B4914991541000000000000000058E6115FE371E2C0D823F05D149915410000000000000000A42D5322E371E2C007ECAD7214991541000000000000000094A024E2E271E2C0FC234287149915410000000000000000A8598D9EE271E2C0A684AA9B14991541000000000000000000D49457E271E2C0C9CBE4AF14991541000000000000000070EA420DE271E2C045BCEEC3149915410000000000000000C4D69FBFE171E2C0551EC6D7149915410000000000000000B430B46EE171E2C0CCBF68EB14991541000000000000000004ED881AE171E2C05274D4FE149915410000000000000000905C27C3E071E2C0A41507121599154100000000000000001C2B9968E071E2C0D283FE241599154100000000000000007C5EE80AE071E2C077A5B83715991541000000000000000040551FAADF71E2C0F767334A159915410000000000000000B4C54846DF71E2C0BBBF6C5C159915410000000000000000A0BC6FDFDE71E2C068A8626E159915410000000000000000109C9F75DE71E2C01B251380159915410000000000000000181AE408DE71E2C0A0407C91159915410000000000000000843F4999DD71E2C0A70D9CA21599154100000000000000008066DB26DD71E2C000A770B31599154100000000000000003839A7B1DC71E2C0CD2FF8C315991541000000000000000084B0B939DC71E2C0B6D330D4159915410000000000000000601220BFDB71E2C01FC718E415991541000000000000000088F0E741DB71E2C05D47AEF3159915410000000000000000E0261FC2DA71E2C0E09AEF0216991541000000000000000004DAD33FDA71E2C06D11DB11169915410000000000000000AC7514BBD971E2C049046F2016991541000000000000000010ABEF33D971E2C069D6A92E169915410000000000000000506F74AAD871E2C09CF4893C169915410000000000000000C4F9B11ED871E2C0BFD50D4A16991541000000000000000054C2B790D771E2C0E3FA3357169915410000000000000000C07F9500D771E2C078EFFA63169915410000000000000000E4255B6ED671E2C078496170169915410000000000000000E0E318DAD571E2C08FA9657C1699154100000000000000007022DF43D571E2C03FBB06881699154100000000000000000C82BEABD471E2C00935439316991541000000000000000000D9C711D471E2C08FD8199E169915410000000000000000AC310C76D371E2C0BA7289A81699154100000000000000008CC89CD8D271E2C0DADB90B2169915410000000000000000540A8B39D271E2C0C7F72EBC1699154100000000000000000C92E898D171E2C000B662C51699154100000000000000001427C7F6D071E2C0CA112BCE1699154100000000000000002CBB3853D071E2C04D1287D616991541000000000000000078684FAECF71E2C0AECA75DE169915410000000000000000806F1D08CF71E2C02C5AF6E51699154100000000000000003C35B560CE71E2C038EC07ED169915410000000000000000E44029B8CD71E2C088B8A9F31699154100000000000000000C3A8C0ECD71E2C03303DBF916991541000000000000000070E6F063CC71E2C0C51C9BFF16991541000000000000000004286AB8CB71E2C04F62E904179915410000000000000000B8FA0A0CCB71E2C07E3DC5091799154100000000000000008072E65ECA71E2C0A5242E0E1799154100000000000000001CB90FB1C971E2C0D49A23121799154100000000000000000C0C9A02C971E2C0DE2FA51517991541000000000000000064BA9853C871E2C06C80B218179915410000000000000000B4221FA4C771E2C004364B1B179915410000000000000000CCB040F4C671E2C016076F1D179915410000000000000000	1	\N	1	\N	0	{1}
224	01020000A0187A0000410000002C6B48E3E471E2C052AA759D13991541000000000000000058FEB8DAE471E2C0DAAD5984139915410000000000000000E83B18D7E471E2C009E8386B13991541000000000000000004B366D8E471E2C0D23817521399154100000000000000002030A4DEE471E2C05280F838139915410000000000000000E4BCCFE9E471E2C02F9EE01F1399154100000000000000005CA0E7F9E471E2C00271D3061399154100000000000000003C5FE90EE571E2C0BBD5D4ED12991541000000000000000034BCD128E571E2C00CA7E8D412991541000000000000000094B89C47E571E2C0CFBC12BC129915410000000000000000B494456BE571E2C073EB56A3129915410000000000000000E8D0C693E571E2C05C03B98A129915410000000000000000302E1AC1E571E2C051D03C7212991541000000000000000044AF38F3E571E2C0EA18E65912991541000000000000000098991A2AE671E2C0F69DB841129915410000000000000000A076B765E671E2C0E619B8291299154100000000000000000C1506A6E671E2C03F40E811129915410000000000000000408AFCEAE671E2C002BD4CFA119915410000000000000000D8339034E771E2C02134E9E211991541000000000000000044B9B582E771E2C0E940C1CB1199154100000000000000008C0D61D5E771E2C07975D8B41199154100000000000000004071852CE871E2C0345A329E11991541000000000000000044741588E871E2C02E6DD28711991541000000000000000010F802E8E871E2C0B321BC71119915410000000000000000BC313F4CE971E2C0A8DFF25B1199154100000000000000005CACBAB4E971E2C01D037A46119915410000000000000000584B6521EA71E2C0B4DB5431119915410000000000000000EC4C2E92EA71E2C027AC861C119915410000000000000000C04C0407EB71E2C0CDA912081199154100000000000000008C46D57FEB71E2C00FFCFBF3109915410000000000000000E4988EFCEB71E2C0F2BB45E010991541000000000000000030081D7DEC71E2C0A0F3F2CC10991541000000000000000070C16C01ED71E2C0EB9D06BA1099154100000000000000007C5D6989ED71E2C0D5A583A71099154100000000000000000CE4FD14EE71E2C027E66C95109915410000000000000000FCCE14A4EE71E2C0F528C583109915410000000000000000A80D9836EF71E2C036278F72109915410000000000000000400871CCEF71E2C05788CD6110991541000000000000000054A38865F071E2C0D4E182511099154100000000000000005843C701F171E2C0CFB6B14110991541000000000000000050D014A1F171E2C0AF775C3210991541000000000000000088B95843F271E2C0BE8185231099154100000000000000005CF979E8F271E2C0CE1E2F1510991541000000000000000004195F90F371E2C0DD845B07109915410000000000000000A834EE3AF471E2C0BDD50CFA0F991541000000000000000030FF0CE8F471E2C0C31E45ED0F99154100000000000000006CC6A097F571E2C0715806E10F991541000000000000000040778E49F671E2C02D6652D50F9915410000000000000000A0A1BAFDF671E2C0F7152BCA0F9915410000000000000000087D09B4F771E2C0192092BF0F991541000000000000000094EC5E6CF871E2C0EF2689B50F991541000000000000000068839E26F971E2C09EB611AC0F99154100000000000000001C89ABE2F971E2C0DC442DA30F991541000000000000000020FE68A0FA71E2C0B130DD9A0F99154100000000000000002CA0B95FFB71E2C047C222930F9915410000000000000000D0EE7F20FC71E2C0B42AFF8B0F991541000000000000000004309EE2FC71E2C0CA8373850F9915410000000000000000AC74F6A5FD71E2C0EECF807F0F9915410000000000000000409D6A6AFE71E2C0EFF9277A0F99154100000000000000007C5EDC2FFF71E2C0E2D469750F9915410000000000000000F4452DF6FF71E2C0001C47710F9915410000000000000000DCBE3EBD0072E2C08D72C06D0F9915410000000000000000B416F2840172E2C0BA63D66A0F99154100000000000000000082284D0272E2C0936289680F99154100000000000000001421C3150372E2C0EBC9D9660F9915410000000000000000	1	\N	1	\N	0	{1}
225	01020000A0187A000041000000AC8F17EF8F72E2C0AEE968550A9915410000000000000000B0EF96FC8F72E2C087D1DD6E0A9915410000000000000000B06902059072E2C038765B880A99154100000000000000002CA758089072E2C0C6CADDA10A9915410000000000000000542099069072E2C078C160BB0A9915410000000000000000541CC4FF8F72E2C07C4CE0D40A991541000000000000000018B1DAF38F72E2C08A5E58EE0A991541000000000000000038C3DEE28F72E2C089EBC4070B99154100000000000000009405D3CC8F72E2C037E921210B99154100000000000000000CF9BAB18F72E2C0C84F6B3A0B9915410000000000000000D4EB9A918F72E2C0911A9D530B9915410000000000000000C4F8776C8F72E2C0A348B36C0B9915410000000000000000980658428F72E2C077DDA9850B9915410000000000000000F8C641138F72E2C087E17C9E0B991541000000000000000070B53CDF8E72E2C0F46228B70B99154100000000000000002C1651A68E72E2C02B76A8CF0B9915410000000000000000B8F487688E72E2C07C36F9E70B99154100000000000000009022EB258E72E2C0BCC616000C9915410000000000000000883585DE8D72E2C0E451FD170C9915410000000000000000248661928D72E2C0AA0BA92F0C9915410000000000000000C82D8C418D72E2C01E3116470C9915410000000000000000D00412EC8C72E2C04009415E0C991541000000000000000078A000928C72E2C09AE525750C9915410000000000000000C05066338C72E2C0D522C18B0C99154100000000000000002C1E52D08B72E2C04F290FA20C991541000000000000000050C7D3688B72E2C0A86D0CB80C991541000000000000000054BEFBFC8A72E2C05771B5CD0C99154100000000000000006026DB8C8A72E2C035C306E30C9915410000000000000000DCD083188A72E2C00C00FDF70C9915410000000000000000943A08A08972E2C01ED3940C0D9915410000000000000000D4887B238972E2C0AEF6CA200D99154100000000000000006086F1A28872E2C089349C340D991541000000000000000040A07E1E8872E2C07C6605480D99154100000000000000008CE237968772E2C0E576035B0D991541000000000000000004F5320A8772E2C02261936D0D9915410000000000000000C417867A8672E2C01732B27F0D9915410000000000000000901F48E78572E2C09E085D910D9915410000000000000000447290508572E2C0FF1591A20D9915410000000000000000300377B68472E2C0639E4BB30D99154100000000000000001C4F14198472E2C043F989C30D9915410000000000000000A05881788372E2C0D19149D30D9915410000000000000000ECA3D7D48272E2C069E787E20D9915410000000000000000E432312E8272E2C0EB8D42F10D9915410000000000000000FC80A8848172E2C0272E77FF0D9915410000000000000000E47E58D88072E2C03C86230D0E9915410000000000000000688E5C298072E2C0EC69451A0E9915410000000000000000FC7DD0777F72E2C0FBC2DA260E99154100000000000000004884D0C37E72E2C08491E1320E9915410000000000000000D83B790D7E72E2C049EC573E0E9915410000000000000000589EE7547D72E2C0FC003C490E99154100000000000000002C00399A7C72E2C092148C530E9915410000000000000000A80B8BDD7B72E2C08383465D0E99154100000000000000005CBCFB1E7B72E2C00FC269660E99154100000000000000005C5AA95E7A72E2C07C5CF46E0E99154100000000000000006875B29C7972E2C053F7E4760E991541000000000000000014E035D97872E2C0944F3A7E0E9915410000000000000000DCAA52147872E2C0EA3AF3840E9915410000000000000000441F284E7772E2C0DFA70E8B0E9915410000000000000000C4BAD5867672E2C0019E8B900E9915410000000000000000E8297BBE7572E2C00F3E69950E99154100000000000000002C4338F57472E2C017C2A6990E9915410000000000000000F4012D2B7472E2C09A7D439D0E9915410000000000000000888179607372E2C0A5DD3EA00E9915410000000000000000E8F73D957272E2C0EA6898A20E9915410000000000000000A4B09AC97172E2C0D1BF4FA40E9915410000000000000000	1	\N	1	\N	0	{1}
226	01020000A0187A000002000000D89B49C2A180E2C0FC3FA867B79615410000000000000000A87E5C406C80E2C0D62D7766989615410000000000000000	1	\N	1	\N	0	{1}
227	01020000A0187A000002000000C04197326F81E2C0CDE87E249296154100000000000000008CDEE3894287E2C0D08D5CA36C9615410000000000000000	1	\N	1	\N	0	{1}
228	01020000A0187A000002000000608DE72CD073E2C04CCE9686D49615410000000000000000BC5D32147273E2C0D70A3C45669615410000000000000000	1	\N	1	\N	0	{1}
229	01020000A0187A00000200000038FEA7AAC888E2C036E98547639615410000000000000000D45BC828A689E2C0BF87A9EA5C9615410000000000000000	1	\N	1	\N	0	{1}
230	01020000A0187A000002000000100B8F3C868CE2C0FA8197D84C96154100000000000000001CD2D794D490E2C02CA69DB53D9615410000000000000000	1	\N	1	\N	0	{1}
231	01020000A0187A000002000000509932EB7192E2C0D9E2E0422F9615410000000000000000C8BEA0104994E2C0B5CCF069169615410000000000000000	1	\N	1	\N	0	{1}
232	01020000A0187A000002000000C8BEA0104994E2C0B5CCF069169615410000000000000000BC4E10851C97E2C0559F1BC1ED9515410000000000000000	1	\N	1	\N	0	{1}
233	01020000A0187A0000020000003CCD6877948CE2C0791D92A64C961541000000000000000030996977948CE2C0D30A93A64C9615410000000000000000	1	\N	1	\N	0	{1}
234	01020000A0187A000002000000705441696B71E2C038876700D9961541000000000000000088197076FE72E2C086493AA7D79615410000000000000000	1	\N	1	\N	0	{1}
235	01020000A0187A000002000000802449A07BA2E2C063723F28D495154100000000000000004CF2D17336A1E2C05129E6D5AB9515410000000000000000	1	\N	1	\N	0	{1}
236	01020000A0187A0000020000004CF2D17336A1E2C05129E6D5AB951541000000000000000070585B5B7FA0E2C08AF61C359D9515410000000000000000	1	\N	1	\N	0	{1}
237	01020000A0187A00000200000070585B5B7FA0E2C08AF61C359D95154100000000000000002C73E230D49FE2C0398B0853959515410000000000000000	1	\N	1	\N	0	{1}
238	01020000A0187A0000020000002C73E230D49FE2C0398B0853959515410000000000000000241F30B6D09EE2C02907485F8E9515410000000000000000	1	\N	1	\N	0	{1}
239	01020000A0187A00000200000078585B5B7FA0E2C089F61C359D951541000000000000000048255C5B7FA0E2C0DCE31D359D9515410000000000000000	1	\N	1	\N	0	{1}
240	01020000A0187A0000020000007C585B5B7FA0E2C089F61C359D9515410000000000000000B4F3BC52B7A0E2C0F38F2EFD969515410000000000000000	1	\N	1	\N	0	{1}
241	01020000A0187A000002000000B4F3BC52B7A0E2C0F38F2EFD969515410000000000000000ACF0434C96A1E2C00B7E5104889515410000000000000000	1	\N	1	\N	0	{1}
242	01020000A0187A000002000000ACF0434C96A1E2C00B7E51048895154100000000000000006CF75C638BA2E2C02D7F95A07D9515410000000000000000	1	\N	1	\N	0	{1}
243	01020000A0187A00000200000080B70863529EE2C00732E555909515410000000000000000241F30B6D09EE2C02907485F8E9515410000000000000000	1	\N	1	\N	0	{1}
244	01020000A0187A0000020000003CFE936D6F9AE2C0EF24E3A6C29515410000000000000000BC4E10851C97E2C0559F1BC1ED9515410000000000000000	1	\N	1	\N	0	{1}
245	01020000A0187A000002000000ACE99B63788BE2C0ED907AB97A9615410000000000000000A07A8111938AE2C0C652E6947E9615410000000000000000	1	\N	1	\N	0	{1}
246	01020000A0187A000002000000A07A8111938AE2C0C652E6947E96154100000000000000005C8FC2F5488AE2C0BA1E85EB6E9615410000000000000000	1	\N	1	\N	0	{1}
247	01020000A0187A0000020000005C8FC2F5488AE2C0BA1E85EB6E9615410000000000000000103F8E04DF89E2C041B3EC475F9615410000000000000000	1	\N	1	\N	0	{1}
268	01020000A0187A000002000000403EFA92BD49E2C0743029E4A6A21541000000000000000054DA32915E49E2C009B89B20A3A215410000000000000000	1	\N	1	\N	0	{1}
248	01020000A0187A000041000000D05BC828A689E2C0BE87A9EA5C96154100000000000000002426EC1EA789E2C0E227DEE35C96154100000000000000005498F415A889E2C0FAAC99DD5C96154100000000000000006437CF0DA989E2C00F8FDCD75C96154100000000000000009C786906AA89E2C0093CA7D25C9615410000000000000000E8C2B0FFAA89E2C0A417FACD5C96154100000000000000004C7092F9AB89E2C0727BD5C95C961541000000000000000040CFFBF3AC89E2C0C9B639C65C96154100000000000000000C24DAEEAD89E2C0C60E27C35C961541000000000000000038AA1AEAAE89E2C041BE9DC05C96154100000000000000000496AAE5AF89E2C0CDF59DBE5C9615410000000000000000A81577E1B089E2C0B6DB27BD5C9615410000000000000000E4526DDDB189E2C0F48B3BBC5C961541000000000000000058747AD9B289E2C03918D9BB5C9615410000000000000000E89E8BD5B389E2C0E18700BC5C961541000000000000000028F78DD1B489E2C0F7D7B1BC5C9615410000000000000000D0A26ECDB589E2C03AFBECBD5C961541000000000000000018CA1AC9B689E2C015DAB1BF5C96154100000000000000002C997FC4B789E2C0A65200C25C96154100000000000000007C418ABFB889E2C0C438D8C45C961541000000000000000054FB27BAB989E2C0F85539C85C96154100000000000000000C0746B4BA89E2C08C6923CC5C961541000000000000000098AED1ADBB89E2C0872896D05C9615410000000000000000D846B8A6BC89E2C0B93D91D55C96154100000000000000000831E79EBD89E2C0BF4914DB5C961541000000000000000024DC4B96BE89E2C00AE31EE15C961541000000000000000044C6D38CBF89E2C0E695B0E75C96154100000000000000000C7E6C82C089E2C084E4C8EE5C9615410000000000000000F8A30377C189E2C0064767F65C9615410000000000000000D4EB866AC289E2C07F2B8BFE5C96154100000000000000000C1EE45CC389E2C00FF633075D96154100000000000000000C19094EC489E2C0DC0061105D96154100000000000000009CD2E33DC589E2C02B9C111A5D96154100000000000000003459622CC689E2C06C0E45245D961541000000000000000060D57219C789E2C03F94FA2E5D9615410000000000000000048B0305C889E2C08F60313A5D9615410000000000000000CCDA02EFC889E2C0989CE8455D961541000000000000000054435FD7C989E2C0F9671F525D9615410000000000000000A06207BECA89E2C0CBD8D45E5D961541000000000000000050F7E9A2CB89E2C0A8FB076C5D9615410000000000000000F4E1F585CC89E2C0C6D3B7795D96154100000000000000004C261A67CD89E2C0075BE3875D9615410000000000000000A0EC4546CE89E2C0098289965D9615410000000000000000E8826823CF89E2C04230A9A55D9615410000000000000000285E71FECF89E2C00D4441B55D96154100000000000000008C1B50D7D089E2C0C59250C55D9615410000000000000000BC81F4ADD189E2C0D9E8D5D55D961541000000000000000018824E82D289E2C0E509D0E65D9615410000000000000000C8394E54D389E2C0C6B03DF85D961541000000000000000014F3E323D489E2C0B68F1D0A5E9615410000000000000000782600F1D489E2C064506E1C5E9615410000000000000000D07B93BBD589E2C00B942E2F5E961541000000000000000088CB8E83D689E2C090F35C425E9615410000000000000000C01FE348D789E2C09CFFF7555E961541000000000000000058B5810BD889E2C0B640FE695E961541000000000000000014FD5BCBD889E2C05F376E7E5E9615410000000000000000C49C6388D989E2C02F5C46935E96154100000000000000003C708A42DA89E2C0F71F85A85E9615410000000000000000708AC2F9DA89E2C0D6EB28BE5E96154100000000000000008436FEADDB89E2C05F2130D45E9615410000000000000000C0F82F5FDC89E2C0B31A99EA5E9615410000000000000000A88F4A0DDD89E2C0A22A62015F9615410000000000000000ECF440B8DD89E2C0D19C89185F9615410000000000000000645E0660DE89E2C0CFB50D305F9615410000000000000000103F8E04DF89E2C042B3EC475F9615410000000000000000	1	\N	1	\N	0	{1}
249	01020000A0187A000002000000D4650318608CE2C04504D66B4F9615410000000000000000E03A5E0F1B8CE2C05F3DB0E1599615410000000000000000	1	\N	1	\N	0	{1}
250	01020000A0187A000002000000E03A5E0F1B8CE2C05F3DB0E15996154100000000000000005CF539AABD8BE2C0DD527C676A9615410000000000000000	1	\N	1	\N	0	{1}
251	01020000A0187A0000020000005CF539AABD8BE2C0DD527C676A9615410000000000000000ACE99B63788BE2C0ED907AB97A9615410000000000000000	1	\N	1	\N	0	{1}
252	01020000A0187A000041000000D8650318608CE2C04604D66B4F96154100000000000000007824F889608CE2C0FF7FC75A4F9615410000000000000000ACEA8FFD608CE2C0C943E5494F9615410000000000000000486BC672618CE2C07BF02F394F9615410000000000000000B44997E9618CE2C04025A8284F96154100000000000000001C1AFE61628CE2C0917F4E184F96154100000000000000008061F6DB628CE2C02D9B23084F9615410000000000000000FC957B57638CE2C01A1228F84E9615410000000000000000E01E89D4638CE2C0987C5CE84E9615410000000000000000E4541A53648CE2C01F71C1D84E961541000000000000000058822AD3648CE2C0588457C94E96154100000000000000004CE3B454658CE2C01A491FBA4E9615410000000000000000B0A5B4D7658CE2C0605019AB4E96154100000000000000009CE9245C668CE2C04729469C4E961541000000000000000070C100E2668CE2C00A61A68D4E961541000000000000000000324369678CE2C0F7823A7F4E9615410000000000000000CC32E7F1678CE2C0711803714E961541000000000000000028AEE77B688CE2C0E5A800634E961541000000000000000074813F07698CE2C0C7B933554E9615410000000000000000487DE993698CE2C091CE9C474E9615410000000000000000A465E0216A8CE2C0B5683C3A4E96154100000000000000002CF21EB16A8CE2C0A207132D4E96154100000000000000004CCE9F416B8CE2C0B92821204E961541000000000000000070995DD36B8CE2C04B4767134E961541000000000000000040E752666C8CE2C092DCE5064E9615410000000000000000C43F7AFA6C8CE2C0B15F9DFA4D9615410000000000000000AC1FCE8F6D8CE2C0A8458EEE4D96154100000000000000006CF848266E8CE2C05A01B9E24D96154100000000000000008C30E5BD6E8CE2C07F031ED74D9615410000000000000000BC239D566F8CE2C0A7BABDCB4D961541000000000000000038236BF06F8CE2C02F9398C04D9615410000000000000000C875498B708CE2C043F7AEB54D961541000000000000000024583227718CE2C0D84E01AB4D961541000000000000000010FD1FC4718CE2C0A7FF8FA04D9615410000000000000000A48D0C62728CE2C02A6D5B964D96154100000000000000007029F200738CE2C09AF8638C4D9615410000000000000000C8E6CAA0738CE2C0E800AA824D9615410000000000000000F0D29041748CE2C0BCE22D794D96154100000000000000005CF23DE3748CE2C06FF8EF6F4D9615410000000000000000E440CC85758CE2C00E9AF0664D961541000000000000000004B23529768CE2C04D1D305E4D9615410000000000000000003174CD768CE2C08DD5AE554D961541000000000000000040A18172778CE2C0D1136D4D4D961541000000000000000070DE5718788CE2C0C4266B454D9615410000000000000000CCBCF0BE788CE2C0AB5AA93D4D961541000000000000000044094666798CE2C06DF927364D9615410000000000000000C889510E7A8CE2C0894AE72E4D961541000000000000000090FD0CB77A8CE2C01593E7274D96154100000000000000003C1D72607B8CE2C0BF1529214D96154100000000000000000C9B7A0A7C8CE2C0C512AC1A4D9615410000000000000000502320B57C8CE2C0F5C770144D9615410000000000000000605C5C607D8CE2C0AE70770E4D961541000000000000000004E7280C7E8CE2C0D745C0084D9615410000000000000000B05E7FB87E8CE2C0E57D4B034D96154100000000000000009C5959657F8CE2C0CE4C19FE4C96154100000000000000003C69B012808CE2C016E429F94C9615410000000000000000381A7EC0808CE2C0BD727DF44C9615410000000000000000F0F4BB6E818CE2C04A2514F04C9615410000000000000000847D631D828CE2C0C325EEEB4C96154100000000000000002C346ECC828CE2C0AC9B0BE84C96154100000000000000006895D57B838CE2C00AAC6CE44C96154100000000000000004C1A932B848CE2C0567911E14C9615410000000000000000BC38A0DB848CE2C08E23FADD4C96154100000000000000009863F68B858CE2C021C826DB4C9615410000000000000000100B8F3C868CE2C0FB8197D84C9615410000000000000000	1	\N	1	\N	0	{1}
253	01020000A0187A000002000000F0F9EF03089DE2C057F24675979515410000000000000000E4B79436369DE2C093FABDA7A29515410000000000000000	1	\N	1	\N	0	{1}
254	01020000A0187A000002000000586846493B88E2C0AA3A9597419615410000000000000000741FCF256D88E2C0D46C690C659615410000000000000000	1	\N	1	\N	0	{1}
255	01020000A0187A000002000000B46746493B88E2C0AE3A9597419615410000000000000000D46478CF5A88E2C07EA0A6E7409615410000000000000000	1	\N	1	\N	0	{1}
256	01020000A0187A000002000000D46478CF5A88E2C07EA0A6E7409615410000000000000000980417098388E2C0725243825D9615410000000000000000	1	\N	1	\N	0	{1}
257	01020000A0187A00004100000038FEA7AAC888E2C037E98547639615410000000000000000702C443DC788E2C01F6269516396154100000000000000008800FDCDC588E2C0449E235A639615410000000000000000DCEA0E5DC488E2C0FA2DB36163961541000000000000000074A1B6EAC288E2C0BED21668639615410000000000000000E4153177C188E2C0677F4D6D639615410000000000000000586BBB02C088E2C0515856716396154100000000000000007CEC928DBE88E2C088B330746396154100000000000000006C01F517BD88E2C0D918DC756396154100000000000000009C251FA2BB88E2C0F2415876639615410000000000000000B0DD4E2CBA88E2C0631AA5756396154100000000000000005CADC1B6B888E2C0A6BFC273639615410000000000000000500DB541B788E2C01E81B170639615410000000000000000106166CDB588E2C001E0716C639615410000000000000000E4EC125AB488E2C04C8F0467639615410000000000000000B8CBF7E7B288E2C09C736A6063961541000000000000000010E55177B188E2C013A3A45863961541000000000000000010E35D08B088E2C02165B44F6396154100000000000000006828589BAE88E2C053329B4563961541000000000000000078C67C30AD88E2C016B45A3A639615410000000000000000687307C8AB88E2C06BC4F42D6396154100000000000000004C803362AA88E2C0A06D6B2063961541000000000000000074CF3BFFA888E2C0F6E9C011639615410000000000000000ACCA5A9FA788E2C044A3F7016396154100000000000000009859CA42A688E2C0933212F16296154100000000000000004CD8C3E9A488E2C0AB5F13DF629615410000000000000000B40D8094A388E2C0A720FECB62961541000000000000000060223743A288E2C07099D5B76296154100000000000000002C9720F6A088E2C03C1B9DA2629615410000000000000000203C73AD9F88E2C00324588C629615410000000000000000882765699E88E2C0EC5D0A75629615410000000000000000E4AC2B2A9D88E2C0AE9EB75C6296154100000000000000004454FBEF9B88E2C0F7E663436296154100000000000000008CD107BB9A88E2C0BB611329629615410000000000000000F8FB838B9988E2C08863CA0D629615410000000000000000C8C5A1619888E2C0D0698DF1619615410000000000000000FC33923D9788E2C02D1A61D46196154100000000000000004856851F9688E2C099414AB6619615410000000000000000343FAA079588E2C0A8D34D976196154100000000000000003CFC2EF69388E2C0B5E97077619615410000000000000000688E40EB9288E2C00BC2B856619615410000000000000000D4E20AE79188E2C00ABF2A356196154100000000000000005CCBB8E99088E2C04466CC12619615410000000000000000B4F773F38F88E2C0945FA3EF60961541000000000000000080EE64048F88E2C02B74B5CB6096154100000000000000009806B31C8E88E2C0A68D08A7609615410000000000000000AC60843C8D88E2C00CB5A281609615410000000000000000E0E0FD638C88E2C0D4118A5B609615410000000000000000D42843938B88E2C0E4E8C434609615410000000000000000B89176CA8A88E2C0809B590D609615410000000000000000A826B9098A88E2C048A64EE55F96154100000000000000003C9F2A518988E2C01FA0AABC5F96154100000000000000004C5AE9A08888E2C01B3974935F9615410000000000000000FC5812F98788E2C06739B2695F9615410000000000000000F039C1598788E2C024806B3F5F9615410000000000000000B43410C38688E2C05002A7145F9615410000000000000000801518358688E2C098C96BE95E96154100000000000000001839F0AF8588E2C033F3C0BD5E9615410000000000000000F888AE338588E2C0B4AEAD915E9615410000000000000000B47767C08488E2C0E23C39655E9615410000000000000000A0FD2D568488E2C07DEE6A385E9615410000000000000000AC9513F58388E2C014234A0B5E9615410000000000000000883A289D8388E2C0C347DEDD5D961541000000000000000000647A4E8388E2C006D62EB05D9615410000000000000000980417098388E2C0725243825D9615410000000000000000	1	\N	1	\N	0	{1}
258	01020000A0187A000059000000586846493B88E2C0AA3A95974196154100000000000000002C33D5B9DC87E2C01F1EAFDBE49515410000000000000000B0E19EA45687E2C0B2FD2BFBBF9515410000000000000000608FB92A6286E2C06C807977A8951541000000000000000080EB41188885E2C03549D7B28F95154100000000000000009CAFC7A4D584E2C0BB2B5B68799515410000000000000000BCB719E31F84E2C0207F27CC589515410000000000000000C0F889EB7882E2C0ECD75ACC119515410000000000000000C0A184DD5782E2C037579C69059515410000000000000000B09E59F30482E2C0CC3C9FDBDD941541000000000000000068225326B681E2C091EDB4D5BF9415410000000000000000BC1C7EFD7E81E2C01A0FBA45A4941541000000000000000024A64C596781E2C0ECD4DCBD86941541000000000000000098DEFA965781E2C02EDFEF5D5F941541000000000000000024A64C596781E2C0F14200A42E94154100000000000000008CF008B09281E2C092411A5C01941541000000000000000068225326B681E2C08128917EEC9315410000000000000000B8EB8D841982E2C02B9AA1A6DE93154100000000000000008C579A50BC82E2C0D6C1BB3CD193154100000000000000009453B4787A83E2C0AD404242CD931541000000000000000064D07CACDE85E2C01D052FBFCD9315410000000000000000D042383F3C87E2C03A2852DACF9315410000000000000000A8C8BF273089E2C09D0FDA5BD69315410000000000000000504053EE368AE2C0949955C7D993154100000000000000004F045481388AE2C06FA6E1CBD99315410000000000000000B3752D153A8AE2C03C680BCFD9931541000000000000000022BA91A93B8AE2C0DF42D2D0D993154100000000000000007CDC323E3D8AE2C0AADE35D1D99315410000000000000000E7DBC2D23E8AE2C0672836D0D99315410000000000000000D7BAF366408AE2C06351D3CDD99315410000000000000000148E77FA418AE2C060CF0DCAD99315410000000000000000C58B008D438AE2C07E5CE6C4D99315410000000000000000691A411E458AE2C019F75DBED99315410000000000000000D3DFEBAD468AE2C097E175B6D993154100000000000000000ED0B33B488AE2C02BA22FADD99315410000000000000000383C4CC7498AE2C089028DA2D993154100000000000000004EE168504B8AE2C08D0F9096D99315410000000000000000DCF6BDD64C8AE2C0D6183B89D993154100000000000000009A3D005A4E8AE2C055B0907AD99315410000000000000000EF0DE5D94F8AE2C0CEA9936AD9931541000000000000000052662256518AE2C04B1A4759D9931541000000000000000093F96ECE528AE2C08757AE46D99315410000000000000000F73C8242548AE2C046F7CC32D99315410000000000000000387614B2558AE2C0A5CEA61DD9931541000000000000000059C9DE1C578AE2C05EF13F07D993154100000000000000004B469B82588AE2C0FEB09CEFD893154100000000000000006CF604E3598AE2C0119CC1D6D89315410000000000000000D3E9D73D5B8AE2C03E7DB3BCD893154100000000000000006544D1925C8AE2C05F5A77A1D89315410000000000000000BD4AAFE15D8AE2C086731285D89315410000000000000000D46E312A5F8AE2C0F8418A67D89315410000000000000000765C186C608AE2C02677E448D89315410000000000000000750526A7618AE2C08DFB2629D89315410000000000000000A0AD1DDB628AE2C096ED5708D893154100000000000000007BF6C307648AE2C065A07DE6D79315410000000000000000ADEADE2C658AE2C0A59A9EC3D793154100000000000000002F09364A668AE2C04395C19FD793154100000000000000002E50925F678AE2C0247AED7AD79315410000000000000000A847BE6C688AE2C0CE622955D79315410000000000000000BC0B8671698AE2C00A977C2ED79315410000000000000000A556B76D6A8AE2C07E8BEE06D79315410000000000000000728A21616B8AE2C03DE086DED6931541000000000000000060BA954B6C8AE2C04C5F4DB5D69315410000000000000000E9B3E62C6D8AE2C025FB498BD693154100000000000000007A07E9046E8AE2C02ECD8460D69315410000000000000000CF1073D36E8AE2C025140635D6931541000000000000000001FF5C986F8AE2C09232D608D693154100000000000000002DDC8053708AE2C020ADFDDBD59315410000000000000000C794BA04718AE2C0FE2885AED5931541000000000000000090FEE7AB718AE2C0326A7580D5931541000000000000000029DFE848728AE2C0EC51D751D593154100000000000000004EF29EDB728AE2C0C9DCB322D59315410000000000000000A7EFED63738AE2C0202114F3D493154100000000000000003F90BBE1738AE2C0384D01C3D493154100000000000000009293EF54748AE2C08DA58492D493154100000000000000003EC473BD748AE2C0FF82A761D4931541000000000000000046FC331B758AE2C007517330D49315410000000000000000F9281E6E758AE2C0E98BF1FED393154100000000000000006A4E22B6758AE2C0DABE2BCDD39315410000000000000000888A32F3758AE2C030822B9BD39315410000000000000000C9174325768AE2C08279FA68D393154100000000000000006F4F4A4C768AE2C0D151A236D3931541000000000000000066AB4068768AE2C0A7BF2C04D39315410000000000000000B6C72079768AE2C03B7DA3D1D293154100000000000000008F63E77E768AE2C08F48109FD29315410000000000000000E4619379768AE2C091E17C6CD29315410000000000000000A9C92569768AE2C03708F339D293154100000000000000009CC5A14D768AE2C0A17A7C07D29315410000000000000000E8C254AB5D8AE2C0EE6D270EAC9315410000000000000000	1	\N	1	\N	0	{1}
259	01020000A0187A000002000000EC432155F19BE2C038D6F62A939315410000000000000000A46717D6629CE2C0544FC2148E9315410000000000000000	1	\N	1	\N	0	{1}
260	01020000A0187A00000200000084167CFA0D9DE2C0B9C14769869315410000000000000000BCCB0D47E09CE2C016448C2D769315410000000000000000	1	\N	1	\N	0	{1}
261	01020000A0187A000002000000B8F76D2BC7A2E2C0CF00C8F71293154100000000000000002CF6D49C20A2E2C0DA6E69CFAB9215410000000000000000	1	\N	1	\N	0	{1}
262	01020000A0187A0000020000007C0704F469A2E2C009C7E33BD99215410000000000000000A8F7B70B2FA2E2C00E8550A0DA9215410000000000000000	1	\N	1	\N	0	{1}
263	01020000A0187A0000020000002CF6D49C20A2E2C0DA6E69CFAB9215410000000000000000584F5A2ACBA1E2C047561CAC899215410000000000000000	1	\N	1	\N	0	{1}
269	01020000A0187A000043000000043FF53D8471E2C07FE84991219815410000000000000000A4BCBAC78371E2C0BBF694B81F98154100000000000000007BD8189D8371E2C0973713691F981541000000000000000008030A628371E2C0EF87BB191F9815410000000000000000575698168371E2C0067A9BCA1E9815410000000000000000F5B9D0BA8271E2C09D96C07B1E9815410000000000000000C0E0C24E8271E2C09E5A382D1E9815410000000000000000364681D28171E2C0D03410DF1D98154100000000000000004A2B21468171E2C08B8355911D9815410000000000000000C592BAA98071E2C06F9215441D9815410000000000000000273D68FD7F71E2C01B985DF71C981541000000000000000016A447417F71E2C0EFB33AAB1C981541000000000000000052F578757E71E2C0C8EBB95F1C9815410000000000000000350D1F9A7D71E2C0CB29E8141C9815410000000000000000BA705FAF7C71E2C02B3AD2CA1B9815410000000000000000174762B57B71E2C0FCC884811B9815410000000000000000DA5252AC7A71E2C006600C391B981541000000000000000099EA5C947971E2C0A16475F11A981541000000000000000036F1B16D7871E2C09615CCAA1A9815410000000000000000A6CD83387771E2C007891C651A9815410000000000000000596207F57571E2C05CAA72201A98154100000000000000002B0474A37471E2C03C38DADC199815410000000000000000ED7003447371E2C089C25E9A19981541000000000000000086C5F1D67171E2C067A80B59199815410000000000000000AA737D5C7071E2C04616EC181998154100000000000000002A37E7D46E71E2C0FF030BDA189815410000000000000000E50A72406D71E2C0EE32739C189815410000000000000000521D639F6B71E2C0202C2F60189815410000000000000000A7C401F26971E2C0823E4925189815410000000000000000AB7297386871E2C01E7DCBEB17981541000000000000000022A86F736671E2C063BDBFB3179815410000000000000000E3E7D7A26471E2C078952F7D1798154100000000000000009AA91FC76271E2C0945A2448179815410000000000000000294C98E06071E2C0691FA714179815410000000000000000C50795EF5E71E2C094B2C0E2169815410000000000000000B4DF6AF45C71E2C01F9D79B2169815410000000000000000C69370EF5A71E2C00621DA831698154100000000000000007B91FEE05871E2C0D337EA56169815410000000000000000E7E46EC95671E2C03D91B12B16981541000000000000000049291DA95471E2C0D89137021698154100000000000000005C7966805271E2C0D45183DA159815410000000000000000735FA94F5071E2C0C29B9BB415981541000000000000000044C545174E71E2C06EEB869015981541000000000000000086E39CD74B71E2C0C16C4B6E1598154100000000000000004E3111914971E2C0B5FAEE4D159815410000000000000000365306444771E2C0521E772F159815410000000000000000560AE1F04471E2C0BE0DE912159815410000000000000000022307984271E2C057AB49F81498154100000000000000006663DF394071E2C0DF849DDF149815410000000000000000F079D1D63D71E2C0B2D2E8C814981541000000000000000091EB456F3B71E2C00F772FB4149815410000000000000000E101A6033971E2C06EFD74A114981541000000000000000019B95B943671E2C0E599BC90149815410000000000000000F5ADD1213471E2C09A280982149815410000000000000000760B73AC3171E2C0472D5D751498154100000000000000008D78AB342F71E2C0CCD2BA6A149815410000000000000000B105E7BA2C71E2C0CFEA2362149815410000000000000000641A923F2A71E2C070ED995B149815410000000000000000AA6219C32771E2C003F91D571498154100000000000000006CBCE9452571E2C0E2D1B054149815410000000000000000E32470C82271E2C04EE25254149815410000000000000000E8A5194B2071E2C0563A0456149815410000000000000000564353CE1D71E2C0DC8FC45914981541000000000000000063E889521B71E2C09D3E935F149815410000000000000000FB542AD81871E2C04E486F67149815410000000000000000280BA15F1671E2C0C554577114981541000000000000000018D6DDBAEF6EE2C09045CE29189815410000000000000000	1	\N	1	\N	0	{1}
270	01020000A0187A000007010000C0856086B798E2C0D453EBC99894154100000000000000000CC51046849AE2C0BA8774EE67941541000000000000000066E43147859AE2C0844B9CD2679415410000000000000000C3CAA443869AE2C048C11AB6679415410000000000000000F29A4D3B879AE2C07D0EF3986794154100000000000000001AFF102E889AE2C0F26A287B679415410000000000000000B92BD41B899AE2C06F20BE5C6794154100000000000000009BE27C048A9AE2C05F8AB73D679415410000000000000000C175F1E78A9AE2C06A15181E67941541000000000000000031CA18C68B9AE2C0183FE3FD669415410000000000000000C55ADA9E8C9AE2C071951CDD669415410000000000000000D43A1E728D9AE2C091B6C7BB669415410000000000000000E018CD3F8E9AE2C04A50E8996694154100000000000000002541D0078F9AE2C0B51F827766941541000000000000000017A011CA8F9AE2C0CFF09854669415410000000000000000D9C47B86909AE2C0079E303166941541000000000000000096E3F93C919AE2C0D60F4D0D669415410000000000000000CCD777ED919AE2C0513CF2E86594154100000000000000008926E297929AE2C0B32624C46594154100000000000000008F00263C939AE2C0F3DEE69E659415410000000000000000654431DA939AE2C04C813E796594154100000000000000005E80F271949AE2C0CE352F5365941541000000000000000080F45803959AE2C0E02FBD2C6594154100000000000000005E94548E959AE2C0D3ADEC05659415410000000000000000E208D612969AE2C065F8C1DE649415410000000000000000F7B1CE90969AE2C0486241B76494154100000000000000002EA83008979AE2C0A8476F8F64941541000000000000000042BEEE78979AE2C0B10D50676494154100000000000000008D82FCE2979AE2C01322E83E64941541000000000000000068404E46989AE2C082FA3B166494154100000000000000007701D9A2989AE2C03D1450ED639415410000000000000000DE8E92F8989AE2C08AF328C463941541000000000000000061727147999AE2C03823CB9A6394154100000000000000006DF76C8F999AE2C021343B71639415410000000000000000152C7DD0999AE2C0A6BC7D47639415410000000000000000ECE19A0A9A9AE2C02F58971D639415410000000000000000D1AEBF3D9A9AE2C0A9A68CF3629415410000000000000000A8EDE5699A9AE2C0024C62C9629415410000000000000000F4BE088F9A9AE2C0A6EF1C9F629415410000000000000000670924AD9A9AE2C0FD3BC1746294154100000000000000004D7A34C49A9AE2C0E6DD534A629415410000000000000000F58537D49A9AE2C03484D91F629415410000000000000000F0672BDD9A9AE2C027DF56F561941541000000000000000046230FDF9A9AE2C0EC9FD0CA6194154100000000000000009482E2D99A9AE2C012784BA06194154100000000000000000D18A6CD9A9AE2C00D19CC756194154100000000000000006F3D5BBA9A9AE2C0AB33574B619415410000000000000000DB1304A09A9AE2C09477F1206194154100000000000000009683A37E9A9AE2C0C2929FF6609415410000000000000000BC3B3D569A9AE2C0FF3066CC609415410000000000000000D2B1D5269A9AE2C05FFB49A26094154100000000000000004F2172F0999AE2C0C2974F78609415410000000000000000028B18B3999AE2C046A87B4E6094154100000000000000006CB4CF6E999AE2C0D0CAD224609415410000000000000000FC269F23999AE2C0829859FB5F9415410000000000000000432F8FD1989AE2C03AA514D25F941541000000000000000000DCA878989AE2C0127F08A95F941541000000000000000024FDF518989AE2C0E2AD39805F9415410000000000000000BF2281B2979AE2C0B9B2AC575F9415410000000000000000D29B5545979AE2C06307662F5F941541000000000000000010757FD1969AE2C0EB1D6A075F94154100000000000000008C770B57969AE2C01A60BDDF5E94154100000000000000004D2707D6959AE2C0FC2E64B85E9415410000000000000000D1C1804E959AE2C065E262915E94154100000000000000007B3C87C0949AE2C075C8BD6A5E9415410000000000000000EC422A2C949AE2C01F2579445E9415410000000000000000781A3F221E9AE2C00729159C409415410000000000000000D06F4E320599E2C0ACF63F3401941541000000000000000003B372B30499E2C061FB1417019415410000000000000000FD8F63380499E2C02D2DA9F9009415410000000000000000184E29C10399E2C0C086FEDB009415410000000000000000B0F2CB4D0399E2C0080717BE0094154100000000000000009A4053DE0299E2C008B1F49F0094154100000000000000009FB7C6720299E2C0BC8B9981009415410000000000000000FA932D0B0299E2C0EEA10763009415410000000000000000D9CD8EA70199E2C01A024144009415410000000000000000EB18F1470199E2C047BE4725009415410000000000000000E8E35AEC0099E2C0E5EB1D060094154100000000000000002258D2940099E2C0A6A3C5E6FF93154100000000000000001D595D410099E2C0600141C7FF93154100000000000000002A8401F2FF98E2C0E12392A7FF93154100000000000000000330C4A6FF98E2C0CF2CBB87FF9315410000000000000000736CAA5FFF98E2C08640BE67FF9315410000000000000000FC01B91CFF98E2C0EB859D47FF93154100000000000000008571F4DDFE98E2C04E265B27FF931541000000000000000010F460A3FE98E2C0444DF906FF9315410000000000000000697A026DFE98E2C07C287AE6FE9315410000000000000000EDACDC3AFE98E2C0A1E7DFC5FE931541000000000000000042EBF20CFE98E2C030BC2CA5FE9315410000000000000000224C48E3FD98E2C053D96284FE9315410000000000000000239DDFBDFD98E2C0BA738463FE93154100000000000000008962BB9CFD98E2C078C19342FE931541000000000000000018D7DD7FFD98E2C0DAF99221FE9315410000000000000000F1EB4867FD98E2C044558400FE93154100000000000000006E48FE52FD98E2C0050D6ADFFD9315410000000000000000054AFF42FD98E2C0385B46BEFD931541000000000000000034044D37FD98E2C0997A1B9DFD93154100000000000000006940E82FFD98E2C05EA6EB7BFD9315410000000000000000FC7DD12CFD98E2C0151AB95AFD93154100000000000000001EF2082EFD98E2C07A118639FD9315410000000000000000DC878E33FD98E2C050C85418FD93154100000000000000001CE0613DFD98E2C03D7A27F7FC9315410000000000000000A751824BFD98E2C0A36200D6FC931541000000000000000031E9EE5DFD98E2C077BCE1B4FC93154100000000000000006E69A674FD98E2C01FC2CD93FC9315410000000000000000204BA78FFD98E2C047ADC672FC931541000000000000000039BDEFAEFD98E2C0BFB6CE51FC9315410000000000000000F7A47DD2FD98E2C05216E830FC9315410000000000000000059E4EFAFD98E2C09E021510FC9315410000000000000000ACFA5F26FE98E2C0F5B057EFFB9315410000000000000000FAC3AE56FE98E2C02E55B2CEFB9315410000000000000000F6B9378BFE98E2C0852127AEFB9315410000000000000000DE53F7C3FE98E2C07446B88DFB93154100000000000000005BC0E900FF98E2C08CF2676DFB9315410000000000000000CAE50A42FF98E2C05152384DFB93154100000000000000007F625687FF98E2C014902B2DFB9315410000000000000000118DC7D0FF98E2C0CBD3430DFB9315410000000000000000AA74591E0099E2C0F24283EDFA93154100000000000000005FE106700099E2C05F00ECCDFA93154100000000000000008554CAC50099E2C0242C80AEFA931541000000000000000014099E1F0199E2C065E3418FFA931541000000000000000007F47B7D0199E2C035403370FA9315410000000000000000C5C45DDF0199E2C074595651FA931541000000000000000092E53C450299E2C0A942AD32FA9315410000000000000000FA7B12AF0299E2C0DE0B3A14FA93154100000000000000004869D71C0399E2C07EC1FEF5F99315410000000000000000074B848E0399E2C0306CFDD7F99315410000000000000000797B11040499E2C0B61038BAF993154100000000000000002012777D0499E2C0C8AFB09CF9931541000000000000000043E4ACFA0499E2C0F445697FF993154100000000000000007E85AA7B0599E2C078CB6362F99315410000000000000000504867000699E2C02434A245F993154100000000000000000002A3AD9099E2C08882AAC8DB9315410000000000000000EE0318719199E2C0F4DEEF9DDB9315410000000000000000178F472C9299E2C09414A272DB93154100000000000000009EF515DF9299E2C0A98AC746DB9315410000000000000000DBC668899399E2C044BD661ADB931541000000000000000042D3262B9499E2C0513C86EDDA93154100000000000000001D3038C49499E2C09EAA2CC0DA9315410000000000000000143B86549599E2C0E0BC6092DA93154100000000000000008A9DFBDB9599E2C0B5382964DA9315410000000000000000C14F845A9699E2C0A3F38C35DA9315410000000000000000D09B0DD09699E2C018D29206DA93154100000000000000006920863C9799E2C060C641D7D993154100000000000000006CD3DD9F9799E2C0A5CFA0A7D99315410000000000000000420406FA9799E2C0DEF8B677D993154100000000000000000E5EF14A9899E2C0CC578B47D99315410000000000000000A1E993929899E2C0E90B2517D99315410000000000000000450FE3D09899E2C05C3D8BE6D893154100000000000000004698D5059999E2C0EA1BC5B5D8931541000000000000000055B063319999E2C0E6DDD984D89315410000000000000000B0E686539999E2C020BFD053D89315410000000000000000112F3A6C9999E2C0D2FFB022D8931541000000000000000073E2797B9999E2C090E381F1D7931541000000000000000098BF43819999E2C032B04AC0D7931541000000000000000060EB967D9999E2C0C4AC128FD79315410000000000000000EBF073709999E2C07020E15DD7931541000000000000000081C1DC599999E2C06A51BD2CD793154100000000000000004BB4D4399999E2C0E083AEFBD69315410000000000000000D38560109999E2C0E3F8BBCAD69315410000000000000000525786DD9899E2C058EDEC99D69315410000000000000000C9AD4DA19899E2C0E4984869D69315410000000000000000E070BF5B9899E2C0D82CD638D6931541000000000000000098E9E50C9899E2C028D39C08D69315410000000000000000C9C0CCB49799E2C055ADA3D8D5931541000000000000000061FD80539799E2C062D3F1A8D593154100000000000000007B0211E99699E2C0C8528E79D59315410000000000000000418D8C759699E2C06A2D804AD5931541000000000000000094B204F99599E2C08A58CE1BD5931541000000000000000086DC8B739599E2C0C6BB7FEDD49315410000000000000000A2C735E59499E2C00E309BBFD493154100000000000000000280174E9499E2C0A57E2792D49315410000000000000000305E47AE9399E2C01C602B65D49315410000000000000000D803DD059399E2C0567BAD38D493154100000000000000004C58F1549299E2C08D64B40CD49315410000000000000000D4849E9B9199E2C0569C46E1D39315410000000000000000CCF0FFD99099E2C0AF8E6AB6D393154100000000000000009F3D32109099E2C00692268CD393154100000000000000008342533E8F99E2C04FE68062D39315410000000000000000130882648E99E2C015B47F39D39315410000000000000000B8C3DE828D99E2C0910B2911D39315410000000000000000E7D28A998C99E2C0C2E382E9D293154100000000000000002EB6A8A88B99E2C0901993C2D293154100000000000000001F0C5CB08A99E2C0EB6E5F9CD29315410000000000000000078CC9B08999E2C0F189ED76D29315410000000000000000840017AA8899E2C01AF44252D29315410000000000000000EC416B9C8799E2C06419652ED293154100000000000000008F30EE878699E2C08747590BD29315410000000000000000D2AEC86C8599E2C02EAD24E9D19315410000000000000000239B244B8499E2C02E59CCC7D19315410000000000000000C7C92C238399E2C0CC3955A7D1931541000000000000000089FE0CF58199E2C0001CC487D193154100000000000000003AE6F1C08099E2C0BDAA1D69D193154100000000000000001E1009877F99E2C0446E664BD1931541000000000000000027E780477E99E2C078CBA22ED1931541000000000000000020AB88027D99E2C03303D712D19315410000000000000000AC6950B87B99E2C0AD3107F8D093154100000000000000001C446A7D5799E2C0EE329F1ACE931541000000000000000027C17D545799E2C0507EAE14CE93154100000000000000001CE3BF2B5799E2C04AC9B80ECE931541000000000000000019D130035799E2C09619BE08CE931541000000000000000011B2D0DA5699E2C0F074BE02CE9315410000000000000000C9AC9FB25699E2C01CE1B9FCCD9315410000000000000000D8E79D8A5699E2C0E163B0F6CD9315410000000000000000AA89CB625699E2C00A03A2F0CD93154100000000000000007AB8283B5699E2C06AC48EEACD9315410000000000000000599AB5135699E2C0D4AD76E4CD9315410000000000000000285572EC5599E2C023C559DECD93154100000000000000009B0E5FC55599E2C0361038D8CD931541000000000000000036EC7B9E5599E2C0F09411D2CD93154100000000000000005113C9775599E2C03959E6CBCD931541000000000000000016A946515599E2C0FD62B6C5CD93154100000000000000007DD2F42A5599E2C02EB881BFCD931541000000000000000054B4D3045599E2C0C05E48B9CD93154100000000000000003773E3DE5499E2C0AE5C0AB3CD9315410000000000000000943324B95499E2C0F6B7C7ACCD9315410000000000000000A91996935499E2C09B7680A6CD93154100000000000000008849396E5499E2C0A59E34A0CD93154100000000000000000FE70D495499E2C01F36E499CD9315410000000000000000F11514245499E2C019438F93CD9315410000000000000000AEF94BFF5399E2C0A8CB358DCD931541000000000000000099B5B5DA5399E2C0E5D5D786CD9315410000000000000000D26C51B65399E2C0EC677580CD93154100000000000000004C421F925399E2C0E0870E7ACD9315410000000000000000C9581F6E5399E2C0E53BA373CD9315410000000000000000D9D2514A5399E2C0278A336DCD9315410000000000000000DED2B6265399E2C0D278BF66CD9315410000000000000000097B4E035399E2C01A0E4760CD931541000000000000000058ED18E05299E2C03550CA59CD93154100000000000000009C4B16BD5299E2C05D454953CD931541000000000000000073B7469A5299E2C0D2F3C34CCD93154100000000000000004952AA775299E2C0D6613A46CD93154100000000000000005B3D41555299E2C0B095AC3FCD9315410000000000000000B3990B335299E2C0AC951A39CD93154100000000000000002C8809115299E2C019688432CD93154100000000000000006B293BEF5199E2C04913EA2BCD9315410000000000000000E99DA0CD5199E2C0949D4B25CD9315410000000000000000E9053AAC5199E2C0550DA91ECD93154100000000000000007E81078B5199E2C0EB680218CD93154100000000000000008930096A5199E2C0B9B65711CD9315410000000000000000B7323F495199E2C025FDA80ACD931541000000000000000085A7A9285199E2C09B42F603CD93154100000000000000003DAE48085199E2C0888D3FFDCC9315410000000000000000F6651CE85099E2C060E484F6CC931541000000000000000096ED24C85099E2C0984DC6EFCC9315410000000000000000CD6362A85099E2C0ABCF03E9CC93154100000000000000001BE7D4885099E2C015713DE2CC9315410000000000000000CC957C695099E2C0593873DBCC9315410000000000000000FA8D594A5099E2C0FB2BA5D4CC93154100000000000000008BED6B2B5099E2C08552D3CDCC931541000000000000000031D2B30C5099E2C082B2FDC6CC93154100000000000000006C5931EE4F99E2C0835224C0CC931541000000000000000087A0E4CF4F99E2C01B3947B9CC93154100000000000000009CC4CDB14F99E2C0E26C66B2CC93154100000000000000008DE2EC934F99E2C072F481ABCC93154100000000000000000D1742764F99E2C06AD699A4CC9315410000000000000000977ECD584F99E2C06B19AE9DCC931541000000000000000076358F3B4F99E2C01BC4BE96CC9315410000000000000000BC57871E4F99E2C023DDCB8FCC93154100000000000000004A01B6014F99E2C02E6BD588CC9315410000000000000000CD4D1BE54E99E2C0ED74DB81CC9315410000000000000000BC58B7C84E99E2C01101DE7ACC9315410000000000000000AC0F741F3D99E2C07C2D621CC89315410000000000000000	1	\N	1	\N	0	{1}
271	01020000A0187A00004300000040719C0B399AE2C0240729E0B2931541000000000000000068287A8DA09BE2C0BF98900AA29315410000000000000000D6921170A29BE2C0A25A57F4A193154100000000000000003672CF4FA49BE2C0C1702CDDA193154100000000000000009385952CA69BE2C0205111C5A19315410000000000000000E2BB4506A89BE2C0E98007ACA19315410000000000000000EA35C2DCA99BE2C054941092A193154100000000000000002248EDAFAB9BE2C08E2E2E77A19315410000000000000000927CA97FAD9BE2C09B01625BA19315410000000000000000B094D94BAF9BE2C040CEAD3EA19315410000000000000000358B6014B19BE2C0E2631321A19315410000000000000000F29521D9B29BE2C06AA09402A19315410000000000000000A627009AB49BE2C02A7033E3A09315410000000000000000C2F1DF56B69BE2C0B9CDF1C2A093154100000000000000003AE6A40FB89BE2C0D6C1D1A1A09315410000000000000000443933C4B99BE2C04863D57FA093154100000000000000001F636F74BB9BE2C0B8D6FE5CA09315410000000000000000C9213E20BD9BE2C0954E5039A09315410000000000000000BA7A84C7BE9BE2C0EA0ACC14A0931541000000000000000099BC276AC09BE2C03D5974EF9F9315410000000000000000E8800D08C29BE2C06B944BC99F9315410000000000000000B0AD1BA1C39BE2C07E2454A29F931541000000000000000028773835C59BE2C08B7E907A9F93154100000000000000004F614AC4C69BE2C0842403529F93154100000000000000009141384EC89BE2C017A5AE289F93154100000000000000005340E9D2C99BE2C0809B95FE9E93154100000000000000008EDA4452CB9BE2C05FAFBAD39E931541000000000000000053E332CCCC9BE2C08E9420A89E931541000000000000000054859B40CE9BE2C0F70ACA7B9E9315410000000000000000664467AFCF9BE2C065DEB94E9E9315410000000000000000FCFE7E18D19BE2C058E6F2209E931541000000000000000099EFCB7BD29BE2C0D60578F29D931541000000000000000046AE37D9D39BE2C0412B4CC39D9315410000000000000000F331AC30D59BE2C0205072939D9315410000000000000000E3D11382D69BE2C0F478ED629D9315410000000000000000054759CDD79BE2C009B5C0319D93154100000000000000004EAD6712D99BE2C03F1EEFFF9C931541000000000000000009852A51DA9BE2C0DCD87BCD9C93154100000000000000001FB48D89DB9BE2C059136A9A9C931541000000000000000062877DBBDC9BE2C02C06BD669C9315410000000000000000C6B3E6E6DD9BE2C097F377329C93154100000000000000009B57B60BDF9BE2C073279EFD9B9315410000000000000000BBFBD929E09BE2C0F9F632C89B9315410000000000000000B8943F41E19BE2C08CC039929B9315410000000000000000FB83D551E29BE2C087EBB55B9B9315410000000000000000E6988A5BE39BE2C0FFE7AA249B9315410000000000000000E3114E5EE49BE2C0942E1CED9A9315410000000000000000779D0F5AE59BE2C02F400DB59A9315410000000000000000495BBF4EE69BE2C0D4A5817C9A93154100000000000000001FDD4D3CE79BE2C05FF07C439A9315410000000000000000DD27AC22E89BE2C053B8020A9A931541000000000000000070B4CB01E99BE2C09A9D16D0999315410000000000000000BF709ED9E99BE2C04C47BC959993154100000000000000008AC016AAEA9BE2C07763F75A999315410000000000000000467E2773EB9BE2C0E0A6CB1F999315410000000000000000F2FBC334EC9BE2C0C6CC3CE4989315410000000000000000E603E0EEEC9BE2C0AC964EA898931541000000000000000093D96FA1ED9BE2C017CC046C989315410000000000000000463A684CEE9BE2C0513A632F989315410000000000000000DA5DBEEFEE9BE2C030B46DF297931541000000000000000067F7678BEF9BE2C0D21128B5979315410000000000000000E9355B1FF09BE2C064309677979315410000000000000000DEC48EABF09BE2C0E3F1BB39979315410000000000000000DCCCF92FF19BE2C0DA3C9DFB96931541000000000000000020F493ACF19BE2C028FC3DBD969315410000000000000000185F5521F29BE2C0BB1EA27E969315410000000000000000EC432155F19BE2C038D6F62A939315410000000000000000	1	\N	1	\N	0	{1}
272	01020000A0187A000002000000548CA8CB029CE2C06BDBD146A39315410000000000000000FC31AC30D59BE2C0205072939D9315410000000000000000	1	\N	1	\N	0	{1}
273	01020000A0187A0000030000004487C011B17CE2C0DED5AB4886AA15410000000000000000F8B13C5AB27CE2C0164399F485AA154100000000000000008CF809881F7DE2C0FA0EC96467AA15410000000000000000	1	\N	1	\N	0	{1}
274	01020000A0187A00000200000058ECBCD6539CE2C04F073411899315410000000000000000A46717D6629CE2C0544FC2148E9315410000000000000000	1	\N	1	\N	0	{1}
275	01020000A0187A0000080000005C5E3CA4A887E2C0899A8688D69515410000000000000000142ACFFC8589E2C0BD04D463BC9515410000000000000000903D3A7A888AE2C0DD66591EAC9515410000000000000000F4BB6E08728BE2C0AE47638D9995154100000000000000002CEDBC29398CE2C04DF7D298879515410000000000000000406F365E288DE2C0B21B8E3273951541000000000000000028D20996808EE2C03FA2D17252951541000000000000000078048D30A590E2C06E24E20B279515410000000000000000	1	\N	1	\N	0	{1}
276	01020000A0187A0000030000007C048D30A590E2C06E24E20B27951541000000000000000098713EAE8491E2C0E20AD10414951541000000000000000010FF0D969C94E2C0673E6933D89415410000000000000000	1	\N	1	\N	0	{1}
277	01020000A0187A00000600000010FF0D969C94E2C0673E6933D8941541000000000000000028C71A673795E2C03D5041E6CF94154100000000000000002865BA05B595E2C0F1852056C9941541000000000000000054B230A43196E2C02C6B2B2DC0941541000000000000000088F173B60997E2C096AE035FB29415410000000000000000C0856086B798E2C0D453EBC9989415410000000000000000	1	\N	1	\N	0	{1}
278	01020000A0187A000002000000BCF8EB3B4CA0E2C056FF83EB2593154100000000000000003C04BDAFBD9EE2C0A84695253A9315410000000000000000	1	\N	1	\N	0	{1}
279	01020000A0187A000002000000BCF8EB3B4CA0E2C056FF83EB259315410000000000000000584591FCECA0E2C0B9BA8B53209315410000000000000000	1	\N	1	\N	0	{1}
280	01020000A0187A000002000000584F5A2ACBA1E2C047561CAC89921541000000000000000044DD4FCBBDA1E2C02DEF807F749215410000000000000000	1	\N	1	\N	0	{1}
281	01020000A0187A000002000000584591FCECA0E2C0B9BA8B53209315410000000000000000B8F76D2BC7A2E2C0CF00C8F7129315410000000000000000	1	\N	1	\N	0	{1}
282	01020000A0187A00000200000044DD4FCBBDA1E2C02DEF807F749215410000000000000000F4964C808CA1E2C024060AA95E9215410000000000000000	1	\N	1	\N	0	{1}
283	01020000A0187A00000200000044F6DE3757A1E2C0B29404DB4E9215410000000000000000F4964C808CA1E2C024060AA95E9215410000000000000000	1	\N	1	\N	0	{1}
284	01020000A0187A0000020000003C719C0B399AE2C0240729E0B29315410000000000000000E822B05E2699E2C0E051128DBE9315410000000000000000	1	\N	1	\N	0	{1}
285	01020000A0187A000002000000E822B05E2699E2C0E051128DBE9315410000000000000000D438E7B23E99E2C0CBAD3080C89315410000000000000000	1	\N	1	\N	0	{1}
286	01020000A0187A000002000000984108B34F99E2C0D53796C9B0931541000000000000000040DD2EFA6C99E2C0CCD7BF8CBB9315410000000000000000	1	\N	1	\N	0	{1}
287	01020000A0187A00000D000000802449A07BA2E2C063723F28D49515410000000000000000D0FB942936A4E2C060F1F8D20D9615410000000000000000709E5BE48DA5E2C09E074D1C3C9615410000000000000000585F817F19A8E2C05D289F978D96154100000000000000003CF419D894AAE2C0E3BA59B0DC961541000000000000000048E0F2A2FAABE2C0BC714A3508971541000000000000000070063DDB29AEE2C0319AB58E49971541000000000000000068881D04F8AEE2C07A9B1479609715410000000000000000805943E7C7B0E2C0D7B122F9999715410000000000000000849A356C0DB3E2C0FEBC59CAD897154100000000000000002C407FC5E1B3E2C05375A10BF09715410000000000000000D86B4AADA4B4E2C0F1FC7C60049815410000000000000000644497322BB4E2C047C37768189815410000000000000000	1	\N	1	\N	0	{1}
288	01020000A0187A00000A000000A84FABB4A1B3E2C09B12F53F299815410000000000000000B8D9860235B3E2C06F6EAC3D3A9815410000000000000000047236789CB1E2C0C19316DB1598154100000000000000008830A787BAAFE2C038290B0CEC9715410000000000000000C8C6248A4BAEE2C06A41CE26CE971541000000000000000004FE91F6F9ACE2C0E8DF97ADB5971541000000000000000098646115D3ABE2C073022757A29715410000000000000000C8B6751152AAE2C086776718A19715410000000000000000E838F82384A8E2C086776718A1971541000000000000000054107AB16EA6E2C086776718A19715410000000000000000	1	\N	1	\N	0	{1}
289	01020000A0187A00000900000054107AB16EA6E2C086776718A1971541000000000000000054107AB16EA6E2C0B7B9FE0DB69715410000000000000000B4338CEC60A6E2C0BD8CE9A9CC9715410000000000000000D4BDF6AF3EA6E2C0C8424F55ED971541000000000000000014C74049FFA5E2C0E49127842898154100000000000000004C2D8B1DA6A5E2C0EA619DA7729815410000000000000000C4FAD54F30A5E2C05A5EAEE4CE981541000000000000000000A66924CEA4E2C0708EBFD01C99154100000000000000003C841A7386A4E2C0141FCB0D569915410000000000000000	1	\N	1	\N	0	{1}
290	01020000A0187A0000060000003C841A7386A4E2C0141FCB0D569915410000000000000000988146B368A4E2C02D212CCE6D9915410000000000000000F4BDB5B6FCA3E2C0A11D3D0BCA99154100000000000000006891938D52A3E2C036A596D2509A154100000000000000003C3088C8D3A2E2C09137DED3C69A15410000000000000000381B620BB8A2E2C023EE653EDE9A15410000000000000000	1	\N	1	\N	0	{1}
291	01020000A0187A000002000000C45D3D027248E2C01C2C448AB4A21541000000000000000040C30E01A948E2C0A40FCC9E9CA215410000000000000000	1	\N	1	\N	0	{1}
292	01020000A0187A0000020000001068C58D2BB4E2C047C37768189815410000000000000000A84FABB4A1B3E2C09B12F53F299815410000000000000000	1	\N	1	\N	0	{1}
293	01020000A0187A000002000000A8243233E0B3E2C0154F519D2198154100000000000000007055766AFCB3E2C02DD53924259815410000000000000000	1	\N	1	\N	0	{1}
294	01020000A0187A0000020000009C6637518DA5E2C0B34F44128698154100000000000000009C4E95D57BA2E2C0E2EB8265769815410000000000000000	1	\N	1	\N	0	{1}
295	01020000A0187A0000020000009C4E95D57BA2E2C0E2EB82657698154100000000000000009C4E95D57BA2E2C0E66580825F9815410000000000000000	1	\N	1	\N	0	{1}
296	01020000A0187A00000200000008F456534BA5E2C0F50CF0BDB998154100000000000000002863E71BECA6E2C0652E230FC29815410000000000000000	1	\N	1	\N	0	{1}
297	01020000A0187A0000020000002863E71BECA6E2C0652E230FC298154100000000000000008030B6B500A7E2C08EC889F1B59815410000000000000000	1	\N	1	\N	0	{1}
298	01020000A0187A000002000000A86D7606CAA4E2C0645A351A2099154100000000000000003430E1073CA4E2C0B942CD521D9915410000000000000000	1	\N	1	\N	0	{1}
299	01020000A0187A0000020000003430E1073CA4E2C0B942CD521D99154100000000000000000C6AC8E0EA9FE2C0334EAE1EF99815410000000000000000	1	\N	1	\N	0	{1}
300	01020000A0187A0000020000000C6AC8E0EA9FE2C0334EAE1EF99815410000000000000000D071A1750CA0E2C0DDB6060AE49815410000000000000000	1	\N	1	\N	0	{1}
301	01020000A0187A000002000000300092B920A4E2C00FA5CB48AB99154100000000000000002CEFB332EBA0E2C07A2F29339F9915410000000000000000	1	\N	1	\N	0	{1}
302	01020000A0187A0000020000002CEFB332EBA0E2C07A2F29339F991541000000000000000020CE57D5F1A0E2C06FA7C5EC949915410000000000000000	1	\N	1	\N	0	{1}
303	01020000A0187A000002000000E0E05E0A4EA3E2C08CBAEC05559A15410000000000000000F0D66D03DDA2E2C0FB803C20539A15410000000000000000	1	\N	1	\N	0	{1}
304	01020000A0187A000002000000F0D66D03DDA2E2C0FB803C20539A15410000000000000000E0B32E1C4B9EE2C0E6A1B3BA1D9A15410000000000000000	1	\N	1	\N	0	{1}
305	01020000A0187A000002000000E0B32E1C4B9EE2C0E6A1B3BA1D9A1541000000000000000034CAEB9B6D9EE2C02D080D28119A15410000000000000000	1	\N	1	\N	0	{1}
306	01020000A0187A000002000000381B620BB8A2E2C023EE653EDE9A15410000000000000000001FA80C7B9FE2C04B9A47C7CD9A15410000000000000000	1	\N	1	\N	0	{1}
307	01020000A0187A000002000000001FA80C7B9FE2C04B9A47C7CD9A154100000000000000009C12F8AF829FE2C016FA19E5C29A15410000000000000000	1	\N	1	\N	0	{1}
308	01020000A0187A0000020000002CAEF119C17EE2C0ACCDFF2BFFAA15410000000000000000ECE4DC8EBA82E2C0F1EDC84D24AB15410000000000000000	1	\N	1	\N	0	{1}
309	01020000A0187A000002000000ECE4DC8EBA82E2C0F1EDC84D24AB15410000000000000000BCEEFAAD9F82E2C0C5E204172FAB15410000000000000000	1	\N	1	\N	0	{1}
310	01020000A0187A000002000000287C02E00275E2C0DC1629666DA615410000000000000000D449B63ADD77E2C0C2A6CEA385A615410000000000000000	1	\N	1	\N	0	{1}
311	01020000A0187A000002000000D449B63ADD77E2C0C2A6CEA385A61541000000000000000018E059B0207AE2C0E3C1FE888EA615410000000000000000	1	\N	1	\N	0	{1}
312	01020000A0187A000002000000FC357FA24D76E2C026F960B271AC154100000000000000004849186E4A76E2C03F50D9A573AC15410000000000000000	1	\N	1	\N	0	{1}
313	01020000A0187A0000020000004849186E4A76E2C03F50D9A573AC15410000000000000000C4770E8F7F75E2C0D6AAD8B86EAC15410000000000000000	1	\N	1	\N	0	{1}
314	01020000A0187A000002000000C4770E8F7F75E2C0D6AAD8B86EAC154100000000000000008C3F84799374E2C0FB337CC803AD15410000000000000000	1	\N	1	\N	0	{1}
315	01020000A0187A0000020000008C3F84799374E2C0FB337CC803AD15410000000000000000345A0E74C975E2C08E4814DA0CAD15410000000000000000	1	\N	1	\N	0	{1}
316	01020000A0187A00000200000090E9D069627BE2C05F6BEF5319AD1541000000000000000090551A993F7BE2C0C891398B31AD15410000000000000000	1	\N	1	\N	0	{1}
317	01020000A0187A00000200000090551A993F7BE2C0C891398B31AD15410000000000000000345A0E74C975E2C08E4814DA0CAD15410000000000000000	1	\N	1	\N	0	{1}
318	01020000A0187A000002000000345A0E74C975E2C08E4814DA0CAD15410000000000000000C4478BB36A74E2C0BF50C076D8AD15410000000000000000	1	\N	1	\N	0	{1}
319	01020000A0187A000002000000C4478BB36A74E2C0BF50C076D8AD154100000000000000002CCC6B4DFD74E2C00FC83420DCAD15410000000000000000	1	\N	1	\N	0	{1}
320	01020000A0187A00000200000090E9D069627BE2C05F6BEF5319AD15410000000000000000BC70E742B17BE2C094C9A91D1DAD15410000000000000000	1	\N	1	\N	0	{1}
321	01020000A0187A000002000000BC70E742B17BE2C094C9A91D1DAD15410000000000000000ECCBCF79007CE2C059AC13992AAD15410000000000000000	1	\N	1	\N	0	{1}
322	01020000A0187A000002000000ECCBCF79007CE2C059AC13992AAD15410000000000000000282D5CD6697CE2C0799ACCF838AD15410000000000000000	1	\N	1	\N	0	{1}
323	01020000A0187A000002000000282D5CD6697CE2C0799ACCF838AD15410000000000000000CCC820F72D80E2C00B8849384CAD15410000000000000000	1	\N	1	\N	0	{1}
324	01020000A0187A000002000000CCC820F72D80E2C00B8849384CAD1541000000000000000070395E01D186E2C0E456410C57AD15410000000000000000	1	\N	1	\N	0	{1}
325	01020000A0187A00000200000070395E01D186E2C0E456410C57AD1541000000000000000014416C51E087E2C0FF1A7BEBB9AC15410000000000000000	1	\N	1	\N	0	{1}
326	01020000A0187A00000200000014416C51E087E2C0FF1A7BEBB9AC15410000000000000000CCFAA9B63988E2C0D318247CBBAC15410000000000000000	1	\N	1	\N	0	{1}
327	01020000A0187A000002000000C45D3D027248E2C01C2C448AB4A21541000000000000000048749F84834BE2C0CE12CFCED3A215410000000000000000	1	\N	1	\N	0	{1}
328	01020000A0187A00000200000048749F84834BE2C0CE12CFCED3A215410000000000000000246E1EEF074BE2C04FA8125A01A315410000000000000000	1	\N	1	\N	0	{1}
329	01020000A0187A000002000000246E1EEF074BE2C04FA8125A01A3154100000000000000002C836A038C4FE2C07319373521A315410000000000000000	1	\N	1	\N	0	{1}
330	01020000A0187A0000020000002C836A038C4FE2C07319373521A315410000000000000000B0058D01DB79E2C0EFC241372BA415410000000000000000	1	\N	1	\N	0	{1}
331	01020000A0187A000002000000B0058D01DB79E2C0EFC241372BA415410000000000000000287C02E00275E2C0DC1629666DA615410000000000000000	1	\N	1	\N	0	{1}
332	01020000A0187A000002000000287C02E00275E2C0DC1629666DA6154100000000000000002858E3ECD66EE2C07F1B62BCFDA815410000000000000000	1	\N	1	\N	0	{1}
333	01020000A0187A0000020000002858E3ECD66EE2C07F1B62BCFDA8154100000000000000004487C011D17AE2C0994A3F61A5A915410000000000000000	1	\N	1	\N	0	{1}
334	01020000A0187A0000020000004487C011D17AE2C0994A3F61A5A915410000000000000000D4743D518678E2C07DF0DAA548AA15410000000000000000	1	\N	1	\N	0	{1}
335	01020000A0187A000002000000D4743D518678E2C07DF0DAA548AA154100000000000000004487C011B17CE2C0DED5AB4886AA15410000000000000000	1	\N	1	\N	0	{1}
336	01020000A0187A0000020000004487C011B17CE2C0DED5AB4886AA154100000000000000007064E517627FE2C0383AE727ADAA15410000000000000000	1	\N	1	\N	0	{1}
337	01020000A0187A0000020000007064E517627FE2C0383AE727ADAA154100000000000000002CAEF119C17EE2C0ACCDFF2BFFAA15410000000000000000	1	\N	1	\N	0	{1}
338	01020000A0187A0000020000002CAEF119C17EE2C0ACCDFF2BFFAA1541000000000000000090E9D069627BE2C05F6BEF5319AD15410000000000000000	1	\N	1	\N	0	{1}
339	01020000A0187A000002000000A46717D6629CE2C0544FC2148E931541000000000000000084167CFA0D9DE2C0B9C14769869315410000000000000000	1	\N	1	\N	0	{1}
340	01020000A0187A000004000000381B620BB8A2E2C023EE653EDE9A15410000000000000000BC2FF2F9B3A2E2C0611734EBE19A15410000000000000000884AD97A8AA8E2C062DB85C2FC9A15410000000000000000385B8530CCA8E2C0D66CF655E99A15410000000000000000	1	\N	1	\N	0	{1}
341	01020000A0187A000004000000688E396843A3E2C0CC55DDEB5E9A15410000000000000000E4327FE4B0A4E2C02B1326EC649A15410000000000000000544B43F520A8E2C028770AAE6D9A15410000000000000000941B093239A8E2C004E3D8995D9A15410000000000000000	1	\N	1	\N	0	{1}
342	01020000A0187A000002000000F002F54A3188E2C04229ADCA37961541000000000000000080DD80819288E2C0103AE281359615410000000000000000	1	\N	1	\N	0	{1}
343	01020000A0187A000002000000E0398D4AEF3DE2C0E94E245D9DA215410000000000000000E0A0E3DC2139E2C01FD0D88882A415410000000000000000	1	\N	1	\N	0	{1}
344	01020000A0187A000002000000E0A646E28F3AE2C0EE8B5C17F2A315410000000000000000E405B828EC38E2C0D8436B31EFA315410000000000000000	1	\N	1	\N	0	{1}
\.


--
-- Data for Name: model_parms; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.model_parms (id, type, parm_name, model_name, mapping_expression, macro_name, mapping_direction) FROM stdin;
\.


--
-- Data for Name: network; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.network (id, description) FROM stdin;
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
-- Data for Name: sensor_source; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.sensor_source (id, sensor_id, type, template, measure, function, conn_type, conns, ids, test_value, description) FROM stdin;
\.


--
-- Data for Name: sensor_target; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.sensor_target (id, sensor_id, type, template, ids, target, test_value, description) FROM stdin;
\.


--
-- Data for Name: sensors; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.sensors (id) FROM stdin;
\.


--
-- Data for Name: source_conn_type; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.source_conn_type (id, source_id, conn_type, active) FROM stdin;
\.


--
-- Data for Name: source_conns; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.source_conns (id, source_id, connection_id, active) FROM stdin;
\.


--
-- Data for Name: source_ids; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.source_ids (id, source_id, feature_id, active) FROM stdin;
\.


--
-- Data for Name: source_template; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.source_template (id, source_id, template, active) FROM stdin;
\.


--
-- Data for Name: streets; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.streets (id, geom, length_m, costs_eur7m, source, target) FROM stdin;
\.


--
-- Data for Name: submodels; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.submodels (id, submodel, geom) FROM stdin;
\.


--
-- Data for Name: supervisory_ctrl; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.supervisory_ctrl (id, submodel) FROM stdin;
\.


--
-- Data for Name: target_ids; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.target_ids (id, target_id, feature_id, active) FROM stdin;
\.


--
-- Data for Name: target_template; Type: TABLE DATA; Schema: a; Owner: postgres
--

COPY a.target_template (id, target_id, template, active) FROM stdin;
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

SELECT pg_catalog.setval('a.energy_plants_id_seq', 2, true);


--
-- Name: feature_decoupling_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.feature_decoupling_id_seq', 1, false);


--
-- Name: invoked_sensor_source_signals_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.invoked_sensor_source_signals_id_seq', 1, false);


--
-- Name: invoked_sensor_target_signals_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.invoked_sensor_target_signals_id_seq', 1, false);


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
-- Name: lines_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.lines_id_seq', 344, true);


--
-- Name: model_parms_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.model_parms_id_seq', 1, false);


--
-- Name: network_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.network_id_seq', 1, false);


--
-- Name: pipes_model_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.pipes_model_id_seq', 1, false);


--
-- Name: sensor_source_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.sensor_source_id_seq', 1, false);


--
-- Name: sensor_target_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.sensor_target_id_seq', 1, false);


--
-- Name: sensors_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.sensors_id_seq', 1, false);


--
-- Name: source_conn_type_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.source_conn_type_id_seq', 1, false);


--
-- Name: source_conns_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.source_conns_id_seq', 1, false);


--
-- Name: source_ids_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.source_ids_id_seq', 1, false);


--
-- Name: source_template_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.source_template_id_seq', 1, false);


--
-- Name: streets_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.streets_id_seq', 1, false);


--
-- Name: submodels_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.submodels_id_seq', 1, false);


--
-- Name: supervisory_ctrl_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.supervisory_ctrl_id_seq', 1, false);


--
-- Name: target_ids_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.target_ids_id_seq', 1, false);


--
-- Name: target_template_id_seq; Type: SEQUENCE SET; Schema: a; Owner: postgres
--

SELECT pg_catalog.setval('a.target_template_id_seq', 1, false);


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
-- Name: feature_decoupling feature_decoupling_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.feature_decoupling
    ADD CONSTRAINT feature_decoupling_pkey PRIMARY KEY (id);


--
-- Name: pipes_model id_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.pipes_model
    ADD CONSTRAINT id_pkey PRIMARY KEY (id);


--
-- Name: invoked_sensor_source_signals invoked_sensor_source_signals_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.invoked_sensor_source_signals
    ADD CONSTRAINT invoked_sensor_source_signals_pkey PRIMARY KEY (id);


--
-- Name: invoked_sensor_target_signals invoked_sensor_target_signals_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.invoked_sensor_target_signals
    ADD CONSTRAINT invoked_sensor_target_signals_pkey PRIMARY KEY (id);


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
-- Name: lines lines_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.lines
    ADD CONSTRAINT lines_pkey PRIMARY KEY (id);


--
-- Name: model_parms model_parms_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.model_parms
    ADD CONSTRAINT model_parms_pkey PRIMARY KEY (id);


--
-- Name: network network_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.network
    ADD CONSTRAINT network_pkey PRIMARY KEY (id);


--
-- Name: sensor_source sensor_source_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.sensor_source
    ADD CONSTRAINT sensor_source_pkey PRIMARY KEY (id);


--
-- Name: sensor_target sensor_target_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.sensor_target
    ADD CONSTRAINT sensor_target_pkey PRIMARY KEY (id);


--
-- Name: sensors sensors_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.sensors
    ADD CONSTRAINT sensors_pkey PRIMARY KEY (id);


--
-- Name: source_conn_type source_conn_type_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_conn_type
    ADD CONSTRAINT source_conn_type_pkey PRIMARY KEY (id);


--
-- Name: source_conns source_conns_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_conns
    ADD CONSTRAINT source_conns_pkey PRIMARY KEY (id);


--
-- Name: source_ids source_ids_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_ids
    ADD CONSTRAINT source_ids_pkey PRIMARY KEY (id);


--
-- Name: source_template source_template_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_template
    ADD CONSTRAINT source_template_pkey PRIMARY KEY (id);


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
-- Name: supervisory_ctrl supervisory_ctrl_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.supervisory_ctrl
    ADD CONSTRAINT supervisory_ctrl_pkey PRIMARY KEY (id);


--
-- Name: target_ids target_ids_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.target_ids
    ADD CONSTRAINT target_ids_pkey PRIMARY KEY (id);


--
-- Name: target_template target_template_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.target_template
    ADD CONSTRAINT target_template_pkey PRIMARY KEY (id);


--
-- Name: time_manager_tair time_manager_tair_pkey; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.time_manager_tair
    ADD CONSTRAINT time_manager_tair_pkey PRIMARY KEY (id);


--
-- Name: invoked_sensor_source_signals unique_sensor_source_id; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.invoked_sensor_source_signals
    ADD CONSTRAINT unique_sensor_source_id UNIQUE (sensor_id);


--
-- Name: invoked_sensor_target_signals unique_sensor_target_id; Type: CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.invoked_sensor_target_signals
    ADD CONSTRAINT unique_sensor_target_id UNIQUE (sensor_id);


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
-- Name: feature_decoupling column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.feature_decoupling FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: invoked_sensor_source_signals column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.invoked_sensor_source_signals FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: invoked_sensor_target_signals column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.invoked_sensor_target_signals FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: junction_connections column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.junction_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: junctions column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.junctions FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: lines column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.lines FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: model_parms column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.model_parms FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


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
-- Name: sensor_source column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.sensor_source FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: sensor_target column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.sensor_target FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: sensors column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.sensors FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: source_conn_type column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.source_conn_type FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: source_conns column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.source_conns FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: source_ids column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.source_ids FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: source_template column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.source_template FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: streets column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.streets FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: submodels column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.submodels FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: supervisory_ctrl column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.supervisory_ctrl FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: target_ids column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.target_ids FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


--
-- Name: target_template column_update_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER column_update_trigger AFTER UPDATE ON a.target_template FOR EACH ROW EXECUTE FUNCTION public.my_trigger_update_function();


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
-- Name: feature_decoupling my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.feature_decoupling FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: invoked_sensor_source_signals my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.invoked_sensor_source_signals FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: invoked_sensor_target_signals my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.invoked_sensor_target_signals FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: junction_connections my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.junction_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: junctions my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.junctions FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: lines my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.lines FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: model_parms my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.model_parms FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


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
-- Name: sensor_source my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.sensor_source FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: sensor_target my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.sensor_target FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: sensors my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.sensors FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: source_conn_type my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.source_conn_type FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: source_conns my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.source_conns FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: source_ids my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.source_ids FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: source_template my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.source_template FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: streets my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.streets FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: submodels my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.submodels FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: supervisory_ctrl my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.supervisory_ctrl FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: target_ids my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.target_ids FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


--
-- Name: target_template my_delete_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_delete_trigger AFTER DELETE ON a.target_template FOR EACH ROW EXECUTE FUNCTION public.my_trigger_delete_function();


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
-- Name: feature_decoupling my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.feature_decoupling FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: invoked_sensor_source_signals my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.invoked_sensor_source_signals FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: invoked_sensor_target_signals my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.invoked_sensor_target_signals FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: junction_connections my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.junction_connections FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: junctions my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.junctions FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: lines my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.lines FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: model_parms my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.model_parms FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


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
-- Name: sensor_source my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.sensor_source FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: sensor_target my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.sensor_target FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: sensors my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.sensors FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: source_conn_type my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.source_conn_type FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: source_conns my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.source_conns FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: source_ids my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.source_ids FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: source_template my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.source_template FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: streets my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.streets FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: submodels my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.submodels FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: supervisory_ctrl my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.supervisory_ctrl FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: target_ids my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.target_ids FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


--
-- Name: target_template my_insert_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_insert_trigger AFTER INSERT ON a.target_template FOR EACH ROW EXECUTE FUNCTION public.my_trigger_insert_function();


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
-- Name: feature_decoupling my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.feature_decoupling FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: invoked_sensor_source_signals my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.invoked_sensor_source_signals FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: invoked_sensor_target_signals my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.invoked_sensor_target_signals FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: junction_connections my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.junction_connections FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: junctions my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.junctions FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: lines my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.lines FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: model_parms my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.model_parms FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


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
-- Name: sensor_source my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.sensor_source FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: sensor_target my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.sensor_target FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: sensors my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.sensors FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: source_conn_type my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.source_conn_type FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: source_conns my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.source_conns FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: source_ids my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.source_ids FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: source_template my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.source_template FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: streets my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.streets FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: submodels my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.submodels FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: supervisory_ctrl my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.supervisory_ctrl FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: target_ids my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.target_ids FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: target_template my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.target_template FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: time_manager_tair my_truncate_trigger; Type: TRIGGER; Schema: a; Owner: postgres
--

CREATE TRIGGER my_truncate_trigger AFTER TRUNCATE ON a.time_manager_tair FOR EACH STATEMENT EXECUTE FUNCTION public.my_trigger_truncate_function();


--
-- Name: sensor_source sensor_source_sensor_id_fkey; Type: FK CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.sensor_source
    ADD CONSTRAINT sensor_source_sensor_id_fkey FOREIGN KEY (sensor_id) REFERENCES a.sensors(id) ON DELETE CASCADE;


--
-- Name: sensor_target sensor_target_sensor_id_fkey; Type: FK CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.sensor_target
    ADD CONSTRAINT sensor_target_sensor_id_fkey FOREIGN KEY (sensor_id) REFERENCES a.sensors(id) ON DELETE CASCADE;


--
-- Name: source_conn_type source_conn_type_source_id_fkey; Type: FK CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_conn_type
    ADD CONSTRAINT source_conn_type_source_id_fkey FOREIGN KEY (source_id) REFERENCES a.sensors(id) ON DELETE CASCADE;


--
-- Name: source_conns source_conns_source_id_fkey; Type: FK CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_conns
    ADD CONSTRAINT source_conns_source_id_fkey FOREIGN KEY (source_id) REFERENCES a.sensors(id) ON DELETE CASCADE;


--
-- Name: source_ids source_ids_source_id_fkey; Type: FK CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_ids
    ADD CONSTRAINT source_ids_source_id_fkey FOREIGN KEY (source_id) REFERENCES a.sensors(id) ON DELETE CASCADE;


--
-- Name: source_template source_template_source_id_fkey; Type: FK CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.source_template
    ADD CONSTRAINT source_template_source_id_fkey FOREIGN KEY (source_id) REFERENCES a.sensors(id) ON DELETE CASCADE;


--
-- Name: target_ids target_ids_target_id_fkey; Type: FK CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.target_ids
    ADD CONSTRAINT target_ids_target_id_fkey FOREIGN KEY (target_id) REFERENCES a.sensors(id) ON DELETE CASCADE;


--
-- Name: target_template target_template_target_id_fkey; Type: FK CONSTRAINT; Schema: a; Owner: postgres
--

ALTER TABLE ONLY a.target_template
    ADD CONSTRAINT target_template_target_id_fkey FOREIGN KEY (target_id) REFERENCES a.sensors(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict OkOYMcyewFknCYjiNHBlzyOSjsZEgAWqpvijZt51AIefjMOrPg3mhOK5oIQLJtQ

