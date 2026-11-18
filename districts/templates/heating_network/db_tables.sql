SET client_encoding = 'UTF8';

--
-- Data for Name: bundle_pipes; Type: TABLE DATA; Schema: public;
--

COPY public.bundle_pipes (id, pipe_bundle_type_id, sequence, pipe_id, x, y, ambient) FROM stdin;
1	1	2	1	-0.5	1	2
2	1	1	1	0.5	1	2
3	2	1	5	0.0	1	2
4	2	2	5	0.25	1	2
5	3	1	11	0.0	1	2
6	3	2	11	0.25	1	2
7	4	1	6	0.0	1	2
8	4	2	6	0.25	1	2
9	5	1	8	0.0	1	2
10	5	2	8	0.25	1	2
11	6	1	3	0.0	1	2
12	6	2	3	0.25	1	2
13	7	1	4	0.0	1	2
14	7	2	4	0.25	1	2
15	8	1	2	0.0	1	2
16	8	2	2	0.25	1	2
17	9	1	9	0.0	1	2
18	9	2	9	0.25	1	2
19	10	1	7	0.0	1	2
20	10	2	7	0.25	1	2
21	11	1	10	0.0	1	2
22	11	2	10	0.25	1	2
23	12	1	29	-0.02295	1	2
24	12	2	29	0.02295	1	2
25	13	1	30	-0.02635	1	2
26	13	2	30	0.02635	1	2
27	14	1	31	-0.0307	1	2
28	14	2	31	0.0307	1	2
29	15	1	32	-0.03365	1	2
30	15	2	32	0.03365	1	2
31	16	1	33	-0.04015	1	2
32	16	2	33	0.04015	1	2
33	17	1	34	-0.04805	1	2
34	17	2	34	0.04805	1	2
35	18	1	35	-0.05695	1	2
36	18	2	35	0.05695	1	2
37	19	1	36	-0.06965	1	2
38	19	2	36	0.06965	1	2
39	20	1	37	-0.08485	1	2
40	20	2	37	0.08485	1	2
41	21	1	38	-0.10415	1	2
42	21	2	38	0.10415	1	2
43	22	1	39	-0.13205	1	2
44	22	2	39	0.13205	1	2
45	23	1	43	0	1.02227	2
46	23	2	43	0	0.97773	2
47	24	1	46	0	1.018	2
48	24	2	46	0	0.982	2
49	25	1	47	0	1.019	2
50	25	2	47	0	0.981	2
51	26	1	71	0	1.01517	2
52	26	2	71	0	0.98483	2
53	27	1	72	0	1.01767	2
54	27	2	72	0	0.98233	2
55	28	1	73	0	1.0185	2
56	28	2	73	0	0.9815	2
57	29	1	74	0	1.02177	2
58	29	2	74	0	0.97823	2
59	30	1	75	0	1.02293	2
60	30	2	75	0	0.97707	2
61	31	1	76	0	1.02533	2
62	31	2	76	0	0.97467	2
63	32	1	77	0	1.02667	2
64	32	2	77	0	0.97333	2
65	33	1	78	0	1.02907	2
66	33	2	78	0	0.97093	2
67	34	1	79	0	1.03393	2
68	34	2	79	0	0.96607	2
69	35	1	80	0	1.03713	2
70	35	2	80	0	0.96287	2
71	36	1	81	0	1.0393	2
72	36	2	81	0	0.9607	2
73	37	1	82	0	1.0425	2
74	37	2	82	0	0.9575	2
75	38	1	83	0	1.0445	2
76	38	2	83	0	0.9555	2
77	39	1	89	0	1.01767	2
78	39	2	90	0	0.98233	2
79	40	1	91	0	1.02093	2
80	40	2	92	0	0.97907	2
81	41	1	93	0	1.02417	2
82	41	2	94	0	0.97583	2
83	42	1	95	0	1.02773	2
84	42	2	96	0	0.97227	2
85	43	1	97	0	1.03093	2
86	43	2	98	0	0.96907	2
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
25	10	2	11
24	10	3	8
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
7	1	t	70	\N	0.1	Supply: 70 °C;0.1kg/s
8	2	t	30	\N	0.1	Return: 30 °C;0.1kg/s
9	1	t	18	\N	0.1	Supply: 18 °C;0.1kg/s
10	2	t	10	\N	0.1	Return: 10 °C;0.1kg/s
11	1	t	10	\N	0.1	Supply: 10 °C;0.1kg/s
12	2	t	18	\N	0.1	Return: 18 °C;0.1kg/s
\.


--
-- Data for Name: customer_templates; Type: TABLE DATA; Schema: public;
--

COPY public.customer_templates (id, template, template_name, conn_bundle_type, description) FROM stdin;
1	1	simplified_consumer	1	
\.


--
-- Data for Name: energy_plant_templates; Type: TABLE DATA; Schema: public;
--

COPY public.energy_plant_templates (id, template, template_name, conn_bundle_type, description) FROM stdin;
1	1	ideal_heat_source	7	This type of energy plant supplies heat by one supply and return line.
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
1	pipe bundle
2	pipes: 5,5
3	pipes: 11,11
4	pipes: 6,6
5	pipes: 8,8
6	pipes: 3,3
7	pipes: 4,4
8	pipes: 2,2
9	pipes: 9,9
10	pipes: 7,7
11	pipes: 10,10
12	twin pipe Isoplus DRD-20: pipes: 29,29; 1 m depth
13	twin pipe Isoplus DRD-25: pipes: 30,30; 1 m depth
14	twin pipe Isoplus DRD-32: pipes: 31,31; 1 m depth
15	twin pipe Isoplus DRD-40: pipes: 32,32; 1 m depth
16	twin pipe Isoplus DRD-50: pipes: 33,33; 1 m depth
17	twin pipe Isoplus DRD-65: pipes: 34,34; 1 m depth
18	twin pipe Isoplus DRD-80: pipes: 35,35; 1 m depth
19	twin pipe Isoplus DRD-100: pipes: 36,36; 1 m depth
20	twin pipe Isoplus DRD-125: pipes: 37,37; 1 m depth
21	twin pipe Isoplus DRD-150: pipes: 38,38; 1 m depth
22	twin pipe Isoplus DRD-200: pipes: 39,39; 1 m depth
23	twin pipe isoplus isoflex 28+28: pipes: 43,43; 1 m depth
24	twin pipe isoplus isocu 22+22: pipes: 46,46; 1 m depth
25	twin pipe isoplus isocu 28+28: pipes: 47,47; 1 m depth
26	twin pipe isoplus isopex H-20+20: pipes: 71,71; 1 m depth
27	twin pipe isoplus isopex H-20+20 v: pipes: 72,72; 1 m depth
28	twin pipe isoplus isopex H-25+25: pipes: 73,73; 1 m depth
29	twin pipe isoplus isopex H-25+25 v: pipes: 74,74; 1 m depth
30	twin pipe isoplus isopex H-32+32: pipes: 75,75; 1 m depth
31	twin pipe isoplus isopex H-32+32 v: pipes: 76,76; 1 m depth
32	twin pipe isoplus isopex H-40+40: pipes: 77,77; 1 m depth
33	twin pipe isoplus isopex H-40+40 v: pipes: 78,78; 1 m depth
34	twin pipe isoplus isopex H-50+50: pipes: 79,79; 1 m depth
35	twin pipe isoplus isopex H-50+50 v: pipes: 80,80; 1 m depth
36	twin pipe isoplus isopex H-63+63: pipes: 81,81; 1 m depth
37	twin pipe isoplus isopex H-63+63 v: pipes: 82,82; 1 m depth
38	twin pipe isoplus isopex H-75+75: pipes: 83,83; 1 m depth
39	twin pipe isoplus isopex S-25+20: pipes: 89,90; 1 m depth
40	twin pipe isoplus isopex S-32+20: pipes: 91,92; 1 m depth
41	twin pipe isoplus isopex S-40+25: pipes: 93,94; 1 m depth
42	twin pipe isoplus isopex S-50+32: pipes: 95,96; 1 m depth
43	twin pipe isoplus isopex S-63+32: pipes: 97,98; 1 m depth
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
-- Data for Name: versionhandling; Type: TABLE DATA; Schema: public;
--

COPY public.versionhandling (id, name, id_base, description) FROM stdin;
1	base1	0	base version
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
-- Data for Name: customer_model_parms; Type: TABLE DATA; Schema: public;
--

COPY public.model_parms (id, parm_name, model_name, mapping_expression, macro_name, mapping_direction, type) FROM stdin;
1	QRat	hx_substation	"load_w"	:FEATURE	-->	1
2	FloorArea	loadmodel	"gfa_m2"	:FEATURE	-->	1
3	Kvs	vlvbid_substation	"load_w"/30/4180*3.6	:FEATURE	-->	1
\.

--
-- Data for Name: sensors; Type: TABLE DATA; Schema: public;
--

COPY public.sensors (id) FROM stdin;
1
\.


--
-- Data for Name: sensor_source; Type: TABLE DATA; Schema: public;
--

COPY public.sensor_source (id, sensor_id, type, template, measure, function, conn_type, conns, test_value, description) FROM stdin;
1	1	1	1	5	1	1	1	1.0	weak point control
\.


--
-- Data for Name: sensor_target; Type: TABLE DATA; Schema: public;
--

COPY public.sensor_target (id, sensor_id, type, template, test_value, description) FROM stdin;
1	1	2	1	1.0	weak point control
\.

--
-- Data for Name: source_template; Type: TABLE DATA; Schema: public;
--

COPY public.source_template (id, source_id, template, active) FROM stdin;
1	1	1	t
\.

--
-- Data for Name: target_template; Type: TABLE DATA; Schema: public;
--

COPY public.target_template (id, target_id, template, active) FROM stdin;
1	1	1	t
\.


--
-- Data for Name: invoked_sensor_source_signals; Type: TABLE DATA; Schema: public;
--

COPY public.invoked_sensor_source_signals (id, type, sensor_id, templates, multi_signal, test_value, description) FROM stdin;
1	1	1	{1}	false	1.0	weak point control
\.


--
-- Data for Name: invoked_sensor_target_signals; Type: TABLE DATA; Schema: public;
--

COPY public.invoked_sensor_target_signals (id, type, sensor_id, templates, multi_signal, test_value, description) FROM stdin;
1	2	1	{1}	false	1.0	weak point control
\.





------------ data for version tables------------

--
-- Data for Name: buildings; Type: TABLE DATA; Schema: base1; Owner: postgres
--

