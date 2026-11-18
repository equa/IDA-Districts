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
29	14	1	43	0	1.02227	2
30	14	2	43	0	0.97773	2
31	15	1	46	0	1.018	2
32	15	2	46	0	0.982	2
33	16	1	47	0	1.019	2
34	16	2	47	0	0.981	2
35	17	1	71	0	1.01517	2
36	17	2	71	0	0.98483	2
37	18	1	72	0	1.01767	2
38	18	2	72	0	0.98233	2
39	19	1	73	0	1.0185	2
40	19	2	73	0	0.9815	2
41	20	1	74	0	1.02177	2
42	20	2	74	0	0.97823	2
43	21	1	75	0	1.02293	2
44	21	2	75	0	0.97707	2
45	22	1	76	0	1.02533	2
46	22	2	76	0	0.97467	2
47	23	1	77	0	1.02667	2
48	23	2	77	0	0.97333	2
49	24	1	78	0	1.02907	2
50	24	2	78	0	0.97093	2
51	25	1	79	0	1.03393	2
52	25	2	79	0	0.96607	2
53	26	1	80	0	1.03713	2
54	26	2	80	0	0.96287	2
55	27	1	81	0	1.0393	2
56	27	2	81	0	0.9607	2
57	28	1	82	0	1.0425	2
58	28	2	82	0	0.9575	2
59	29	1	83	0	1.0445	2
60	29	2	83	0	0.9555	2
61	30	1	89	0	1.01767	2
62	30	2	90	0	0.98233	2
63	31	1	91	0	1.02093	2
64	31	2	92	0	0.97907	2
65	32	1	93	0	1.02417	2
66	32	2	94	0	0.97583	2
67	33	1	95	0	1.02773	2
68	33	2	96	0	0.97227	2
69	34	1	97	0	1.03093	2
70	34	2	98	0	0.96907	2
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
4	PE-Xa	0.38	2300	938	600	0.00015	17	\N
5	Ground	1.18	1344	1387	\N	\N	\N	\N
6	P195GH	55.2	430	7850	211800	0.0000113	195	\N
7	Cu-DHP	305	386	8940	132000	0.0000168	65	\N
8	PE 100	0.4	2350	960	1000	0.00018	23	\N
9	PE-LLD	0.33	1900	950	\N	\N	\N	\N
10	PUR flexible foam	0.0221	130	60	\N	\N	\N	\N
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

