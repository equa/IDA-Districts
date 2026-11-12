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
7	3	1	29	-0.02295	1	2
8	3	2	29	0.02295	1	2
9	4	1	30	-0.02635	1	2
10	4	2	30	0.02635	1	2
11	5	1	31	-0.0307	1	2
12	5	2	31	0.0307	1	2
13	6	1	32	-0.03365	1	2
14	6	2	32	0.03365	1	2
15	7	1	33	-0.04015	1	2
16	7	2	33	0.04015	1	2
17	8	1	34	-0.04805	1	2
18	8	2	34	0.04805	1	2
19	9	1	35	-0.05695	1	2
20	9	2	35	0.05695	1	2
21	10	1	36	-0.06965	1	2
22	10	2	36	0.06965	1	2
23	11	1	37	-0.08485	1	2
24	11	2	37	0.08485	1	2
25	12	1	38	-0.10415	1	2
26	12	2	38	0.10415	1	2
27	13	1	39	-0.13205	1	2
28	13	2	39	0.13205	1	2
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

COPY public.materials (id, name, thermal_conductivity_w7mkelvin, specific_heat_j7kgkelvin, density_kg7m3, youngs_modulus_n7mm2, thermal_expansion_17kelvin, yield_strength_n7mm2, poissons_ratio) FROM stdin;
1	P235TR1	55.2	460	7850	211800	0.0000113	235	0.3
2	Polyurethan foam	0.027	130	60	\N	\N	\N	\N
3	PEHD	0.4	1900	950	1000	0.00018	23	\N
4	PEX	0.38	550	938	\N	\N	\N	\N
5	Ground	1.18	1344	1387	\N	\N	\N	\N
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
3	\N	\N	twin pipe Isoplus DRD-20: pipes: 29,29; 1 m depth
4	\N	\N	twin pipe Isoplus DRD-25: pipes: 30,30; 1 m depth
5	\N	\N	twin pipe Isoplus DRD-32: pipes: 31,31; 1 m depth
6	\N	\N	twin pipe Isoplus DRD-40: pipes: 32,32; 1 m depth
7	\N	\N	twin pipe Isoplus DRD-50: pipes: 33,33; 1 m depth
8	\N	\N	twin pipe Isoplus DRD-65: pipes: 34,34; 1 m depth
9	\N	\N	twin pipe Isoplus DRD-80: pipes: 35,35; 1 m depth
10	\N	\N	twin pipe Isoplus DRD-100: pipes: 36,36; 1 m depth
11	\N	\N	twin pipe Isoplus DRD-125: pipes: 37,37; 1 m depth
12	\N	\N	twin pipe Isoplus DRD-150: pipes: 38,38; 1 m depth
13	\N	\N	twin pipe Isoplus DRD-200: pipes: 39,39; 1 m depth
\.


--
-- Data for Name: pipe_constructions; Type: TABLE DATA; Schema: public;
--