COPY base1.buildings (id, b_id, z_id, substation_id, submodel, geom, z_bh_m, z_height_m) FROM stdin;
2	1	1	1	2	0106000020E8640000010000000103000000010000000B000000F262A615DBD72E416A55C052683C59415DE07AC9C7D72E419820D7786A3C5941609A7020DED72E416B570BA36C3C594124A2C935FDD72E4162E25BAC6C3C5941BD40852E0DD82E41533CB7616C3C594127DF004F2ED82E4160117F486B3C5941C4AFFDD323D82E41E8174A60683C5941B0AEF1760BD82E411310F234693C594126FEA44BF9D72E4170598F74693C59416143CEBBE8D72E4138DD687C693C5941F262A615DBD72E416A55C052683C5941	0	2.7
3	1	2	1	2	0106000020E8640000010000000103000000010000000B000000F262A615DBD72E416A55C052683C59415DE07AC9C7D72E419820D7786A3C5941609A7020DED72E416B570BA36C3C594124A2C935FDD72E4162E25BAC6C3C5941BD40852E0DD82E41533CB7616C3C594127DF004F2ED82E4160117F486B3C5941C4AFFDD323D82E41E8174A60683C5941B0AEF1760BD82E411310F234693C594126FEA44BF9D72E4170598F74693C59416143CEBBE8D72E4138DD687C693C5941F262A615DBD72E416A55C052683C5941	3	2.7
4	1	3	1	2	0106000020E8640000010000000103000000010000000B000000F262A615DBD72E416A55C052683C59415DE07AC9C7D72E419820D7786A3C5941609A7020DED72E416B570BA36C3C594124A2C935FDD72E4162E25BAC6C3C5941BD40852E0DD82E41533CB7616C3C594127DF004F2ED82E4160117F486B3C5941C4AFFDD323D82E41E8174A60683C5941B0AEF1760BD82E411310F234693C594126FEA44BF9D72E4170598F74693C59416143CEBBE8D72E4138DD687C693C5941F262A615DBD72E416A55C052683C5941	6	2.7
5	1	4	1	2	0106000020E8640000010000000103000000010000000B000000F262A615DBD72E416A55C052683C59415DE07AC9C7D72E419820D7786A3C5941609A7020DED72E416B570BA36C3C594124A2C935FDD72E4162E25BAC6C3C5941BD40852E0DD82E41533CB7616C3C594127DF004F2ED82E4160117F486B3C5941C4AFFDD323D82E41E8174A60683C5941B0AEF1760BD82E411310F234693C594126FEA44BF9D72E4170598F74693C59416143CEBBE8D72E4138DD687C693C5941F262A615DBD72E416A55C052683C5941	9	2.7
6	2	1	2	2	0106000020E864000001000000010300000001000000050000000E66184B15D82E41D646BE0F4E3C5941BA3C6329F8D72E41AE9AF9884A3C5941027FA3FD0BD82E41C2C7DAFB473C59415A6B5B1F29D82E417816A0824B3C59410E66184B15D82E41D646BE0F4E3C5941	0	2.7
7	2	2	2	2	0106000020E864000001000000010300000001000000050000000E66184B15D82E41D646BE0F4E3C5941BA3C6329F8D72E41AE9AF9884A3C5941027FA3FD0BD82E41C2C7DAFB473C59415A6B5B1F29D82E417816A0824B3C59410E66184B15D82E41D646BE0F4E3C5941	3	2.7
8	2	3	2	2	0106000020E864000001000000010300000001000000050000000E66184B15D82E41D646BE0F4E3C5941BA3C6329F8D72E41AE9AF9884A3C5941027FA3FD0BD82E41C2C7DAFB473C59415A6B5B1F29D82E417816A0824B3C59410E66184B15D82E41D646BE0F4E3C5941	6	2.7
9	3	1	3	2	0106000020E8640000010000000103000000010000000500000070CCC2CE41D72E41C6486808583C59413CC7F2E438D72E41B2548A3C543C5941DE717EF74BD72E41E2B9629A533C5941A3F98F3655D72E41268E8053573C594170CCC2CE41D72E41C6486808583C5941	0	2.7
10	3	2	3	2	0106000020E8640000010000000103000000010000000500000070CCC2CE41D72E41C6486808583C59413CC7F2E438D72E41B2548A3C543C5941DE717EF74BD72E41E2B9629A533C5941A3F98F3655D72E41268E8053573C594170CCC2CE41D72E41C6486808583C5941	3	2.7
11	3	3	3	2	0106000020E8640000010000000103000000010000000500000070CCC2CE41D72E41C6486808583C59413CC7F2E438D72E41B2548A3C543C5941DE717EF74BD72E41E2B9629A533C5941A3F98F3655D72E41268E8053573C594170CCC2CE41D72E41C6486808583C5941	6	2.7
12	4	1	4	2	0106000020E8640000010000000103000000010000000500000041A287E19ED72E4173A752B8593C5941CB594ADAC9D72E41405E4F02593C59413ECB002EC7D72E4125931B7D563C5941446C37359CD72E4154081F33573C594141A287E19ED72E4173A752B8593C5941	0	2.7
13	4	2	4	2	0106000020E8640000010000000103000000010000000500000041A287E19ED72E4173A752B8593C5941CB594ADAC9D72E41405E4F02593C59413ECB002EC7D72E4125931B7D563C5941446C37359CD72E4154081F33573C594141A287E19ED72E4173A752B8593C5941	3	2.7
14	4	3	4	2	0106000020E8640000010000000103000000010000000500000041A287E19ED72E4173A752B8593C5941CB594ADAC9D72E41405E4F02593C59413ECB002EC7D72E4125931B7D563C5941446C37359CD72E4154081F33573C594141A287E19ED72E4173A752B8593C5941	6	2.7
15	5	1	5	2	0106000020E86400000100000001030000000100000005000000C0FFDE6525D82E41A25AEAC75B3C5941403954AC01D82E41687AE3E6563C59411E66B50213D82E414C19EDEC543C59414AA907BD36D82E41574F3FCD593C5941C0FFDE6525D82E41A25AEAC75B3C5941	0	2.7
16	5	2	5	2	0106000020E86400000100000001030000000100000005000000C0FFDE6525D82E41A25AEAC75B3C5941403954AC01D82E41687AE3E6563C59411E66B50213D82E414C19EDEC543C59414AA907BD36D82E41574F3FCD593C5941C0FFDE6525D82E41A25AEAC75B3C5941	3	2.7
17	5	3	5	2	0106000020E86400000100000001030000000100000005000000C0FFDE6525D82E41A25AEAC75B3C5941403954AC01D82E41687AE3E6563C59411E66B50213D82E414C19EDEC543C59414AA907BD36D82E41574F3FCD593C5941C0FFDE6525D82E41A25AEAC75B3C5941	6	2.7
18	5	4	5	2	0106000020E86400000100000001030000000100000005000000C0FFDE6525D82E41A25AEAC75B3C5941403954AC01D82E41687AE3E6563C59411E66B50213D82E414C19EDEC543C59414AA907BD36D82E41574F3FCD593C5941C0FFDE6525D82E41A25AEAC75B3C5941	9	2.7
19	5	5	5	2	0106000020E86400000100000001030000000100000005000000C0FFDE6525D82E41A25AEAC75B3C5941403954AC01D82E41687AE3E6563C59411E66B50213D82E414C19EDEC543C59414AA907BD36D82E41574F3FCD593C5941C0FFDE6525D82E41A25AEAC75B3C5941	12	2.7
20	6	1	6	2	0106000020E86400000100000001030000000100000005000000506DCB85FAD72E41944839E05F3C5941C8421BD512D82E41C076625A5D3C594178FAD16901D82E41218543BD5A3C5941E2109E17E9D72E4132320E435D3C5941506DCB85FAD72E41944839E05F3C5941	0	2.7
21	6	2	6	2	0106000020E86400000100000001030000000100000005000000506DCB85FAD72E41944839E05F3C5941C8421BD512D82E41C076625A5D3C594178FAD16901D82E41218543BD5A3C5941E2109E17E9D72E4132320E435D3C5941506DCB85FAD72E41944839E05F3C5941	3	2.7
22	6	3	6	2	0106000020E86400000100000001030000000100000005000000506DCB85FAD72E41944839E05F3C5941C8421BD512D82E41C076625A5D3C594178FAD16901D82E41218543BD5A3C5941E2109E17E9D72E4132320E435D3C5941506DCB85FAD72E41944839E05F3C5941	6	2.7
23	7	1	7	2	0106000020E86400000100000001030000000100000005000000C472950E3AD82E41B787F1174A3C5941920C97161CD82E41308A6811463C5941C0696B672FD82E419E6B4FD4433C59413A916B5F4DD82E41A80DD9DA473C5941C472950E3AD82E41B787F1174A3C5941	0	2.7
24	7	2	7	2	0106000020E86400000100000001030000000100000005000000C472950E3AD82E41B787F1174A3C5941920C97161CD82E41308A6811463C5941C0696B672FD82E419E6B4FD4433C59413A916B5F4DD82E41A80DD9DA473C5941C472950E3AD82E41B787F1174A3C5941	3	2.7
25	7	3	7	2	0106000020E86400000100000001030000000100000005000000C472950E3AD82E41B787F1174A3C5941920C97161CD82E41308A6811463C5941C0696B672FD82E419E6B4FD4433C59413A916B5F4DD82E41A80DD9DA473C5941C472950E3AD82E41B787F1174A3C5941	6	2.7
26	8	1	8	2	0106000020E86400000100000001030000000100000005000000B6F55300EED72E41DE349149513C59414C1D24A0D5D72E41923852DD4D3C59416D778530E9D72E414C2820AC4B3C5941273FB38700D82E418DDE02234F3C5941B6F55300EED72E41DE349149513C5941	0	2.7
27	8	2	8	2	0106000020E86400000100000001030000000100000005000000B6F55300EED72E41DE349149513C59414C1D24A0D5D72E41923852DD4D3C59416D778530E9D72E414C2820AC4B3C5941273FB38700D82E418DDE02234F3C5941B6F55300EED72E41DE349149513C5941	3	2.7
28	8	3	8	2	0106000020E86400000100000001030000000100000005000000B6F55300EED72E41DE349149513C59414C1D24A0D5D72E41923852DD4D3C59416D778530E9D72E414C2820AC4B3C5941273FB38700D82E418DDE02234F3C5941B6F55300EED72E41DE349149513C5941	6	2.7
29	9	1	9	2	0106000020E8640000010000000103000000010000000B0000000700F5E7EFD62E414B5CC6FE5A3C59410ED5FF4662D72E41507774E7653C5941DB4B2B8C70D72E41965F4EBB633C59410A71D7ACACD72E41D7C44E05693C59416A8DB59AC5D72E4174306929663C59419ED9089DB1D72E41AC67957A633C594145F64F1BAAD72E417C225325643C5941D7EC37CF69D72E415434E8DD5D3C5941475A5DFD58D72E41E5C18EAD603C59418D42CD1501D72E41F91A67F8573C59410700F5E7EFD62E414B5CC6FE5A3C5941	0	2.7
30	9	2	9	2	0106000020E8640000010000000103000000010000000B0000000700F5E7EFD62E414B5CC6FE5A3C59410ED5FF4662D72E41507774E7653C5941DB4B2B8C70D72E41965F4EBB633C59410A71D7ACACD72E41D7C44E05693C59416A8DB59AC5D72E4174306929663C59419ED9089DB1D72E41AC67957A633C594145F64F1BAAD72E417C225325643C5941D7EC37CF69D72E415434E8DD5D3C5941475A5DFD58D72E41E5C18EAD603C59418D42CD1501D72E41F91A67F8573C59410700F5E7EFD62E414B5CC6FE5A3C5941	3	2.7
31	9	3	9	2	0106000020E8640000010000000103000000010000000B0000000700F5E7EFD62E414B5CC6FE5A3C59410ED5FF4662D72E41507774E7653C5941DB4B2B8C70D72E41965F4EBB633C59410A71D7ACACD72E41D7C44E05693C59416A8DB59AC5D72E4174306929663C59419ED9089DB1D72E41AC67957A633C594145F64F1BAAD72E417C225325643C5941D7EC37CF69D72E415434E8DD5D3C5941475A5DFD58D72E41E5C18EAD603C59418D42CD1501D72E41F91A67F8573C59410700F5E7EFD62E414B5CC6FE5A3C5941	6	2.7
32	9	4	9	2	0106000020E8640000010000000103000000010000000B0000000700F5E7EFD62E414B5CC6FE5A3C59410ED5FF4662D72E41507774E7653C5941DB4B2B8C70D72E41965F4EBB633C59410A71D7ACACD72E41D7C44E05693C59416A8DB59AC5D72E4174306929663C59419ED9089DB1D72E41AC67957A633C594145F64F1BAAD72E417C225325643C5941D7EC37CF69D72E415434E8DD5D3C5941475A5DFD58D72E41E5C18EAD603C59418D42CD1501D72E41F91A67F8573C59410700F5E7EFD62E414B5CC6FE5A3C5941	9	2.7
33	10	1	10	2	0106000020E8640000010000000103000000010000000500000004C5203BA3D72E4172409F635F3C59417CE642F1CCD72E4135C26FF25E3C5941BAE41B02CBD72E41345015215C3C59415A16114EA1D72E41A3EA06935C3C594104C5203BA3D72E4172409F635F3C5941	0	2.7
34	10	2	10	2	0106000020E8640000010000000103000000010000000500000004C5203BA3D72E4172409F635F3C59417CE642F1CCD72E4135C26FF25E3C5941BAE41B02CBD72E41345015215C3C59415A16114EA1D72E41A3EA06935C3C594104C5203BA3D72E4172409F635F3C5941	3	2.7
35	10	3	10	2	0106000020E8640000010000000103000000010000000500000004C5203BA3D72E4172409F635F3C59417CE642F1CCD72E4135C26FF25E3C5941BAE41B02CBD72E41345015215C3C59415A16114EA1D72E41A3EA06935C3C594104C5203BA3D72E4172409F635F3C5941	6	2.7
36	11	1	11	2	0106000020E8640000010000000103000000010000000500000089F1621370D72E41987969A0583C5941889F35F562D72E41148547BE523C594120A7F7B576D72E414625CA00523C5941EA41B94E85D72E41A0D47FD9573C594189F1621370D72E41987969A0583C5941	0	2.7
37	11	2	11	2	0106000020E8640000010000000103000000010000000500000089F1621370D72E41987969A0583C5941889F35F562D72E41148547BE523C594120A7F7B576D72E414625CA00523C5941EA41B94E85D72E41A0D47FD9573C594189F1621370D72E41987969A0583C5941	3	2.7
38	11	3	11	2	0106000020E8640000010000000103000000010000000500000089F1621370D72E41987969A0583C5941889F35F562D72E41148547BE523C594120A7F7B576D72E414625CA00523C5941EA41B94E85D72E41A0D47FD9573C594189F1621370D72E41987969A0583C5941	6	2.7
39	40	1	40	2	0106000020E86400000100000001030000000100000005000000FD8903720AD82E4168008B56363C5941FB29EF0123D82E41941DE7DB333C5941FEE3D69432D82E41E981B32B363C59410E8344D71AD82E4127A5F0D5383C5941FD8903720AD82E4168008B56363C5941	0	2.7
40	40	2	40	2	0106000020E86400000100000001030000000100000005000000FD8903720AD82E4168008B56363C5941FB29EF0123D82E41941DE7DB333C5941FEE3D69432D82E41E981B32B363C59410E8344D71AD82E4127A5F0D5383C5941FD8903720AD82E4168008B56363C5941	3	2.7
41	40	3	40	2	0106000020E86400000100000001030000000100000005000000FD8903720AD82E4168008B56363C5941FB29EF0123D82E41941DE7DB333C5941FEE3D69432D82E41E981B32B363C59410E8344D71AD82E4127A5F0D5383C5941FD8903720AD82E4168008B56363C5941	6	2.7
42	41	1	41	2	0106000020E864000001000000010300000001000000050000008034CDF0CDD72E41E45C363B433C5941534FCE3BDFD72E419DECCF53413C594130AFC298F9D72E4126C0700F453C59410E4F9DCFE7D72E4119D204F9463C59418034CDF0CDD72E41E45C363B433C5941	0	2.7
43	41	2	41	2	0106000020E864000001000000010300000001000000050000008034CDF0CDD72E41E45C363B433C5941534FCE3BDFD72E419DECCF53413C594130AFC298F9D72E4126C0700F453C59410E4F9DCFE7D72E4119D204F9463C59418034CDF0CDD72E41E45C363B433C5941	3	2.7
44	41	3	41	2	0106000020E864000001000000010300000001000000050000008034CDF0CDD72E41E45C363B433C5941534FCE3BDFD72E419DECCF53413C594130AFC298F9D72E4126C0700F453C59410E4F9DCFE7D72E4119D204F9463C59418034CDF0CDD72E41E45C363B433C5941	6	2.7
45	19	1	19	2	0106000020E8640000010000000103000000010000001200000038F4CCF313D62E41E59CBB34113C594170BDCDC34DD62E41C848E1EB183C594162D77DB352D62E41CBCB949F1A3C594182236A0F80D62E412DA79B90243C5941D8DDDDAC7CD62E41D1D757F8253C59417071650E3AD62E414E90914D293C5941FF87838B2CD62E41E7774DD6253C59415AB12FDA54D62E415C132FFB233C59419477EAFB54D62E4100B1404A233C5941A252AA4B37D62E410DC8438B1C3C59414322311D2DD62E418868B5FB193C59414D19487127D62E41E157F8A71A3C594142EBC98614D62E415126812D183C594190B519F4F7D52E41850F96971B3C5941FAAF22D7DFD52E41486DC240183C5941729557A805D62E411373911E143C59418C925F2902D62E41267DD25D133C594138F4CCF313D62E41E59CBB34113C5941	0	2.7
46	19	2	19	2	0106000020E8640000010000000103000000010000001200000038F4CCF313D62E41E59CBB34113C594170BDCDC34DD62E41C848E1EB183C594162D77DB352D62E41CBCB949F1A3C594182236A0F80D62E412DA79B90243C5941D8DDDDAC7CD62E41D1D757F8253C59417071650E3AD62E414E90914D293C5941FF87838B2CD62E41E7774DD6253C59415AB12FDA54D62E415C132FFB233C59419477EAFB54D62E4100B1404A233C5941A252AA4B37D62E410DC8438B1C3C59414322311D2DD62E418868B5FB193C59414D19487127D62E41E157F8A71A3C594142EBC98614D62E415126812D183C594190B519F4F7D52E41850F96971B3C5941FAAF22D7DFD52E41486DC240183C5941729557A805D62E411373911E143C59418C925F2902D62E41267DD25D133C594138F4CCF313D62E41E59CBB34113C5941	3	2.7
47	19	3	19	2	0106000020E8640000010000000103000000010000001200000038F4CCF313D62E41E59CBB34113C594170BDCDC34DD62E41C848E1EB183C594162D77DB352D62E41CBCB949F1A3C594182236A0F80D62E412DA79B90243C5941D8DDDDAC7CD62E41D1D757F8253C59417071650E3AD62E414E90914D293C5941FF87838B2CD62E41E7774DD6253C59415AB12FDA54D62E415C132FFB233C59419477EAFB54D62E4100B1404A233C5941A252AA4B37D62E410DC8438B1C3C59414322311D2DD62E418868B5FB193C59414D19487127D62E41E157F8A71A3C594142EBC98614D62E415126812D183C594190B519F4F7D52E41850F96971B3C5941FAAF22D7DFD52E41486DC240183C5941729557A805D62E411373911E143C59418C925F2902D62E41267DD25D133C594138F4CCF313D62E41E59CBB34113C5941	6	2.7
48	19	4	19	2	0106000020E8640000010000000103000000010000001200000038F4CCF313D62E41E59CBB34113C594170BDCDC34DD62E41C848E1EB183C594162D77DB352D62E41CBCB949F1A3C594182236A0F80D62E412DA79B90243C5941D8DDDDAC7CD62E41D1D757F8253C59417071650E3AD62E414E90914D293C5941FF87838B2CD62E41E7774DD6253C59415AB12FDA54D62E415C132FFB233C59419477EAFB54D62E4100B1404A233C5941A252AA4B37D62E410DC8438B1C3C59414322311D2DD62E418868B5FB193C59414D19487127D62E41E157F8A71A3C594142EBC98614D62E415126812D183C594190B519F4F7D52E41850F96971B3C5941FAAF22D7DFD52E41486DC240183C5941729557A805D62E411373911E143C59418C925F2902D62E41267DD25D133C594138F4CCF313D62E41E59CBB34113C5941	9	2.7
49	19	5	19	2	0106000020E8640000010000000103000000010000001200000038F4CCF313D62E41E59CBB34113C594170BDCDC34DD62E41C848E1EB183C594162D77DB352D62E41CBCB949F1A3C594182236A0F80D62E412DA79B90243C5941D8DDDDAC7CD62E41D1D757F8253C59417071650E3AD62E414E90914D293C5941FF87838B2CD62E41E7774DD6253C59415AB12FDA54D62E415C132FFB233C59419477EAFB54D62E4100B1404A233C5941A252AA4B37D62E410DC8438B1C3C59414322311D2DD62E418868B5FB193C59414D19487127D62E41E157F8A71A3C594142EBC98614D62E415126812D183C594190B519F4F7D52E41850F96971B3C5941FAAF22D7DFD52E41486DC240183C5941729557A805D62E411373911E143C59418C925F2902D62E41267DD25D133C594138F4CCF313D62E41E59CBB34113C5941	12	2.7
50	19	6	19	2	0106000020E8640000010000000103000000010000001200000038F4CCF313D62E41E59CBB34113C594170BDCDC34DD62E41C848E1EB183C594162D77DB352D62E41CBCB949F1A3C594182236A0F80D62E412DA79B90243C5941D8DDDDAC7CD62E41D1D757F8253C59417071650E3AD62E414E90914D293C5941FF87838B2CD62E41E7774DD6253C59415AB12FDA54D62E415C132FFB233C59419477EAFB54D62E4100B1404A233C5941A252AA4B37D62E410DC8438B1C3C59414322311D2DD62E418868B5FB193C59414D19487127D62E41E157F8A71A3C594142EBC98614D62E415126812D183C594190B519F4F7D52E41850F96971B3C5941FAAF22D7DFD52E41486DC240183C5941729557A805D62E411373911E143C59418C925F2902D62E41267DD25D133C594138F4CCF313D62E41E59CBB34113C5941	15	2.7
51	20	1	20	2	0106000020E864000001000000010300000001000000050000009C6787094ED62E410266AF35333C59412ADCD05441D62E4103AA084D2F3C594151BA6EF897D62E41C9285FEB2A3C594130F716ADA4D62E412C3A07D42E3C59419C6787094ED62E410266AF35333C5941	0	2.7
52	20	2	20	2	0106000020E864000001000000010300000001000000050000009C6787094ED62E410266AF35333C59412ADCD05441D62E4103AA084D2F3C594151BA6EF897D62E41C9285FEB2A3C594130F716ADA4D62E412C3A07D42E3C59419C6787094ED62E410266AF35333C5941	3	2.7
53	20	3	20	2	0106000020E864000001000000010300000001000000050000009C6787094ED62E410266AF35333C59412ADCD05441D62E4103AA084D2F3C594151BA6EF897D62E41C9285FEB2A3C594130F716ADA4D62E412C3A07D42E3C59419C6787094ED62E410266AF35333C5941	6	2.7
54	20	4	20	2	0106000020E864000001000000010300000001000000050000009C6787094ED62E410266AF35333C59412ADCD05441D62E4103AA084D2F3C594151BA6EF897D62E41C9285FEB2A3C594130F716ADA4D62E412C3A07D42E3C59419C6787094ED62E410266AF35333C5941	9	2.7
55	20	5	20	2	0106000020E864000001000000010300000001000000050000009C6787094ED62E410266AF35333C59412ADCD05441D62E4103AA084D2F3C594151BA6EF897D62E41C9285FEB2A3C594130F716ADA4D62E412C3A07D42E3C59419C6787094ED62E410266AF35333C5941	12	2.7
56	22	1	22	2	0106000020E86400000100000001030000000100000005000000D815DE94DBD52E413D815D45753C5941404A161E02D62E41ADD8F5E0743C59411F5F7D4BFFD52E4102FB2298703C5941FC2A1FC5D8D52E41D67097FC703C5941D815DE94DBD52E413D815D45753C5941	0	2.7
57	22	2	22	2	0106000020E86400000100000001030000000100000005000000D815DE94DBD52E413D815D45753C5941404A161E02D62E41ADD8F5E0743C59411F5F7D4BFFD52E4102FB2298703C5941FC2A1FC5D8D52E41D67097FC703C5941D815DE94DBD52E413D815D45753C5941	3	2.7
58	22	3	22	2	0106000020E86400000100000001030000000100000005000000D815DE94DBD52E413D815D45753C5941404A161E02D62E41ADD8F5E0743C59411F5F7D4BFFD52E4102FB2298703C5941FC2A1FC5D8D52E41D67097FC703C5941D815DE94DBD52E413D815D45753C5941	6	2.7
59	22	4	22	2	0106000020E86400000100000001030000000100000005000000D815DE94DBD52E413D815D45753C5941404A161E02D62E41ADD8F5E0743C59411F5F7D4BFFD52E4102FB2298703C5941FC2A1FC5D8D52E41D67097FC703C5941D815DE94DBD52E413D815D45753C5941	9	2.7
60	22	5	22	2	0106000020E86400000100000001030000000100000005000000D815DE94DBD52E413D815D45753C5941404A161E02D62E41ADD8F5E0743C59411F5F7D4BFFD52E4102FB2298703C5941FC2A1FC5D8D52E41D67097FC703C5941D815DE94DBD52E413D815D45753C5941	12	2.7
61	22	6	22	2	0106000020E86400000100000001030000000100000005000000D815DE94DBD52E413D815D45753C5941404A161E02D62E41ADD8F5E0743C59411F5F7D4BFFD52E4102FB2298703C5941FC2A1FC5D8D52E41D67097FC703C5941D815DE94DBD52E413D815D45753C5941	15	2.7
62	27	1	27	2	0106000020E86400000100000001030000000100000005000000BC6944EE39D62E41D11A197C663C59410BC8811713D62E419AD9BF09673C594113D730BD17D62E4191B2E81B6C3C59414C7F21933ED62E419796F78E6B3C5941BC6944EE39D62E41D11A197C663C5941	0	2.7
63	27	2	27	2	0106000020E86400000100000001030000000100000005000000BC6944EE39D62E41D11A197C663C59410BC8811713D62E419AD9BF09673C594113D730BD17D62E4191B2E81B6C3C59414C7F21933ED62E419796F78E6B3C5941BC6944EE39D62E41D11A197C663C5941	3	2.7
64	27	3	27	2	0106000020E86400000100000001030000000100000005000000BC6944EE39D62E41D11A197C663C59410BC8811713D62E419AD9BF09673C594113D730BD17D62E4191B2E81B6C3C59414C7F21933ED62E419796F78E6B3C5941BC6944EE39D62E41D11A197C663C5941	6	2.7
65	27	4	27	2	0106000020E86400000100000001030000000100000005000000BC6944EE39D62E41D11A197C663C59410BC8811713D62E419AD9BF09673C594113D730BD17D62E4191B2E81B6C3C59414C7F21933ED62E419796F78E6B3C5941BC6944EE39D62E41D11A197C663C5941	9	2.7
66	27	5	27	2	0106000020E86400000100000001030000000100000005000000BC6944EE39D62E41D11A197C663C59410BC8811713D62E419AD9BF09673C594113D730BD17D62E4191B2E81B6C3C59414C7F21933ED62E419796F78E6B3C5941BC6944EE39D62E41D11A197C663C5941	12	2.7
67	27	6	27	2	0106000020E86400000100000001030000000100000005000000BC6944EE39D62E41D11A197C663C59410BC8811713D62E419AD9BF09673C594113D730BD17D62E4191B2E81B6C3C59414C7F21933ED62E419796F78E6B3C5941BC6944EE39D62E41D11A197C663C5941	15	2.7
68	28	1	28	2	0106000020E86400000100000001030000000100000005000000FEE331E8D1D52E41599BB80D4D3C5941FEF360FEE1D52E4137A840F1493C5941880E4D261CD62E4137660D1F4F3C5941CEE6C6780AD62E4152171921523C5941FEE331E8D1D52E41599BB80D4D3C5941	0	2.7
69	28	2	28	2	0106000020E86400000100000001030000000100000005000000FEE331E8D1D52E41599BB80D4D3C5941FEF360FEE1D52E4137A840F1493C5941880E4D261CD62E4137660D1F4F3C5941CEE6C6780AD62E4152171921523C5941FEE331E8D1D52E41599BB80D4D3C5941	3	2.7
70	28	3	28	2	0106000020E86400000100000001030000000100000005000000FEE331E8D1D52E41599BB80D4D3C5941FEF360FEE1D52E4137A840F1493C5941880E4D261CD62E4137660D1F4F3C5941CEE6C6780AD62E4152171921523C5941FEE331E8D1D52E41599BB80D4D3C5941	6	2.7
71	28	4	28	2	0106000020E86400000100000001030000000100000005000000FEE331E8D1D52E41599BB80D4D3C5941FEF360FEE1D52E4137A840F1493C5941880E4D261CD62E4137660D1F4F3C5941CEE6C6780AD62E4152171921523C5941FEE331E8D1D52E41599BB80D4D3C5941	9	2.7
72	28	5	28	2	0106000020E86400000100000001030000000100000005000000FEE331E8D1D52E41599BB80D4D3C5941FEF360FEE1D52E4137A840F1493C5941880E4D261CD62E4137660D1F4F3C5941CEE6C6780AD62E4152171921523C5941FEE331E8D1D52E41599BB80D4D3C5941	12	2.7
73	28	6	28	2	0106000020E86400000100000001030000000100000005000000FEE331E8D1D52E41599BB80D4D3C5941FEF360FEE1D52E4137A840F1493C5941880E4D261CD62E4137660D1F4F3C5941CEE6C6780AD62E4152171921523C5941FEE331E8D1D52E41599BB80D4D3C5941	15	2.7
74	29	1	29	2	0106000020E8640000010000000103000000010000000700000076262CA4B4D62E413DD4C3F8303C5941C7FB88BA77D62E4153B32BA83B3C5941A73A934F92D62E41D76B94043E3C59418F6A16029AD62E4186B651AB3C3C5941CA73606AABD62E41B2DA469D393C59419AB94639CFD62E4175462E55333C594176262CA4B4D62E413DD4C3F8303C5941	0	2.7
75	29	2	29	2	0106000020E8640000010000000103000000010000000700000076262CA4B4D62E413DD4C3F8303C5941C7FB88BA77D62E4153B32BA83B3C5941A73A934F92D62E41D76B94043E3C59418F6A16029AD62E4186B651AB3C3C5941CA73606AABD62E41B2DA469D393C59419AB94639CFD62E4175462E55333C594176262CA4B4D62E413DD4C3F8303C5941	3	2.7
76	29	3	29	2	0106000020E8640000010000000103000000010000000700000076262CA4B4D62E413DD4C3F8303C5941C7FB88BA77D62E4153B32BA83B3C5941A73A934F92D62E41D76B94043E3C59418F6A16029AD62E4186B651AB3C3C5941CA73606AABD62E41B2DA469D393C59419AB94639CFD62E4175462E55333C594176262CA4B4D62E413DD4C3F8303C5941	6	2.7
77	29	4	29	2	0106000020E8640000010000000103000000010000000700000076262CA4B4D62E413DD4C3F8303C5941C7FB88BA77D62E4153B32BA83B3C5941A73A934F92D62E41D76B94043E3C59418F6A16029AD62E4186B651AB3C3C5941CA73606AABD62E41B2DA469D393C59419AB94639CFD62E4175462E55333C594176262CA4B4D62E413DD4C3F8303C5941	9	2.7
78	29	5	29	2	0106000020E8640000010000000103000000010000000700000076262CA4B4D62E413DD4C3F8303C5941C7FB88BA77D62E4153B32BA83B3C5941A73A934F92D62E41D76B94043E3C59418F6A16029AD62E4186B651AB3C3C5941CA73606AABD62E41B2DA469D393C59419AB94639CFD62E4175462E55333C594176262CA4B4D62E413DD4C3F8303C5941	12	2.7
79	30	1	30	2	0106000020E8640000010000000103000000010000000500000048FB4342F4D52E41931A5267423C59414E1D4D2F05D62E410372E8833F3C5941781C705A50D62E410306273F463C594130FE8EA33FD62E41468F6119493C594148FB4342F4D52E41931A5267423C5941	0	2.7
80	30	2	30	2	0106000020E8640000010000000103000000010000000500000048FB4342F4D52E41931A5267423C59414E1D4D2F05D62E410372E8833F3C5941781C705A50D62E410306273F463C594130FE8EA33FD62E41468F6119493C594148FB4342F4D52E41931A5267423C5941	3	2.7
81	30	3	30	2	0106000020E8640000010000000103000000010000000500000048FB4342F4D52E41931A5267423C59414E1D4D2F05D62E410372E8833F3C5941781C705A50D62E410306273F463C594130FE8EA33FD62E41468F6119493C594148FB4342F4D52E41931A5267423C5941	6	2.7
82	30	4	30	2	0106000020E8640000010000000103000000010000000500000048FB4342F4D52E41931A5267423C59414E1D4D2F05D62E410372E8833F3C5941781C705A50D62E410306273F463C594130FE8EA33FD62E41468F6119493C594148FB4342F4D52E41931A5267423C5941	9	2.7
83	30	5	30	2	0106000020E8640000010000000103000000010000000500000048FB4342F4D52E41931A5267423C59414E1D4D2F05D62E410372E8833F3C5941781C705A50D62E410306273F463C594130FE8EA33FD62E41468F6119493C594148FB4342F4D52E41931A5267423C5941	12	2.7
84	31	1	31	2	0106000020E8640000010000000103000000010000000500000098137DE716D62E41E15EBE24363C5941A043604E0FD62E4199B1E2E7333C59410A16E98A2AD62E41DBE09277323C5941266C032432D62E41FACD6EB4343C594198137DE716D62E41E15EBE24363C5941	0	2.7
85	31	2	31	2	0106000020E8640000010000000103000000010000000500000098137DE716D62E41E15EBE24363C5941A043604E0FD62E4199B1E2E7333C59410A16E98A2AD62E41DBE09277323C5941266C032432D62E41FACD6EB4343C594198137DE716D62E41E15EBE24363C5941	3	2.7
86	32	1	32	2	0106000020E86400000100000001030000000100000005000000823B488D25D62E41B474B0923A3C594171FE23CE3DD62E41B09D06F4373C5941945BDA3D73D62E41C7F559CB3F3C59415005841D62D62E41F93FB00B433C5941823B488D25D62E41B474B0923A3C5941	0	2.7
87	32	2	32	2	0106000020E86400000100000001030000000100000005000000823B488D25D62E41B474B0923A3C594171FE23CE3DD62E41B09D06F4373C5941945BDA3D73D62E41C7F559CB3F3C59415005841D62D62E41F93FB00B433C5941823B488D25D62E41B474B0923A3C5941	3	2.7
88	32	3	32	2	0106000020E86400000100000001030000000100000005000000823B488D25D62E41B474B0923A3C594171FE23CE3DD62E41B09D06F4373C5941945BDA3D73D62E41C7F559CB3F3C59415005841D62D62E41F93FB00B433C5941823B488D25D62E41B474B0923A3C5941	6	2.7
89	32	4	32	2	0106000020E86400000100000001030000000100000005000000823B488D25D62E41B474B0923A3C594171FE23CE3DD62E41B09D06F4373C5941945BDA3D73D62E41C7F559CB3F3C59415005841D62D62E41F93FB00B433C5941823B488D25D62E41B474B0923A3C5941	9	2.7
90	35	1	35	2	0106000020E86400000100000001030000000100000007000000E22A4FAF73D62E4103C2FCE7113C59411AA71A1E83D62E4171FF2947153C5941A8A4B71694D62E416DD30112143C5941D7CFC0649FD62E411549538A163C59417B698E837DD62E4168D677F3183C5941B4C29AC962D62E416880061C133C5941E22A4FAF73D62E4103C2FCE7113C5941	0	2.7
91	35	2	35	2	0106000020E86400000100000001030000000100000007000000E22A4FAF73D62E4103C2FCE7113C59411AA71A1E83D62E4171FF2947153C5941A8A4B71694D62E416DD30112143C5941D7CFC0649FD62E411549538A163C59417B698E837DD62E4168D677F3183C5941B4C29AC962D62E416880061C133C5941E22A4FAF73D62E4103C2FCE7113C5941	3	2.7
92	47	1	47	2	0106000020E86400000100000001030000000200000005000000D2152B4E66D62E41F72543A74E3C5941BA77E2B599D62E41C8D04D52533C5941693F7A2801D72E41BEB574B7473C59415C20179BB6D62E41096620DF403C5941D2152B4E66D62E41F72543A74E3C5941050000009CE524A18FD62E41EA21990B4D3C5941039688C6B3D62E41FFE01EF8463C5941741762B2CED62E41328AAA7A493C594168DFBADF9ED62E41D625D28D4E3C59419CE524A18FD62E41EA21990B4D3C5941	0	2.7
93	47	2	47	2	0106000020E86400000100000001030000000200000005000000D2152B4E66D62E41F72543A74E3C5941BA77E2B599D62E41C8D04D52533C5941693F7A2801D72E41BEB574B7473C59415C20179BB6D62E41096620DF403C5941D2152B4E66D62E41F72543A74E3C5941050000009CE524A18FD62E41EA21990B4D3C5941039688C6B3D62E41FFE01EF8463C5941741762B2CED62E41328AAA7A493C594168DFBADF9ED62E41D625D28D4E3C59419CE524A18FD62E41EA21990B4D3C5941	3	2.7
94	47	3	47	2	0106000020E86400000100000001030000000200000005000000D2152B4E66D62E41F72543A74E3C5941BA77E2B599D62E41C8D04D52533C5941693F7A2801D72E41BEB574B7473C59415C20179BB6D62E41096620DF403C5941D2152B4E66D62E41F72543A74E3C5941050000009CE524A18FD62E41EA21990B4D3C5941039688C6B3D62E41FFE01EF8463C5941741762B2CED62E41328AAA7A493C594168DFBADF9ED62E41D625D28D4E3C59419CE524A18FD62E41EA21990B4D3C5941	6	2.7
95	47	4	47	2	0106000020E86400000100000001030000000200000005000000D2152B4E66D62E41F72543A74E3C5941BA77E2B599D62E41C8D04D52533C5941693F7A2801D72E41BEB574B7473C59415C20179BB6D62E41096620DF403C5941D2152B4E66D62E41F72543A74E3C5941050000009CE524A18FD62E41EA21990B4D3C5941039688C6B3D62E41FFE01EF8463C5941741762B2CED62E41328AAA7A493C594168DFBADF9ED62E41D625D28D4E3C59419CE524A18FD62E41EA21990B4D3C5941	9	2.7
96	47	5	47	2	0106000020E86400000100000001030000000200000005000000D2152B4E66D62E41F72543A74E3C5941BA77E2B599D62E41C8D04D52533C5941693F7A2801D72E41BEB574B7473C59415C20179BB6D62E41096620DF403C5941D2152B4E66D62E41F72543A74E3C5941050000009CE524A18FD62E41EA21990B4D3C5941039688C6B3D62E41FFE01EF8463C5941741762B2CED62E41328AAA7A493C594168DFBADF9ED62E41D625D28D4E3C59419CE524A18FD62E41EA21990B4D3C5941	12	2.7
97	47	6	47	2	0106000020E86400000100000001030000000200000005000000D2152B4E66D62E41F72543A74E3C5941BA77E2B599D62E41C8D04D52533C5941693F7A2801D72E41BEB574B7473C59415C20179BB6D62E41096620DF403C5941D2152B4E66D62E41F72543A74E3C5941050000009CE524A18FD62E41EA21990B4D3C5941039688C6B3D62E41FFE01EF8463C5941741762B2CED62E41328AAA7A493C594168DFBADF9ED62E41D625D28D4E3C59419CE524A18FD62E41EA21990B4D3C5941	15	2.7
98	47	7	47	2	0106000020E86400000100000001030000000200000005000000D2152B4E66D62E41F72543A74E3C5941BA77E2B599D62E41C8D04D52533C5941693F7A2801D72E41BEB574B7473C59415C20179BB6D62E41096620DF403C5941D2152B4E66D62E41F72543A74E3C5941050000009CE524A18FD62E41EA21990B4D3C5941039688C6B3D62E41FFE01EF8463C5941741762B2CED62E41328AAA7A493C594168DFBADF9ED62E41D625D28D4E3C59419CE524A18FD62E41EA21990B4D3C5941	18	2.7
99	12	1	12	2	0106000020E8640000010000000103000000010000000500000086A0FF37A3D72E4188097686533C5941C8B464DC9CD72E41C60813F4503C5941FA5C77FFBDD72E41B5F0F28C4F3C59415C4A1E21C4D72E4158BD7754523C594186A0FF37A3D72E4188097686533C5941	0	2.7
100	12	2	12	2	0106000020E8640000010000000103000000010000000500000086A0FF37A3D72E4188097686533C5941C8B464DC9CD72E41C60813F4503C5941FA5C77FFBDD72E41B5F0F28C4F3C59415C4A1E21C4D72E4158BD7754523C594186A0FF37A3D72E4188097686533C5941	3	2.7
101	12	3	12	2	0106000020E8640000010000000103000000010000000500000086A0FF37A3D72E4188097686533C5941C8B464DC9CD72E41C60813F4503C5941FA5C77FFBDD72E41B5F0F28C4F3C59415C4A1E21C4D72E4158BD7754523C594186A0FF37A3D72E4188097686533C5941	6	2.7
102	13	1	13	2	0106000020E864000001000000010300000001000000050000001C1DA2F809D82E417C2D82AF173C5941EE4F165A31D82E4184AEF8071F3C5941F2CAAC0919D82E41F681850F213C59416ECEFBA8F1D72E4147BF5AB6193C59411C1DA2F809D82E417C2D82AF173C5941	0	2.7
103	13	2	13	2	0106000020E864000001000000010300000001000000050000001C1DA2F809D82E417C2D82AF173C5941EE4F165A31D82E4184AEF8071F3C5941F2CAAC0919D82E41F681850F213C59416ECEFBA8F1D72E4147BF5AB6193C59411C1DA2F809D82E417C2D82AF173C5941	3	2.7
104	13	3	13	2	0106000020E864000001000000010300000001000000050000001C1DA2F809D82E417C2D82AF173C5941EE4F165A31D82E4184AEF8071F3C5941F2CAAC0919D82E41F681850F213C59416ECEFBA8F1D72E4147BF5AB6193C59411C1DA2F809D82E417C2D82AF173C5941	6	2.7
105	13	4	13	2	0106000020E864000001000000010300000001000000050000001C1DA2F809D82E417C2D82AF173C5941EE4F165A31D82E4184AEF8071F3C5941F2CAAC0919D82E41F681850F213C59416ECEFBA8F1D72E4147BF5AB6193C59411C1DA2F809D82E417C2D82AF173C5941	9	2.7
106	13	5	13	2	0106000020E864000001000000010300000001000000050000001C1DA2F809D82E417C2D82AF173C5941EE4F165A31D82E4184AEF8071F3C5941F2CAAC0919D82E41F681850F213C59416ECEFBA8F1D72E4147BF5AB6193C59411C1DA2F809D82E417C2D82AF173C5941	12	2.7
107	13	6	13	2	0106000020E864000001000000010300000001000000050000001C1DA2F809D82E417C2D82AF173C5941EE4F165A31D82E4184AEF8071F3C5941F2CAAC0919D82E41F681850F213C59416ECEFBA8F1D72E4147BF5AB6193C59411C1DA2F809D82E417C2D82AF173C5941	15	2.7
108	14	1	14	2	0106000020E86400000100000001030000000100000005000000947C947B72D72E4102A981FA353C5941C1C6ABFF1DD72E41DA59AEF92E3C59419A58B3902CD72E418BA9563C2C3C59415A01AA0C81D72E41ED452B3D333C5941947C947B72D72E4102A981FA353C5941	0	2.7
109	14	2	14	2	0106000020E86400000100000001030000000100000005000000947C947B72D72E4102A981FA353C5941C1C6ABFF1DD72E41DA59AEF92E3C59419A58B3902CD72E418BA9563C2C3C59415A01AA0C81D72E41ED452B3D333C5941947C947B72D72E4102A981FA353C5941	3	2.7
110	14	3	14	2	0106000020E86400000100000001030000000100000005000000947C947B72D72E4102A981FA353C5941C1C6ABFF1DD72E41DA59AEF92E3C59419A58B3902CD72E418BA9563C2C3C59415A01AA0C81D72E41ED452B3D333C5941947C947B72D72E4102A981FA353C5941	6	2.7
111	14	4	14	2	0106000020E86400000100000001030000000100000005000000947C947B72D72E4102A981FA353C5941C1C6ABFF1DD72E41DA59AEF92E3C59419A58B3902CD72E418BA9563C2C3C59415A01AA0C81D72E41ED452B3D333C5941947C947B72D72E4102A981FA353C5941	9	2.7
112	14	5	14	2	0106000020E86400000100000001030000000100000005000000947C947B72D72E4102A981FA353C5941C1C6ABFF1DD72E41DA59AEF92E3C59419A58B3902CD72E418BA9563C2C3C59415A01AA0C81D72E41ED452B3D333C5941947C947B72D72E4102A981FA353C5941	12	2.7
113	14	6	14	2	0106000020E86400000100000001030000000100000005000000947C947B72D72E4102A981FA353C5941C1C6ABFF1DD72E41DA59AEF92E3C59419A58B3902CD72E418BA9563C2C3C59415A01AA0C81D72E41ED452B3D333C5941947C947B72D72E4102A981FA353C5941	15	2.7
114	14	7	14	2	0106000020E86400000100000001030000000100000005000000947C947B72D72E4102A981FA353C5941C1C6ABFF1DD72E41DA59AEF92E3C59419A58B3902CD72E418BA9563C2C3C59415A01AA0C81D72E41ED452B3D333C5941947C947B72D72E4102A981FA353C5941	18	2.7
115	15	1	15	2	0106000020E86400000100000001030000000100000005000000565BC051C8D72E41CBB8800D1D3C59418823F45AF7D72E41C77523AA253C594153BC7CC9DBD72E41979A0602283C5941FA902AC3ACD72E417BF771651F3C5941565BC051C8D72E41CBB8800D1D3C5941	0	2.7
116	15	2	15	2	0106000020E86400000100000001030000000100000005000000565BC051C8D72E41CBB8800D1D3C59418823F45AF7D72E41C77523AA253C594153BC7CC9DBD72E41979A0602283C5941FA902AC3ACD72E417BF771651F3C5941565BC051C8D72E41CBB8800D1D3C5941	3	2.7
117	15	3	15	2	0106000020E86400000100000001030000000100000005000000565BC051C8D72E41CBB8800D1D3C59418823F45AF7D72E41C77523AA253C594153BC7CC9DBD72E41979A0602283C5941FA902AC3ACD72E417BF771651F3C5941565BC051C8D72E41CBB8800D1D3C5941	6	2.7
118	15	4	15	2	0106000020E86400000100000001030000000100000005000000565BC051C8D72E41CBB8800D1D3C59418823F45AF7D72E41C77523AA253C594153BC7CC9DBD72E41979A0602283C5941FA902AC3ACD72E417BF771651F3C5941565BC051C8D72E41CBB8800D1D3C5941	9	2.7
119	15	5	15	2	0106000020E86400000100000001030000000100000005000000565BC051C8D72E41CBB8800D1D3C59418823F45AF7D72E41C77523AA253C594153BC7CC9DBD72E41979A0602283C5941FA902AC3ACD72E417BF771651F3C5941565BC051C8D72E41CBB8800D1D3C5941	12	2.7
120	15	6	15	2	0106000020E86400000100000001030000000100000005000000565BC051C8D72E41CBB8800D1D3C59418823F45AF7D72E41C77523AA253C594153BC7CC9DBD72E41979A0602283C5941FA902AC3ACD72E417BF771651F3C5941565BC051C8D72E41CBB8800D1D3C5941	15	2.7
121	16	1	16	2	0106000020E8640000010000000103000000010000000500000094178CA13BD72E41A3A75A313D3C5941422F5598F2D62E41D52AC20C373C59414E6BEE6900D72E410473387D343C5941885D4F7549D72E4109FA93A23A3C594194178CA13BD72E41A3A75A313D3C5941	0	2.7
122	16	2	16	2	0106000020E8640000010000000103000000010000000500000094178CA13BD72E41A3A75A313D3C5941422F5598F2D62E41D52AC20C373C59414E6BEE6900D72E410473387D343C5941885D4F7549D72E4109FA93A23A3C594194178CA13BD72E41A3A75A313D3C5941	3	2.7
123	16	3	16	2	0106000020E8640000010000000103000000010000000500000094178CA13BD72E41A3A75A313D3C5941422F5598F2D62E41D52AC20C373C59414E6BEE6900D72E410473387D343C5941885D4F7549D72E4109FA93A23A3C594194178CA13BD72E41A3A75A313D3C5941	6	2.7
124	16	4	16	2	0106000020E8640000010000000103000000010000000500000094178CA13BD72E41A3A75A313D3C5941422F5598F2D62E41D52AC20C373C59414E6BEE6900D72E410473387D343C5941885D4F7549D72E4109FA93A23A3C594194178CA13BD72E41A3A75A313D3C5941	9	2.7
125	16	5	16	2	0106000020E8640000010000000103000000010000000500000094178CA13BD72E41A3A75A313D3C5941422F5598F2D62E41D52AC20C373C59414E6BEE6900D72E410473387D343C5941885D4F7549D72E4109FA93A23A3C594194178CA13BD72E41A3A75A313D3C5941	12	2.7
126	16	6	16	2	0106000020E8640000010000000103000000010000000500000094178CA13BD72E41A3A75A313D3C5941422F5598F2D62E41D52AC20C373C59414E6BEE6900D72E410473387D343C5941885D4F7549D72E4109FA93A23A3C594194178CA13BD72E41A3A75A313D3C5941	15	2.7
127	16	7	16	2	0106000020E8640000010000000103000000010000000500000094178CA13BD72E41A3A75A313D3C5941422F5598F2D62E41D52AC20C373C59414E6BEE6900D72E410473387D343C5941885D4F7549D72E4109FA93A23A3C594194178CA13BD72E41A3A75A313D3C5941	18	2.7
128	18	1	18	2	0106000020E8640000010000000103000000010000000500000082191E1BC9D62E41B26648783F3C594112E418E9D9D62E41F14884963C3C5941D9B6052118D72E4190A53D2B423C5941639A596006D72E41602E9123453C594182191E1BC9D62E41B26648783F3C5941	0	2.7
129	18	2	18	2	0106000020E8640000010000000103000000010000000500000082191E1BC9D62E41B26648783F3C594112E418E9D9D62E41F14884963C3C5941D9B6052118D72E4190A53D2B423C5941639A596006D72E41602E9123453C594182191E1BC9D62E41B26648783F3C5941	3	2.7
130	18	3	18	2	0106000020E8640000010000000103000000010000000500000082191E1BC9D62E41B26648783F3C594112E418E9D9D62E41F14884963C3C5941D9B6052118D72E4190A53D2B423C5941639A596006D72E41602E9123453C594182191E1BC9D62E41B26648783F3C5941	6	2.7
131	18	4	18	2	0106000020E8640000010000000103000000010000000500000082191E1BC9D62E41B26648783F3C594112E418E9D9D62E41F14884963C3C5941D9B6052118D72E4190A53D2B423C5941639A596006D72E41602E9123453C594182191E1BC9D62E41B26648783F3C5941	9	2.7
132	18	5	18	2	0106000020E8640000010000000103000000010000000500000082191E1BC9D62E41B26648783F3C594112E418E9D9D62E41F14884963C3C5941D9B6052118D72E4190A53D2B423C5941639A596006D72E41602E9123453C594182191E1BC9D62E41B26648783F3C5941	12	2.7
133	18	6	18	2	0106000020E8640000010000000103000000010000000500000082191E1BC9D62E41B26648783F3C594112E418E9D9D62E41F14884963C3C5941D9B6052118D72E4190A53D2B423C5941639A596006D72E41602E9123453C594182191E1BC9D62E41B26648783F3C5941	15	2.7
134	18	7	18	2	0106000020E8640000010000000103000000010000000500000082191E1BC9D62E41B26648783F3C594112E418E9D9D62E41F14884963C3C5941D9B6052118D72E4190A53D2B423C5941639A596006D72E41602E9123453C594182191E1BC9D62E41B26648783F3C5941	18	2.7
135	21	1	21	2	0106000020E8640000010000000103000000010000000C00000089A70F39D7D62E41993A0B62633C5941B77E2F12EED62E41B481AD7B653C5941AAE600DDEAD62E41442F6207663C59415B4FCEF4DDD62E411A542735683C5941113B90F6E4D62E4119F5A4DA683C594180EFB958DDD62E41555AA8236A3C59414680BC5FDAD62E41958C66A36A3C59413AFD997BB5D62E41ECCD2A38673C5941FC291EBFC6D62E41EF923051643C59418057EDCFCDD62E41ADC319F9643C5941258A57D1D3D62E4199F944F6633C594189A70F39D7D62E41993A0B62633C5941	0	2.7
136	21	2	21	2	0106000020E8640000010000000103000000010000000C00000089A70F39D7D62E41993A0B62633C5941B77E2F12EED62E41B481AD7B653C5941AAE600DDEAD62E41442F6207663C59415B4FCEF4DDD62E411A542735683C5941113B90F6E4D62E4119F5A4DA683C594180EFB958DDD62E41555AA8236A3C59414680BC5FDAD62E41958C66A36A3C59413AFD997BB5D62E41ECCD2A38673C5941FC291EBFC6D62E41EF923051643C59418057EDCFCDD62E41ADC319F9643C5941258A57D1D3D62E4199F944F6633C594189A70F39D7D62E41993A0B62633C5941	3	2.7
137	21	3	21	2	0106000020E8640000010000000103000000010000000C00000089A70F39D7D62E41993A0B62633C5941B77E2F12EED62E41B481AD7B653C5941AAE600DDEAD62E41442F6207663C59415B4FCEF4DDD62E411A542735683C5941113B90F6E4D62E4119F5A4DA683C594180EFB958DDD62E41555AA8236A3C59414680BC5FDAD62E41958C66A36A3C59413AFD997BB5D62E41ECCD2A38673C5941FC291EBFC6D62E41EF923051643C59418057EDCFCDD62E41ADC319F9643C5941258A57D1D3D62E4199F944F6633C594189A70F39D7D62E41993A0B62633C5941	6	2.7
138	21	4	21	2	0106000020E8640000010000000103000000010000000C00000089A70F39D7D62E41993A0B62633C5941B77E2F12EED62E41B481AD7B653C5941AAE600DDEAD62E41442F6207663C59415B4FCEF4DDD62E411A542735683C5941113B90F6E4D62E4119F5A4DA683C594180EFB958DDD62E41555AA8236A3C59414680BC5FDAD62E41958C66A36A3C59413AFD997BB5D62E41ECCD2A38673C5941FC291EBFC6D62E41EF923051643C59418057EDCFCDD62E41ADC319F9643C5941258A57D1D3D62E4199F944F6633C594189A70F39D7D62E41993A0B62633C5941	9	2.7
139	21	5	21	2	0106000020E8640000010000000103000000010000000C00000089A70F39D7D62E41993A0B62633C5941B77E2F12EED62E41B481AD7B653C5941AAE600DDEAD62E41442F6207663C59415B4FCEF4DDD62E411A542735683C5941113B90F6E4D62E4119F5A4DA683C594180EFB958DDD62E41555AA8236A3C59414680BC5FDAD62E41958C66A36A3C59413AFD997BB5D62E41ECCD2A38673C5941FC291EBFC6D62E41EF923051643C59418057EDCFCDD62E41ADC319F9643C5941258A57D1D3D62E4199F944F6633C594189A70F39D7D62E41993A0B62633C5941	12	2.7
140	23	1	23	2	0106000020E8640000010000000103000000010000000B00000006EC55A102D72E41A17580846E3C59417AE301002BD72E41BBD5924D723C5941DAEA539937D72E418408D534703C5941801E643C30D72E41B88D67846F3C59411E86BB0440D72E41BB3BA0E56C3C5941208975D824D72E41B467DF596A3C59418DAE81F420D72E419CE2BDFE6A3C5941EC64091118D72E41725FC4796C3C5941E232E03712D72E410E0588ED6B3C5941D111825E06D72E41044777E56D3C594106EC55A102D72E41A17580846E3C5941	0	2.7
141	23	2	23	2	0106000020E8640000010000000103000000010000000B00000006EC55A102D72E41A17580846E3C59417AE301002BD72E41BBD5924D723C5941DAEA539937D72E418408D534703C5941801E643C30D72E41B88D67846F3C59411E86BB0440D72E41BB3BA0E56C3C5941208975D824D72E41B467DF596A3C59418DAE81F420D72E419CE2BDFE6A3C5941EC64091118D72E41725FC4796C3C5941E232E03712D72E410E0588ED6B3C5941D111825E06D72E41044777E56D3C594106EC55A102D72E41A17580846E3C5941	3	2.7
142	23	3	23	2	0106000020E8640000010000000103000000010000000B00000006EC55A102D72E41A17580846E3C59417AE301002BD72E41BBD5924D723C5941DAEA539937D72E418408D534703C5941801E643C30D72E41B88D67846F3C59411E86BB0440D72E41BB3BA0E56C3C5941208975D824D72E41B467DF596A3C59418DAE81F420D72E419CE2BDFE6A3C5941EC64091118D72E41725FC4796C3C5941E232E03712D72E410E0588ED6B3C5941D111825E06D72E41044777E56D3C594106EC55A102D72E41A17580846E3C5941	6	2.7
143	23	4	23	2	0106000020E8640000010000000103000000010000000B00000006EC55A102D72E41A17580846E3C59417AE301002BD72E41BBD5924D723C5941DAEA539937D72E418408D534703C5941801E643C30D72E41B88D67846F3C59411E86BB0440D72E41BB3BA0E56C3C5941208975D824D72E41B467DF596A3C59418DAE81F420D72E419CE2BDFE6A3C5941EC64091118D72E41725FC4796C3C5941E232E03712D72E410E0588ED6B3C5941D111825E06D72E41044777E56D3C594106EC55A102D72E41A17580846E3C5941	9	2.7
144	23	5	23	2	0106000020E8640000010000000103000000010000000B00000006EC55A102D72E41A17580846E3C59417AE301002BD72E41BBD5924D723C5941DAEA539937D72E418408D534703C5941801E643C30D72E41B88D67846F3C59411E86BB0440D72E41BB3BA0E56C3C5941208975D824D72E41B467DF596A3C59418DAE81F420D72E419CE2BDFE6A3C5941EC64091118D72E41725FC4796C3C5941E232E03712D72E410E0588ED6B3C5941D111825E06D72E41044777E56D3C594106EC55A102D72E41A17580846E3C5941	12	2.7
145	34	1	34	2	0106000020E864000001000000010300000001000000080000000C49BA81ADD62E415D4920BE543C5941CFBCDE99C5D62E413C697E2C523C59417834A286D0D62E41D7D1603A533C5941429CF670E6D62E41C2B7A48C513C5941BB0AC495F6D62E41BEEDC1C0543C5941E92BE715E5D62E4172A50E21563C5941E0CA7DE4D7D62E41D960119A583C59410C49BA81ADD62E415D4920BE543C5941	0	2.7
146	34	2	34	2	0106000020E864000001000000010300000001000000080000000C49BA81ADD62E415D4920BE543C5941CFBCDE99C5D62E413C697E2C523C59417834A286D0D62E41D7D1603A533C5941429CF670E6D62E41C2B7A48C513C5941BB0AC495F6D62E41BEEDC1C0543C5941E92BE715E5D62E4172A50E21563C5941E0CA7DE4D7D62E41D960119A583C59410C49BA81ADD62E415D4920BE543C5941	3	2.7
147	34	3	34	2	0106000020E864000001000000010300000001000000080000000C49BA81ADD62E415D4920BE543C5941CFBCDE99C5D62E413C697E2C523C59417834A286D0D62E41D7D1603A533C5941429CF670E6D62E41C2B7A48C513C5941BB0AC495F6D62E41BEEDC1C0543C5941E92BE715E5D62E4172A50E21563C5941E0CA7DE4D7D62E41D960119A583C59410C49BA81ADD62E415D4920BE543C5941	6	2.7
148	34	4	34	2	0106000020E864000001000000010300000001000000080000000C49BA81ADD62E415D4920BE543C5941CFBCDE99C5D62E413C697E2C523C59417834A286D0D62E41D7D1603A533C5941429CF670E6D62E41C2B7A48C513C5941BB0AC495F6D62E41BEEDC1C0543C5941E92BE715E5D62E4172A50E21563C5941E0CA7DE4D7D62E41D960119A583C59410C49BA81ADD62E415D4920BE543C5941	9	2.7
149	36	1	36	2	0106000020E86400000100000001030000000100000005000000429CF670E6D62E41C2B7A48C513C5941B1A5FEBF0DD72E41206A778F4E3C5941F5FD3EAA20D72E41E7036C70513C5941BB0AC495F6D62E41BEEDC1C0543C5941429CF670E6D62E41C2B7A48C513C5941	0	2.7
150	36	2	36	2	0106000020E86400000100000001030000000100000005000000429CF670E6D62E41C2B7A48C513C5941B1A5FEBF0DD72E41206A778F4E3C5941F5FD3EAA20D72E41E7036C70513C5941BB0AC495F6D62E41BEEDC1C0543C5941429CF670E6D62E41C2B7A48C513C5941	3	2.7
151	36	3	36	2	0106000020E86400000100000001030000000100000005000000429CF670E6D62E41C2B7A48C513C5941B1A5FEBF0DD72E41206A778F4E3C5941F5FD3EAA20D72E41E7036C70513C5941BB0AC495F6D62E41BEEDC1C0543C5941429CF670E6D62E41C2B7A48C513C5941	6	2.7
152	37	1	37	2	0106000020E8640000010000000103000000010000000500000088ED1F6A46D72E412D552A434D3C5941F5FD3EAA20D72E41E7036C70513C5941B1A5FEBF0DD72E41206A778F4E3C59419EDD637133D72E415BA0C86C4A3C594188ED1F6A46D72E412D552A434D3C5941	0	2.7
153	37	2	37	2	0106000020E8640000010000000103000000010000000500000088ED1F6A46D72E412D552A434D3C5941F5FD3EAA20D72E41E7036C70513C5941B1A5FEBF0DD72E41206A778F4E3C59419EDD637133D72E415BA0C86C4A3C594188ED1F6A46D72E412D552A434D3C5941	3	2.7
154	37	3	37	2	0106000020E8640000010000000103000000010000000500000088ED1F6A46D72E412D552A434D3C5941F5FD3EAA20D72E41E7036C70513C5941B1A5FEBF0DD72E41206A778F4E3C59419EDD637133D72E415BA0C86C4A3C594188ED1F6A46D72E412D552A434D3C5941	6	2.7
155	37	4	37	2	0106000020E8640000010000000103000000010000000500000088ED1F6A46D72E412D552A434D3C5941F5FD3EAA20D72E41E7036C70513C5941B1A5FEBF0DD72E41206A778F4E3C59419EDD637133D72E415BA0C86C4A3C594188ED1F6A46D72E412D552A434D3C5941	9	2.7
156	37	5	37	2	0106000020E8640000010000000103000000010000000500000088ED1F6A46D72E412D552A434D3C5941F5FD3EAA20D72E41E7036C70513C5941B1A5FEBF0DD72E41206A778F4E3C59419EDD637133D72E415BA0C86C4A3C594188ED1F6A46D72E412D552A434D3C5941	12	2.7
157	38	1	38	2	0106000020E8640000010000000103000000010000000B000000B50C269E36D72E41C1D7B641463C5941FAC0D3E145D72E41D9567C70443C5941B2B8E13144D72E416CF79D36443C5941141655DA5ED72E417FF13024413C5941B5761EF571D72E415A6AC2C5433C59416C1F6C3B62D72E419A46AB76453C594158E564FE76D72E4126DB3059483C5941060984AA69D72E418E1F32B8493C5941B2E3DDED67D72E411613F56E493C594112E06E3A57D72E41EB63381F4B3C5941B50C269E36D72E41C1D7B641463C5941	0	2.7
158	38	2	38	2	0106000020E8640000010000000103000000010000000B000000B50C269E36D72E41C1D7B641463C5941FAC0D3E145D72E41D9567C70443C5941B2B8E13144D72E416CF79D36443C5941141655DA5ED72E417FF13024413C5941B5761EF571D72E415A6AC2C5433C59416C1F6C3B62D72E419A46AB76453C594158E564FE76D72E4126DB3059483C5941060984AA69D72E418E1F32B8493C5941B2E3DDED67D72E411613F56E493C594112E06E3A57D72E41EB63381F4B3C5941B50C269E36D72E41C1D7B641463C5941	3	2.7
159	38	3	38	2	0106000020E8640000010000000103000000010000000B000000B50C269E36D72E41C1D7B641463C5941FAC0D3E145D72E41D9567C70443C5941B2B8E13144D72E416CF79D36443C5941141655DA5ED72E417FF13024413C5941B5761EF571D72E415A6AC2C5433C59416C1F6C3B62D72E419A46AB76453C594158E564FE76D72E4126DB3059483C5941060984AA69D72E418E1F32B8493C5941B2E3DDED67D72E411613F56E493C594112E06E3A57D72E41EB63381F4B3C5941B50C269E36D72E41C1D7B641463C5941	6	2.7
160	38	4	38	2	0106000020E8640000010000000103000000010000000B000000B50C269E36D72E41C1D7B641463C5941FAC0D3E145D72E41D9567C70443C5941B2B8E13144D72E416CF79D36443C5941141655DA5ED72E417FF13024413C5941B5761EF571D72E415A6AC2C5433C59416C1F6C3B62D72E419A46AB76453C594158E564FE76D72E4126DB3059483C5941060984AA69D72E418E1F32B8493C5941B2E3DDED67D72E411613F56E493C594112E06E3A57D72E41EB63381F4B3C5941B50C269E36D72E41C1D7B641463C5941	9	2.7
161	38	5	38	2	0106000020E8640000010000000103000000010000000B000000B50C269E36D72E41C1D7B641463C5941FAC0D3E145D72E41D9567C70443C5941B2B8E13144D72E416CF79D36443C5941141655DA5ED72E417FF13024413C5941B5761EF571D72E415A6AC2C5433C59416C1F6C3B62D72E419A46AB76453C594158E564FE76D72E4126DB3059483C5941060984AA69D72E418E1F32B8493C5941B2E3DDED67D72E411613F56E493C594112E06E3A57D72E41EB63381F4B3C5941B50C269E36D72E41C1D7B641463C5941	12	2.7
162	39	1	39	2	0106000020E8640000010000000103000000010000000500000000D1998773D72E41C61BCF573F3C594198AFE5EC82D72E413290D3823D3C5941B58D77C39DD72E41C9818340413C594196CDF1CB8DD72E41D2FB172A433C594100D1998773D72E41C61BCF573F3C5941	0	2.7
163	39	2	39	2	0106000020E8640000010000000103000000010000000500000000D1998773D72E41C61BCF573F3C594198AFE5EC82D72E413290D3823D3C5941B58D77C39DD72E41C9818340413C594196CDF1CB8DD72E41D2FB172A433C594100D1998773D72E41C61BCF573F3C5941	3	2.7
164	39	3	39	2	0106000020E8640000010000000103000000010000000500000000D1998773D72E41C61BCF573F3C594198AFE5EC82D72E413290D3823D3C5941B58D77C39DD72E41C9818340413C594196CDF1CB8DD72E41D2FB172A433C594100D1998773D72E41C61BCF573F3C5941	6	2.7
165	39	4	39	2	0106000020E8640000010000000103000000010000000500000000D1998773D72E41C61BCF573F3C594198AFE5EC82D72E413290D3823D3C5941B58D77C39DD72E41C9818340413C594196CDF1CB8DD72E41D2FB172A433C594100D1998773D72E41C61BCF573F3C5941	9	2.7
166	42	1	42	2	0106000020E8640000010000000103000000010000000500000070D8CEF394D72E41283891603B3C59413B750B13A6D72E41ABEC8A68393C5941D79A060DC2D72E41CD7ABE363D3C5941D0B57B85AFD72E41DBE3B73F3F3C594170D8CEF394D72E41283891603B3C5941	0	2.7
167	42	2	42	2	0106000020E8640000010000000103000000010000000500000070D8CEF394D72E41283891603B3C59413B750B13A6D72E41ABEC8A68393C5941D79A060DC2D72E41CD7ABE363D3C5941D0B57B85AFD72E41DBE3B73F3F3C594170D8CEF394D72E41283891603B3C5941	3	2.7
168	42	3	42	2	0106000020E8640000010000000103000000010000000500000070D8CEF394D72E41283891603B3C59413B750B13A6D72E41ABEC8A68393C5941D79A060DC2D72E41CD7ABE363D3C5941D0B57B85AFD72E41DBE3B73F3F3C594170D8CEF394D72E41283891603B3C5941	6	2.7
169	42	4	42	2	0106000020E8640000010000000103000000010000000500000070D8CEF394D72E41283891603B3C59413B750B13A6D72E41ABEC8A68393C5941D79A060DC2D72E41CD7ABE363D3C5941D0B57B85AFD72E41DBE3B73F3F3C594170D8CEF394D72E41283891603B3C5941	9	2.7
170	44	1	44	2	0106000020E864000001000000010300000001000000050000009EFD87B7B8D72E416E740F60373C594188CBF243CAD72E4194627175353C594120BBA688E5D72E415BB6F33C393C594186F29EAAD3D72E411FD1A8393B3C59419EFD87B7B8D72E416E740F60373C5941	0	2.7
171	44	2	44	2	0106000020E864000001000000010300000001000000050000009EFD87B7B8D72E416E740F60373C594188CBF243CAD72E4194627175353C594120BBA688E5D72E415BB6F33C393C594186F29EAAD3D72E411FD1A8393B3C59419EFD87B7B8D72E416E740F60373C5941	3	2.7
172	44	3	44	2	0106000020E864000001000000010300000001000000050000009EFD87B7B8D72E416E740F60373C594188CBF243CAD72E4194627175353C594120BBA688E5D72E415BB6F33C393C594186F29EAAD3D72E411FD1A8393B3C59419EFD87B7B8D72E416E740F60373C5941	6	2.7
173	44	4	44	2	0106000020E864000001000000010300000001000000050000009EFD87B7B8D72E416E740F60373C594188CBF243CAD72E4194627175353C594120BBA688E5D72E415BB6F33C393C594186F29EAAD3D72E411FD1A8393B3C59419EFD87B7B8D72E416E740F60373C5941	9	2.7
174	46	1	46	2	0106000020E8640000010000000103000000010000000900000090132A6507D82E414A3C2565303C5941C85FB8D713D82E415BAB6BFF2E3C5941F2F500EC16D82E41992BA5772F3C59417CD573A71BD82E410B75B7E22E3C5941267DA31C2AD82E41E825B1F9303C5941B259718B1CD82E4121B61073323C594180C8B4F718D82E417A6AE8E5313C5941F60C291915D82E416CABB24F323C594190132A6507D82E414A3C2565303C5941	0	2.7
175	46	2	46	2	0106000020E8640000010000000103000000010000000900000090132A6507D82E414A3C2565303C5941C85FB8D713D82E415BAB6BFF2E3C5941F2F500EC16D82E41992BA5772F3C59417CD573A71BD82E410B75B7E22E3C5941267DA31C2AD82E41E825B1F9303C5941B259718B1CD82E4121B61073323C594180C8B4F718D82E417A6AE8E5313C5941F60C291915D82E416CABB24F323C594190132A6507D82E414A3C2565303C5941	3	2.7
176	46	3	46	2	0106000020E8640000010000000103000000010000000900000090132A6507D82E414A3C2565303C5941C85FB8D713D82E415BAB6BFF2E3C5941F2F500EC16D82E41992BA5772F3C59417CD573A71BD82E410B75B7E22E3C5941267DA31C2AD82E41E825B1F9303C5941B259718B1CD82E4121B61073323C594180C8B4F718D82E417A6AE8E5313C5941F60C291915D82E416CABB24F323C594190132A6507D82E414A3C2565303C5941	6	2.7
177	17	1	17	2	0106000020E864000001000000010300000001000000050000001643B044A5D72E41D4ACCEC12E3C5941737E24CD6CD72E4155D2913F243C59412C7E8B4585D72E41A98DA233223C5941AD4B69B9BDD72E41DFB989B62C3C59411643B044A5D72E41D4ACCEC12E3C5941	0	2.7
178	17	2	17	2	0106000020E864000001000000010300000001000000050000001643B044A5D72E41D4ACCEC12E3C5941737E24CD6CD72E4155D2913F243C59412C7E8B4585D72E41A98DA233223C5941AD4B69B9BDD72E41DFB989B62C3C59411643B044A5D72E41D4ACCEC12E3C5941	3	2.7
179	17	3	17	2	0106000020E864000001000000010300000001000000050000001643B044A5D72E41D4ACCEC12E3C5941737E24CD6CD72E4155D2913F243C59412C7E8B4585D72E41A98DA233223C5941AD4B69B9BDD72E41DFB989B62C3C59411643B044A5D72E41D4ACCEC12E3C5941	6	2.7
180	17	4	17	2	0106000020E864000001000000010300000001000000050000001643B044A5D72E41D4ACCEC12E3C5941737E24CD6CD72E4155D2913F243C59412C7E8B4585D72E41A98DA233223C5941AD4B69B9BDD72E41DFB989B62C3C59411643B044A5D72E41D4ACCEC12E3C5941	9	2.7
181	17	5	17	2	0106000020E864000001000000010300000001000000050000001643B044A5D72E41D4ACCEC12E3C5941737E24CD6CD72E4155D2913F243C59412C7E8B4585D72E41A98DA233223C5941AD4B69B9BDD72E41DFB989B62C3C59411643B044A5D72E41D4ACCEC12E3C5941	12	2.7
182	17	6	17	2	0106000020E864000001000000010300000001000000050000001643B044A5D72E41D4ACCEC12E3C5941737E24CD6CD72E4155D2913F243C59412C7E8B4585D72E41A98DA233223C5941AD4B69B9BDD72E41DFB989B62C3C59411643B044A5D72E41D4ACCEC12E3C5941	15	2.7
183	43	1	43	2	0106000020E86400000100000001030000000100000005000000FCBE6CEDEDD72E4119EEE6EC3E3C59412740BA4501D82E41B3A611CC3C3C5941802FFFA51ED82E41CE3BDDF9403C59410651C9650BD82E416D395222433C5941FCBE6CEDEDD72E4119EEE6EC3E3C5941	0	2.7
184	43	2	43	2	0106000020E86400000100000001030000000100000005000000FCBE6CEDEDD72E4119EEE6EC3E3C59412740BA4501D82E41B3A611CC3C3C5941802FFFA51ED82E41CE3BDDF9403C59410651C9650BD82E416D395222433C5941FCBE6CEDEDD72E4119EEE6EC3E3C5941	3	2.7
185	43	3	43	2	0106000020E86400000100000001030000000100000005000000FCBE6CEDEDD72E4119EEE6EC3E3C59412740BA4501D82E41B3A611CC3C3C5941802FFFA51ED82E41CE3BDDF9403C59410651C9650BD82E416D395222433C5941FCBE6CEDEDD72E4119EEE6EC3E3C5941	6	2.7
186	45	1	45	2	0106000020E86400000100000001030000000100000009000000BEDDE817BED72E41CE968BEE493C59416A4BF227BCD72E41EBC45A384A3C594192BA4A13AFD72E4108ED1A6E483C59414AD7D78AB1D72E41830C8E21483C59412E7B18BDABD72E41CA957457473C594169B9A176BCD72E4106CC1E79453C5941C1919DBDD4D72E415CA8DBF9483C5941361E30C9C4D72E419DF6C6D54A3C5941BEDDE817BED72E41CE968BEE493C5941	0	2.7
187	45	2	45	2	0106000020E86400000100000001030000000100000009000000BEDDE817BED72E41CE968BEE493C59416A4BF227BCD72E41EBC45A384A3C594192BA4A13AFD72E4108ED1A6E483C59414AD7D78AB1D72E41830C8E21483C59412E7B18BDABD72E41CA957457473C594169B9A176BCD72E4106CC1E79453C5941C1919DBDD4D72E415CA8DBF9483C5941361E30C9C4D72E419DF6C6D54A3C5941BEDDE817BED72E41CE968BEE493C5941	3	2.7
188	45	3	45	2	0106000020E86400000100000001030000000100000009000000BEDDE817BED72E41CE968BEE493C59416A4BF227BCD72E41EBC45A384A3C594192BA4A13AFD72E4108ED1A6E483C59414AD7D78AB1D72E41830C8E21483C59412E7B18BDABD72E41CA957457473C594169B9A176BCD72E4106CC1E79453C5941C1919DBDD4D72E415CA8DBF9483C5941361E30C9C4D72E419DF6C6D54A3C5941BEDDE817BED72E41CE968BEE493C5941	6	2.7
189	25	11	25	3	0106000020E86400000100000001030000000100000005000000FB03DFE24AD62E4129572D8C5C3C59418B262C6368D62E41B2FBA08C573C59415E5F8ECD5DD62E41D4594896563C59413FE5C42A3CD62E41D633A30F593C5941FB03DFE24AD62E4129572D8C5C3C5941	0	2.7
190	25	12	25	3	0106000020E86400000100000001030000000100000005000000FB03DFE24AD62E4129572D8C5C3C59418B262C6368D62E41B2FBA08C573C59415E5F8ECD5DD62E41D4594896563C59413FE5C42A3CD62E41D633A30F593C5941FB03DFE24AD62E4129572D8C5C3C5941	3	2.7
191	25	1	25	3	0106000020E86400000100000001030000000100000006000000E8C7344A6AD62E41EF76DB5C5F3C5941A7C8872F7AD62E414E7952D15C3C59410176BAA988D62E4166D3D27B5A3C59418B262C6368D62E41B2FBA08C573C5941FB03DFE24AD62E4129572D8C5C3C5941E8C7344A6AD62E41EF76DB5C5F3C5941	0	2.7
192	25	2	25	3	0106000020E86400000100000001030000000100000006000000E8C7344A6AD62E41EF76DB5C5F3C5941A7C8872F7AD62E414E7952D15C3C59410176BAA988D62E4166D3D27B5A3C59418B262C6368D62E41B2FBA08C573C5941FB03DFE24AD62E4129572D8C5C3C5941E8C7344A6AD62E41EF76DB5C5F3C5941	3	2.7
193	25	3	25	3	0106000020E86400000100000001030000000100000006000000E8C7344A6AD62E41EF76DB5C5F3C5941A7C8872F7AD62E414E7952D15C3C59410176BAA988D62E4166D3D27B5A3C59418B262C6368D62E41B2FBA08C573C5941FB03DFE24AD62E4129572D8C5C3C5941E8C7344A6AD62E41EF76DB5C5F3C5941	6	2.7
194	25	4	25	3	0106000020E86400000100000001030000000100000006000000E8C7344A6AD62E41EF76DB5C5F3C5941A7C8872F7AD62E414E7952D15C3C59410176BAA988D62E4166D3D27B5A3C59418B262C6368D62E41B2FBA08C573C5941FB03DFE24AD62E4129572D8C5C3C5941E8C7344A6AD62E41EF76DB5C5F3C5941	9	2.7
195	25	5	25	3	0106000020E86400000100000001030000000100000006000000E8C7344A6AD62E41EF76DB5C5F3C5941A7C8872F7AD62E414E7952D15C3C59410176BAA988D62E4166D3D27B5A3C59418B262C6368D62E41B2FBA08C573C5941FB03DFE24AD62E4129572D8C5C3C5941E8C7344A6AD62E41EF76DB5C5F3C5941	12	2.7
196	25	6	25	3	0106000020E86400000100000001030000000100000006000000E8C7344A6AD62E41EF76DB5C5F3C5941A7C8872F7AD62E414E7952D15C3C59410176BAA988D62E4166D3D27B5A3C59418B262C6368D62E41B2FBA08C573C5941FB03DFE24AD62E4129572D8C5C3C5941E8C7344A6AD62E41EF76DB5C5F3C5941	15	2.7
197	25	7	25	3	0106000020E86400000100000001030000000100000006000000E8C7344A6AD62E41EF76DB5C5F3C5941A7C8872F7AD62E414E7952D15C3C59410176BAA988D62E4166D3D27B5A3C59418B262C6368D62E41B2FBA08C573C5941FB03DFE24AD62E4129572D8C5C3C5941E8C7344A6AD62E41EF76DB5C5F3C5941	18	2.7
198	25	8	25	3	0106000020E86400000100000001030000000100000006000000E8C7344A6AD62E41EF76DB5C5F3C5941A7C8872F7AD62E414E7952D15C3C59410176BAA988D62E4166D3D27B5A3C59418B262C6368D62E41B2FBA08C573C5941FB03DFE24AD62E4129572D8C5C3C5941E8C7344A6AD62E41EF76DB5C5F3C5941	21	2.7
199	25	9	25	3	0106000020E86400000100000001030000000100000006000000E8C7344A6AD62E41EF76DB5C5F3C5941A7C8872F7AD62E414E7952D15C3C59410176BAA988D62E4166D3D27B5A3C59418B262C6368D62E41B2FBA08C573C5941FB03DFE24AD62E4129572D8C5C3C5941E8C7344A6AD62E41EF76DB5C5F3C5941	24	2.7
200	25	10	25	3	0106000020E86400000100000001030000000100000006000000E8C7344A6AD62E41EF76DB5C5F3C5941A7C8872F7AD62E414E7952D15C3C59410176BAA988D62E4166D3D27B5A3C59418B262C6368D62E41B2FBA08C573C5941FB03DFE24AD62E4129572D8C5C3C5941E8C7344A6AD62E41EF76DB5C5F3C5941	27	2.7
201	25	13	25	3	0106000020E86400000100000001030000000100000005000000A7C8872F7AD62E414E7952D15C3C59415CD8EFC196D62E41DA46B26E5F3C5941B0FE713AA4D62E41708463FD5C3C59410176BAA988D62E4166D3D27B5A3C5941A7C8872F7AD62E414E7952D15C3C5941	0	2.7
202	25	14	25	3	0106000020E86400000100000001030000000100000005000000A7C8872F7AD62E414E7952D15C3C59415CD8EFC196D62E41DA46B26E5F3C5941B0FE713AA4D62E41708463FD5C3C59410176BAA988D62E4166D3D27B5A3C5941A7C8872F7AD62E414E7952D15C3C5941	3	2.7
\.

