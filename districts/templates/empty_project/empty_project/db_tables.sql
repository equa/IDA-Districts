SET client_encoding = 'UTF8';

----------data for public tables------------

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