COPY public.pipe_bundle_types (id, description) FROM stdin;
1	2 pipes; 1m depth; 0.5m distance
2	4 pipes; 1m depth; 0.5m distance
3	twin pipe Isoplus DRD-20: pipes: 29,29; 1 m depth
4	twin pipe Isoplus DRD-25: pipes: 30,30; 1 m depth
5	twin pipe Isoplus DRD-32: pipes: 31,31; 1 m depth
6	twin pipe Isoplus DRD-40: pipes: 32,32; 1 m depth
7	twin pipe Isoplus DRD-50: pipes: 33,33; 1 m depth
8	twin pipe Isoplus DRD-65: pipes: 34,34; 1 m depth
9	twin pipe Isoplus DRD-80: pipes: 35,35; 1 m depth
10	twin pipe Isoplus DRD-100: pipes: 36,36; 1 m depth
11	twin pipe Isoplus DRD-125: pipes: 37,37; 1 m depth
12	twin pipe Isoplus DRD-150: pipes: 38,38; 1 m depth
13	twin pipe Isoplus DRD-200: pipes: 39,39; 1 m depth
14	twin pipe isoplus isoflex 28+28: pipes: 43,43; 1 m depth
15	twin pipe isoplus isocu 22+22: pipes: 46,46; 1 m depth
16	twin pipe isoplus isocu 28+28: pipes: 47,47; 1 m depth
17	twin pipe isoplus isopex H-20+20: pipes: 71,71; 1 m depth
18	twin pipe isoplus isopex H-20+20 v: pipes: 72,72; 1 m depth
19	twin pipe isoplus isopex H-25+25: pipes: 73,73; 1 m depth
20	twin pipe isoplus isopex H-25+25 v: pipes: 74,74; 1 m depth
21	twin pipe isoplus isopex H-32+32: pipes: 75,75; 1 m depth
22	twin pipe isoplus isopex H-32+32 v: pipes: 76,76; 1 m depth
23	twin pipe isoplus isopex H-40+40: pipes: 77,77; 1 m depth
24	twin pipe isoplus isopex H-40+40 v: pipes: 78,78; 1 m depth
25	twin pipe isoplus isopex H-50+50: pipes: 79,79; 1 m depth
26	twin pipe isoplus isopex H-50+50 v: pipes: 80,80; 1 m depth
27	twin pipe isoplus isopex H-63+63: pipes: 81,81; 1 m depth
28	twin pipe isoplus isopex H-63+63 v: pipes: 82,82; 1 m depth
29	twin pipe isoplus isopex H-75+75: pipes: 83,83; 1 m depth
30	twin pipe isoplus isopex S-25+20: pipes: 89,90; 1 m depth
31	twin pipe isoplus isopex S-32+20: pipes: 91,92; 1 m depth
32	twin pipe isoplus isopex S-40+25: pipes: 93,94; 1 m depth
33	twin pipe isoplus isopex S-50+32: pipes: 95,96; 1 m depth
34	twin pipe isoplus isopex S-63+32: pipes: 97,98; 1 m depth
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
51	isoflex 20: 20 x 2 mm P195GH, 25.5 mm PUR flexible foam, 75 x 2 mm PE-LLD
52	isoflex 28: 28 x 2 mm P195GH, 21.5 mm PUR flexible foam, 75 x 2 mm PE-LLD
53	isoflex 28 v: 28 x 2 mm P195GH, 29 mm PUR flexible foam, 90 x 2 mm PE-LLD
54	isoflex 28+28 twin pipe casing: PUR flexible foam (radius 52.8 mm), 110 x 2.2 mm PE-LLD
55	isoflex 28+28 carrier pipe: 28 x 2 mm P195GH
56	isocu 22: 22 x 1 mm Cu-DHP, 19.5 mm PUR flexible foam, 65 x 2 mm PE-LLD
57	isocu 28: 28 x 1.2 mm Cu-DHP, 21.5 mm PUR flexible foam, 75 x 2 mm PE-LLD
58	isocu 22+22 twin pipe casing: PUR flexible foam (radius 43 mm), 90 x 2 mm PE-LLD
59	isocu 22+22 carrier pipe: 22 x 1 mm Cu-DHP
60	isocu 28+28 twin pipe casing: PUR flexible foam (radius 43 mm), 90 x 2 mm PE-LLD
61	isocu 28+28 carrier pipe: 28 x 1.2 mm Cu-DHP
62	isopex H-25: 25 x 2.3 mm PE-Xa, 23 mm PUR flexible foam, 75 x 2 mm PE-LLD
63	isopex H-25 v: 25 x 2.3 mm PE-Xa, 30.5 mm PUR flexible foam, 90 x 2 mm PE-LLD
64	isopex H-32: 32 x 2.9 mm PE-Xa, 19.5 mm PUR flexible foam, 75 x 2 mm PE-LLD
65	isopex H-32 v: 32 x 2.9 mm PE-Xa, 27 mm PUR flexible foam, 90 x 2 mm PE-LLD
66	isopex H-40: 40 x 3.7 mm PE-Xa, 23 mm PUR flexible foam, 90 x 2 mm PE-LLD
67	isopex H-40 v: 40 x 3.7 mm PE-Xa, 32.8 mm PUR flexible foam, 110 x 2.2 mm PE-LLD
68	isopex H-50: 50 x 4.6 mm PE-Xa, 27.8 mm PUR flexible foam, 110 x 2.2 mm PE-LLD
69	isopex H-50 v: 50 x 4.6 mm PE-Xa, 35 mm PUR flexible foam, 125 x 2.5 mm PE-LLD
70	isopex H-63: 63 x 5.8 mm PE-Xa, 28.5 mm PUR flexible foam, 125 x 2.5 mm PE-LLD
71	isopex H-63 v: 63 x 5.8 mm PE-Xa, 35.7 mm PUR flexible foam, 140 x 2.8 mm PE-LLD
72	isopex H-75: 75 x 6.8 mm PE-Xa, 29.7 mm PUR flexible foam, 140 x 2.8 mm PE-LLD
73	isopex H-75 v: 75 x 6.8 mm PE-Xa, 39.3 mm PUR flexible foam, 160 x 3.2 mm PE-LLD
74	isopex H-90: 90 x 8.2 mm PE-Xa, 31.8 mm PUR flexible foam, 160 x 3.2 mm PE-LLD
75	isopex H-90 v: 90 x 8.2 mm PE-Xa, 41.4 mm PUR flexible foam, 180 x 3.6 mm PE-LLD
76	isopex H-110: 110 x 10 mm PE-Xa, 31.4 mm PUR flexible foam, 180 x 3.6 mm PE-LLD
77	isopex H-110 v: 110 x 10 mm PE-Xa, 41 mm PUR flexible foam, 200 x 4 mm PE-LLD
78	isopex H-125: 125 x 11.4 mm PE-Xa, 23.9 mm PUR flexible foam, 180 x 3.6 mm PE-LLD
79	isopex H-125 v: 125 x 11.4 mm PE-Xa, 33.5 mm PUR flexible foam, 200 x 4 mm PE-LLD
80	isopex H-140: 140 x 12.7 mm PE-Xa, 26 mm PUR flexible foam, 200 x 4 mm PE-LLD
81	isopex H-110 u: 110 x 10 mm PE-Xa, 21.8 mm PUR flexible foam, 160 x 3.2 mm PE-LLD
82	isopex H-125 Stg.: 125 x 11.4 mm PE-Xa, 45.5 mm PUR flexible foam, 225 x 4.5 mm PE-LLD
83	isopex H-140 Stg.: 140 x 12.7 mm PE-Xa, 38 mm PUR flexible foam, 225 x 4.5 mm PE-LLD
84	isopex H-160 Stg.: 160 x 14.6 mm PE-Xa, 40 mm PUR flexible foam, 250 x 5 mm PE-LLD
85	isopex H-20+20 twin pipe casing: PUR flexible foam (radius 35.5 mm), 75 x 2 mm PE-LLD
86	isopex H-20+20 carrier pipe: 20 x 2 mm PE-Xa
87	isopex H-20+20 v twin pipe casing: PUR flexible foam (radius 43 mm), 90 x 2 mm PE-LLD
88	isopex H-20+20 v carrier pipe: 20 x 2 mm PE-Xa
89	isopex H-25+25 twin pipe casing: PUR flexible foam (radius 43 mm), 90 x 2 mm PE-LLD
90	isopex H-25+25 carrier pipe: 25 x 2.3 mm PE-Xa
91	isopex H-25+25 v twin pipe casing: PUR flexible foam (radius 52.8 mm), 110 x 2.2 mm PE-LLD
92	isopex H-25+25 v carrier pipe: 25 x 2.3 mm PE-Xa
93	isopex H-32+32 twin pipe casing: PUR flexible foam (radius 52.8 mm), 110 x 2.2 mm PE-LLD
94	isopex H-32+32 carrier pipe: 32 x 2.9 mm PE-Xa
95	isopex H-32+32 v twin pipe casing: PUR flexible foam (radius 60 mm), 125 x 2.5 mm PE-LLD
96	isopex H-32+32 v carrier pipe: 32 x 2.9 mm PE-Xa
97	isopex H-40+40 twin pipe casing: PUR flexible foam (radius 60 mm), 125 x 2.5 mm PE-LLD
98	isopex H-40+40 carrier pipe: 40 x 3.7 mm PE-Xa
99	isopex H-40+40 v twin pipe casing: PUR flexible foam (radius 67.2 mm), 140 x 2.8 mm PE-LLD
100	isopex H-40+40 v carrier pipe: 40 x 3.7 mm PE-Xa
101	isopex H-50+50 twin pipe casing: PUR flexible foam (radius 76.8 mm), 160 x 3.2 mm PE-LLD
102	isopex H-50+50 carrier pipe: 50 x 4.6 mm PE-Xa
103	isopex H-50+50 v twin pipe casing: PUR flexible foam (radius 86.4 mm), 180 x 3.6 mm PE-LLD
104	isopex H-50+50 v carrier pipe: 50 x 4.6 mm PE-Xa
105	isopex H-63+63 twin pipe casing: PUR flexible foam (radius 86.4 mm), 180 x 3.6 mm PE-LLD
106	isopex H-63+63 carrier pipe: 63 x 5.8 mm PE-Xa
107	isopex H-63+63 v twin pipe casing: PUR flexible foam (radius 96 mm), 200 x 4 mm PE-LLD
108	isopex H-63+63 v carrier pipe: 63 x 5.8 mm PE-Xa
109	isopex H-75+75 twin pipe casing: PUR flexible foam (radius 96 mm), 200 x 4 mm PE-LLD
110	isopex H-75+75 carrier pipe: 75 x 6.8 mm PE-Xa
111	isopex S-25: 25 x 3.5 mm PE-Xa, 23 mm PUR flexible foam, 75 x 2 mm PE-LLD
112	isopex S-32: 32 x 4.4 mm PE-Xa, 19.5 mm PUR flexible foam, 75 x 2 mm PE-LLD
113	isopex S-40: 40 x 5.5 mm PE-Xa, 23 mm PUR flexible foam, 90 x 2 mm PE-LLD
114	isopex S-50: 50 x 6.9 mm PE-Xa, 27.8 mm PUR flexible foam, 110 x 2.2 mm PE-LLD
115	isopex S-63: 63 x 8.7 mm PE-Xa, 28.5 mm PUR flexible foam, 125 x 2.5 mm PE-LLD
116	isopex S-25+20 twin pipe casing: PUR flexible foam (radius 43 mm), 90 x 2 mm PE-LLD
117	isopex S-25+20 carrier pipe: 25 x 3.5 mm PE-Xa
118	isopex S-25+20 carrier pipe: 20 x 2.8 mm PE-Xa
119	isopex S-32+20 twin pipe casing: PUR flexible foam (radius 52.8 mm), 110 x 2.2 mm PE-LLD
120	isopex S-32+20 carrier pipe: 32 x 4.4 mm PE-Xa
121	isopex S-32+20 carrier pipe: 20 x 2.8 mm PE-Xa
122	isopex S-40+25 twin pipe casing: PUR flexible foam (radius 60 mm), 125 x 2.5 mm PE-LLD
123	isopex S-40+25 carrier pipe: 40 x 5.5 mm PE-Xa
124	isopex S-40+25 carrier pipe: 25 x 3.5 mm PE-Xa
125	isopex S-50+32 twin pipe casing: PUR flexible foam (radius 67.2 mm), 140 x 2.8 mm PE-LLD
126	isopex S-50+32 carrier pipe: 50 x 6.9 mm PE-Xa
127	isopex S-50+32 carrier pipe: 32 x 4.4 mm PE-Xa
128	isopex S-63+32 twin pipe casing: PUR flexible foam (radius 76.8 mm), 160 x 3.2 mm PE-LLD
129	isopex S-63+32 carrier pipe: 63 x 8.7 mm PE-Xa
130	isopex S-63+32 carrier pipe: 32 x 4.4 mm PE-Xa
131	isoclima 20: 20 x 2 mm PE 100, 20.5 mm PUR flexible foam, 65 x 2 mm PE-LLD
132	isoclima 25: 25 x 2.3 mm PE 100, 23 mm PUR flexible foam, 75 x 2 mm PE-LLD
133	isoclima 32: 32 x 2.9 mm PE 100, 19.5 mm PUR flexible foam, 75 x 2 mm PE-LLD
134	isoclima 40: 40 x 3.7 mm PE 100, 23 mm PUR flexible foam, 90 x 2 mm PE-LLD
135	isoclima 50: 50 x 4.6 mm PE 100, 27.8 mm PUR flexible foam, 110 x 2.2 mm PE-LLD
136	isoclima 63: 63 x 5.8 mm PE 100, 28.5 mm PUR flexible foam, 125 x 2.5 mm PE-LLD
137	isoclima 75: 75 x 6.8 mm PE 100, 29.7 mm PUR flexible foam, 140 x 2.8 mm PE-LLD
138	isoclima 90: 90 x 8.2 mm PE 100, 31.8 mm PUR flexible foam, 160 x 3.2 mm PE-LLD
139	isoclima 110: 110 x 10 mm PE 100, 31.4 mm PUR flexible foam, 180 x 3.6 mm PE-LLD
140	isoclima 110 u: 110 x 10 mm PE 100, 21.8 mm PUR flexible foam, 160 x 3.2 mm PE-LLD
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
118	51	6	0.002	1
119	51	10	0.0255	2
120	51	9	0.002	3
121	52	6	0.002	1
122	52	10	0.0215	2
123	52	9	0.002	3
124	53	6	0.002	1
125	53	10	0.029	2
126	53	9	0.002	3
127	54	10	0.0528	1
128	54	9	0.0022	2
129	55	6	0.002	1
130	56	7	0.001	1
131	56	10	0.0195	2
132	56	9	0.002	3
133	57	7	0.0012	1
134	57	10	0.0215	2
135	57	9	0.002	3
136	58	10	0.043	1
137	58	9	0.002	2
138	59	7	0.001	1
139	60	10	0.043	1
140	60	9	0.002	2
141	61	7	0.0012	1
142	62	4	0.0023	1
143	62	10	0.023	2
144	62	9	0.002	3
145	63	4	0.0023	1
146	63	10	0.0305	2
147	63	9	0.002	3
148	64	4	0.0029	1
149	64	10	0.0195	2
150	64	9	0.002	3
151	65	4	0.0029	1
152	65	10	0.027	2
153	65	9	0.002	3
154	66	4	0.0037	1
155	66	10	0.023	2
156	66	9	0.002	3
157	67	4	0.0037	1
158	67	10	0.0328	2
159	67	9	0.0022	3
160	68	4	0.0046	1
161	68	10	0.0278	2
162	68	9	0.0022	3
163	69	4	0.0046	1
164	69	10	0.035	2
165	69	9	0.0025	3
166	70	4	0.0058	1
167	70	10	0.0285	2
168	70	9	0.0025	3
169	71	4	0.0058	1
170	71	10	0.0357	2
171	71	9	0.0028	3
172	72	4	0.0068	1
173	72	10	0.0297	2
174	72	9	0.0028	3
175	73	4	0.0068	1
176	73	10	0.0393	2
177	73	9	0.0032	3
178	74	4	0.0082	1
179	74	10	0.0318	2
180	74	9	0.0032	3
181	75	4	0.0082	1
182	75	10	0.0414	2
183	75	9	0.0036	3
184	76	4	0.01	1
185	76	10	0.0314	2
186	76	9	0.0036	3
187	77	4	0.01	1
188	77	10	0.041	2
189	77	9	0.004	3
190	78	4	0.0114	1
191	78	10	0.0239	2
192	78	9	0.0036	3
193	79	4	0.0114	1
194	79	10	0.0335	2
195	79	9	0.004	3
196	80	4	0.0127	1
197	80	10	0.026	2
198	80	9	0.004	3
199	81	4	0.01	1
200	81	10	0.0218	2
201	81	9	0.0032	3
202	82	4	0.0114	1
203	82	10	0.0455	2
204	82	9	0.0045	3
205	83	4	0.0127	1
206	83	10	0.038	2
207	83	9	0.0045	3
208	84	4	0.0146	1
209	84	10	0.04	2
210	84	9	0.005	3
211	85	10	0.0355	1
212	85	9	0.002	2
213	86	4	0.002	1
214	87	10	0.043	1
215	87	9	0.002	2
216	88	4	0.002	1
217	89	10	0.043	1
218	89	9	0.002	2
219	90	4	0.0023	1
220	91	10	0.0528	1
221	91	9	0.0022	2
222	92	4	0.0023	1
223	93	10	0.0528	1
224	93	9	0.0022	2
225	94	4	0.0029	1
226	95	10	0.06	1
227	95	9	0.0025	2
228	96	4	0.0029	1
229	97	10	0.06	1
230	97	9	0.0025	2
231	98	4	0.0037	1
232	99	10	0.0672	1
233	99	9	0.0028	2
234	100	4	0.0037	1
235	101	10	0.0768	1
236	101	9	0.0032	2
237	102	4	0.0046	1
238	103	10	0.0864	1
239	103	9	0.0036	2
240	104	4	0.0046	1
241	105	10	0.0864	1
242	105	9	0.0036	2
243	106	4	0.0058	1
244	107	10	0.096	1
245	107	9	0.004	2
246	108	4	0.0058	1
247	109	10	0.096	1
248	109	9	0.004	2
249	110	4	0.0068	1
250	111	4	0.0035	1
251	111	10	0.023	2
252	111	9	0.002	3
253	112	4	0.0044	1
254	112	10	0.0195	2
255	112	9	0.002	3
256	113	4	0.0055	1
257	113	10	0.023	2
258	113	9	0.002	3
259	114	4	0.0069	1
260	114	10	0.0278	2
261	114	9	0.0022	3
262	115	4	0.0087	1
263	115	10	0.0285	2
264	115	9	0.0025	3
265	116	10	0.043	1
266	116	9	0.002	2
267	117	4	0.0035	1
268	118	4	0.0028	1
269	119	10	0.0528	1
270	119	9	0.0022	2
271	120	4	0.0044	1
272	121	4	0.0028	1
273	122	10	0.06	1
274	122	9	0.0025	2
275	123	4	0.0055	1
276	124	4	0.0035	1
277	125	10	0.0672	1
278	125	9	0.0028	2
279	126	4	0.0069	1
280	127	4	0.0044	1
281	128	10	0.0768	1
282	128	9	0.0032	2
283	129	4	0.0087	1
284	130	4	0.0044	1
285	131	8	0.002	1
286	131	10	0.0205	2
287	131	9	0.002	3
288	132	8	0.0023	1
289	132	10	0.023	2
290	132	9	0.002	3
291	133	8	0.0029	1
292	133	10	0.0195	2
293	133	9	0.002	3
294	134	8	0.0037	1
295	134	10	0.023	2
296	134	9	0.002	3
297	135	8	0.0046	1
298	135	10	0.0278	2
299	135	9	0.0022	3
300	136	8	0.0058	1
301	136	10	0.0285	2
302	136	9	0.0025	3
303	137	8	0.0068	1
304	137	10	0.0297	2
305	137	9	0.0028	3
306	138	8	0.0082	1
307	138	10	0.0318	2
308	138	9	0.0032	3
309	139	8	0.01	1
310	139	10	0.0314	2
311	139	9	0.0036	3
312	140	8	0.01	1
313	140	10	0.0218	2
314	140	9	0.0032	3
\.


