% Expert rules with exceptions (answer set programming, clingo syntax). Version 2, 24-nov-2026.
% Written from the components Daniela Camberos gave as the domain expert.
% Facts: offers.lp (build_facts.py) and expert_facts.lp (build_expert_facts.py).
% `not` is negation as failure: a component holds unless a more specific rule blocks it.

#defined contact_agreed_with_recruiter/1.
#defined unsolicited_contact/1.
#defined internship/1.
#defined entry_level/1.
#defined seasonal/1.
#defined sales/1.
#defined security/1.
#defined operational_role/1.
#defined job_board_posting/1.
#defined personal_contact/1.
#defined employer_verified/1.
#defined intermediary/1.
#defined expert_doubtful/1.
#defined asks_for_photo/1.
#defined coded_language/1.
#defined recruitment_role/1.
#defined employer_never_named/1.
#defined social_network/1.
#defined direct_message/1.
#defined no_job_described/1.

verified_employer(O) :- verified_posting(O).
verified_employer(O) :- large_verified_employer(O).
verified_employer(O) :- employer_verified(O).
% A recruitment agency that exists counts as a verified employer even when it does not name its client:
% clients often ask for confidentiality, and that does not make the offer false (expert, 24-nov-2026).
% In the data, `verificacion` of an agency posting refers to the agency, so employer_verified already covers it.
% It is not enough that a company exists when the account that publishes is not the company's: many offers use
% the name of a real company to hook people (expert, 24-nov-2026). Those postings carry verificacion = dudas.

% ---- An employer that advertises on social media counts as verified when the post carries
%      one strong signal, or two of the weaker ones. The signals are the domain expert's.
strong_signal(pagina_propia_con_seguidores; pagina_oficial_con_seguidores; pagina_verificada;
              correo_corporativo; sucursal_verificable).
weak_signal(sitio_propio; direccion_de_sucursal; persona_con_nombre; varios_canales;
            perfil_especifico; pagina_de_reclutamiento; cita_en_oficina_publica).
validated_on_social(O) :- validation_signal(O, S), strong_signal(S).
validated_on_social(O) :- validation_signal(O, S1), validation_signal(O, S2), weak_signal(S1), weak_signal(S2), S1 < S2.
verified_employer(O) :- validated_on_social(O).

% ---- A recruiter is verifiable when the profile is a built one: it has followers, it shows
%      activity, and it is related to the vacancy. All three are needed. Given by the domain expert.
recruiter_signal(con_seguidores; con_actividad; relacionado_con_la_vacante).
verifiable_recruiter(O) :- recruiter_profile(O, con_seguidores), recruiter_profile(O, con_actividad),
                           recruiter_profile(O, relacionado_con_la_vacante).
#show verifiable_recruiter/1.
#show validated_on_social/1.

personal_channel(O) :- personal_contact(O).
personal_channel(O) :- has(O, whatsapp_sin_logo).
personal_channel(O) :- has(O, messenger_a_whatsapp).

pay_high(O) :- has(O, sueldo_alto).
pay_high(O) :- high_pay(O).

% ---- Component 1. High pay,
%      unless the offer asks for experience and the employer is verified,
%      unless it is a sales, promoter or demonstrator job at a verified employer that is not
%      reached through a personal channel (the published top figure includes commission),
%      unless it is a highly specialised post (doctorate, mathematics, computer science, AI) at a verified employer,
%      unless it is a security guard post at a verified employer.
c1_default(O) :- pay_high(O).
c1(O)    :- pay_high(O), not ab_c1(O).
ab_c1(O) :- requires_experience(O), verified_employer(O).
ab_c1(O) :- sales(O), verified_employer(O), not personal_channel(O).
ab_c1(O) :- specialised_role(O), verified_employer(O).
ab_c1(O) :- security(O), verified_employer(O).

% ---- Component 2. Urgent hiring,
%      unless it is a seasonal sales job at a large, verified employer,
%      unless it is an operational post at a verified employer, large or small,
%      unless it is an internship at a verified employer,
%      unless it is a security guard post at a verified employer,
%      unless the only urgency is the "urgent" badge that a formal job board puts on the posting
%      (the badge does not count; urgency written in the offer does, and so does any urgency
%      on social networks, where people are recruited).
c2_default(O) :- has(O, contratacion_urgente).
c2(O)    :- has(O, contratacion_urgente), not ab_c2(O).
ab_c2(O) :- sales(O), seasonal(O), large_verified_employer(O).
ab_c2(O) :- operational_role(O), verified_employer(O).
ab_c2(O) :- internship(O), verified_employer(O).
ab_c2(O) :- security(O), verified_employer(O).
ab_c2(O) :- portal_badge_only(O).