--
-- Data for Name: climate; Type: TABLE DATA; Schema: base1;
--

COPY base1.climate (id, name, file_name, latitude, longitude, timezone, height) FROM stdin;
1	Solna	$districts_path$\\climate\\BROMMA.PRN	59.366	-17.9999	-1	27
\.


--
-- Data for Name: customer_connections; Type: TABLE DATA; Schema: base1;
--

COPY base1.customer_connections (id, cid, c_seq, lid) FROM stdin;
665	1	1	10000026
666	2	1	618
667	3	1	605
668	4	1	10000011
669	5	1	10000013
670	6	1	584
671	7	1	582
672	8	1	600
673	9	1	578
674	10	1	658
675	11	1	624
676	12	1	614
677	13	1	10000028
678	14	1	10000007
679	15	1	10000018
680	16	1	589
681	17	1	593
682	18	1	671
683	19	1	602
684	20	1	596
685	21	1	10000009
686	22	1	10000016
687	23	1	10000015
688	25	1	664
689	27	1	621
690	28	1	10000021
691	29	1	612
692	30	1	10000006
693	31	1	10000019
694	32	1	10000023
695	34	1	630
696	35	1	10000024
697	36	1	629
698	37	1	603
699	38	1	637
700	39	1	615
701	40	1	651
702	41	1	617
703	42	1	645
704	43	1	10000008
705	44	1	650
706	45	1	634
707	46	1	648
708	47	1	675
\.

