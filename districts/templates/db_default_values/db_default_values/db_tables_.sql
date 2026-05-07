SET client_encoding = 'UTF8';

----------data for public tables------------


--
-- Data for Name: bundle_pipes; Type: TABLE DATA; Schema: public;
--

COPY public.bundle_pipes (id, pipe_bundle_type_id, sequence, pipe_id, x, y, ambient) FROM stdin;
1	1	1	1	-0.25	1	2
2	1	2	1	0.25	1	2
3	2	1	1	-0.75	1	2
4	2	2	1	-0.25	1	2
5	2	3	1	0.25	1	2
6	2	4	1	0.75	1	2
\.


--
-- Data for Name: bundle_type_conns; Type: TABLE DATA; Schema: public;
--

COPY public.bundle_type_conns (id, conn_bundle_type_id, sequence, conn_type_id, description) FROM stdin;
1	1	1	1	1 sup temp 70; 1 ret temp 30
2	2	1	2	1 sup temp 10; 1 ret temp 18
3	3	1	3	1 sup temp 18; 1 ret temp 10
4	4	1	4	2 sup temp 70&10; 2 ret temp 30&18
5	5	1	5	2 sup temp 70&10; 1 ret temp 30
6	6	1	1	1 sup temp 70; 1 ret temp 30
7	6	2	6	1 sup temp 70; 1 ret temp 30; mdot
8	7	1	6	1 sup temp 70; 1 ret temp 30; mdot
9	8	1	7	1 sup temp 18; 1 ret temp 10; mdot
10	9	1	8	1 sup temp 10; 1 ret temp 18; mdot
11	10	1	9	2 sup temp 70&10; 1 ret temp 18; mdot
12	11	1	10	2 sup temp 70&10 mdot; 2 ret temp 30&18 mdot
13	12	1	2	1 sup temp 10; 1 ret temp 18
14	12	2	8	1 sup temp 10; 1 ret temp 18; mdot
15	13	1	4	2 sup temp 70&10; 2 ret temp 30&18
16	13	2	10	2 sup temp 70&10 mdot; 2 ret temp 30 mdot
17	14	1	5	2 sup temp 70&10; 1 ret temp 30
18	14	2	9	2 sup temp 70&10; 1 ret temp 30; mdot
19	15	1	3	1 sup temp 18; 1 ret temp 10
20	15	2	7	1 sup temp 18; 1 ret temp 10; mdot
\.


--
-- Data for Name: conn_bundle_types; Type: TABLE DATA; Schema: public;
--

COPY public.conn_bundle_types (id, description) FROM stdin;
1	1 type: type 1: 1 sup temp 70; 1 ret temp 30
2	1 type: type 2: 1 sup temp 10; 1 ret temp 18
3	1 type: type 3: 1 sup temp 18; 1 ret temp 10
4	1 type: type 4: 2 sup temp 70&10; 2 ret temp 30&18
5	1 type: type 5: 2 sup temp 70&10; 1 ret temp 30
6	2 types: type 1: 1 sup temp 70; 1 ret temp 30;; type 6: 1 sup temp 70; 1 ret temp 30; mdot
7	1 type: type 6: 1 sup temp 70; 1 ret temp 30; mdot
8	1 type: type 7: 1 sup temp 18; 1 ret temp 10; mdot
9	1 type: type 8: 1 sup temp 10; 1 ret temp 18; mdot
10	1 type: type 9: 2 sup temp 70&10; 1 ret temp 30; mdot
11	1 type: type 10: 2 sup temp 70&10 mdot; 2 ret temp 30&18 mdot
12	2 types: type 2: 1 sup temp 10; 1 ret temp 18;; type 8: 1 sup temp 10; 1 ret temp 18; mdot
13	2 types: type 4: 2 sup temp 70&10; 2 ret temp 30&18;; type 10: 2 sup temp 70&10; 2 ret temp 30&18; mdot
14	2 types: type 5: 2 sup temp 70&10; 1 ret temp 30;; type 9: 2 sup temp 70&10; 1 ret temp 30; mdot
15	2 types: type 3: 1 sup temp 18; 1 ret temp 10;; type 7: 1 sup temp 18; 1 ret temp 10; mdot
\.