COPY public.pipe_constructions (id, name) FROM stdin;
1	DRE-20 Standard: 26.9 x 2.6 mm P235TR1, 28.55 mm Polyurethan foam, 90 x 3 mm PEHD
2	DRE-25 Standard: 33.7 x 3.2 mm P235TR1, 25.15 mm Polyurethan foam, 90 x 3 mm PEHD
3	DRE-32 Standard: 42.4 x 3.2 mm P235TR1, 30.8 mm Polyurethan foam, 110 x 3 mm PEHD
4	DRE-40 Standard: 48.3 x 3.2 mm P235TR1, 27.85 mm Polyurethan foam, 110 x 3 mm PEHD
5	DRE-50 Standard: 60.3 x 3.2 mm P235TR1, 29.35 mm Polyurethan foam, 125 x 3 mm PEHD
6	DRE-65 Standard: 76.1 x 3.2 mm P235TR1, 28.95 mm Polyurethan foam, 140 x 3 mm PEHD
7	DRE-80 Standard: 88.9 x 3.2 mm P235TR1, 32.55 mm Polyurethan foam, 160 x 3 mm PEHD
8	DRE-100 Standard: 114.3 x 3.6 mm P235TR1, 39.65 mm Polyurethan foam, 200 x 3.2 mm PEHD
9	DRE-125 Standard: 139.7 x 3.6 mm P235TR1, 39.25 mm Polyurethan foam, 225 x 3.4 mm PEHD
10	DRE-150 Standard: 168.3 x 4 mm P235TR1, 37.25 mm Polyurethan foam, 250 x 3.6 mm PEHD
11	DRE-175 Standard: 193.7 x 4.5 mm P235TR1, 39.25 mm Polyurethan foam, 280 x 3.9 mm PEHD
12	DRE-200 Standard: 219.1 x 4.5 mm P235TR1, 43.85 mm Polyurethan foam, 315 x 4.1 mm PEHD
13	DRE-225 Standard: 244.5 x 5 mm P235TR1, 50.75 mm Polyurethan foam, 355 x 4.5 mm PEHD
14	DRE-250 Standard: 273 x 5 mm P235TR1, 58.7 mm Polyurethan foam, 400 x 4.8 mm PEHD
15	DRE-300 Standard: 323.9 x 5.6 mm P235TR1, 57.85 mm Polyurethan foam, 450 x 5.2 mm PEHD
16	DRE-350 Standard: 355.6 x 5.6 mm P235TR1, 66.6 mm Polyurethan foam, 500 x 5.6 mm PEHD
17	DRE-400 Standard: 406.4 x 6.3 mm P235TR1, 70.8 mm Polyurethan foam, 560 x 6 mm PEHD
18	DRE-450 Standard: 457 x 6.3 mm P235TR1, 79.9 mm Polyurethan foam, 630 x 6.6 mm PEHD
19	DRE-500 Standard: 508 x 6.3 mm P235TR1, 94.1 mm Polyurethan foam, 710 x 6.9 mm PEHD
20	DRE-550 Standard: 558.8 x 6.3 mm P235TR1, 68.4 mm Polyurethan foam, 710 x 7.2 mm PEHD
21	DRE-600 Standard: 610 x 7.1 mm P235TR1, 87.1 mm Polyurethan foam, 800 x 7.9 mm PEHD
22	DRE-650 Standard: 660 x 7.1 mm P235TR1, 111.3 mm Polyurethan foam, 900 x 8.7 mm PEHD
23	DRE-700 Standard: 711 x 8 mm P235TR1, 85.8 mm Polyurethan foam, 900 x 8.7 mm PEHD
24	DRE-750 Standard: 762 x 8 mm P235TR1, 109.6 mm Polyurethan foam, 1000 x 9.4 mm PEHD
25	DRE-800 Standard: 813 x 8.8 mm P235TR1, 84.1 mm Polyurethan foam, 1000 x 9.4 mm PEHD
26	DRE-850 Standard: 864 x 8.8 mm P235TR1, 107.8 mm Polyurethan foam, 1100 x 10.2 mm PEHD
27	DRE-900 Standard: 914 x 10 mm P235TR1, 82.8 mm Polyurethan foam, 1100 x 10.2 mm PEHD
28	DRE-1000 Standard: 1016 x 11 mm P235TR1, 81 mm Polyurethan foam, 1200 x 11 mm PEHD
29	DRD-20 twin pipe carrier: 26.9 x 2.6 mm P235TR1
30	DRD-25 twin pipe carrier: 33.7 x 3.2 mm P235TR1
31	DRD-32 twin pipe carrier: 42.4 x 3.2 mm P235TR1
32	DRD-40 twin pipe carrier: 48.3 x 3.2 mm P235TR1
33	DRD-50 twin pipe carrier: 60.3 x 3.2 mm P235TR1
34	DRD-65 twin pipe carrier: 76.1 x 3.2 mm P235TR1
35	DRD-80 twin pipe carrier: 88.9 x 3.2 mm P235TR1
36	DRD-100 twin pipe carrier: 114.3 x 3.6 mm P235TR1
37	DRD-125 twin pipe carrier: 139.7 x 3.6 mm P235TR1
38	DRD-150 twin pipe carrier: 168.3 x 4 mm P235TR1
39	DRD-200 twin pipe carrier: 219.1 x 4.5 mm P235TR1
40	DRD-20 Standard twin pipe casing: Polyurethan foam (radius 59.5 mm), 125 x 3 mm PEHD
41	DRD-25 Standard twin pipe casing: Polyurethan foam (radius 67 mm), 140 x 3 mm PEHD
42	DRD-32 Standard twin pipe casing: Polyurethan foam (radius 77 mm), 160 x 3 mm PEHD
43	DRD-40 Standard twin pipe casing: Polyurethan foam (radius 77 mm), 160 x 3 mm PEHD
44	DRD-50 Standard twin pipe casing: Polyurethan foam (radius 96.8 mm), 200 x 3.2 mm PEHD
45	DRD-65 Standard twin pipe casing: Polyurethan foam (radius 109.1 mm), 225 x 3.4 mm PEHD
46	DRD-80 Standard twin pipe casing: Polyurethan foam (radius 121.4 mm), 250 x 3.6 mm PEHD
47	DRD-100 Standard twin pipe casing: Polyurethan foam (radius 153.4 mm), 315 x 4.1 mm PEHD
48	DRD-125 Standard twin pipe casing: Polyurethan foam (radius 195.2 mm), 400 x 4.8 mm PEHD
49	DRD-150 Standard twin pipe casing: Polyurethan foam (radius 219.8 mm), 450 x 5.2 mm PEHD
50	DRD-200 Standard twin pipe casing: Polyurethan foam (radius 274 mm), 560 x 6 mm PEHD
\.