% ---- Component 3. Urgent hiring with no experience needed,
%      unless the exception of component 2 holds,
%      unless the post is entry level or an internship at a verified employer.
c3_default(O) :- has(O, contratacion_urgente), has(O, sin_experiencia).
c3(O)    :- has(O, contratacion_urgente), has(O, sin_experiencia), not ab_c3(O).
ab_c3(O) :- ab_c2(O).
ab_c3(O) :- entry_level(O), verified_employer(O).
ab_c3(O) :- internship(O), verified_employer(O).

% ---- Component 4. An offer that arrives by WhatsApp or e-mail without the person having looked
%      for a job,
%      unless the person agreed with the recruiter to talk through that channel,
%      unless it is a recruiter on a professional network with a real profile and a verifiable employer.
c4_default(O) :- unsolicited_contact(O).
c4(O)    :- unsolicited_contact(O), not ab_c4(O).
ab_c4(O) :- contact_agreed_with_recruiter(O).
ab_c4(O) :- verifiable_recruiter(O).

% ---- Component 5. The only way in is a personal channel (a WhatsApp number, a private message,
%      a Hotmail or Gmail address),
%      unless the employer is verified.
c5_default(O) :- personal_channel(O).
c5(O)    :- personal_channel(O), not ab_c5(O).
ab_c5(O) :- verified_employer(O).

% ---- Component 6. The person has to put up money to work (buy the products, pay to release
%      the pay). A job does not charge for working.
c6_default(O) :- asks_for_money(O).
c6(O)    :- asks_for_money(O).

% ---- Component 7. The offer does not say what the job is.
c7_default(O) :- no_job_described(O).
c7(O)    :- no_job_described(O), not ab_c7(O).
% A verifiable recruiter on a professional network often does not name the post in the first message.
ab_c7(O) :- verifiable_recruiter(O).

% ---- Component 8. The offer uses the name or logo of a brand or public body that is not the
%      one publishing it.
c8_default(O) :- borrowed_name(O).
c8(O)    :- borrowed_name(O).

% ---- Component 9. The job is in another state or the transport is paid for,
%      unless the employer is verified (a real employer can offer a post at another branch).
moves_person(O) :- has(O, empleo_fuera_estado).
moves_person(O) :- has(O, traslado_pagado).
moves_person(O) :- relocation(O).
c9_default(O) :- moves_person(O).
c9(O)    :- moves_person(O), not ab_c9(O).
ab_c9(O) :- verified_employer(O).

% ---- Component 10. The real job is not the one advertised. This is known only after contact
%      (at the "training" or the interview), not from the text of the offer.
c10_default(O) :- different_job(O).
c10(O)    :- different_job(O).

% ---- Component 11. The job is one of those the Consejo Ciudadano reports as the false offers
%      used to hook trafficking victims (waitress, receptionist, masseuse, maid, domestic service,
%      care work, adult entertainment), unless the employer is verified.
c11_default(O) :- trafficking_risk_role(O).
c11(O)    :- trafficking_risk_role(O), not ab_c11(O).
ab_c11(O) :- verified_employer(O).

% ---- Component 12. A security post (guard, escort, bodyguard driver), unless the employer is verified.
%      Security guard is the most frequent bait in the press offers the expert labelled as danger.
c12_default(O) :- security(O).
c12(O)    :- security(O), not ab_c12(O).
ab_c12(O) :- verified_employer(O).

% ---- Component 13. It asks for "good presentation" and does not say what the job is.
c13_default(O) :- appearance_required(O), no_job_described(O).
c13(O)    :- appearance_required(O), no_job_described(O).

% ---- Component 14. It asks for personal documents or bank details before any interview.
c14_default(O) :- asks_for_documents(O).
c14(O)    :- asks_for_documents(O).

% ---- Component 15. It asks to download or install something, or to do a job test,
%      unless the employer is verified.
c15_default(O) :- asks_to_download(O).
c15(O)    :- asks_to_download(O), not ab_c15(O).
ab_c15(O) :- verified_employer(O).

% ---- Component 16. The person is told to come to a place that is not an established workplace:
%      a bus terminal, a ranch, a house, a hotel, a car park, a fast-food restaurant.
c16_default(O) :- unestablished_meeting_place(O).
c16(O)    :- unestablished_meeting_place(O).

% ---- Component 17. The offer is addressed only to women or to an age range, unless the employer is verified.
c17_default(O) :- women_or_age_targeted(O).
c17(O)    :- women_or_age_targeted(O), not ab_c17(O).
ab_c17(O) :- verified_employer(O).

% ---- Version 2 (24-nov-2026), after the second blind test. Components 18 to 22 are new.