--
-- Data for Name: connection_type_connections; Type: TABLE DATA; Schema: public;
--

COPY public.connection_type_connections (id, connection_type_id, sequence, connection_id) FROM stdin;
1	1	1	1
2	1	2	2
3	2	1	3
4	2	2	4
5	3	1	5
6	3	2	6
7	4	1	1
8	4	2	3
9	4	3	2
10	4	4	4
11	5	1	1
12	5	2	3
13	5	3	2
14	6	1	7
15	6	2	8
16	7	1	9
17	7	2	10
18	8	1	11
19	8	2	12
20	9	1	7
21	9	2	11
22	9	3	8
23	10	1	7
24	10	3	8
25	10	2	11
26	10	4	12
\.


--
-- Data for Name: connection_types; Type: TABLE DATA; Schema: public;
--

COPY public.connection_types (id, description) FROM stdin;
0	Unkown
1	1 sup temp 70; 1 ret temp 30
2	1 sup temp 10; 1 ret temp 18
3	1 sup temp 18; 1 ret temp 10
4	2 sup temp 70&10; 2 ret temp 30&18
5	2 sup temp 70&10; 1 ret temp 30
6	1 sup temp 70; 1 ret temp 30; mdot
7	1 sup temp 18; 1 ret temp 10; mdot
8	1 sup temp 10; 1 ret temp 18; mdot
9	2 sup temp 70&10; 1 ret temp 30; mdot
10	2 sup temp 70&10 mdot; 2 ret temp 30 mdot
\.


--
-- Data for Name: connections; Type: TABLE DATA; Schema: public;
--

COPY public.connections (id, type, p_ctrl, temp, p, mdot, description) FROM stdin;
1	1	f	70	100000	\N	Supply: 70 °C;100000Pa
2	2	f	30	0	\N	Return: 30 °C;0Pa
3	1	f	10	100000	\N	Supply: 10 °C;100000Pa
4	2	f	18	0	\N	Return: 18 °C;0Pa
5	1	f	18	100000	\N	Supply: 18 °C;100000Pa
6	2	f	10	0	\N	Return: 10 °C;0Pa
7	1	t	70	\N	-0.1	Supply: 70 °C;-0.1kg/s
8	2	t	30	\N	0.1	Return: 30 °C;0.1kg/s
9	1	t	18	\N	-0.1	Supply: 18 °C;-0.1kg/s
10	2	t	10	\N	0.1	Return: 10 °C;0.1kg/s
11	1	t	10	\N	-0.1	Supply: 10 °C;-0.1kg/s
12	2	t	18	\N	0.1	Return: 18 °C;0.1kg/s
\.


--
-- Data for Name: customer_templates; Type: TABLE DATA; Schema: public;
--

COPY public.customer_templates (id, template, template_name, conn_bundle_type, description) FROM stdin;
1	1	simplified_consumer	1	This type of customer is heated by one supply and return line.
2	2	simplified_consumer_2sup_2ret	4	This type of customer is heated and cooled by two supply and return lines.
3	3	simplified_consumer_2sup_1ret	5	This type of customer is heated and cooled by two supply and one return line.
4	4	simplified_consumer_hp	3	This type of customer is heated by one supply and return line. The temperature level is raised by means of a heat pump.
\.


--
-- Data for Name: energy_plant_templates; Type: TABLE DATA; Schema: public;
--

COPY public.energy_plant_templates (id, template, template_name, conn_bundle_type, description) FROM stdin;
1	1	ideal_heat_source	7	This type of heating plant supplies heat by one supply and return line.
2	2	ideal_cooling_source	9	This type of cooling plant supplies cold by one supply and return line.
3	3	ideal_heat_cooling_source_2sup_2ret	11	This type of energy plant supplies heat and cold by two supply and return lines.
4	4	ideal_heat_cooling_source_2sup_1ret	10	This type of energy plant supplies heat and cold by two supply and one return line.
\.


--
-- Data for Name: junction_types; Type: TABLE DATA; Schema: public;
--