--
-- Data for Name: pipe_layers; Type: TABLE DATA; Schema: public;
--

COPY public.pipe_layers (id, pipe_construction_id, materialid, thickness, sequence) FROM stdin;
1	1	1	0.0026	1
2	1	2	0.02855	2
3	1	3	0.003	3
4	2	1	0.0032	1
5	2	2	0.02515	2
6	2	3	0.003	3
7	3	1	0.0032	1
8	3	2	0.0308	2
9	3	3	0.003	3
10	4	1	0.0032	1
11	4	2	0.02785	2
12	4	3	0.003	3
13	5	1	0.0032	1
14	5	2	0.02935	2
15	5	3	0.003	3
16	6	1	0.0032	1
17	6	2	0.02895	2
18	6	3	0.003	3
19	7	1	0.0032	1
20	7	2	0.03255	2
21	7	3	0.003	3
22	8	1	0.0036	1
23	8	2	0.03965	2
24	8	3	0.0032	3
25	9	1	0.0036	1
26	9	2	0.03925	2
27	9	3	0.0034	3
28	10	1	0.004	1
29	10	2	0.03725	2
30	10	3	0.0036	3
31	11	1	0.0045	1
32	11	2	0.03925	2
33	11	3	0.0039	3
34	12	1	0.0045	1
35	12	2	0.04385	2
36	12	3	0.0041	3
37	13	1	0.005	1
38	13	2	0.05075	2
39	13	3	0.0045	3
40	14	1	0.005	1
41	14	2	0.0587	2
42	14	3	0.0048	3
43	15	1	0.0056	1
44	15	2	0.05785	2
45	15	3	0.0052	3
46	16	1	0.0056	1
47	16	2	0.0666	2
48	16	3	0.0056	3
49	17	1	0.0063	1
50	17	2	0.0708	2
51	17	3	0.006	3
52	18	1	0.0063	1
53	18	2	0.0799	2
54	18	3	0.0066	3
55	19	1	0.0063	1
56	19	2	0.0941	2
57	19	3	0.0069	3
58	20	1	0.0063	1
59	20	2	0.0684	2
60	20	3	0.0072	3
61	21	1	0.0071	1
62	21	2	0.0871	2
63	21	3	0.0079	3
64	22	1	0.0071	1
65	22	2	0.1113	2
66	22	3	0.0087	3
67	23	1	0.008	1
68	23	2	0.0858	2
69	23	3	0.0087	3
70	24	1	0.008	1
71	24	2	0.1096	2
72	24	3	0.0094	3
73	25	1	0.0088	1
74	25	2	0.0841	2
75	25	3	0.0094	3
76	26	1	0.0088	1
77	26	2	0.1078	2
78	26	3	0.0102	3
79	27	1	0.01	1
80	27	2	0.0828	2
81	27	3	0.0102	3
82	28	1	0.011	1
83	28	2	0.081	2
84	28	3	0.011	3
85	29	1	0.0026	1
86	30	1	0.0032	1
87	31	1	0.0032	1
88	32	1	0.0032	1
89	33	1	0.0032	1
90	34	1	0.0032	1
91	35	1	0.0032	1
92	36	1	0.0036	1
93	37	1	0.0036	1
94	38	1	0.004	1
95	39	1	0.0045	1
96	40	2	0.0595	1
97	40	3	0.003	2
98	41	2	0.067	1
99	41	3	0.003	2
100	42	2	0.077	1
101	42	3	0.003	2
102	43	2	0.077	1
103	43	3	0.003	2
104	44	2	0.0968	1
105	44	3	0.0032	2
106	45	2	0.1091	1
107	45	3	0.0034	2
108	46	2	0.1214	1
109	46	3	0.0036	2
110	47	2	0.1534	1
111	47	3	0.0041	2
112	48	2	0.1952	1
113	48	3	0.0048	2
114	49	2	0.2198	1
115	49	3	0.0052	2
116	50	2	0.274	1
117	50	3	0.006	2
\.