% ---- Component 18. It asks for a photo of the person, unless the employer is verified.
%      A photo is not a document: an events agency may ask for one (expert, 24-nov-2026).
c18_default(O) :- asks_for_photo(O).
c18(O)    :- asks_for_photo(O), not ab_c18(O).
ab_c18(O) :- verified_employer(O).

% ---- Component 19. It uses the codes or emojis of criminal groups ("pollitos": migrants or newly
%      recruited youths; rooster, ninja, pizza, "4 letras", #maña...).
c19_default(O) :- coded_language(O).
c19(O)    :- coded_language(O).

% ---- Component 20. The employer is never named and the offer circulates on a social network or a personal channel.
c20_default(O) :- employer_never_named(O).
c20(O)    :- employer_never_named(O), social_network(O).
c20(O)    :- employer_never_named(O), personal_channel(O).
c20(O)    :- employer_never_named(O), direct_message(O).

% ---- Component 21. High pay together with no employer named, no clear experience or no job described.
%      In the press cases, 56 of the 87 with high pay have at least one of the three; 4 of 309 legitimate postings do.
c21_default(O) :- pay_high(O), employer_never_named(O).
c21_default(O) :- pay_high(O), has(O, sin_experiencia).
c21_default(O) :- pay_high(O), no_job_described(O).
c21(O)    :- c21_default(O).

% ---- Component 22. A job that appears as bait in the press cases (security, waiting and bar work, events,
%      field work, construction, kitchen, domestic work, cleaning, call centre, driver),
%      unless the employer is verified. Alone it only asks the person to verify: these jobs are not to be stigmatised.
c22_default(O) :- recruitment_role(O).
c22(O)    :- recruitment_role(O), not ab_c22(O).
ab_c22(O) :- verified_employer(O).

holds(O, 18) :- c18(O).  holds(O, 19) :- c19(O).  holds(O, 20) :- c20(O).  holds(O, 21) :- c21(O).  holds(O, 22) :- c22(O).
holds_default(O, 18) :- c18_default(O).  holds_default(O, 19) :- c19_default(O).  holds_default(O, 20) :- c20_default(O).
holds_default(O, 21) :- c21_default(O).  holds_default(O, 22) :- c22_default(O).

% ---- Three levels (expert, 24-nov-2026).
%      alerta:   at least one strong component.
%      verifica: only weak components: the person should check the employer before going on.
%      escalar:  component 10, the real job is another one. It is known only after arriving, so it does not warn
%                about an offer: it means the person is already in it and has to be referred.
strong(6;8;9;13;14;16;17;18;19;20;21).
weak(1;2;3;4;5;7;11;12;15;22).
alerta(O)   :- holds(O, N), strong(N).
verifica(O) :- holds(O, N), weak(N), not alerta(O).
escalar(O)  :- holds(O, 10).
#show alerta/1.  #show verifica/1.  #show escalar/1.

% ---- How many components an offer has, with and without the exceptions.
component(1..22).
holds(O, 16) :- c16(O).  holds(O, 17) :- c17(O).
holds_default(O, 16) :- c16_default(O).  holds_default(O, 17) :- c17_default(O).
holds(O, 11) :- c11(O).  holds(O, 12) :- c12(O).  holds(O, 13) :- c13(O).  holds(O, 14) :- c14(O).  holds(O, 15) :- c15(O).
holds_default(O, 11) :- c11_default(O).  holds_default(O, 12) :- c12_default(O).  holds_default(O, 13) :- c13_default(O).  holds_default(O, 14) :- c14_default(O).  holds_default(O, 15) :- c15_default(O).
holds(O, 1) :- c1(O).  holds(O, 2) :- c2(O).  holds(O, 3) :- c3(O).  holds(O, 4) :- c4(O).  holds(O, 5) :- c5(O).  holds(O, 6) :- c6(O).  holds(O, 7) :- c7(O).  holds(O, 8) :- c8(O).  holds(O, 9) :- c9(O).  holds(O, 10) :- c10(O).
holds_default(O, 1) :- c1_default(O).  holds_default(O, 2) :- c2_default(O).
holds_default(O, 3) :- c3_default(O).  holds_default(O, 4) :- c4_default(O).
holds_default(O, 5) :- c5_default(O).  holds_default(O, 6) :- c6_default(O).  holds_default(O, 7) :- c7_default(O).  holds_default(O, 8) :- c8_default(O).  holds_default(O, 9) :- c9_default(O).  holds_default(O, 10) :- c10_default(O).
n_components(O, N)         :- offer(O), N = #count { C : holds(O, C) }.
n_components_default(O, N) :- offer(O), N = #count { C : holds_default(O, C) }.

#show holds/2.  #show holds_default/2.  #show n_components/2.  #show n_components_default/2.