--
-- Data for Name: lines; Type: TABLE DATA; Schema: base1;
--

COPY base1.lines (id, geom, network, type, pipe_bundle_type_id, zeta, submodel) FROM stdin;
567	01020000A0E864000004000000102FEB06A6D72E417F2BE5E36C3C5941000000000000394054581622AFD72E415EB90B2B6B3C594100000000000039408C9002C2B0D72E4132DC43DC6A3C594100000000000039403487B360F5D72E416849F5E4623C59410000000000003A40	1	2	2	\N	{1}
568	01020000A0E864000002000000CA0914A742D62E4188194A9C503C59410000000000003C4011D609944ED62E41E19F66DB4E3C59410000000000003C40	1	2	3	\N	{1}
570	01020000A0E864000004000000EFD6A5A3CED62E411592DADB5D3C59410000000000003B400D98EEC4BED62E4162B540D15E3C59410000000000003B40242A5CD8B8D62E419F46502C5F3C59410000000000003B4071340294A6D62E4160195246613C59410000000000003B40	1	2	4	\N	{1}
577	01020000A0E864000004000000B859A4EFDCD62E412E9425355B3C59410000000000003A4074A016CEEBD62E41FFC249925C3C59410000000000003A4074A016CEEBD62E41FFC249925C3C59410000000000003A40F097903E46D72E41E23367DE643C59410000000000003A40	1	2	5	\N	{1}
578	01020000A0E864000002000000F097903E46D72E41E23367DE643C59410000000000003A4028BA9C255CD72E4100EB7723613C59410000000000003A40	1	5	4	\N	{1}
579	01020000A0E864000003000000F097903E46D72E41E23367DE643C59410000000000003A40232E840088D72E41D0D7D3E66A3C59410000000000003840102FEB06A6D72E417F2BE5E36C3C59410000000000003940	1	2	4	\N	{1}
582	01020000A0E86400000200000097F30EB71CD82E411C16E978433C594100000000008040406E6202BB34D82E41047520F6463C59410000000000004040	1	5	6	\N	{1}
583	01020000A0E86400000200000084214F42F9D72E4193D61349473C5941000000000000404097F30EB71CD82E411C16E978433C59410000000000804040	1	2	7	\N	{1}
584	01020000A0E86400000200000060216E5E10D82E410B5887E55F3C59410000000000003940645DD5F6FDD72E412606BC4E5D3C59410000000000003940	1	5	8	\N	{1}
588	01020000A0E864000002000000AECD4826E9D62E41E83F0A37343C594100000000000037401E95DCD8FDD62E419527E184303C59410000000000003740	1	2	9	\N	{1}
589	01020000A0E864000003000000AECD4826E9D62E41E83F0A37343C594100000000000037402D546D051ED72E4130ED61D7383C594100000000000039402D546D051ED72E4130ED61D7383C59410000000000003940	1	5	2	\N	{1}
591	01020000A0E8640000040000009403263E30D72E41C3257EB3273C594100000000000036409403263E30D72E41C3257EB3273C59410000000000003640E8D4C8B964D72E419AAB1A222D3C5941000000000000374061FF03D367D72E41D180D3902D3C59410000000000003740	1	2	10	\N	{1}
592	01020000A0E8640000030000001E95DCD8FDD62E419527E184303C594100000000000037409403263E30D72E41C3257EB3273C594100000000000036409403263E30D72E41C3257EB3273C59410000000000003640	1	2	5	\N	{1}
593	01020000A0E86400000200000061FF03D367D72E41D180D3902D3C59410000000000003740BB83544395D72E41E20BB47A283C59410000000000003540	1	5	4	\N	{1}
595	01020000A0E864000003000000AF56A11E9FD62E41C8BD0E26273C59410000000000003740421371C88DD62E414B58B3FE273C594100000000000037402AF0776063D62E41DE0310112A3C59410000000000003740	1	2	4	\N	{1}
596	01020000A0E8640000020000002AF0776063D62E41DE0310112A3C59410000000000003740A836F10073D62E41A49B86102F3C59410000000000003840	1	5	2	\N	{1}
600	01020000A0E8640000020000006963EEBDD4D72E41E1FF74364B3C59410000000000003E402692613DEBD72E41E1AF3A7B4E3C59410000000000003E40	1	5	6	\N	{1}
601	01020000A0E8640000050000001E95DCD8FDD62E419527E184303C59410000000000003740703B2F3DE3D62E412C3DE4332E3C5941000000000000374048691E6EBBD62E41CB03E3C32A3C59410000000000003740A6F0AFBCAAD62E41296878A2283C59410000000000003740AF56A11E9FD62E41C8BD0E26273C59410000000000003740	1	2	5	\N	{1}
602	01020000A0E86400000200000046D5C67468D62E41D0384993193C59410000000000003840D905A11945D62E41432A3AFB1B3C59410000000000003840	1	5	5	\N	{1}
603	01020000A0E8640000020000001F9B089533D72E4137E20382523C59410000000000003940D101C50D2AD72E41FA6AE5EC4D3C59410000000000003B40	1	5	7	\N	{1}
604	01020000A0E864000004000000C52EF72011D72E41F49F256C543C59410000000000003940C52EF72011D72E41F49F256C543C594100000000000039400CA5464522D72E41F0A9FF11533C594100000000000039401F9B089533D72E4137E20382523C59410000000000003940	1	2	4	\N	{1}
605	01020000A0E8640000020000003111694F3FD72E41EE897820523C59410000000000003A4091EFF8F646D72E4172D1E2CE553C59410000000000003A40	1	5	8	\N	{1}
606	01020000A0E8640000020000001F9B089533D72E4137E20382523C594100000000000039403111694F3FD72E41EE897820523C59410000000000003A40	1	2	4	\N	{1}
610	01020000A0E864000002000000766E66B3A0D62E411249EF26413C59410000000000003A40297697E8C5D62E41DF6408823A3C59410000000000003840	1	2	9	\N	{1}
611	01020000A0E86400000300000011D609944ED62E41E19F66DB4E3C59410000000000003C40A1A9F3A555D62E412E4448D14D3C59410000000000003C40766E66B3A0D62E411249EF26413C59410000000000003A40	1	2	9	\N	{1}
612	01020000A0E864000002000000297697E8C5D62E41DF6408823A3C59410000000000003840EA69D979A3D62E41253FBB7E373C59410000000000003840	1	5	4	\N	{1}
613	01020000A0E864000002000000297697E8C5D62E41DF6408823A3C59410000000000003840AECD4826E9D62E41E83F0A37343C59410000000000003740	1	2	9	\N	{1}
614	01020000A0E8640000020000003671D59EAAD72E416F6EF3A34E3C59410000000000003D402AA185BAB0D72E41AA56FA93513C59410000000000003B40	1	5	8	\N	{1}
615	01020000A0E864000002000000B97379B16ED72E4187E3E1C93C3C59410000000000003C40E2DEB79688D72E41E05C8F54403C59410000000000003D40	1	5	6	\N	{1}
616	01020000A0E864000002000000A9E81BEAF7D72E417244186E473C5941000000000000404084214F42F9D72E4193D61349473C59410000000000004040	1	2	2	\N	{1}
617	01020000A0E86400000200000084214F42F9D72E4193D61349473C59410000000000004040F5EAC7B1E3D72E4147780427443C59410000000000004040	1	5	6	\N	{1}
618	01020000A0E864000002000000A9E81BEAF7D72E417244186E473C5941000000000000404060AF5FA410D82E41CD83CC054B3C59410000000000004040	1	5	6	\N	{1}
621	01020000A0E864000002000000855007DA08D62E4131732FE5663C594100000000000040406C51F3D528D62E411899284C693C59410000000000003F40	1	5	2	\N	{1}
623	01020000A0E8640000020000006E832F446AD72E410A3F32BB503C59410000000000003A403671D59EAAD72E416F6EF3A34E3C59410000000000003D40	1	2	4	\N	{1}
624	01020000A0E8640000020000006E832F446AD72E410A3F32BB503C59410000000000003A407E9F54D973D72E4118B5FD56553C59410000000000003B40	1	5	6	\N	{1}
625	01020000A0E8640000020000003111694F3FD72E41EE897820523C59410000000000003A406E832F446AD72E410A3F32BB503C59410000000000003A40	1	2	4	\N	{1}
628	01020000A0E864000004000000B859A4EFDCD62E412E9425355B3C59410000000000003A4004A8C29EE0D62E41974B46855A3C59410000000000003A40BD412BBAF1D62E41A2D0A453573C59410000000000003A40BD412BBAF1D62E41A2D0A453573C59410000000000003A40	1	2	10	\N	{1}
629	01020000A0E864000004000000C52EF72011D72E41F49F256C543C59410000000000003940C52EF72011D72E41F49F256C543C5941000000000000394068F7FBE302D72E410FF81F9A513C5941000000000000394068F7FBE302D72E410FF81F9A513C59410000000000003940	1	5	6	\N	{1}
630	01020000A0E864000003000000BD412BBAF1D62E41A2D0A453573C59410000000000003A40BD412BBAF1D62E41A2D0A453573C59410000000000003A40786E3DBCD3D62E415B2C12D1543C59410000000000003940	1	5	9	\N	{1}
631	01020000A0E864000006000000BD412BBAF1D62E41A2D0A453573C59410000000000003A40BD412BBAF1D62E41A2D0A453573C59410000000000003A40F566D3B0F5D62E41D05F3596563C59410000000000003A40F566D3B0F5D62E41D05F3596563C59410000000000003A40C52EF72011D72E41F49F256C543C59410000000000003940C52EF72011D72E41F49F256C543C59410000000000003940	1	2	10	\N	{1}
632	01020000A0E8640000060000003671D59EAAD72E416F6EF3A34E3C59410000000000003D40FFDF6627B0D72E41F28FED754E3C59410000000000003D404201C9E5BCD72E41083710BB4D3C59410000000000003E407F632E4AC7D72E41CB4420A54C3C59410000000000003E40FC070F2FCBD72E4192AB9B3D4C3C59410000000000003E402141FB76D4D72E41A95E163E4B3C59410000000000003E40	1	2	4	\N	{1}
633	01020000A0E8640000020000006963EEBDD4D72E41E1FF74364B3C59410000000000003E40A9E81BEAF7D72E417244186E473C59410000000000004040	1	2	2	\N	{1}
634	01020000A0E8640000020000002141FB76D4D72E41A95E163E4B3C59410000000000003E4072667AAFBFD72E41EACD3B39483C59410000000000003F40	1	5	6	\N	{1}
635	01020000A0E8640000020000002141FB76D4D72E41A95E163E4B3C59410000000000003E406963EEBDD4D72E41E1FF74364B3C59410000000000003E40	1	2	2	\N	{1}
636	01020000A0E864000002000000635908973CD72E4107FC3783423C59410000000000003B40B97379B16ED72E4187E3E1C93C3C59410000000000003C40	1	2	4	\N	{1}
637	01020000A0E864000002000000635908973CD72E4107FC3783423C59410000000000003B40A423422B58D72E41B169D748463C59410000000000003C40	1	5	2	\N	{1}
645	01020000A0E864000002000000A029B43292D72E41A19013BD383C59410000000000003B40AA627F4DABD72E4110531F543C3C59410000000000003D40	1	5	6	\N	{1}
646	01020000A0E864000002000000A029B43292D72E41A19013BD383C59410000000000003B4025B35F53B6D72E41B79087CA343C59410000000000003C40	1	2	4	\N	{1}
648	01020000A0E864000002000000511D6B7FFED72E41793CC3E72C3C59410000000000003C40990469D118D82E4181824FAB303C59410000000000003C40	1	5	8	\N	{1}
649	01020000A0E8640000020000009D62AB62EBD72E411C335DFE2E3C59410000000000003A40511D6B7FFED72E41793CC3E72C3C59410000000000003C40	1	2	2	\N	{1}
650	01020000A0E86400000200000025B35F53B6D72E41B79087CA343C59410000000000003C40C685C118CFD72E4108865C55383C59410000000000003C40	1	5	6	\N	{1}
651	01020000A0E8640000020000009D62AB62EBD72E411C335DFE2E3C59410000000000003A40743922991ED82E413C9A3051363C59410000000000804040	1	5	8	\N	{1}
652	01020000A0E86400000200000025B35F53B6D72E41B79087CA343C59410000000000003C409D62AB62EBD72E411C335DFE2E3C59410000000000003A40	1	2	4	\N	{1}
656	01020000A0E8640000030000003487B360F5D72E416849F5E4623C59410000000000003A407037A5B6E4D72E41D03C9D5E603C5941000000000000394006FCFDA5DCD72E4128266F155D3C59410000000000003940	1	2	6	\N	{1}
657	01020000A0E8640000030000003487B360F5D72E416849F5E4623C59410000000000003A40C9AE8B8C0ED82E417FA74619603C5941000000000000394060216E5E10D82E410B5887E55F3C59410000000000003940	1	2	2	\N	{1}
658	01020000A0E86400000200000006FCFDA5DCD72E4128266F155D3C59410000000000003940EF121A20B7D72E410F438AC25D3C59410000000000003940	1	5	6	\N	{1}
660	01020000A0E864000003000000AF56A11E9FD62E41C8BD0E26273C59410000000000003740BC2D125975D62E4107350E891C3C5941000000000000384046D5C67468D62E41D0384993193C59410000000000003840	1	2	5	\N	{1}
664	01020000A0E864000002000000717DBB7E86D62E41A339A0AB563C59410000000000003A40FD0230DE6BD62E41BDB7543A5B3C59410000000000003A40	1	5	4	\N	{1}
669	01020000A0E86400000600000022EE826E95D62E417471761E553C59410000000000003A40DABD12389BD62E4196E5CF7C543C59410000000000003A40CACE82F1ADD62E41796C1071523C59410000000000003940EC30397CF2D62E41B82782FA4A3C59410000000000003940D5E982C419D72E416FD6A47D463C59410000000000003A40D5E982C419D72E416FD6A47D463C59410000000000003A40	1	2	5	\N	{1}
670	01020000A0E86400000300000022EE826E95D62E417471761E553C59410000000000003A407E240358C7D62E419DF9BE79593C59410000000000003A40B859A4EFDCD62E412E9425355B3C59410000000000003A40	1	2	5	\N	{1}
671	01020000A0E864000003000000D5E982C419D72E416FD6A47D463C59410000000000003A40D5E982C419D72E416FD6A47D463C59410000000000003A409ADE2696F0D62E419C95C5DB403C59410000000000003940	1	5	2	\N	{1}
672	01020000A0E864000003000000D5E982C419D72E416FD6A47D463C59410000000000003A40D5E982C419D72E416FD6A47D463C59410000000000003A40635908973CD72E4107FC3783423C59410000000000003B40	1	2	10	\N	{1}
675	01020000A0E864000002000000DAF3C06E79D62E4142ADD2AA523C59410000000000003940C6E277438BD62E4115404B7C4F3C59410000000000003940	1	5	5	\N	{1}
676	01020000A0E864000002000000DAF3C06E79D62E4142ADD2AA523C5941000000000000394022EE826E95D62E417471761E553C59410000000000003A40	1	2	9	\N	{1}
10000002	01020000A0E864000005000000CA0914A742D62E4188194A9C503C59410000000000003C407446438E60D62E415E90DB34533C59410000000000003B40752E30D664D62E41CAB00F99533C59410000000000003B404241EC7E67D62E41B36F2AD7533C59410000000000003B40717DBB7E86D62E41A339A0AB563C59410000000000003A40	1	2	5	\N	{1}
10000003	01020000A0E864000003000000717DBB7E86D62E41A339A0AB563C59410000000000003A4022B4924D8AD62E41DB7C9E04573C59410000000000003A40EFD6A5A3CED62E411592DADB5D3C59410000000000003B40	1	2	10	\N	{1}
10000004	01020000A0E864000005000000D6518C66E5D52E41AB3522B45D3C59410000000000003D40086E6802D7D52E4184EB87715B3C59410000000000003D40320BF6BFF7D52E41DB46A82F583C59410000000000003C404A0C2BA030D62E415D6CD642533C59410000000000003C40CA0914A742D62E4188194A9C503C59410000000000003C40	1	2	3	\N	{1}
10000006	01020000A0E86400000500000011D609944ED62E41E19F66DB4E3C59410000000000003C407F68315B33D62E41E45B826A4C3C59410000000000003E40B14503331ED62E41404CB32D4A3C594100000000000040405E6FFCBF09D62E418846B11F483C59410000000000804040E4A1CD4722D62E41FCF2244F443C59410000000000804040	1	5	2	\N	{1}
10000007	01020000A0E86400000300000061FF03D367D72E41D180D3902D3C5941000000000000374075D3DA166BD72E41BCDD7E052E3C59410000000000003740BA7830864FD72E413B6F6B1B313C59410000000000003840	1	5	4	\N	{1}
10000008	01020000A0E86400000300000097F30EB71CD82E411C16E978433C59410000000000804040949A47BB1DD82E4164BDEC5C433C5941000000000080404034B19E4F06D82E41DD98D5F53F3C59410000000000004040	1	5	6	\N	{1}
10000009	01020000A0E86400000500000071340294A6D62E4160195246613C59410000000000003B40CCF5366EA7D62E412A4A8941623C59410000000000003B40F47A6196A5D62E412771E8D1633C59410000000000003B40E8F64CC2A2D62E418F85A1EE643C59410000000000003D4006D741F8D2D62E41B00A0DD9663C59410000000000003D40	1	5	2	\N	{1}
10000010	01020000A0E86400000500000071340294A6D62E4160195246613C59410000000000003B40C87ACE688DD62E410843FD63623C59410000000000003B4090784BCB3CD62E414B54A32E633C59410000000000003F40CE274C2314D62E4115621D8C643C59410000000000004040855007DA08D62E4131732FE5663C59410000000000004040	1	2	4	\N	{1}
10000011	01020000A0E86400000300000006FCFDA5DCD72E4128266F155D3C59410000000000003940740DCB8FD6D72E41019ACE7F573C59410000000000003B40AAF0C107B3D72E4192E8B61A583C59410000000000003B40	1	5	8	\N	{1}
10000013	01020000A0E86400000300000060216E5E10D82E410B5887E55F3C5941000000000000394081AC0FF334D82E41406A5ED55B3C59410000000000003A4091DAF3341CD82E4199BF545A583C59410000000000003A40	1	5	7	\N	{1}
10000015	01020000A0E864000008000000EFD6A5A3CED62E411592DADB5D3C59410000000000003B409087E7E7DBD62E410C44861E5F3C59410000000000003B40A5459F871BD72E4100AD3C29653C59410000000000003B40F93B646B67D72E4152F105E76B3C59410000000000003840CA7F66B860D72E41CFFA32366D3C59410000000000003840AEB1BB5F54D72E41ABA322A06F3C594100000000000039408600DABA4CD72E41AB199343713C5941000000000000394066872EF822D72E41D3163F386E3C59410000000000003940	1	5	2	\N	{1}
10000016	01020000A0E864000005000000855007DA08D62E4131732FE5663C594100000000000040400B2F9324FCD52E41E5EF048A693C5941000000000080414039D7B325EDD52E41BA99EC296B3C59410000000000804140FA69598ECED52E4158520F7A6E3C59410000000000004140CCB9F770EDD52E416ED4C9EE723C59410000000000804240	1	5	7	\N	{1}
10000017	01020000A0E864000003000000B97379B16ED72E4187E3E1C93C3C59410000000000003C405E1DB2F590D72E4151C8B6DF383C59410000000000003B40A029B43292D72E41A19013BD383C59410000000000003B40	1	2	4	\N	{1}
10000018	01020000A0E8640000090000009403263E30D72E41C3257EB3273C594100000000000036409403263E30D72E41C3257EB3273C594100000000000036408E406E7136D72E41AF58079E263C594100000000000036408E406E7136D72E41AF58079E263C5941000000000000364010902F594CD72E4134170686233C59410000000000003640B8FD3A5F67D72E413533FED2203C59410000000000003540B5F90EE89CD72E41F59421B01C3C5941000000000000344061543EC5ACD72E415DFF29761B3C5941000000000000344021D1AC0ED2D72E419987D187223C59410000000000003440	1	5	4	\N	{1}
10000019	01020000A0E8640000040000002AF0776063D62E41DE0310112A3C594100000000000037405CE3008B34D62E41BFF4CC5A2C3C59410000000000003840A13719870ED62E41D56654182E3C59410000000000003940C31632B920D62E41CC94284E343C59410000000000003D40	1	5	7	\N	{1}
10000021	01020000A0E864000004000000CA0914A742D62E4188194A9C503C59410000000000003C40E82C038828D62E418E2FC4574E3C59410000000000003E407714C9D607D62E41541A3A3D4B3C59410000000000003F40CCDEF6B4F6D52E41DC1A110F4E3C59410000000000004040	1	5	2	\N	{1}
10000023	01020000A0E864000005000000766E66B3A0D62E411249EF26413C59410000000000003A40D4CD5C0596D62E41510DC95B403C59410000000000003A40E4D61D8686D62E41EA16F051403C59410000000000003C40B5F44C0776D62E41096A1B12413C59410000000000003C40E3F6FFB04DD62E4153004F523D3C59410000000000003E40	1	5	2	\N	{1}
10000024	01020000A0E86400000300000046D5C67468D62E41D0384993193C594100000000000038405E9DA1F162D62E410516474F183C59410000000000003840FDBE28F37FD62E41DB396E92153C59410000000000003840	1	5	6	\N	{1}
10000026	01020000A0E864000005000000102FEB06A6D72E417F2BE5E36C3C5941000000000000394004A2B27FB9D72E4198CFEEFA6D3C594100000000000039403C3D905FDAD72E413E97E7B46E3C59410000000000003A4017F82129FCD72E41D6E71F9F6E3C59410000000000003A408224D886FBD72E41C47A17B06A3C59410000000000003A40	1	5	2	\N	{1}
10000027	01020000A0E86400000400000011D609944ED62E41E19F66DB4E3C59410000000000003C4018985D2A6CD62E411CEF9582513C59410000000000003B40BFE0861072D62E411125A805523C59410000000000003B40DAF3C06E79D62E4142ADD2AA523C59410000000000003940	1	2	11	\N	{1}
10000028	01020000A0E864000006000000511D6B7FFED72E41793CC3E72C3C59410000000000003C40E40507FB03D82E41B80F664E2C3C59410000000000003C40261F9F2E35D82E41E329F0ED263C5941000000000000394046E7F17F3AD82E41361C6659263C594100000000000039409CA06F8B4BD82E418690596E243C5941000000000000374052D4AA8111D82E4102726D5F1C3C59410000000000003540	1	5	2	\N	{1}
\.


