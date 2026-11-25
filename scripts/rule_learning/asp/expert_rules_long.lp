% The expert rules written out in full: every exception appears in the body as an explicit negation.
% Each rule here is longer than in expert_rules.lp, where a component is "trigger, not ab(O)" and the
% exceptions are separate rules. The two files say the same thing; check_long_rules.py loads both and
% Clingo confirms that l(O, N) and holds(O, N) coincide on every offer.
% The definitions (verified_employer, personal_channel, pay_high, moves_person, verifiable_recruiter)
% are the ones of expert_rules.lp. `not` is negation as failure.

% ---- 1. High pay.
%      Alert when the employer is not verified; or when it is verified but the offer asks for no
%      experience, is not a specialised post, is not a security post, and is not a sales job
%      (or is a sales job reached through a personal channel).
l(O, 1) :- pay_high(O), not verified_employer(O).
l(O, 1) :- pay_high(O), verified_employer(O), not requires_experience(O), not specialised_role(O),
           not security(O), not sales(O).
l(O, 1) :- pay_high(O), verified_employer(O), not requires_experience(O), not specialised_role(O),
           not security(O), sales(O), personal_channel(O).

% ---- 2. Urgent hiring (the "urgent" badge of a formal job board does not count).
l(O, 2) :- has(O, contratacion_urgente), not portal_badge_only(O), not verified_employer(O).
l(O, 2) :- has(O, contratacion_urgente), not portal_badge_only(O), verified_employer(O),
           not operational_role(O), not internship(O), not security(O), not sales(O).
l(O, 2) :- has(O, contratacion_urgente), not portal_badge_only(O), verified_employer(O),
           not operational_role(O), not internship(O), not security(O), sales(O), not seasonal(O).
l(O, 2) :- has(O, contratacion_urgente), not portal_badge_only(O), verified_employer(O),
           not operational_role(O), not internship(O), not security(O), sales(O), seasonal(O),
           not large_verified_employer(O).

% ---- 3. Urgent hiring with no experience needed.
l(O, 3) :- has(O, contratacion_urgente), has(O, sin_experiencia), not portal_badge_only(O),
           not verified_employer(O).
l(O, 3) :- has(O, contratacion_urgente), has(O, sin_experiencia), not portal_badge_only(O),
           verified_employer(O), not operational_role(O), not internship(O), not security(O),
           not entry_level(O), not sales(O).
l(O, 3) :- has(O, contratacion_urgente), has(O, sin_experiencia), not portal_badge_only(O),
           verified_employer(O), not operational_role(O), not internship(O), not security(O),
           not entry_level(O), sales(O), not seasonal(O).
l(O, 3) :- has(O, contratacion_urgente), has(O, sin_experiencia), not portal_badge_only(O),
           verified_employer(O), not operational_role(O), not internship(O), not security(O),
           not entry_level(O), sales(O), seasonal(O), not large_verified_employer(O).

% ---- 4. The offer arrives without the person having looked for it.
l(O, 4) :- unsolicited_contact(O), not contact_agreed_with_recruiter(O), not verifiable_recruiter(O).

% ---- 5. The only way in is a personal channel.
l(O, 5) :- personal_channel(O), not verified_employer(O).

% ---- 6. The person has to put up money to work.
l(O, 6) :- asks_for_money(O).

% ---- 7. The offer does not say what the job is.
l(O, 7) :- no_job_described(O), not verifiable_recruiter(O).

% ---- 8. It uses the name or logo of someone else.
l(O, 8) :- borrowed_name(O).

% ---- 9. Another state, or the transport is paid for.
l(O, 9) :- moves_person(O), not verified_employer(O).

% ---- 10. The real job is not the one advertised (known only after contact).
l(O, 10) :- different_job(O).

% ---- 11. A job the Consejo Ciudadano reports as bait for trafficking.
l(O, 11) :- trafficking_risk_role(O), not verified_employer(O).

% ---- 12. A security post.
l(O, 12) :- security(O), not verified_employer(O).

% ---- 13. "Good presentation" and no job described.
l(O, 13) :- appearance_required(O), no_job_described(O).

% ---- 14. Documents or bank details before any interview.
l(O, 14) :- asks_for_documents(O).

% ---- 15. Download or install something, or do a job test.
l(O, 15) :- asks_to_download(O), not verified_employer(O).

% ---- 16. The person is sent to a place that is not an established workplace.
l(O, 16) :- unestablished_meeting_place(O).

% ---- 17. Addressed only to women or to an age range.
l(O, 17) :- women_or_age_targeted(O), not verified_employer(O).

% ---- Version 2 (24-nov-2026).
% ---- 18. Asks for a photo of the person, and the employer is not verified.
l(O, 18) :- asks_for_photo(O), not verified_employer(O).

% ---- 19. Uses codes or emojis of criminal groups.
l(O, 19) :- coded_language(O).

% ---- 20. Never names the employer and circulates on a social network or a personal channel.
l(O, 20) :- employer_never_named(O), social_network(O).
l(O, 20) :- employer_never_named(O), personal_channel(O).
l(O, 20) :- employer_never_named(O), direct_message(O).

% ---- 21. High pay with no employer named, no experience asked or no job described.
l(O, 21) :- pay_high(O), employer_never_named(O).
l(O, 21) :- pay_high(O), has(O, sin_experiencia).
l(O, 21) :- pay_high(O), no_job_described(O).

% ---- 22. A job used as bait in the press cases, and the employer is not verified (only asks to verify).
l(O, 22) :- recruitment_role(O), not verified_employer(O).

% ---- Levels. 10 is not a warning: the person is already in it.
l_alerta(O)   :- l(O, N), N != 10, N != 1, N != 2, N != 3, N != 4, N != 5, N != 7, N != 11, N != 12, N != 15, N != 22.
l_verifica(O) :- l(O, N), N != 10, not l_alerta(O).
l_escalar(O)  :- l(O, 10).

#show l/2.