COPY public.junction_types (id, type, description) FROM stdin;
0	unkown	Unkown
1	cross	Also known as a 4-way tee. A cross allows four segments of pipe to connect.
2	end_cap	An end cap is a coupling with only one socket for connecting to a pipe segment. It is used to close the otherwise open end of a pipe
3	reducer	A coupling where one socket opening has a smaller diameter than the other socket opening.
4	tee	A fitting for combining or dividing flow. It has three or four socket openings.
5	y_connector	A type of tee which allows three pipe segments to be joined. Two of the pipe sockecs are at a 45 degree angle to each other.
\.


--
-- Data for Name: line_types; Type: TABLE DATA; Schema: public;
--

COPY public.line_types (id, type, description) FROM stdin;
0	unkown	Unkown
1	service_pipe	The subtype feature layer Service Pipe describes the linear containers that transport the water or steam from the distribution pipe to the customer or customer pipe. Service Pipe is intended to be used for storing the representation of the physical pipe through all stages of its engineering life cycle (proposed, active, inactive, retired, removed, and abandoned).
2	distribution_pipe	The subtype feature layer Distribution Pipe describes the linear containers that transport the water or steam from the transmission pipe to the service pipe. Distribution Pipe is intended to be used for storing the representation of the physical pipe through all stages of its engineering life cycle (proposed, active, inactive, retired, removed, and abandoned).
3	transmission_pipe	The subtype feature layer Transmission pipe describes the linear containers that transport the water or steam from the production facility to the distribution pipe. Transmission pipe is intended to be used for storing the representation of the physical pipe through all stages of its engineering life cycle (proposed, active, inactive, retired, removed, and abandoned).
4	station_pipe	The subtype feature layer Station Pipe describes the linear containers that transport the water or steam within a station facility. Station Pipe is intended to be used for storing the representation of the physical pipe through all stages of its engineering life cycle (proposed, active, inactive, retired, removed, and abandoned).
5	customer_pipe	The subtype feature layer Customer Pipe describes the linear containers that transport the water or steam within the customer building. Customer Pipe is intended to be used for storing the representation of the physical pipe through all stages of its engineering life cycle (proposed, active, inactive, retired, removed, and abandoned).
\.


--
-- Data for Name: liquids; Type: TABLE DATA; Schema: public;
--

COPY public.liquids (id, liquid) FROM stdin;
1	Water
2	Freezium
3	Ethylene_Glycol
4	Propylene_Glycol
5	Ethanol
6	Methanol
7	Glycerol
8	Ammonia
9	Potassium_Carbonate
10	Calcium_Chloride
11	Magnesium_Chloride
12	Sodium_Chloride
13	Potassium_Acetate
\.


--
-- Data for Name: materials; Type: TABLE DATA; Schema: public;
--

COPY public.materials (id, name, thermal_conductivity_w7mkelvin, specific_heat_j7kgkelvin, density_kg7m3) FROM stdin;
1	P235TR1	55.2	460	7850
2	Polyurethan foam	0.027	130	60
3	PEHD	0.4	1900	950
4	PEX	0.38	550	938
5	Ground	1.18	1344	1387
\.


--
-- Data for Name: measure; Type: TABLE DATA; Schema: public;
--

COPY public.measure (id, measure, unit) FROM stdin;
1	temperature	°C
2	pressure	Pa
3	mass_flow	kg/s
4	power	W
5	custom	
\.


--
-- Data for Name: pipe_ambient; Type: TABLE DATA; Schema: public;
--

COPY public.pipe_ambient (id, ambient) FROM stdin;
1	ambient_air
2	ground
3	duct
\.


--
-- Data for Name: pipe_bundle_types; Type: TABLE DATA; Schema: public;
--

COPY public.pipe_bundle_types (id, invest_costs, operation_costs, description) FROM stdin;
1	\N	\N	2 pipes; 1m depth; 0.5m distance
2	\N	\N	4 pipes; 1m depth; 0.5m distance
\.


--
-- Data for Name: pipe_constructions; Type: TABLE DATA; Schema: public;
--

COPY public.pipe_constructions (id, name) FROM stdin;
1	0.01 m P235TR1 0.08 m Polyurethan foam
2	0.01 m P235TR1 0.12 m Polyurethan foam
\.