--
-- Data for Name: pipes; Type: TABLE DATA; Schema: public;
--

COPY public.pipes (id, name, innerpipediameter, piperoughnessfactor, pipe_construction_id, costs, description, series, casing_construction_id, maintenance_pct, lifetime_a, p_max_bar, example, min_bend_radius_m) FROM stdin;
1	Isoplus DRE-20	0.0217	0.00002	1	35.5	DN20; Da Casing Pipe 90 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
2	Isoplus DRE-25	0.0273	0.00002	2	43.5	DN25; Da Casing Pipe 90 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
3	Isoplus DRE-32	0.036	0.00002	3	55.5	DN32; Da Casing Pipe 110 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
4	Isoplus DRE-40	0.0419	0.00002	4	68.5	DN40; Da Casing Pipe 110 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
5	Isoplus DRE-50	0.0539	0.00002	5	84.5	DN50; Da Casing Pipe 125 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
6	Isoplus DRE-65	0.0697	0.00002	6	108.5	DN65; Da Casing Pipe 140 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
7	Isoplus DRE-80	0.0825	0.00002	7	132.5	DN80; Da Casing Pipe 160 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
8	Isoplus DRE-100	0.1071	0.00002	8	164	DN100; Da Casing Pipe 200 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
9	Isoplus DRE-125	0.1325	0.00002	9	203	DN125; Da Casing Pipe 225 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
10	Isoplus DRE-150	0.1603	0.00002	10	241.5	DN150; Da Casing Pipe 250 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
11	Isoplus DRE-175	0.1847	0.00002	11	280	DN175; Da Casing Pipe 280 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
12	Isoplus DRE-200	0.2101	0.00002	12	318	DN200; Da Casing Pipe 315 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
13	Isoplus DRE-225	0.2345	0.00002	13	356	DN225; Da Casing Pipe 355 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
14	Isoplus DRE-250	0.263	0.00002	14	393.5	DN250; Da Casing Pipe 400 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
15	Isoplus DRE-300	0.3127	0.00002	15	468.5	DN300; Da Casing Pipe 450 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
16	Isoplus DRE-350	0.3444	0.00002	16	543	DN350; Da Casing Pipe 500 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
17	Isoplus DRE-400	0.3938	0.00002	17	621.5	DN400; Da Casing Pipe 560 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
18	Isoplus DRE-450	0.4444	0.00002	18	697.8	DN450; Da Casing Pipe 630 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
19	Isoplus DRE-500	0.4954	0.00002	19	774	DN500; Da Casing Pipe 710 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
20	Isoplus DRE-550	0.5462	0.00002	20	850.2	DN550; Da Casing Pipe 710 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
21	Isoplus DRE-600	0.5958	0.00002	21	926.5	DN600; Da Casing Pipe 800 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
22	Isoplus DRE-650	0.6458	0.00002	22	1002.7	DN650; Da Casing Pipe 900 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
23	Isoplus DRE-700	0.695	0.00002	23	1079	DN700; Da Casing Pipe 900 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
24	Isoplus DRE-750	0.746	0.00002	24	1155.2	DN750; Da Casing Pipe 1000 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
25	Isoplus DRE-800	0.7954	0.00002	25	1231.5	DN800; Da Casing Pipe 1000 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
26	Isoplus DRE-850	0.8464	0.00002	26	1307.8	DN850; Da Casing Pipe 1100 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
27	Isoplus DRE-900	0.894	0.00002	27	1384	DN900; Da Casing Pipe 1100 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
28	Isoplus DRE-1000	0.994	0.00002	28	1536.5	DN1000; Da Casing Pipe 1200 mm Standard	Isoplus DRE Standard	\N	1	40	16	t	\N
29	Isoplus DRD-20	0.0217	0.00002	29	35.5	DN20; twin pipe, Da Casing Pipe 125 mm Standard, clear pipe distance 19 mm	Isoplus DRD Standard	40	1	40	16	t	\N
30	Isoplus DRD-25	0.0273	0.00002	30	43.5	DN25; twin pipe, Da Casing Pipe 140 mm Standard, clear pipe distance 19 mm	Isoplus DRD Standard	41	1	40	16	t	\N
31	Isoplus DRD-32	0.036	0.00002	31	55.5	DN32; twin pipe, Da Casing Pipe 160 mm Standard, clear pipe distance 19 mm	Isoplus DRD Standard	42	1	40	16	t	\N
32	Isoplus DRD-40	0.0419	0.00002	32	68.5	DN40; twin pipe, Da Casing Pipe 160 mm Standard, clear pipe distance 19 mm	Isoplus DRD Standard	43	1	40	16	t	\N
33	Isoplus DRD-50	0.0539	0.00002	33	84.5	DN50; twin pipe, Da Casing Pipe 200 mm Standard, clear pipe distance 20 mm	Isoplus DRD Standard	44	1	40	16	t	\N
34	Isoplus DRD-65	0.0697	0.00002	34	108.5	DN65; twin pipe, Da Casing Pipe 225 mm Standard, clear pipe distance 20 mm	Isoplus DRD Standard	45	1	40	16	t	\N
35	Isoplus DRD-80	0.0825	0.00002	35	132.5	DN80; twin pipe, Da Casing Pipe 250 mm Standard, clear pipe distance 25 mm	Isoplus DRD Standard	46	1	40	16	t	\N
36	Isoplus DRD-100	0.1071	0.00002	36	164	DN100; twin pipe, Da Casing Pipe 315 mm Standard, clear pipe distance 25 mm	Isoplus DRD Standard	47	1	40	16	t	\N
37	Isoplus DRD-125	0.1325	0.00002	37	203	DN125; twin pipe, Da Casing Pipe 400 mm Standard, clear pipe distance 30 mm	Isoplus DRD Standard	48	1	40	16	t	\N
38	Isoplus DRD-150	0.1603	0.00002	38	241.5	DN150; twin pipe, Da Casing Pipe 450 mm Standard, clear pipe distance 40 mm	Isoplus DRD Standard	49	1	40	16	t	\N
39	Isoplus DRD-200	0.2101	0.00002	39	318	DN200; twin pipe, Da Casing Pipe 560 mm Standard, clear pipe distance 45 mm	Isoplus DRD Standard	50	1	40	16	t	\N
40	isoplus isoflex 20	0.016	0.00001	51	\N	isoplus planning manual chapter 3 (2015/2016); Da 75 mm; casing wall assumed 2 mm	isoplus isoflex	\N	\N	\N	25	f	0.8
41	isoplus isoflex 28	0.024	0.00001	52	\N	isoplus planning manual chapter 3 (2015/2016); Da 75 mm; casing wall assumed 2 mm	isoplus isoflex	\N	\N	\N	25	f	0.8
42	isoplus isoflex 28 v	0.024	0.00001	53	\N	isoplus planning manual chapter 3 (2015/2016); Da 90 mm; casing wall assumed 2 mm	isoplus isoflex v	\N	\N	\N	25	f	0.9
43	isoplus isoflex 28+28	0.024	0.00001	55	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 110 mm; casing wall 2.2 mm and carriers one above the other with 16.53 mm clearance assumed	isoplus isoflex twin	54	\N	\N	25	f	1.1
44	isoplus isocu 22	0.02	0.0000015	56	\N	isoplus planning manual chapter 3 (2015/2016); Da 65 mm; casing wall assumed 2 mm	isoplus isocu	\N	\N	\N	25	f	0.8
45	isoplus isocu 28	0.0256	0.0000015	57	\N	isoplus planning manual chapter 3 (2015/2016); Da 75 mm; casing wall assumed 2 mm	isoplus isocu	\N	\N	\N	25	f	0.8
46	isoplus isocu 22+22	0.02	0.0000015	59	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 90 mm; casing wall 2 mm and carriers one above the other with 14 mm clearance assumed	isoplus isocu twin	58	\N	\N	25	f	0.9
47	isoplus isocu 28+28	0.0256	0.0000015	61	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 90 mm; casing wall 2 mm and carriers one above the other with 10 mm clearance assumed	isoplus isocu twin	60	\N	\N	25	f	0.9
48	isoplus isopex H-25	0.0204	0.000007	62	\N	isoplus planning manual chapter 3 (2015/2016); Da 75 mm; casing wall assumed 2 mm	isoplus isopex H	\N	\N	\N	6	f	0.7
49	isoplus isopex H-25 v	0.0204	0.000007	63	\N	isoplus planning manual chapter 3 (2015/2016); Da 90 mm; casing wall assumed 2 mm	isoplus isopex H v	\N	\N	\N	6	f	0.8
50	isoplus isopex H-32	0.0262	0.000007	64	\N	isoplus planning manual chapter 3 (2015/2016); Da 75 mm; casing wall assumed 2 mm	isoplus isopex H	\N	\N	\N	6	f	0.8
51	isoplus isopex H-32 v	0.0262	0.000007	65	\N	isoplus planning manual chapter 3 (2015/2016); Da 90 mm; casing wall assumed 2 mm	isoplus isopex H v	\N	\N	\N	6	f	0.8
52	isoplus isopex H-40	0.0326	0.000007	66	\N	isoplus planning manual chapter 3 (2015/2016); Da 90 mm; casing wall assumed 2 mm	isoplus isopex H	\N	\N	\N	6	f	0.8
53	isoplus isopex H-40 v	0.0326	0.000007	67	\N	isoplus planning manual chapter 3 (2015/2016); Da 110 mm; casing wall assumed 2.2 mm	isoplus isopex H v	\N	\N	\N	6	f	0.9
54	isoplus isopex H-50	0.0408	0.000007	68	\N	isoplus planning manual chapter 3 (2015/2016); Da 110 mm; casing wall assumed 2.2 mm	isoplus isopex H	\N	\N	\N	6	f	0.9
55	isoplus isopex H-50 v	0.0408	0.000007	69	\N	isoplus planning manual chapter 3 (2015/2016); Da 125 mm; casing wall assumed 2.5 mm	isoplus isopex H v	\N	\N	\N	6	f	1
56	isoplus isopex H-63	0.0514	0.000007	70	\N	isoplus planning manual chapter 3 (2015/2016); Da 125 mm; casing wall assumed 2.5 mm	isoplus isopex H	\N	\N	\N	6	f	1
57	isoplus isopex H-63 v	0.0514	0.000007	71	\N	isoplus planning manual chapter 3 (2015/2016); Da 140 mm; casing wall assumed 2.8 mm	isoplus isopex H v	\N	\N	\N	6	f	1.1
58	isoplus isopex H-75	0.0614	0.000007	72	\N	isoplus planning manual chapter 3 (2015/2016); Da 140 mm; casing wall assumed 2.8 mm	isoplus isopex H	\N	\N	\N	6	f	1.1
59	isoplus isopex H-75 v	0.0614	0.000007	73	\N	isoplus planning manual chapter 3 (2015/2016); Da 160 mm; casing wall assumed 3.2 mm	isoplus isopex H v	\N	\N	\N	6	f	1.2
60	isoplus isopex H-90	0.0736	0.000007	74	\N	isoplus planning manual chapter 3 (2015/2016); Da 160 mm; casing wall assumed 3.2 mm	isoplus isopex H	\N	\N	\N	6	f	1.2
61	isoplus isopex H-90 v	0.0736	0.000007	75	\N	isoplus planning manual chapter 3 (2015/2016); Da 180 mm; casing wall assumed 3.6 mm	isoplus isopex H v	\N	\N	\N	6	f	1.4
62	isoplus isopex H-110	0.09	0.000007	76	\N	isoplus planning manual chapter 3 (2015/2016); Da 180 mm; casing wall assumed 3.6 mm	isoplus isopex H	\N	\N	\N	6	f	1.4
63	isoplus isopex H-110 v	0.09	0.000007	77	\N	isoplus planning manual chapter 3 (2015/2016); Da 200 mm; casing wall assumed 4 mm	isoplus isopex H v	\N	\N	\N	6	f	1.6
64	isoplus isopex H-125	0.1022	0.000007	78	\N	isoplus planning manual chapter 3 (2015/2016); Da 180 mm; casing wall assumed 3.6 mm	isoplus isopex H	\N	\N	\N	6	f	1.4
65	isoplus isopex H-125 v	0.1022	0.000007	79	\N	isoplus planning manual chapter 3 (2015/2016); Da 200 mm; casing wall assumed 4 mm	isoplus isopex H v	\N	\N	\N	6	f	1.6
66	isoplus isopex H-140	0.1146	0.000007	80	\N	isoplus planning manual chapter 3 (2015/2016); Da 200 mm; casing wall assumed 4 mm	isoplus isopex H	\N	\N	\N	6	f	1.6
67	isoplus isopex H-110 u	0.09	0.000007	81	\N	isoplus planning manual chapter 3 (2015/2016); Da 160 mm; casing wall assumed 3.2 mm	isoplus isopex H u	\N	\N	\N	6	f	1.2
68	isoplus isopex H-125 Stg.	0.1022	0.000007	82	\N	isoplus planning manual chapter 3 (2015/2016); Da 225 mm; casing wall assumed 4.5 mm	isoplus isopex H bar	\N	\N	\N	6	f	\N
69	isoplus isopex H-140 Stg.	0.1146	0.000007	83	\N	isoplus planning manual chapter 3 (2015/2016); Da 225 mm; casing wall assumed 4.5 mm	isoplus isopex H bar	\N	\N	\N	6	f	\N
70	isoplus isopex H-160 Stg.	0.1308	0.000007	84	\N	isoplus planning manual chapter 3 (2015/2016); Da 250 mm; casing wall assumed 5 mm	isoplus isopex H bar	\N	\N	\N	6	f	\N
71	isoplus isopex H-20+20	0.016	0.000007	86	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 75 mm; casing wall 2 mm and carriers one above the other with 10.33 mm clearance assumed	isoplus isopex H twin	85	\N	\N	6	f	0.9
72	isoplus isopex H-20+20 v	0.016	0.000007	88	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 90 mm; casing wall 2 mm and carriers one above the other with 15.33 mm clearance assumed	isoplus isopex H twin v	87	\N	\N	6	f	0.9
73	isoplus isopex H-25+25	0.0204	0.000007	90	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 90 mm; casing wall 2 mm and carriers one above the other with 12 mm clearance assumed	isoplus isopex H twin	89	\N	\N	6	f	0.9
74	isoplus isopex H-25+25 v	0.0204	0.000007	92	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 110 mm; casing wall 2.2 mm and carriers one above the other with 18.53 mm clearance assumed	isoplus isopex H twin v	91	\N	\N	6	f	0.9
75	isoplus isopex H-32+32	0.0262	0.000007	94	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 110 mm; casing wall 2.2 mm and carriers one above the other with 13.87 mm clearance assumed	isoplus isopex H twin	93	\N	\N	6	f	0.9
76	isoplus isopex H-32+32 v	0.0262	0.000007	96	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 125 mm; casing wall 2.5 mm and carriers one above the other with 18.67 mm clearance assumed	isoplus isopex H twin v	95	\N	\N	6	f	1
77	isoplus isopex H-40+40	0.0326	0.000007	98	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 125 mm; casing wall 2.5 mm and carriers one above the other with 13.33 mm clearance assumed	isoplus isopex H twin	97	\N	\N	6	f	1
78	isoplus isopex H-40+40 v	0.0326	0.000007	100	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 140 mm; casing wall 2.8 mm and carriers one above the other with 18.13 mm clearance assumed	isoplus isopex H twin v	99	\N	\N	6	f	1.1
79	isoplus isopex H-50+50	0.0408	0.000007	102	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 160 mm; casing wall 3.2 mm and carriers one above the other with 17.87 mm clearance assumed	isoplus isopex H twin	101	\N	\N	6	f	1.2
80	isoplus isopex H-50+50 v	0.0408	0.000007	104	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 180 mm; casing wall 3.6 mm and carriers one above the other with 24.27 mm clearance assumed	isoplus isopex H twin v	103	\N	\N	6	f	1.4
81	isoplus isopex H-63+63	0.0514	0.000007	106	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 180 mm; casing wall 3.6 mm and carriers one above the other with 15.6 mm clearance assumed	isoplus isopex H twin	105	\N	\N	6	f	1.4
82	isoplus isopex H-63+63 v	0.0514	0.000007	108	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 200 mm; casing wall 4 mm and carriers one above the other with 22 mm clearance assumed	isoplus isopex H twin v	107	\N	\N	6	f	1.6
83	isoplus isopex H-75+75	0.0614	0.000007	110	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 200 mm; casing wall 4 mm and carriers one above the other with 14 mm clearance assumed	isoplus isopex H twin	109	\N	\N	6	f	1.4
84	isoplus isopex S-25	0.018	0.000007	111	\N	isoplus planning manual chapter 3 (2015/2016); Da 75 mm; casing wall assumed 2 mm	isoplus isopex S	\N	\N	\N	10	f	0.7
85	isoplus isopex S-32	0.0232	0.000007	112	\N	isoplus planning manual chapter 3 (2015/2016); Da 75 mm; casing wall assumed 2 mm	isoplus isopex S	\N	\N	\N	10	f	0.8
86	isoplus isopex S-40	0.029	0.000007	113	\N	isoplus planning manual chapter 3 (2015/2016); Da 90 mm; casing wall assumed 2 mm	isoplus isopex S	\N	\N	\N	10	f	0.8
87	isoplus isopex S-50	0.0362	0.000007	114	\N	isoplus planning manual chapter 3 (2015/2016); Da 110 mm; casing wall assumed 2.2 mm	isoplus isopex S	\N	\N	\N	10	f	0.9
88	isoplus isopex S-63	0.0456	0.000007	115	\N	isoplus planning manual chapter 3 (2015/2016); Da 125 mm; casing wall assumed 2.5 mm	isoplus isopex S	\N	\N	\N	10	f	1
89	isoplus isopex S-25+20 (25 mm)	0.018	0.000007	117	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 90 mm; casing wall 2 mm and carriers one above the other with 12.83 mm clearance assumed	\N	116	\N	\N	10	f	0.9
90	isoplus isopex S-25+20 (20 mm)	0.0144	0.000007	118	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 90 mm; casing wall 2 mm and carriers one above the other with 12.83 mm clearance assumed	\N	116	\N	\N	10	f	0.9
91	isoplus isopex S-32+20 (32 mm)	0.0232	0.000007	120	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 110 mm; casing wall 2.2 mm and carriers one above the other with 15.87 mm clearance assumed	\N	119	\N	\N	10	f	0.9
92	isoplus isopex S-32+20 (20 mm)	0.0144	0.000007	121	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 110 mm; casing wall 2.2 mm and carriers one above the other with 15.87 mm clearance assumed	\N	119	\N	\N	10	f	0.9
93	isoplus isopex S-40+25 (40 mm)	0.029	0.000007	123	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 125 mm; casing wall 2.5 mm and carriers one above the other with 15.83 mm clearance assumed	\N	122	\N	\N	10	f	1
94	isoplus isopex S-40+25 (25 mm)	0.018	0.000007	124	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 125 mm; casing wall 2.5 mm and carriers one above the other with 15.83 mm clearance assumed	\N	122	\N	\N	10	f	1
95	isoplus isopex S-50+32 (50 mm)	0.0362	0.000007	126	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 140 mm; casing wall 2.8 mm and carriers one above the other with 14.47 mm clearance assumed	\N	125	\N	\N	10	f	1.1
96	isoplus isopex S-50+32 (32 mm)	0.0232	0.000007	127	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 140 mm; casing wall 2.8 mm and carriers one above the other with 14.47 mm clearance assumed	\N	125	\N	\N	10	f	1.1
97	isoplus isopex S-63+32 (63 mm)	0.0456	0.000007	129	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 160 mm; casing wall 3.2 mm and carriers one above the other with 14.37 mm clearance assumed	\N	128	\N	\N	10	f	1.2
98	isoplus isopex S-63+32 (32 mm)	0.0232	0.000007	130	\N	isoplus planning manual chapter 3 (2015/2016); twin pipe, Da 160 mm; casing wall 3.2 mm and carriers one above the other with 14.37 mm clearance assumed	\N	128	\N	\N	10	f	1.2
99	isoplus isoclima 20	0.016	0.000015	131	\N	isoplus planning manual chapter 3 (2015/2016); Da 65 mm; casing wall assumed 2 mm	isoplus isoclima	\N	\N	\N	11.6	f	0.8
100	isoplus isoclima 25	0.0204	0.000015	132	\N	isoplus planning manual chapter 3 (2015/2016); Da 75 mm; casing wall assumed 2 mm	isoplus isoclima	\N	\N	\N	11.6	f	0.8
101	isoplus isoclima 32	0.0262	0.000015	133	\N	isoplus planning manual chapter 3 (2015/2016); Da 75 mm; casing wall assumed 2 mm	isoplus isoclima	\N	\N	\N	11.6	f	0.9
102	isoplus isoclima 40	0.0326	0.000015	134	\N	isoplus planning manual chapter 3 (2015/2016); Da 90 mm; casing wall assumed 2 mm	isoplus isoclima	\N	\N	\N	11.6	f	0.9
103	isoplus isoclima 50	0.0408	0.000015	135	\N	isoplus planning manual chapter 3 (2015/2016); Da 110 mm; casing wall assumed 2.2 mm	isoplus isoclima	\N	\N	\N	11.6	f	1
104	isoplus isoclima 63	0.0514	0.000015	136	\N	isoplus planning manual chapter 3 (2015/2016); Da 125 mm; casing wall assumed 2.5 mm	isoplus isoclima	\N	\N	\N	11.6	f	1.1
105	isoplus isoclima 75	0.0614	0.000015	137	\N	isoplus planning manual chapter 3 (2015/2016); Da 140 mm; casing wall assumed 2.8 mm	isoplus isoclima	\N	\N	\N	11.6	f	1.2
106	isoplus isoclima 90	0.0736	0.000015	138	\N	isoplus planning manual chapter 3 (2015/2016); Da 160 mm; casing wall assumed 3.2 mm	isoplus isoclima	\N	\N	\N	11.6	f	1.4
107	isoplus isoclima 110	0.09	0.000015	139	\N	isoplus planning manual chapter 3 (2015/2016); Da 180 mm; casing wall assumed 3.6 mm	isoplus isoclima	\N	\N	\N	11.6	f	1.4
108	isoplus isoclima 110 u	0.09	0.000015	140	\N	isoplus planning manual chapter 3 (2015/2016); Da 160 mm; casing wall assumed 3.2 mm	isoplus isoclima u	\N	\N	\N	11.6	f	1.4
\.