--
-- Data for Name: network; Type: TABLE DATA; Schema: base1;
--

COPY base1.network (id, description) FROM stdin;
1	This is the main network.
\.




--
-- Data for Name: streets; Type: TABLE DATA; Schema: base1;
--

COPY base1.streets (id, geom, costs_eur7m, source, target, surface) FROM stdin;
1	0102000020E864000005000000AF56A11E9FD62E41C8BD0E26273C5941A6F0AFBCAAD62E41296878A2283C594148691E6EBBD62E41CB03E3C32A3C5941703B2F3DE3D62E412C3DE4332E3C59411E95DCD8FDD62E419527E184303C5941	100	\N	\N	paved
2	0102000020E864000002000000E82C038828D62E418E2FC4574E3C59417446438E60D62E415E90DB34533C5941	100	\N	\N	paved
3	0102000020E86400000B000000691749B5A5D42E4147ED6FFF383C5941B48CC3F3CBD42E41B30558AF383C5941E86467FEE8D42E411C91395B383C594163A6AE71FAD42E414519EBC9383C59411EABBA570BD52E4107272384393C5941A00D38CA55D52E414EF9BE243E3C5941D64BB7C064D52E417A5232183F3C594137D34A6973D52E410A676F07403C5941A5AF3EA8BDD52E418F714EB1443C59411401271BF4D52E41CF63A55D493C5941E82C038828D62E418E2FC4574E3C5941	100	\N	\N	paved
4	0102000020E86400000200000018985D2A6CD62E411CEF9582513C59417F68315B33D62E41E45B826A4C3C5941	100	\N	\N	paved
5	0102000020E864000005000000B859A4EFDCD62E412E9425355B3C59417E240358C7D62E419DF9BE79593C594122EE826E95D62E417471761E553C5941BFE0861072D62E411125A805523C594118985D2A6CD62E411CEF9582513C5941	100	\N	\N	paved
6	0102000020E864000007000000766E66B3A0D62E411249EF26413C5941D4CD5C0596D62E41510DC95B403C5941E4D61D8686D62E41EA16F051403C5941B5F44C0776D62E41096A1B12413C5941441E5E6545D62E41498882094A3C594130AB470238D62E4193152D604A3C5941B14503331ED62E41404CB32D4A3C5941	100	\N	\N	paved
7	0102000020E86400000400000057564C50D1D72E41D5002BAF523C594106FCFDA5DCD72E4128266F155D3C59417037A5B6E4D72E41D03C9D5E603C59413487B360F5D72E416849F5E4623C5941	100	\N	\N	paved
8	0102000020E864000004000000CE274C2314D62E4115621D8C643C59410B2F9324FCD52E41E5EF048A693C594139D7B325EDD52E41BA99EC296B3C5941B2C4DFA069D52E4175374268793C5941	100	\N	\N	paved
9	0102000020E864000006000000C1CEEC8E6CD62E41585EA643733C5941025D488496D62E411E5B5209683C5941CCC127B8A1D62E41C6E04857653C5941F47A6196A5D62E412771E8D1633C5941CCF5366EA7D62E412A4A8941623C594171340294A6D62E4160195246613C5941	100	\N	\N	paved
10	0102000020E86400000B000000266CF6F4D7D72E416EA0A1DC713C59411D83817F05D82E4142DD75A7713C59413E0F67811BD82E41BB89BA5B713C59414C764A5048D82E413BE05F6D6F3C59419CD4280F18D92E41E92D926C653C594158427B5181D92E41AA7C0A62603C59418472F8D299D92E41C8EF112E5F3C59417EE8199E26DA2E41B1920381583C594149A33D0F37DA2E4177D903B8573C5941346F2BB48BDA2E41675A4986533C5941071ACD6799DA2E4151355E8C513C5941	100	\N	\N	paved
11	0102000020E8640000080000001E95DCD8FDD62E419527E184303C5941766E66B3A0D62E411249EF26413C5941A1A9F3A555D62E412E4448D14D3C59414A0C2BA030D62E415D6CD642533C5941320BF6BFF7D52E41DB46A82F583C5941C486304241D52E41E59891576A3C594196207A63ABD42E411CB5716C7E3C59416CDC6DDF9CD42E4163B78C5E803C5941	100	\N	\N	paved
12	0102000020E8640000070000001E95DCD8FDD62E419527E184303C59419403263E30D72E41C3257EB3273C59418E406E7136D72E41AF58079E263C594110902F594CD72E4134170686233C5941B8FD3A5F67D72E413533FED2203C5941B5F90EE89CD72E41F59421B01C3C594161543EC5ACD72E415DFF29761B3C5941	100	\N	\N	paved
13	0102000020E8640000030000005CE3008B34D62E41BFF4CC5A2C3C594175529DAF1DD62E418423476F253C5941DA4A55AF17D62E4187B986B6253C5941	100	\N	\N	paved
14	0102000020E864000005000000AF56A11E9FD62E41C8BD0E26273C5941421371C88DD62E414B58B3FE273C59415CE3008B34D62E41BFF4CC5A2C3C5941BE99FF9CDAD52E41ABFCC078303C59410AE63E19C7D52E41746F6DB3313C5941	100	\N	\N	paved
15	0102000020E86400000F000000E25AB0CC9AD72E4116C5C3906F3C5941102FEB06A6D72E417F2BE5E36C3C594154581622AFD72E415EB90B2B6B3C59418C9002C2B0D72E4132DC43DC6A3C59413487B360F5D72E416849F5E4623C5941C9AE8B8C0ED82E417FA74619603C5941EC08E897ABD82E41FE32C2A74E3C594196DC072209D92E417009B8B5443C5941D4C0ABF26DD92E41212E7ACB393C5941AAECBFED7AD92E41A8C47F57383C5941607BE9807FD92E4147A2A6D4373C59415C89B8BFBED92E4154B0B10A313C59418012F4A5DCD92E419F22F68B2E3C594111B3FB81FBD92E41211B11252D3C59413330F4F00FDA2E412D692E8A2B3C5941	100	\N	\N	paved
16	0102000020E8640000080000008472F8D299D92E41C8EF112E5F3C594160F3686890D92E41D848A8065C3C59410E2376E78CD92E41366333BE5A3C5941E0BFDC5282D92E41BB547ADF563C5941C69A5E6178D92E41CF4172A2543C594196DC072209D92E417009B8B5443C59411AE929159FD82E4152B6A973353C5941261F9F2E35D82E41E329F0ED263C5941	100	\N	\N	paved
17	0102000020E86400000E0000008021D3494BD72E417311FD448D3C5941C2F7B55547D72E41F0BFA3CA893C59414C68CE4734D72E41DD4F7171873C5941EFB4D6751FD72E41F37D4411853C594110BB369822D72E416D551A32833C59412C34FA9123D72E410D271B9E823C5941ECF451C730D72E41E960706A803C5941B2E9379234D72E41E775F9F37A3C594196ED008235D72E4158C9E43D7A3C594148C877063BD72E419FFFAB06763C5941F889E4CD45D72E41137F97BF723C5941AEB1BB5F54D72E41ABA322A06F3C5941CA7F66B860D72E41CFFA32366D3C5941F93B646B67D72E4152F105E76B3C5941	100	\N	\N	paved
18	0102000020E864000005000000FA7C367011D62E41CC8B95700D3C59418BDD024820D62E4194F49C6B0F3C59415E9DA1F162D62E410516474F183C5941BC2D125975D62E4107350E891C3C5941AF56A11E9FD62E41C8BD0E26273C5941	100	\N	\N	paved
19	0102000020E8640000050000007F68315B33D62E41E45B826A4C3C5941B14503331ED62E41404CB32D4A3C5941B7E6FEB001D62E41A9FC6750473C59412C89BF48D4D52E41349CD3FB423C594174C6E2957DD52E41CBDF4F793D3C5941	100	\N	\N	paved
20	0102000020E864000009000000EFD6A5A3CED62E411592DADB5D3C59419087E7E7DBD62E410C44861E5F3C5941A5459F871BD72E4100AD3C29653C5941F93B646B67D72E4152F105E76B3C5941B412291A72D72E415391E2D96C3C5941B84FCA327CD72E41AA855C866D3C5941E25AB0CC9AD72E4116C5C3906F3C594115CCAFDDB6D72E41C5CC9BDE703C5941266CF6F4D7D72E416EA0A1DC713C5941	100	\N	\N	paved
21	0102000020E86400000A000000071ACD6799DA2E4151355E8C513C59411CE35CC385DA2E41B4423C82503C59417880DCB557DA2E41A5E11D70523C59418424A7692DDA2E41EC5FD962543C59414D50143A1CDA2E41150D3D4B553C594160F3686890D92E41D848A8065C3C59418A09AB240ED92E4106F5D140623C5941C26193DF15D82E41CB7842276E3C5941F8396FDA00D82E41C185199C6E3C59413C3D905FDAD72E413E97E7B46E3C5941	100	\N	\N	paved
22	0102000020E8640000050000007446438E60D62E415E90DB34533C5941752E30D664D62E41CAB00F99533C59414241EC7E67D62E41B36F2AD7533C594122B4924D8AD62E41DB7C9E04573C5941EFD6A5A3CED62E411592DADB5D3C5941	100	\N	\N	paved
23	0102000020E864000002000000EFD6A5A3CED62E411592DADB5D3C5941B859A4EFDCD62E412E9425355B3C5941	100	\N	\N	paved
24	0102000020E8640000060000003C3D905FDAD72E413E97E7B46E3C594104A2B27FB9D72E4198CFEEFA6D3C5941102FEB06A6D72E417F2BE5E36C3C5941232E840088D72E41D0D7D3E66A3C594174A016CEEBD62E41FFC249925C3C5941B859A4EFDCD62E412E9425355B3C5941	100	\N	\N	paved
25	0102000020E864000003000000481B74E67ED72E41BC4168C9303C5941E8D4C8B964D72E419AAB1A222D3C59419403263E30D72E41C3257EB3273C5941	100	\N	\N	paved
26	0102000020E86400000F000000B859A4EFDCD62E412E9425355B3C594104A8C29EE0D62E41974B46855A3C5941F566D3B0F5D62E41D05F3596563C59410CA5464522D72E41F0A9FF11533C5941FFDF6627B0D72E41F28FED754E3C59414201C9E5BCD72E41083710BB4D3C59417F632E4AC7D72E41CB4420A54C3C5941FC070F2FCBD72E4192AB9B3D4C3C59411AE929159FD82E4152B6A973353C5941ACAAFFBEF1D82E412BBBE47E2B3C5941E88BBC4220D92E41BDB291E4253C5941680687F028D92E4195F734D9243C59411674D64D4DD92E41110EC977203C5941BB9FCECB68D92E41FC275B781E3C59410088716E84D92E4172E209C41D3C5941	100	\N	\N	paved
27	0102000020E86400000200000022EE826E95D62E417471761E553C594122B4924D8AD62E41DB7C9E04573C5941	100	\N	\N	paved
28	0102000020E8640000050000005E1DB2F590D72E4151C8B6DF383C5941EC30397CF2D62E41B82782FA4A3C5941CACE82F1ADD62E41796C1071523C5941DABD12389BD62E4196E5CF7C543C594122EE826E95D62E417471761E553C5941	100	\N	\N	paved
29	0102000020E864000003000000261F9F2E35D82E41E329F0ED263C5941E40507FB03D82E41B80F664E2C3C59415E1DB2F590D72E4151C8B6DF383C5941	100	\N	\N	paved
30	0102000020E8640000030000009D709653C4D82E41EBBDB9D6163C594146E7F17F3AD82E41361C6659263C5941261F9F2E35D82E41E329F0ED263C5941	100	\N	\N	paved
31	0102000020E86400000400000071340294A6D62E4160195246613C5941C87ACE688DD62E410843FD63623C594190784BCB3CD62E414B54A32E633C5941CE274C2314D62E4115621D8C643C5941	100	\N	\N	paved
32	0102000020E864000004000000EFD6A5A3CED62E411592DADB5D3C59410D98EEC4BED62E4162B540D15E3C5941242A5CD8B8D62E419F46502C5F3C594171340294A6D62E4160195246613C5941	100	\N	\N	paved
\.


