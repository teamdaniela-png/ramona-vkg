% Learning rules with exceptions, written directly in ASP (a small ILP search solved by clingo).
%
% Hypothesis space:   positive(O) :- D(O), not ab(O, D).        up to max_defaults default rules
%                     ab(O, D)    :- E(O).                       up to max_exceptions exceptions per default
% where D ranges over default_candidate/1 and E over exception_candidate/1.
% clingo picks the hypothesis with the fewest misclassified training examples,
% paying rule_cost for every default and every exception it keeps.
%
% Input: feat(O, F), example(O), pos(O), default_candidate(F), exception_candidate(F).

#defined exception_candidate/1.

#const max_defaults = 2.
#const max_exceptions = 2.
#const rule_cost = 2.

{ in(D) : default_candidate(D) } max_defaults.
{ ex(D, E) : exception_candidate(E), E != D } max_exceptions :- in(D).

ab(O, D)    :- ex(D, E), feat(O, E), example(O).
positive(O) :- in(D), feat(O, D), not ab(O, D), example(O).

error(O) :- example(O), pos(O), not positive(O).
error(O) :- example(O), not pos(O), positive(O).

% an exception has to block something, and a default has to cover something
:- ex(D, E), not blocks(D, E).
blocks(D, E) :- ex(D, E), feat(O, D), feat(O, E), example(O).

#minimize { 1, O : error(O) ; rule_cost, D : in(D) ; rule_cost, D, E : ex(D, E) }.

#show in/1.
#show ex/2.