--
-- Data for Name: pipe_series; Type: TABLE DATA; Schema: public;
--

COPY public.pipe_series (id, name, system_type, standard, t_max_continuous_c, t_max_peak_c, t_min_c, sigma_ax_max_n7mm2, safety_factor, description) FROM stdin;
1	Isoplus DRE Standard	rigid_single	EN 253	120	140	\N	\N	\N	isoplus rigid single pipes (planning manual chapter 2); temperatures of EN 253, axial stress by EN 13941 from Re
2	Isoplus DRD Standard	rigid_twin	EN 15698-1	120	140	\N	\N	\N	isoplus rigid twin pipes (planning manual chapter 2); temperatures of EN 253, axial stress by EN 13941 from Re
3	isoplus isoflex	flexible_metal	EN 15632-4	120	140	\N	150	\N	isoplus planning manual chapter 3 (2015/2016), 3.2 isoflex: steel P195GH
4	isoplus isoflex v	flexible_metal	EN 15632-4	120	140	\N	150	\N	isoplus planning manual chapter 3 (2015/2016), 3.2 isoflex, reinforced insulation
5	isoplus isoflex twin	flexible_metal	EN 15632-4	120	140	\N	150	\N	isoplus planning manual chapter 3 (2015/2016), 3.2 isoflex twin pipe
6	isoplus isocu	flexible_metal	EN 15632-4	120	140	\N	110	\N	isoplus planning manual chapter 3 (2015/2016), 3.4 isocu: copper Cu-DHP
7	isoplus isocu twin	flexible_metal	EN 15632-4	120	140	\N	110	\N	isoplus planning manual chapter 3 (2015/2016), 3.4 isocu twin pipes
8	isoplus isopex H	flexible_plastic	EN 15632-2	80	95	\N	\N	1.25	isoplus planning manual chapter 3 (2015/2016), 3.5 isopex heating 6 bar: PE-Xa SDR 11; ratings DIN 16893, water
9	isoplus isopex H u	flexible_plastic	EN 15632-2	80	95	\N	\N	1.25	isoplus planning manual chapter 3 (2015/2016), 3.5 isopex heating, reduced insulation
10	isoplus isopex H v	flexible_plastic	EN 15632-2	80	95	\N	\N	1.25	isoplus planning manual chapter 3 (2015/2016), 3.5 isopex heating, reinforced insulation
11	isoplus isopex H bar	flexible_plastic	EN 15632-2	80	95	\N	\N	1.25	isoplus planning manual chapter 3 (2015/2016), 3.5 isopex heating, straight 12 m bars
12	isoplus isopex H twin	flexible_plastic	EN 15632-2	80	95	\N	\N	1.25	isoplus planning manual chapter 3 (2015/2016), 3.5 isopex heating twin pipes
13	isoplus isopex H twin v	flexible_plastic	EN 15632-2	80	95	\N	\N	1.25	isoplus planning manual chapter 3 (2015/2016), 3.5 isopex heating twin pipes, reinforced insulation
14	isoplus isopex S	flexible_plastic	EN 15632-2	80	95	\N	\N	1.25	isoplus planning manual chapter 3 (2015/2016), 3.5 isopex sanitary 10 bar: PE-Xa; ratings DIN 16893, water
15	isoplus isopex S twin	flexible_plastic	EN 15632-2	80	95	\N	\N	1.25	isoplus planning manual chapter 3 (2015/2016), 3.5 isopex sanitary twin pipes (unequal carriers; their pipes have no series text and are not resized)
16	isoplus isoclima	flexible_plastic	EN 12201-2	40	\N	-40	\N	1.25	isoplus planning manual chapter 3 (2015/2016), 3.6 isoclima: PE 100 SDR 11, cold water
17	isoplus isoclima u	flexible_plastic	EN 12201-2	40	\N	-40	\N	1.25	isoplus planning manual chapter 3 (2015/2016), 3.6 isoclima, reduced insulation
\.

