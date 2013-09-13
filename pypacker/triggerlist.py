"""TriggerList for handling dynamic headers."""

import logging

logger = logging.getLogger("pypacker")

class TriggerList(list):
	"""
	List with trigger-capabilities representing dynamic header.
	This list can contain raw bytes, tuples or packets representing individual
	header fields. Format Changes to packets in this list aren't allowed after adding.
	_tuples_to_packets() can be overwritten for auto-creating packets using tuples.
	Using bytes or tuples "_pack()" must be overwritten to reassemble bytes.
	A TriggerList must be initiated using the no-parameter constructor and modified
	by using append/extend/del etc.
	"""
	def __init__(self, lst=[], clz=None):
		# set by external Packet
		self.packet = None
		self._cached_result = None
		# a triggerlist is _never_ initiated using constructors
		if len(lst) > 0:
			raise Exception("TriggerList initiated using non-empty list, don't do this!")
		super().__init__([])

	def __iadd__(self, v):
		"""Item can be added using '+=', use 'append()' instead."""
		if type(v) is tuple:
			v = self._tuples_to_packets([v])[0]
		super().append(v)
		self.__handle_mod([v])
		return self

	def __setitem__(self, k, v):
		if type(v) is tuple:
			v = self._tuples_to_packets([v])[0]
		try:
			# remove listener from old packet which gets overwritten
			self[k].remove_change_listener(None, remove_all=True)
		except:
			pass
		super().__setitem__(k, v)
		self.__handle_mod([v])

	# Listener doesn't get removed, assume Packet as header doesn't get reused
	#def __delitem__(self, k):
	#	pass

	def append(self, v):
		if type(v) is tuple:
			v = self._tuples_to_packets([v])[0]
		super().append(v)
		self.__handle_mod([v])

	def extend(self, v):
		if len(v) > 0 and type(v[0]) is tuple:
			v = self._tuples_to_packets(v)

		super().extend(v)
		self.__handle_mod(v)

	def insert(self, pos, v):
		if type(v) is tuple:
			v = self._tuples_to_packets([v])[0]

		super().insert(pos, v)
		self.__handle_mod([v])

	def find_by_id(self, id):
		"""
		Advanced list search for tuple-lists:
		Return all tuples in list with t[0]==id
		"""
		return [v for v in self if v[0] == id]		
	#
	#

	def __handle_mod(self, val):
		"""
		Handle modifications of TriggerList.
		val -- list of bytes, tuples or packets
		"""
		try:
			for v in val:
				v.remove_change_listener(None, remove_all=True)
				v.add_change_listener(self._notify_change)
		# This will fail if val is no packet
		except AttributeError:
			pass

		self._notify_change(val, force_fmt_update=True)
		self._handle_mod(val)

	def _handle_mod(self, val):
		"""
		Handle modifications of tirggerlist (adding, removing etc) for advanced
		header field handling eg IP->offset.

		val -- list of bytes, tuples or Packets
		"""
		pass

	def _tuples_to_packets(self, tuple_list):
		"""
		Convert the given tuple list to a list of packets. This enables convenient
		adding of new fields like IP options using tuples. This function will return
		the original tuple list itself if not overwritten.
		"""
		return tuple_list

	def _notify_change(self, pkt, force_fmt_update=False):
		"""
		Called by informers eg Packets in this list. Reset caches and set correct states
		on Packet containing this TrigerList.
		"""
		try:
			# Structure has changed so we need to recalculate the whole format
			if force_fmt_update or pkt.body_changed:
				self.packet._header_format_changed = True
			# header and/or body changed, clear cache
			self.packet.header_changed = True
		# this only works on Packets
		except AttributeError:
			pass
		# old cache of TriggerList not usable anymore
		self._cached_result = None

	def pack(self):
		"""Called by packet on packeting non-Packet TriggerLists."""
		if self._cached_result is None:
			self._cached_result = self._pack()

		return self._cached_result

	def _pack(self):
		"""
		This must be overwritten to pack textual dynamic headerfields eg HTTP.
		The basic implemenation just concatenates all bytes without change.
		"""
		return b"".join(self)
