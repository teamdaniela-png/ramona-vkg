% Rules with exceptions over the documented offers (answer set programming, clingo syntax).
% Facts come from offers.lp, written by build_facts.py. `not` is negation as failure:
% a rule applies unless a more specific rule blocks it.

% ---- Example 1. Pay well above the verified postings is an alert,
%      unless the job is a driver post that states its requirements,
%      unless that post also says no experience is needed.
alert_pay_default(O) :- high_pay(O).

alert_pay(O)  :- high_pay(O), not ab_pay(O).
ab_pay(O)     :- high_pay(O), driver(O), requirements(O), not ab_driver(O).
ab_driver(O)  :- has(O, sin_experiencia).

% ---- Example 2. Among documented traps, a promise of high pay points to criminal recruitment,
%      unless an advance payment is asked (economic fraud),
%      unless the offer is aimed at women (no conclusion).
kind_pay_default(O, criminal) :- has(O, sueldo_alto).

kind_pay(O, criminal) :- has(O, sueldo_alto), not ab_kind_pay(O).
kind_pay(O, fraud)    :- has(O, sueldo_alto), has(O, pago_adelantado).
ab_kind_pay(O)        :- has(O, pago_adelantado).
ab_kind_pay(O)        :- target(O, women).

% ---- Example 3. An ordinary-sounding job used as the hook points to criminal recruitment,
%      unless the offer is aimed at women (sexual exploitation).
kind_role_default(O, criminal) :- has(O, rol_plausible_gancho).

kind_role(O, criminal) :- has(O, rol_plausible_gancho), not ab_kind_role(O).
kind_role(O, sexual)   :- has(O, rol_plausible_gancho), target(O, women).
ab_kind_role(O)        :- target(O, women).

#show alert_pay_default/1.  #show alert_pay/1.
#show kind_pay_default/2.   #show kind_pay/2.
#show kind_role_default/2.  #show kind_role/2.