--
-- Data for Name: pipe_series_pressure_ratings; Type: TABLE DATA; Schema: public;
--

COPY public.pipe_series_pressure_ratings (id, series_id, years, temperature_c, pressure_bar) FROM stdin;
1	8	1	10	17.9
2	8	1	20	15.8
3	8	1	30	14
4	8	1	40	12.5
5	8	1	50	11.1
6	8	1	60	9.9
7	8	1	70	8.9
8	8	1	80	8
9	8	1	90	7.2
10	8	1	95	6.8
11	8	5	10	17.5
12	8	5	20	15.5
13	8	5	30	13.8
14	8	5	40	12.2
15	8	5	50	10.9
16	8	5	60	9.7
17	8	5	70	8.7
18	8	5	80	7.8
19	8	5	90	7
20	8	5	95	6.6
21	8	10	10	17.4
22	8	10	20	15.4
23	8	10	30	13.7
24	8	10	40	12.1
25	8	10	50	10.8
26	8	10	60	9.7
27	8	10	70	8.6
28	8	10	80	7.7
29	8	10	90	6.9
30	8	25	10	17.2
31	8	25	20	15.2
32	8	25	30	13.5
33	8	25	40	12
34	8	25	50	10.7
35	8	25	60	9.5
36	8	25	70	8.5
37	8	25	80	7.6
38	8	50	10	17.1
39	8	50	20	15.1
40	8	50	30	13.4
41	8	50	40	11.9
42	8	50	50	10.6
43	8	50	60	9.5
44	8	50	70	8.5
45	9	1	10	17.9
46	9	1	20	15.8
47	9	1	30	14
48	9	1	40	12.5
49	9	1	50	11.1
50	9	1	60	9.9
51	9	1	70	8.9
52	9	1	80	8
53	9	1	90	7.2
54	9	1	95	6.8
55	9	5	10	17.5
56	9	5	20	15.5
57	9	5	30	13.8
58	9	5	40	12.2
59	9	5	50	10.9
60	9	5	60	9.7
61	9	5	70	8.7
62	9	5	80	7.8
63	9	5	90	7
64	9	5	95	6.6
65	9	10	10	17.4
66	9	10	20	15.4
67	9	10	30	13.7
68	9	10	40	12.1
69	9	10	50	10.8
70	9	10	60	9.7
71	9	10	70	8.6
72	9	10	80	7.7
73	9	10	90	6.9
74	9	25	10	17.2
75	9	25	20	15.2
76	9	25	30	13.5
77	9	25	40	12
78	9	25	50	10.7
79	9	25	60	9.5
80	9	25	70	8.5
81	9	25	80	7.6
82	9	50	10	17.1
83	9	50	20	15.1
84	9	50	30	13.4
85	9	50	40	11.9
86	9	50	50	10.6
87	9	50	60	9.5
88	9	50	70	8.5
89	10	1	10	17.9
90	10	1	20	15.8
91	10	1	30	14
92	10	1	40	12.5
93	10	1	50	11.1
94	10	1	60	9.9
95	10	1	70	8.9
96	10	1	80	8
97	10	1	90	7.2
98	10	1	95	6.8
99	10	5	10	17.5
100	10	5	20	15.5
101	10	5	30	13.8
102	10	5	40	12.2
103	10	5	50	10.9
104	10	5	60	9.7
105	10	5	70	8.7
106	10	5	80	7.8
107	10	5	90	7
108	10	5	95	6.6
109	10	10	10	17.4
110	10	10	20	15.4
111	10	10	30	13.7
112	10	10	40	12.1
113	10	10	50	10.8
114	10	10	60	9.7
115	10	10	70	8.6
116	10	10	80	7.7
117	10	10	90	6.9
118	10	25	10	17.2
119	10	25	20	15.2
120	10	25	30	13.5
121	10	25	40	12
122	10	25	50	10.7
123	10	25	60	9.5
124	10	25	70	8.5
125	10	25	80	7.6
126	10	50	10	17.1
127	10	50	20	15.1
128	10	50	30	13.4
129	10	50	40	11.9
130	10	50	50	10.6
131	10	50	60	9.5
132	10	50	70	8.5
133	11	1	10	17.9
134	11	1	20	15.8
135	11	1	30	14
136	11	1	40	12.5
137	11	1	50	11.1
138	11	1	60	9.9
139	11	1	70	8.9
140	11	1	80	8
141	11	1	90	7.2
142	11	1	95	6.8
143	11	5	10	17.5
144	11	5	20	15.5
145	11	5	30	13.8
146	11	5	40	12.2
147	11	5	50	10.9
148	11	5	60	9.7
149	11	5	70	8.7
150	11	5	80	7.8
151	11	5	90	7
152	11	5	95	6.6
153	11	10	10	17.4
154	11	10	20	15.4
155	11	10	30	13.7
156	11	10	40	12.1
157	11	10	50	10.8
158	11	10	60	9.7
159	11	10	70	8.6
160	11	10	80	7.7
161	11	10	90	6.9
162	11	25	10	17.2
163	11	25	20	15.2
164	11	25	30	13.5
165	11	25	40	12
166	11	25	50	10.7
167	11	25	60	9.5
168	11	25	70	8.5
169	11	25	80	7.6
170	11	50	10	17.1
171	11	50	20	15.1
172	11	50	30	13.4
173	11	50	40	11.9
174	11	50	50	10.6
175	11	50	60	9.5
176	11	50	70	8.5
177	12	1	10	17.9
178	12	1	20	15.8
179	12	1	30	14
180	12	1	40	12.5
181	12	1	50	11.1
182	12	1	60	9.9
183	12	1	70	8.9
184	12	1	80	8
185	12	1	90	7.2
186	12	1	95	6.8
187	12	5	10	17.5
188	12	5	20	15.5
189	12	5	30	13.8
190	12	5	40	12.2
191	12	5	50	10.9
192	12	5	60	9.7
193	12	5	70	8.7
194	12	5	80	7.8
195	12	5	90	7
196	12	5	95	6.6
197	12	10	10	17.4
198	12	10	20	15.4
199	12	10	30	13.7
200	12	10	40	12.1
201	12	10	50	10.8
202	12	10	60	9.7
203	12	10	70	8.6
204	12	10	80	7.7
205	12	10	90	6.9
206	12	25	10	17.2
207	12	25	20	15.2
208	12	25	30	13.5
209	12	25	40	12
210	12	25	50	10.7
211	12	25	60	9.5
212	12	25	70	8.5
213	12	25	80	7.6
214	12	50	10	17.1
215	12	50	20	15.1
216	12	50	30	13.4
217	12	50	40	11.9
218	12	50	50	10.6
219	12	50	60	9.5
220	12	50	70	8.5
221	13	1	10	17.9
222	13	1	20	15.8
223	13	1	30	14
224	13	1	40	12.5
225	13	1	50	11.1
226	13	1	60	9.9
227	13	1	70	8.9
228	13	1	80	8
229	13	1	90	7.2
230	13	1	95	6.8
231	13	5	10	17.5
232	13	5	20	15.5
233	13	5	30	13.8
234	13	5	40	12.2
235	13	5	50	10.9
236	13	5	60	9.7
237	13	5	70	8.7
238	13	5	80	7.8
239	13	5	90	7
240	13	5	95	6.6
241	13	10	10	17.4
242	13	10	20	15.4
243	13	10	30	13.7
244	13	10	40	12.1
245	13	10	50	10.8
246	13	10	60	9.7
247	13	10	70	8.6
248	13	10	80	7.7
249	13	10	90	6.9
250	13	25	10	17.2
251	13	25	20	15.2
252	13	25	30	13.5
253	13	25	40	12
254	13	25	50	10.7
255	13	25	60	9.5
256	13	25	70	8.5
257	13	25	80	7.6
258	13	50	10	17.1
259	13	50	20	15.1
260	13	50	30	13.4
261	13	50	40	11.9
262	13	50	50	10.6
263	13	50	60	9.5
264	13	50	70	8.5
265	14	1	10	28.3
266	14	1	20	25.1
267	14	1	30	22.3
268	14	1	40	19.8
269	14	1	50	17.7
270	14	1	60	15.8
271	14	1	70	14.1
272	14	1	80	12.7
273	14	1	90	11.4
274	14	1	95	10.8
275	14	5	10	27.8
276	14	5	20	24.6
277	14	5	30	21.9
278	14	5	40	19.4
279	14	5	50	17.3
280	14	5	60	15.5
281	14	5	70	13.8
282	14	5	80	12.4
283	14	5	90	11.1
284	14	10	10	27.6
285	14	10	20	24.4
286	14	10	30	21.7
287	14	10	40	19.3
288	14	10	50	17.2
289	14	10	60	15.3
290	14	10	70	13.7
291	14	10	80	12.3
292	14	10	90	11
293	14	25	10	27.3
294	14	25	20	24.2
295	14	25	30	21.4
296	14	25	40	19.1
297	14	25	50	17
298	14	25	60	15.2
299	14	25	70	13.6
300	14	25	80	12.1
301	14	50	10	27.1
302	14	50	20	24
303	14	50	30	21.3
304	14	50	40	18.9
305	14	50	50	16.8
306	14	50	60	15
307	14	50	70	13.4
308	15	1	10	28.3
309	15	1	20	25.1
310	15	1	30	22.3
311	15	1	40	19.8
312	15	1	50	17.7
313	15	1	60	15.8
314	15	1	70	14.1
315	15	1	80	12.7
316	15	1	90	11.4
317	15	1	95	10.8
318	15	5	10	27.8
319	15	5	20	24.6
320	15	5	30	21.9
321	15	5	40	19.4
322	15	5	50	17.3
323	15	5	60	15.5
324	15	5	70	13.8
325	15	5	80	12.4
326	15	5	90	11.1
327	15	10	10	27.6
328	15	10	20	24.4
329	15	10	30	21.7
330	15	10	40	19.3
331	15	10	50	17.2
332	15	10	60	15.3
333	15	10	70	13.7
334	15	10	80	12.3
335	15	10	90	11
336	15	25	10	27.3
337	15	25	20	24.2
338	15	25	30	21.4
339	15	25	40	19.1
340	15	25	50	17
341	15	25	60	15.2
342	15	25	70	13.6
343	15	25	80	12.1
344	15	50	10	27.1
345	15	50	20	24
346	15	50	30	21.3
347	15	50	40	18.9
348	15	50	50	16.8
349	15	50	60	15
350	15	50	70	13.4
351	16	5	10	20.2
352	16	10	10	19.8
353	16	25	10	19.3
354	16	50	10	19
355	16	5	20	16.9
356	16	10	20	16.6
357	16	25	20	16.2
358	16	50	20	16
359	16	5	30	14.4
360	16	10	30	14.1
361	16	25	30	13.8
362	16	50	30	13.5
363	16	5	40	12.3
364	16	10	40	12.1
365	16	25	40	11.8
366	16	50	40	11.6
367	16	5	50	10.7
368	16	10	50	10.4
369	16	15	50	9.5
370	16	5	60	7.7
371	17	5	10	20.2
372	17	10	10	19.8
373	17	25	10	19.3
374	17	50	10	19
375	17	5	20	16.9
376	17	10	20	16.6
377	17	25	20	16.2
378	17	50	20	16
379	17	5	30	14.4
380	17	10	30	14.1
381	17	25	30	13.8
382	17	50	30	13.5
383	17	5	40	12.3
384	17	10	40	12.1
385	17	25	40	11.8
386	17	50	40	11.6
387	17	5	50	10.7
388	17	10	50	10.4
389	17	15	50	9.5
390	17	5	60	7.7
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

SELECT pg_catalog.setval('public.bundle_pipes_id_seq', 71, false);


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

SELECT pg_catalog.setval('public.materials_id_seq', 11, false);


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

SELECT pg_catalog.setval('public.pipe_bundle_types_id_seq', 35, false);


--
-- Name: pipe_constructions_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_constructions_id_seq', 141, false);


--
-- Name: pipe_layers_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_layers_id_seq', 315, false);


--
-- Name: pipes_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipes_id_seq', 109, false);


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

--
-- Name: pipe_series; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_series_id_seq', 18, false);

--
-- Name: pipe_series_pressure_ratings; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_series_pressure_ratings_id_seq', 391, false);