--
-- Data for Name: pipe_layers; Type: TABLE DATA; Schema: public;
--

COPY public.pipe_layers (id, pipe_construction_id, materialid, thickness, sequence) FROM stdin;
1	1	1	0.01	1
2	1	2	0.08	2
3	2	1	0.01	1
4	2	2	0.12	2
\.


--
-- Data for Name: pipes; Type: TABLE DATA; Schema: public;
--

COPY public.pipes (id, name, innerpipediameter, piperoughnessfactor, pipe_construction_id, costs, description) FROM stdin;
1	Isoplus DRE-20	0.0217	0.000045	1	\N	DN20; Da Casing Pipe 90 mm Standard
2	Isoplus DRE-25	0.0273	0.000045	1	\N	DN25; Da Casing Pipe 90 mm Standard
3	Isoplus DRE-32	0.036	0.000045	1	\N	DN32; Da Casing Pipe 110 mm Standard
4	Isoplus DRE-40	0.0419	0.000045	1	\N	DN40; Da Casing Pipe 110 mm Standard
5	Isoplus DRE-50	0.0539	0.000045	1	\N	DN50; Da Casing Pipe 125 mm Standard
6	Isoplus DRE-65	0.0697	0.000045	1	\N	DN65; Da Casing Pipe 140 mm Standard
7	Isoplus DRE-80	0.0825	0.000045	1	\N	DN80; Da Casing Pipe 160 mm Standard
8	Isoplus DRE-100	0.1071	0.000045	1	\N	DN100; Da Casing Pipe 200 mm Standard
9	Isoplus DRE-125	0.1325	0.000045	1	\N	DN125; Da Casing Pipe 225 mm Standard
10	Isoplus DRE-150	0.1603	0.000045	1	\N	DN150; Da Casing Pipe 250 mm Standard
11	Isoplus DRE-175	0.1847	0.000045	1	\N	DN175; Da Casing Pipe 280 mm Standard
12	Isoplus DRE-200	0.2101	0.000045	1	\N	DN200; Da Casing Pipe 315 mm Standard
13	Isoplus DRE-225	0.2345	0.000045	1	\N	DN225; Da Casing Pipe 355 mm Standard
14	Isoplus DRE-250	0.263	0.000045	1	\N	DN250; Da Casing Pipe 400 mm Standard
15	Isoplus DRE-300	0.3127	0.000045	1	\N	DN300; Da Casing Pipe 450 mm Standard
16	Isoplus DRE-350	0.3444	0.000045	1	\N	DN350; Da Casing Pipe 500 mm Standard
17	Isoplus DRE-400	0.3938	0.000045	1	\N	DN400; Da Casing Pipe 560 mm Standard
18	Isoplus DRE-450	0.4444	0.000045	1	\N	DN450; Da Casing Pipe 630 mm Standard
19	Isoplus DRE-500	0.4954	0.000045	1	\N	DN500; Da Casing Pipe 710 mm Standard
20	Isoplus DRE-550	0.5462	0.000045	1	\N	DN550; Da Casing Pipe 710 mm Standard
21	Isoplus DRE-600	0.5958	0.000045	1	\N	DN600; Da Casing Pipe 800 mm Standard
22	Isoplus DRE-650	0.6458	0.000045	1	\N	DN650; Da Casing Pipe 900 mm Standard
23	Isoplus DRE-700	0.695	0.000045	1	\N	DN700; Da Casing Pipe 900 mm Standard
24	Isoplus DRE-750	0.746	0.000045	1	\N	DN750; Da Casing Pipe 1000 mm Standard
25	Isoplus DRE-800	0.7954	0.000045	1	\N	DN800; Da Casing Pipe 1000 mm Standard
26	Isoplus DRE-850	0.8464	0.000045	1	\N	DN850; Da Casing Pipe 1100 mm Standard
27	Isoplus DRE-900	0.894	0.000045	1	\N	DN900; Da Casing Pipe 1100 mm Standard
28	Isoplus DRE-1000	0.994	0.000045	1	\N	DN1000; Da Casing Pipe 1200 mm Standard
\.


