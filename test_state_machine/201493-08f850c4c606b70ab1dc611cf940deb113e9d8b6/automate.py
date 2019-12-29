#!/usr/bin/env python
#coding=utf8

from automatelib import State, Transition, Automaton, EpsilonTransition


if __name__ == '__main__':
	# Automate de test acceptant l'alphabet {a, b, c} et dont les mots
	# commencent et finissent forcément par a.
	#~ s1 = State('1')
	#~ s2 = State('2')
	#~ s3 = State('3')
	#~ s4 = State('4')
	#~ s5 = State('5')
	#~ s6 = State('6')
	#~ s7 = State('7')
	#~ s8 = State('8')
	#~ s9 = State('9')
	#~ s10 = State('10')
	#~ a = Automaton('abc', 
		#~ states=(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10), 
		#~ initial_states=(s1, s2, s3), 
		#~ final_states=(s7, s8, s9)
	#~ )
	#~ 
	#~ a.add_transition(Transition(s1, s1, 'abc'))
	#~ a.add_transition(Transition(s1, s4, 'a'))
	#~ a.add_transition(Transition(s4, s4, 'abc'))
	#~ a.add_transition(Transition(s4, s7, 'a'))
	#~ 
	#~ a.add_transition(Transition(s2, s2, 'abc'))
	#~ a.add_transition(Transition(s2, s5, 'b'))
	#~ a.add_transition(Transition(s5, s5, 'abc'))
	#~ a.add_transition(Transition(s5, s8, 'b'))
#~ 
	#~ a.add_transition(Transition(s3, s3, 'abc'))
	#~ a.add_transition(Transition(s3, s6, 'c'))
	#~ a.add_transition(Transition(s6, s6, 'abc'))
	#~ a.add_transition(Transition(s6, s9, 'c'))
#~ 
	#~ a.add_transition(EpsilonTransition(s1, s10))
	#~ a.add_transition(EpsilonTransition(s10, s7))
	
	a = State('a')
	a2 = State('a2')
	
	b1 = State('b1')
	b2 = State('b2')
	b3 = State('b3')
	
	found = State('found')
	deuxieme = State('deuxieme')
	
	da1 = State('da1')
	da11 = State('da11')
	da12 = State('da12')
	da13 = State('da13')
	
	done = State('done')
	anothera = State('anothera')
	
	automaton = Automaton('ab',
		states = (a, a2, b1, b2, b3, found, deuxieme, da1, da11, da12, da13, done, anothera),
		initial_states = (a,),
		final_states = (found, )
	)
	automaton.add_transition(Transition(a, a, 'ab'))

	automaton.add_transition(Transition(a, b1, 'a'))
	automaton.add_transition(Transition(b1, b2, 'b'))
	automaton.add_transition(Transition(b2, b3, 'b'))
	automaton.add_transition(Transition(b3, a2, 'a'))
	automaton.add_transition(Transition(a2, found, 'a'))

	automaton.add_transition(Transition(found, found, 'b'))
	automaton.add_transition(EpsilonTransition(found, deuxieme))

	automaton.add_transition(Transition(deuxieme, da1, 'a'))
	automaton.add_transition(EpsilonTransition(da1, da11))
	automaton.add_transition(EpsilonTransition(da11, da12))
	automaton.add_transition(EpsilonTransition(da12, da13))
	automaton.add_transition(EpsilonTransition(da1, da13))
	automaton.add_transition(Transition(da13, done, 'a'))
	automaton.add_transition(Transition(da12, found, 'a'))

	automaton.add_transition(Transition(done, anothera, 'a'))

	automaton.add_transition(EpsilonTransition(anothera, a2))
	automaton.add_transition(Transition(anothera, da12, 'a'))