--
-- Data for Name: pipes; Type: TABLE DATA; Schema: public;
--

COPY public.pipes (id, name, innerpipediameter, piperoughnessfactor, pipe_construction_id, costs, description, series, casing_construction_id) FROM stdin;
1	Isoplus DRE-20	0.0217	0.00002	1	\N	DN20; Da Casing Pipe 90 mm Standard	Isoplus DRE Standard	\N
2	Isoplus DRE-25	0.0273	0.00002	2	\N	DN25; Da Casing Pipe 90 mm Standard	Isoplus DRE Standard	\N
3	Isoplus DRE-32	0.036	0.00002	3	\N	DN32; Da Casing Pipe 110 mm Standard	Isoplus DRE Standard	\N
4	Isoplus DRE-40	0.0419	0.00002	4	\N	DN40; Da Casing Pipe 110 mm Standard	Isoplus DRE Standard	\N
5	Isoplus DRE-50	0.0539	0.00002	5	\N	DN50; Da Casing Pipe 125 mm Standard	Isoplus DRE Standard	\N
6	Isoplus DRE-65	0.0697	0.00002	6	\N	DN65; Da Casing Pipe 140 mm Standard	Isoplus DRE Standard	\N
7	Isoplus DRE-80	0.0825	0.00002	7	\N	DN80; Da Casing Pipe 160 mm Standard	Isoplus DRE Standard	\N
8	Isoplus DRE-100	0.1071	0.00002	8	\N	DN100; Da Casing Pipe 200 mm Standard	Isoplus DRE Standard	\N
9	Isoplus DRE-125	0.1325	0.00002	9	\N	DN125; Da Casing Pipe 225 mm Standard	Isoplus DRE Standard	\N
10	Isoplus DRE-150	0.1603	0.00002	10	\N	DN150; Da Casing Pipe 250 mm Standard	Isoplus DRE Standard	\N
11	Isoplus DRE-175	0.1847	0.00002	11	\N	DN175; Da Casing Pipe 280 mm Standard	Isoplus DRE Standard	\N
12	Isoplus DRE-200	0.2101	0.00002	12	\N	DN200; Da Casing Pipe 315 mm Standard	Isoplus DRE Standard	\N
13	Isoplus DRE-225	0.2345	0.00002	13	\N	DN225; Da Casing Pipe 355 mm Standard	Isoplus DRE Standard	\N
14	Isoplus DRE-250	0.263	0.00002	14	\N	DN250; Da Casing Pipe 400 mm Standard	Isoplus DRE Standard	\N
15	Isoplus DRE-300	0.3127	0.00002	15	\N	DN300; Da Casing Pipe 450 mm Standard	Isoplus DRE Standard	\N
16	Isoplus DRE-350	0.3444	0.00002	16	\N	DN350; Da Casing Pipe 500 mm Standard	Isoplus DRE Standard	\N
17	Isoplus DRE-400	0.3938	0.00002	17	\N	DN400; Da Casing Pipe 560 mm Standard	Isoplus DRE Standard	\N
18	Isoplus DRE-450	0.4444	0.00002	18	\N	DN450; Da Casing Pipe 630 mm Standard	Isoplus DRE Standard	\N
19	Isoplus DRE-500	0.4954	0.00002	19	\N	DN500; Da Casing Pipe 710 mm Standard	Isoplus DRE Standard	\N
20	Isoplus DRE-550	0.5462	0.00002	20	\N	DN550; Da Casing Pipe 710 mm Standard	Isoplus DRE Standard	\N
21	Isoplus DRE-600	0.5958	0.00002	21	\N	DN600; Da Casing Pipe 800 mm Standard	Isoplus DRE Standard	\N
22	Isoplus DRE-650	0.6458	0.00002	22	\N	DN650; Da Casing Pipe 900 mm Standard	Isoplus DRE Standard	\N
23	Isoplus DRE-700	0.695	0.00002	23	\N	DN700; Da Casing Pipe 900 mm Standard	Isoplus DRE Standard	\N
24	Isoplus DRE-750	0.746	0.00002	24	\N	DN750; Da Casing Pipe 1000 mm Standard	Isoplus DRE Standard	\N
25	Isoplus DRE-800	0.7954	0.00002	25	\N	DN800; Da Casing Pipe 1000 mm Standard	Isoplus DRE Standard	\N
26	Isoplus DRE-850	0.8464	0.00002	26	\N	DN850; Da Casing Pipe 1100 mm Standard	Isoplus DRE Standard	\N
27	Isoplus DRE-900	0.894	0.00002	27	\N	DN900; Da Casing Pipe 1100 mm Standard	Isoplus DRE Standard	\N
28	Isoplus DRE-1000	0.994	0.00002	28	\N	DN1000; Da Casing Pipe 1200 mm Standard	Isoplus DRE Standard	\N
29	Isoplus DRD-20	0.0217	0.00002	29	\N	DN20; twin pipe, Da Casing Pipe 125 mm Standard, clear pipe distance 19 mm	Isoplus DRD Standard	40
30	Isoplus DRD-25	0.0273	0.00002	30	\N	DN25; twin pipe, Da Casing Pipe 140 mm Standard, clear pipe distance 19 mm	Isoplus DRD Standard	41
31	Isoplus DRD-32	0.036	0.00002	31	\N	DN32; twin pipe, Da Casing Pipe 160 mm Standard, clear pipe distance 19 mm	Isoplus DRD Standard	42
32	Isoplus DRD-40	0.0419	0.00002	32	\N	DN40; twin pipe, Da Casing Pipe 160 mm Standard, clear pipe distance 19 mm	Isoplus DRD Standard	43
33	Isoplus DRD-50	0.0539	0.00002	33	\N	DN50; twin pipe, Da Casing Pipe 200 mm Standard, clear pipe distance 20 mm	Isoplus DRD Standard	44
34	Isoplus DRD-65	0.0697	0.00002	34	\N	DN65; twin pipe, Da Casing Pipe 225 mm Standard, clear pipe distance 20 mm	Isoplus DRD Standard	45
35	Isoplus DRD-80	0.0825	0.00002	35	\N	DN80; twin pipe, Da Casing Pipe 250 mm Standard, clear pipe distance 25 mm	Isoplus DRD Standard	46
36	Isoplus DRD-100	0.1071	0.00002	36	\N	DN100; twin pipe, Da Casing Pipe 315 mm Standard, clear pipe distance 25 mm	Isoplus DRD Standard	47
37	Isoplus DRD-125	0.1325	0.00002	37	\N	DN125; twin pipe, Da Casing Pipe 400 mm Standard, clear pipe distance 30 mm	Isoplus DRD Standard	48
38	Isoplus DRD-150	0.1603	0.00002	38	\N	DN150; twin pipe, Da Casing Pipe 450 mm Standard, clear pipe distance 40 mm	Isoplus DRD Standard	49
39	Isoplus DRD-200	0.2101	0.00002	39	\N	DN200; twin pipe, Da Casing Pipe 560 mm Standard, clear pipe distance 45 mm	Isoplus DRD Standard	50
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

SELECT pg_catalog.setval('public.bundle_pipes_id_seq', 29, false);


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

SELECT pg_catalog.setval('public.pipe_bundle_types_id_seq', 14, false);


--
-- Name: pipe_constructions_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_constructions_id_seq', 51, false);


--
-- Name: pipe_layers_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_layers_id_seq', 118, false);


--
-- Name: pipes_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipes_id_seq', 40, false);


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
-- Name: building_constructions; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.building_constructions_id_seq', 28, false);

--
-- Name: zone_templates; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.zone_templates_id_seq', 136, false);
