--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

--
-- Name: actor_actor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('actor_actor_id_seq', 200, true);


--
-- Name: category_category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('category_category_id_seq', 16, true);


--
-- Name: film_film_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('film_film_id_seq', 1000, true);


--
-- Name: address_address_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('address_address_id_seq', 605, true);


--
-- Name: city_city_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('city_city_id_seq', 600, true);


--
-- Name: country_country_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('country_country_id_seq', 109, true);


--
-- Name: customer_customer_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('customer_customer_id_seq', 599, true);


--
-- Name: inventory_inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('inventory_inventory_id_seq', 4581, true);


--
-- Name: language_language_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('language_language_id_seq', 6, true);


--
-- Name: payment_payment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('payment_payment_id_seq', 32098, true);


--
-- Name: rental_rental_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('rental_rental_id_seq', 16049, true);


--
-- Name: staff_staff_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('staff_staff_id_seq', 2, true);


--
-- Name: store_store_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('store_store_id_seq', 2, true);


--
-- Data for Name: actor; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE actor DISABLE TRIGGER ALL;




ALTER TABLE actor ENABLE TRIGGER ALL;

--
-- Data for Name: address; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE address DISABLE TRIGGER ALL;



ALTER TABLE address ENABLE TRIGGER ALL;

--
-- Data for Name: category; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE category DISABLE TRIGGER ALL;



ALTER TABLE category ENABLE TRIGGER ALL;

--
-- Data for Name: city; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE city DISABLE TRIGGER ALL;



ALTER TABLE city ENABLE TRIGGER ALL;

--
-- Data for Name: country; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE country DISABLE TRIGGER ALL;



ALTER TABLE country ENABLE TRIGGER ALL;

--
-- Data for Name: customer; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE customer DISABLE TRIGGER ALL;



ALTER TABLE customer ENABLE TRIGGER ALL;

--
-- Data for Name: film; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE film DISABLE TRIGGER ALL;



ALTER TABLE film ENABLE TRIGGER ALL;

--
-- Data for Name: film_actor; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE film_actor DISABLE TRIGGER ALL;



ALTER TABLE film_actor ENABLE TRIGGER ALL;

--
-- Data for Name: film_category; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE film_category DISABLE TRIGGER ALL;



ALTER TABLE film_category ENABLE TRIGGER ALL;

--
-- Data for Name: inventory; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE inventory DISABLE TRIGGER ALL;



ALTER TABLE inventory ENABLE TRIGGER ALL;

--
-- Data for Name: language; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE language DISABLE TRIGGER ALL;



ALTER TABLE language ENABLE TRIGGER ALL;

--
-- Data for Name: payment; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE payment DISABLE TRIGGER ALL;



ALTER TABLE payment ENABLE TRIGGER ALL;

--
-- Data for Name: payment_p2007_01; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE payment_p2007_01 DISABLE TRIGGER ALL;



ALTER TABLE payment_p2007_01 ENABLE TRIGGER ALL;

--
-- Data for Name: payment_p2007_02; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE payment_p2007_02 DISABLE TRIGGER ALL;



ALTER TABLE payment_p2007_02 ENABLE TRIGGER ALL;

--
-- Data for Name: payment_p2007_03; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE payment_p2007_03 DISABLE TRIGGER ALL;



ALTER TABLE payment_p2007_03 ENABLE TRIGGER ALL;

--
-- Data for Name: payment_p2007_04; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE payment_p2007_04 DISABLE TRIGGER ALL;



ALTER TABLE payment_p2007_04 ENABLE TRIGGER ALL;

--
-- Data for Name: payment_p2007_05; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE payment_p2007_05 DISABLE TRIGGER ALL;



ALTER TABLE payment_p2007_05 ENABLE TRIGGER ALL;

--
-- Data for Name: payment_p2007_06; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE payment_p2007_06 DISABLE TRIGGER ALL;



ALTER TABLE payment_p2007_06 ENABLE TRIGGER ALL;

--
-- Data for Name: rental; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE rental DISABLE TRIGGER ALL;



ALTER TABLE rental ENABLE TRIGGER ALL;

--
-- Data for Name: staff; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE staff DISABLE TRIGGER ALL;



ALTER TABLE staff ENABLE TRIGGER ALL;

--
-- Data for Name: store; Type: TABLE DATA; Schema: public; Owner: postgres
--

ALTER TABLE store DISABLE TRIGGER ALL;

INSERT INTO store (store_id, name, manager_staff_id, address_id, last_update) VALUES (1, 'MySakila', 1, 1, '2006-02-15 09:57:12');
INSERT INTO store (store_id, name, manager_staff_id, address_id, last_update) VALUES (2, 'MySQL', 2, 2, '2006-02-15 09:57:12');

ALTER TABLE store ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