--
-- Data for Name: submodels; Type: TABLE DATA; Schema: base1;
--

COPY base1.submodels (id, submodel, geom) FROM stdin;
1	1	0106000020E86400000100000001030000000100000025000000FA69598ECED52E41DB396E12133C594189A07CA7CAD52E419C5DBA1E133C5941E39502E7C6D52E41ABCD2543133C5941ED65D471C3D52E41A63E4A7E133C5941EA69F669C0D52E41D9D9E1CD133C5941519039EDBDD52E415999DD2E143C59417A081614BCD52E41585F839D143C5941FF87BAF0BAD52E41ADA09215153C5941FA69598EBAD52E41DB396E92153C5941FA69598EBAD52E416ED4C9EE723C5941FF87BAF0BAD52E419C6DA56B733C59417A081614BCD52E41F1AEB4E3733C5941519039EDBDD52E41F0745A52743C5941EA69F669C0D52E41703456B3743C5941ED65D471C3D52E41A3CFED02753C5941E39502E7C6D52E419E40123E753C594189A07CA7CAD52E41ADB07D62753C5941FA69598ECED52E416ED4C96E753C59419CA06F8B4BD82E416ED4C96E753C59410D6A4C724FD82E41ADB07D62753C5941B374C63253D82E419E40123E753C5941A9A4F4A756D82E41A3CFED02753C5941ACA0D2AF59D82E41703456B3743C5941457A8F2C5CD82E41F0745A52743C59411C02B3055ED82E41F1AEB4E3733C594197820E295FD82E419C6DA56B733C59419CA06F8B5FD82E416ED4C9EE723C59419CA06F8B5FD82E41DB396E92153C594197820E295FD82E41ADA09215153C59411C02B3055ED82E41585F839D143C5941457A8F2C5CD82E415999DD2E143C5941ACA0D2AF59D82E41D9D9E1CD133C5941A9A4F4A756D82E41A63E4A7E133C5941B374C63253D82E41ABCD2543133C59410D6A4C724FD82E419C5DBA1E133C59419CA06F8B4BD82E41DB396E12133C5941FA69598ECED52E41DB396E12133C5941
\.