--
-- Data for Name: prefered_conn_dir; Type: TABLE DATA; Schema: public;
--

COPY public.prefered_conn_dir (id, name) FROM stdin;
1	supply
2	return
3	Zone_sup_hot
4	Zone_rtn_hot
5	Zone_sup_cold
6	Zone_ret_cold
7	AHU_sup_hot
8	AHU_rtn_hot
9	AHU_sup_cold
10	AHU_rtn_cold
\.


--
-- Data for Name: signal_function; Type: TABLE DATA; Schema: public;
--

COPY public.signal_function (id, function) FROM stdin;
1	min
2	max
3	average
4	add
5	same_signal
6	individual_signals
\.


--
-- Data for Name: type; Type: TABLE DATA; Schema: public;
--

COPY public.type (id, name) FROM stdin;
1	customer
2	energy_plant
3	supervisory
4	results
\.


--
-- Data for Name: versionhandling; Type: TABLE DATA; Schema: public;
--

COPY public.versionhandling (id, name, id_base, description) FROM stdin;
\.



--
-- Name: bundle_pipes_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.bundle_pipes_id_seq', 7, false);


--
-- Name: bundle_type_conns_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.bundle_type_conns_id_seq', 21, false);


--
-- Name: conn_bundle_types_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.conn_bundle_types_id_seq', 16, false);


--
-- Name: connection_type_connections_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.connection_type_connections_id_seq', 27, false);


--
-- Name: connection_types_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.connection_types_id_seq', 12, false);


--
-- Name: connections_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.connections_id_seq', 13, false);



--
-- Name: customer_templates_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.customer_templates_id_seq', 9, false);


--
-- Name: energy_plant_templates_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.energy_plant_templates_id_seq', 6, false);


--
-- Name: junction_types_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.junction_types_id_seq', 6, false);


--
-- Name: line_types_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.line_types_id_seq', 7, false);


--
-- Name: liquids_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.liquids_id_seq', 14, false);


--
-- Name: materials_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.materials_id_seq', 6, false);


--
-- Name: measure_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.measure_id_seq', 6, false);


--
-- Name: pipe_ambient_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_ambient_id_seq', 4, false);


--
-- Name: pipe_bundle_types_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_bundle_types_id_seq', 3, false);


--
-- Name: pipe_constructions_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_constructions_id_seq', 3, false);


--
-- Name: pipe_layers_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_layers_id_seq', 5, false);


--
-- Name: pipes_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipes_id_seq', 29, false);


--
-- Name: prefered_conn_dir_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.prefered_conn_dir_id_seq', 3, false);


--
-- Name: signal_function_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.signal_function_id_seq', 7, false);


--
-- Name: type_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.type_id_seq', 5, false);


--
-- Name: versionhandling_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.versionhandling_id_seq', 1, false);


--
-- Name: customer_connections_id_seq; Type: SEQUENCE SET; Schema: temp;
--

SELECT pg_catalog.setval('temp.customer_connections_id_seq', 1, false);


--
-- Name: device_connections_id_seq; Type: SEQUENCE SET; Schema: temp;
--

SELECT pg_catalog.setval('temp.device_connections_id_seq', 1, false);


--
-- Name: dhw_id_seq; Type: SEQUENCE SET; Schema: temp;
--

SELECT pg_catalog.setval('temp.dhw_id_seq', 1, false);


--
-- Name: energy_plant_connections_id_seq; Type: SEQUENCE SET; Schema: temp;
--

SELECT pg_catalog.setval('temp.energy_plant_connections_id_seq', 1, false);


--
-- Name: junction_connections_id_seq; Type: SEQUENCE SET; Schema: temp;
--

SELECT pg_catalog.setval('temp.junction_connections_id_seq', 1, false);


--
-- Name: temp_id_seq; Type: SEQUENCE SET; Schema: temp;
--

SELECT pg_catalog.setval('temp.temp_id_seq', 1, false);


--
-- Name: building_constructions; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.building_constructions_id_seq', 28, false);

--
-- Name: zone_templates; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.zone_templates_id_seq', 136, false);