--
-- Data for Name: supervisory_ctrl; Type: TABLE DATA; Schema: public;
--

COPY public.supervisory_ctrl (id, submodel) FROM stdin;
1	1
\.





--
-- Data for Name: energy_plants; Type: TABLE DATA; Schema: base1;
--

COPY base1.energy_plants (id, geom, template, network, submodel) FROM stdin;
1	01010000A0E8640000D6518C66E5D52E41AB3522B45D3C59410000000000003D40	1	{1}	1
\.


--
-- Data for Name: invoked_sf; Type: TABLE DATA; Schema: base1;
--

COPY base1.invoked_sf (id, sf, type, vars) FROM stdin;
\.


--
-- Data for Name: junction_connections; Type: TABLE DATA; Schema: base1;
--

COPY base1.junction_connections (id, jid, lid, zeta) FROM stdin;
2280	1	578	1.2
2281	1	577	0.2
2282	1	579	0.5103
2283	2	589	1.2
2284	2	588	0.2
2285	2	613	0.2
2286	3	593	1.2
2287	3	591	0.2
2288	3	10000007	0.3125
2289	4	602	0.2
2290	4	660	0.2
2291	4	10000024	1.2
2292	5	615	1.2
2293	5	636	0.2
2294	5	10000017	0.2
2295	6	637	1.2
2296	6	636	0.3125
2297	6	672	0.2
2298	7	645	1.2
2299	7	646	0.2
2300	7	10000017	0.2
2301	8	648	1.2
2302	8	10000028	0.2
2303	8	649	0.2
2304	9	650	1.2
2305	9	646	0.2
2306	9	652	0.2
2307	10	635	0.3813
2308	10	632	0.2
2309	10	634	1.2
2310	11	635	0.2
2311	11	633	0.2
2312	11	600	1.2
2313	12	567	1.2
2314	12	579	0.2
2315	12	10000026	0.3813
2316	13	567	0.2
2317	13	656	1.2
2318	13	657	0.2
2319	14	568	0.25
2320	14	10000002	1.25
2321	14	10000004	0.25
2322	14	10000021	1.25
2323	15	568	0.25
2324	15	611	1.25
2325	15	10000006	1.25
2326	15	10000027	0.3421
2327	16	570	0.3125
2328	16	10000003	0.2
2329	16	10000015	1.2
2330	17	570	0.2
2331	17	10000009	1.2
2332	17	10000010	0.2
2333	18	577	0.2
2334	18	628	1.2
2335	18	670	0.2
2336	19	583	0.3772
2337	19	616	0.2
2338	19	617	1.2
2339	20	583	0.2
2340	20	10000008	0.2997
2341	20	582	1.2
2342	21	588	0.2
2343	21	592	0.3467
2344	21	601	1.2
2345	22	592	0.2
2346	22	591	0.3843
2347	22	10000018	1.2
2348	23	601	0.2
2349	23	660	0.2
2350	23	595	1.2
2351	24	603	1.2
2352	24	604	0.2
2353	24	606	0.2
2354	25	629	1.2
2355	25	631	0.2
2356	25	604	0.3125
2357	26	625	0.2
2358	26	605	1.2
2359	26	606	0.2
2360	27	610	0.2
2361	27	611	0.2
2362	27	10000023	1.2
2363	28	610	0.2
2364	28	612	1.2
2365	28	613	0.2
2366	29	614	1.2
2367	29	623	0.2
2368	29	632	0.2
2369	30	616	0.2
2370	30	618	1.2
2371	30	633	0.2
2372	31	623	0.2
2373	31	624	1.2
2374	31	625	0.2
2375	32	628	0.5405
2376	32	630	0.2
2377	32	631	1.2
2378	33	649	0.3813
2379	33	651	1.2
2380	33	652	0.2
2381	34	656	0.2
2382	34	658	0.2
2383	34	10000011	1.2
2384	35	657	0.2
2385	35	584	1.2
2386	35	10000013	0.3772
2387	36	664	1.2
2388	36	10000002	0.2
2389	36	10000003	0.3843
2390	37	671	1.2
2391	37	669	0.2
2392	37	672	0.3843
2393	38	675	1.2
2394	38	676	0.3294
2395	38	10000027	0.2
2396	39	595	0.2
2397	39	596	0.3813
2398	39	10000019	1.2
2399	40	621	0.3813
2400	40	10000010	0.2
2401	40	10000016	1.2
2402	41	669	1.2
2403	41	670	0.3467
2404	41	676	0.2
\.


--
-- Data for Name: junctions; Type: TABLE DATA; Schema: base1;
--

COPY base1.junctions (id, geom, type, n_connections, submodel, network, zeta) FROM stdin;
14	01010000A0E8640000CA0914A742D62E4188194A9C503C59410000000000003C40	1	4	1	1	\N
15	01010000A0E864000011D609944ED62E41E19F66DB4E3C59410000000000003C40	1	4	1	1	\N
1	01010000A0E8640000F097903E46D72E41E23367DE643C59410000000000003A40	4	3	1	1	\N
2	01010000A0E8640000AECD4826E9D62E41E83F0A37343C59410000000000003740	4	3	1	1	\N
3	01010000A0E864000061FF03D367D72E41D180D3902D3C59410000000000003740	4	3	1	1	\N
4	01010000A0E864000046D5C67468D62E41D0384993193C59410000000000003840	4	3	1	1	\N
5	01010000A0E8640000B97379B16ED72E4187E3E1C93C3C59410000000000003C40	4	3	1	1	\N
6	01010000A0E8640000635908973CD72E4107FC3783423C59410000000000003B40	4	3	1	1	\N
7	01010000A0E8640000A029B43292D72E41A19013BD383C59410000000000003B40	4	3	1	1	\N
8	01010000A0E8640000511D6B7FFED72E41793CC3E72C3C59410000000000003C40	4	3	1	1	\N
9	01010000A0E864000025B35F53B6D72E41B79087CA343C59410000000000003C40	4	3	1	1	\N
10	01010000A0E86400002141FB76D4D72E41A95E163E4B3C59410000000000003E40	4	3	1	1	\N
11	01010000A0E86400006963EEBDD4D72E41E1FF74364B3C59410000000000003E40	4	3	1	1	\N
12	01010000A0E8640000102FEB06A6D72E417F2BE5E36C3C59410000000000003940	4	3	1	1	\N
13	01010000A0E86400003487B360F5D72E416849F5E4623C59410000000000003A40	4	3	1	1	\N
16	01010000A0E8640000EFD6A5A3CED62E411592DADB5D3C59410000000000003B40	4	3	1	1	\N
17	01010000A0E864000071340294A6D62E4160195246613C59410000000000003B40	4	3	1	1	\N
18	01010000A0E8640000B859A4EFDCD62E412E9425355B3C59410000000000003A40	4	3	1	1	\N
19	01010000A0E864000084214F42F9D72E4193D61349473C59410000000000004040	4	3	1	1	\N
20	01010000A0E864000097F30EB71CD82E411C16E978433C59410000000000804040	4	3	1	1	\N
21	01010000A0E86400001E95DCD8FDD62E419527E184303C59410000000000003740	4	3	1	1	\N
22	01010000A0E86400009403263E30D72E41C3257EB3273C59410000000000003640	4	3	1	1	\N
23	01010000A0E8640000AF56A11E9FD62E41C8BD0E26273C59410000000000003740	4	3	1	1	\N
24	01010000A0E86400001F9B089533D72E4137E20382523C59410000000000003940	4	3	1	1	\N
25	01010000A0E8640000C52EF72011D72E41F49F256C543C59410000000000003940	4	3	1	1	\N
26	01010000A0E86400003111694F3FD72E41EE897820523C59410000000000003A40	4	3	1	1	\N
27	01010000A0E8640000766E66B3A0D62E411249EF26413C59410000000000003A40	4	3	1	1	\N
28	01010000A0E8640000297697E8C5D62E41DF6408823A3C59410000000000003840	4	3	1	1	\N
29	01010000A0E86400003671D59EAAD72E416F6EF3A34E3C59410000000000003D40	4	3	1	1	\N
30	01010000A0E8640000A9E81BEAF7D72E417244186E473C59410000000000004040	4	3	1	1	\N
31	01010000A0E86400006E832F446AD72E410A3F32BB503C59410000000000003A40	4	3	1	1	\N
32	01010000A0E8640000BD412BBAF1D62E41A2D0A453573C59410000000000003A40	4	3	1	1	\N
33	01010000A0E86400009D62AB62EBD72E411C335DFE2E3C59410000000000003A40	4	3	1	1	\N
34	01010000A0E864000006FCFDA5DCD72E4128266F155D3C59410000000000003940	4	3	1	1	\N
35	01010000A0E864000060216E5E10D82E410B5887E55F3C59410000000000003940	4	3	1	1	\N
36	01010000A0E8640000717DBB7E86D62E41A339A0AB563C59410000000000003A40	4	3	1	1	\N
37	01010000A0E8640000D5E982C419D72E416FD6A47D463C59410000000000003A40	4	3	1	1	\N
38	01010000A0E8640000DAF3C06E79D62E4142ADD2AA523C59410000000000003940	4	3	1	1	\N
39	01010000A0E86400002AF0776063D62E41DE0310112A3C59410000000000003740	4	3	1	1	\N
40	01010000A0E8640000855007DA08D62E4131732FE5663C59410000000000004040	4	3	1	1	\N
41	01010000A0E864000022EE826E95D62E417471761E553C59410000000000003A40	4	3	1	1	\N
\.

--
-- Data for Name: customers; Type: TABLE DATA; Schema: base1;
--

COPY base1.customers (id, geom, template, network, load_w, submodel, gfa_m2) FROM stdin;
1	01010000A0E86400008224D886FBD72E41C47A17B06A3C59410000000000003A40	1	{1}	118820.727166313	1	2376.4145433262597
2	01010000A0E864000060AF5FA410D82E41CD83CC054B3C59410000000000004040	1	{1}	43274.5273414689	1	865.490546829378
3	01010000A0E864000091EFF8F646D72E4172D1E2CE553C59410000000000003A40	1	{1}	23525.1622467343	1	470.503244934686
4	01010000A0E8640000AAF0C107B3D72E4192E8B61A583C59410000000000003B40	1	{1}	33060.9403036735	1	661.2188060734701
5	01010000A0E864000091DAF3341CD82E4199BF545A583C59410000000000003A40	1	{1}	77616.1245655517	1	1552.322491311034
6	01010000A0E8640000645DD5F6FDD72E412606BC4E5D3C59410000000000003940	1	{1}	32254.3580732863	1	645.087161465726
7	01010000A0E86400006E6202BB34D82E41047520F6463C59410000000000004040	1	{1}	43453.8015326829	1	869.076030653658
8	01010000A0E86400002692613DEBD72E41E1AF3A7B4E3C59410000000000003E40	1	{1}	35218.1342089207	1	704.362684178414
9	01010000A0E864000028BA9C255CD72E4100EB7723613C59410000000000003A40	1	{1}	380180.003369025	1	7603.6000673805
10	01010000A0E8640000EF121A20B7D72E410F438AC25D3C59410000000000003940	1	{1}	35495.0759972858	1	709.901519945716
11	01010000A0E86400007E9F54D973D72E4118B5FD56553C59410000000000003B40	1	{1}	39209.5146123915	1	784.1902922478299
12	01010000A0E86400002AA185BAB0D72E41AA56FA93513C59410000000000003B40	1	{1}	28941.1712981738	1	578.823425963476
13	01010000A0E864000052D4AA8111D82E4102726D5F1C3C59410000000000003540	1	{1}	155093.295042631	1	3101.86590085262
14	01010000A0E8640000BA7830864FD72E413B6F6B1B313C59410000000000003840	1	{1}	233426.907295876	1	4668.5381459175205
15	01010000A0E864000021D1AC0ED2D72E419987D187223C59410000000000003440	1	{1}	208544.342639792	1	4170.88685279584
16	01010000A0E86400002D546D051ED72E4130ED61D7383C59410000000000003940	1	{1}	190301.628902005	1	3806.0325780401
17	01010000A0E8640000BB83544395D72E41E20BB47A283C59410000000000003540	1	{1}	223552.134839671	1	4471.04269679342
18	01010000A0E86400009ADE2696F0D62E419C95C5DB403C59410000000000003940	1	{1}	194498.075729784	1	3889.96151459568
19	01010000A0E8640000D905A11945D62E41432A3AFB1B3C59410000000000003840	1	{1}	693277.209702341	1	13865.54419404682
20	01010000A0E8640000A836F10073D62E41A49B86102F3C59410000000000003840	1	{1}	197162.608659053	1	3943.25217318106
21	01010000A0E864000006D741F8D2D62E41B00A0DD9663C59410000000000003D40	1	{1}	105074.36626185	1	2101.487325237
22	01010000A0E8640000CCB9F770EDD52E416ED4C9EE723C59410000000000804240	1	{1}	99710.296285094	1	1994.20592570188
23	01010000A0E864000066872EF822D72E41D3163F386E3C59410000000000003940	1	{1}	124068.689966868	1	2481.3737993373597
25	01010000A0E8640000FD0230DE6BD62E41BDB7543A5B3C59410000000000003A40	1	{1}	231869.407840525	1	4637.3881568105
27	01010000A0E86400006C51F3D528D62E411899284C693C59410000000000003F40	1	{1}	119735.635804571	1	2394.7127160914197
28	01010000A0E8640000CCDEF6B4F6D52E41DC1A110F4E3C59410000000000004040	1	{1}	157235.962073562	1	3144.71924147124
29	01010000A0E8640000EA69D979A3D62E41253FBB7E373C59410000000000003840	1	{1}	213938.595537203	1	4278.77191074406
30	01010000A0E8640000E4A1CD4722D62E41FCF2244F443C59410000000000804040	1	{1}	164494.300102267	1	3289.8860020453403
31	01010000A0E8640000C31632B920D62E41CC94284E343C59410000000000003D40	1	{1}	14375.8505026016	1	287.517010052032
32	01010000A0E8640000E3F6FFB04DD62E4153004F523D3C59410000000000003E40	1	{1}	134436.204446154	1	2688.72408892308
34	01010000A0E8640000786E3DBCD3D62E415B2C12D1543C59410000000000003940	1	{1}	103657.835849808	1	2073.15671699616
35	01010000A0E8640000FDBE28F37FD62E41DB396E92153C59410000000000003840	1	{1}	37295.0020773826	1	745.9000415476521
36	01010000A0E864000068F7FBE302D72E410FF81F9A513C59410000000000003940	1	{1}	53699.9169494487	1	1073.998338988974
37	01010000A0E8640000D101C50D2AD72E41FA6AE5EC4D3C59410000000000003B40	1	{1}	93270.6545168077	1	1865.413090336154
38	01010000A0E8640000A423422B58D72E41B169D748463C59410000000000003C40	1	{1}	164319.588708477	1	3286.39177416954
39	01010000A0E8640000E2DEB79688D72E41E05C8F54403C59410000000000003D40	1	{1}	43602.208653259	1	872.04417306518
40	01010000A0E8640000743922991ED82E413C9A3051363C59410000000000804040	1	{1}	29756.7956953668	1	595.135913907336
41	01010000A0E8640000F5EAC7B1E3D72E4147780427443C59410000000000004040	1	{1}	34614.7856890229	1	692.2957137804581
42	01010000A0E8640000AA627F4DABD72E4110531F543C3C59410000000000003D40	1	{1}	49209.7010583541	1	984.1940211670819
43	01010000A0E864000034B19E4F06D82E41DD98D5F53F3C59410000000000004040	1	{1}	43196.6976495307	1	863.9339529906141
44	01010000A0E8640000C685C118CFD72E4108865C55383C59410000000000003C40	1	{1}	48184.4713071468	1	963.689426142936
45	01010000A0E864000072667AAFBFD72E41EACD3B39483C59410000000000003F40	1	{1}	33284.4826836729	1	665.689653673458
46	01010000A0E8640000990469D118D82E4181824FAB303C59410000000000003C40	1	{1}	20621.8314261043	1	412.43662852208604
47	01010000A0E8640000C6E277438BD62E4115404B7C4F3C59410000000000003940	1	{1}	788468.561731659	1	15769.37123463318
\.



--
-- Data for Name: energy_plant_connections; Type: TABLE DATA; Schema: base1;
--

COPY base1.energy_plant_connections (id, epid, ep_seq, lid) FROM stdin;
16	1	1	10000004
\.


--
-- Name: energy_plants; Type: SEQUENCE SET; Schema: base1;
--

SELECT pg_catalog.setval('base1.energy_plants_id_seq', 2, false);

--
-- Name: customers_id_seq; Type: SEQUENCE SET; Schema: base1;
--

SELECT pg_catalog.setval('base1.customers_id_seq', 48, false);

--
-- Name: invoked_sf_id_seq; Type: SEQUENCE SET; Schema: base1;
--

SELECT pg_catalog.setval('base1.invoked_sf_id_seq', 13, true);


--
-- Name: junction_connections_id_seq; Type: SEQUENCE SET; Schema: base1;
--

SELECT pg_catalog.setval('base1.junction_connections_id_seq', 1, false);


--
-- Name: junctions_id_seq; Type: SEQUENCE SET; Schema: base1;
--

SELECT pg_catalog.setval('base1.junctions_id_seq', 414, true);


--
-- Name: lines_id_seq; Type: SEQUENCE SET; Schema: base1;
--

SELECT pg_catalog.setval('base1.lines_id_seq', 677, false);


--
-- Name: sensor_source_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.sensor_source_id_seq', 2, false);


--
-- Name: sensor_target_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.sensor_target_id_seq', 2, false);

--
-- Name: invoked_sensor_target_signals_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.invoked_sensor_target_signals_id_seq', 2, false);

--
-- Name: invoked_sensor_source_signals_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.invoked_sensor_source_signals_id_seq', 2, false);


--
-- Name: source_template_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.source_template_id_seq', 2, false);


--
-- Name: streets_id_seq; Type: SEQUENCE SET; Schema: base1;
--

SELECT pg_catalog.setval('base1.streets_id_seq', 32, true);

--
-- Name: buildings_id_seq; Type: SEQUENCE SET; Schema: base1;
--

SELECT pg_catalog.setval('base1.buildings_id_seq', 203, false);

--
-- Name: target_template_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.target_template_id_seq', 2, false);

--
-- Name: sensors_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.sensors_id_seq', 2, false);

--
-- Name: model_parms_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.model_parms_id_seq', 3, false);


--
-- Name: versionhandling_id_seq; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.versionhandling_id_seq', 2, false);

--
-- Name: building_constructions; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.building_constructions_id_seq', 28, false);

--
-- Name: zone_templates; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.zone_templates_id_seq', 136, false);


--
-- PostgreSQL database dump complete
--

--
-- Name: materials; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.materials_id_seq', 11, false);

--
-- Name: pipe_constructions; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_constructions_id_seq', 141, false);

--
-- Name: pipe_layers; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_layers_id_seq', 315, false);

--
-- Name: pipes; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipes_id_seq', 109, false);

--
-- Name: pipe_bundle_types; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_bundle_types_id_seq', 44, false);

--
-- Name: bundle_pipes; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.bundle_pipes_id_seq', 87, false);

--
-- Name: pipe_series; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_series_id_seq', 18, false);

--
-- Name: pipe_series_pressure_ratings; Type: SEQUENCE SET; Schema: public;
--

SELECT pg_catalog.setval('public.pipe_series_pressure_ratings_id_seq', 391, false);
